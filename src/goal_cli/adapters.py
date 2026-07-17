from __future__ import annotations

import json
import os
import signal
import shlex
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from .config import (
    API_TIK_BASE_URL_ENV_VARS,
    API_TIK_KEY_ENV_VARS,
    COMMAND_TIK_PROVIDERS,
    DEFAULT_API_TIK_BASE_URL,
    DEFAULT_API_TIK_MODEL,
    GoalConfig,
    TikConfig,
    api_tik_value_source,
    resolve_tik_skill_path,
)

if TYPE_CHECKING:
    from .tok_execution import TokExecutionResult


@dataclass(frozen=True)
class ProducerOutcome:
    ok: bool


@dataclass(frozen=True)
class TikOutcome:
    memo_path: Path | None


class GoalProviderAdapters(Protocol):
    def produce_artifact(self, config: GoalConfig, run_dir: Path, timeout_seconds: float | None = None) -> ProducerOutcome:
        pass

    def run_tik(self, config: GoalConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> TikOutcome:
        pass

    def execute_tok(self, config: GoalConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> "TokExecutionResult":
        pass


@dataclass(frozen=True)
class ProductionGoalProviderAdapters:
    def produce_artifact(self, config: GoalConfig, run_dir: Path, timeout_seconds: float | None = None) -> ProducerOutcome:
        containment_root = config.root if config.perpetual.enabled else None
        return ProducerOutcome(
            run_shell_logged(
                config.producer.command,
                config.root,
                run_dir / "producer.log",
                timeout_seconds=timeout_seconds,
                containment_root=containment_root,
            )
        )

    def run_tik(self, config: GoalConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> TikOutcome:
        return TikOutcome(
            run_tik(
                config.tik,
                config.root,
                config.artifact.path,
                prompt,
                run_dir,
                config.tik.label,
                config.artifact.copy_as,
                timeout_seconds=timeout_seconds,
                containment_root=config.root if config.perpetual.enabled and config.tik.provider in COMMAND_TIK_PROVIDERS else None,
            )
        )

    def execute_tok(self, config: GoalConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> "TokExecutionResult":
        from .tok_execution import execute_tok

        return execute_tok(config.tok, prompt, run_dir, timeout_seconds=timeout_seconds)


def run_shell_logged(
    command_text: str,
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
    timeout_seconds: float | None = None,
    containment_root: Path | None = None,
) -> bool:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {command_text}\n# cwd: {cwd}\n\n")
        log_file.flush()
        if _timeout_exhausted(timeout_seconds, log_file):
            return False
        contained_command = build_contained_shell_command(command_text, containment_root) if containment_root is not None else None
        if containment_root is not None and contained_command is None:
            log_file.write("ERROR: no supported mutation containment backend is available.\n")
            return False
        try:
            process = subprocess.Popen(
                contained_command or command_text,
                cwd=cwd,
                shell=contained_command is None,
                executable="/bin/bash" if contained_command is None else None,
                stdin=subprocess.PIPE if stdin is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=run_env,
                start_new_session=True,
            )
        except OSError as exc:
            _log_launch_error(log_file, exc)
            return False
        return _communicate_logged(process, log_file, stdin, timeout_seconds)


def run_command_logged(command: list[str], cwd: Path, log_path: Path, stdin: str, timeout_seconds: float | None = None) -> bool:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(shlex.quote(part) for part in command)}\n# cwd: {cwd}\n\n")
        log_file.flush()
        if _timeout_exhausted(timeout_seconds, log_file):
            return False
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        except OSError as exc:
            _log_launch_error(log_file, exc)
            return False
        return _communicate_logged(process, log_file, stdin, timeout_seconds)


def run_tik(
    config: TikConfig,
    root: Path,
    artifact_path: Path,
    prompt: str,
    run_dir: Path,
    label: str,
    artifact_copy_as: str | None,
    timeout_seconds: float | None = None,
    containment_root: Path | None = None,
) -> Path | None:
    output_path = run_dir / f"{label}_memo.md"
    (run_dir / f"{label}_prompt.md").write_text(prompt, encoding="utf-8")
    if config.provider in COMMAND_TIK_PROVIDERS:
        env = {
            "GOAL_ARTIFACT": str(artifact_path),
            "GOAL_TIK_PROMPT": prompt,
            "GOAL_RUN_DIR": str(run_dir),
        }
        ok = run_shell_logged(
            config.command or "",
            root,
            run_dir / f"{label}_command.log",
            env=env,
            timeout_seconds=timeout_seconds,
            containment_root=containment_root,
        )
        if not ok:
            (run_dir / f"{label}_FAILED.txt").write_text("tik command failed\n", encoding="utf-8")
            return None
        log_text = (run_dir / f"{label}_command.log").read_text(encoding="utf-8")
        output_path.write_text(_stdout_without_header(log_text), encoding="utf-8")
        return output_path

    with tempfile.TemporaryDirectory(prefix="goal-artifact-tik-") as temp_dir:
        tik_dir = Path(temp_dir)
        copy_name = artifact_copy_as or artifact_path.name
        tik_artifact = tik_dir / copy_name
        shutil.copy2(artifact_path, tik_artifact)
        if config.provider == "api":
            model = effective_api_tik_model(config)
            try:
                api_prompt = build_api_tik_prompt(config, root, prompt)
            except OSError as exc:
                (run_dir / f"{label}_openai.log").write_text(f"ERROR: failed to read tik skill: {exc}\n", encoding="utf-8")
                ok = False
            except ValueError as exc:
                (run_dir / f"{label}_openai.log").write_text(f"ERROR: {exc}\n", encoding="utf-8")
                ok = False
            else:
                (run_dir / f"{label}_api_prompt.md").write_text(api_prompt, encoding="utf-8")
                ok = _openai_review(config, tik_artifact, api_prompt, output_path, run_dir / f"{label}_openai.log", model, timeout_seconds)
        elif config.provider == "codex_file":
            ok = _codex_file_review(config, tik_artifact, prompt, output_path, run_dir / f"{label}_codex_file.log", timeout_seconds)
        elif config.provider == "claude_code_file":
            ok = _claude_code_file_review(config, tik_artifact, prompt, output_path, run_dir / f"{label}_claude_code_file.log", timeout_seconds)
        else:
            raise ValueError(f"unsupported tik provider: {config.provider}")

    if not ok:
        (run_dir / f"{label}_FAILED.txt").write_text("tik provider failed\n", encoding="utf-8")
        return None
    return output_path


def mutation_containment_backend() -> str | None:
    if sys.platform == "darwin" and shutil.which("sandbox-exec"):
        return "sandbox-exec"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bwrap"
    return None


def build_contained_shell_command(
    command_text: str,
    containment_root: Path,
    *,
    backend: str | None = None,
) -> list[str] | None:
    backend = backend or mutation_containment_backend()
    root = str(containment_root.resolve(strict=False))
    if backend == "sandbox-exec":
        escaped_root = root.replace("\\", "\\\\").replace('"', '\\"')
        profile = (
            "(version 1)\n"
            "(allow default)\n"
            f'(deny file-write* (require-not (subpath "{escaped_root}")))\n'
        )
        return ["/usr/bin/sandbox-exec", "-p", profile, "/bin/bash", "-lc", command_text]
    if backend == "bwrap":
        return [
            "bwrap",
            "--die-with-parent",
            "--ro-bind",
            "/",
            "/",
            "--bind",
            root,
            root,
            "--tmpfs",
            "/tmp",
            "--chdir",
            root,
            "/bin/bash",
            "-lc",
            command_text,
        ]
    return None


def _codex_file_review(
    config: TikConfig,
    artifact_path: Path,
    prompt: str,
    output_path: Path,
    log_path: Path,
    timeout_seconds: float | None = None,
) -> bool:
    artifact_size = artifact_path.stat().st_size
    if artifact_size > config.max_file_size_bytes:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"ERROR: artifact is {artifact_size} bytes, larger than max_file_size_bytes={config.max_file_size_bytes}.\n",
            encoding="utf-8",
        )
        return False

    command = [
        "codex",
        "exec",
        "-C",
        str(artifact_path.parent),
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--output-last-message",
        str(output_path),
    ]
    if config.model:
        command.extend(["-m", config.model])
    command.append("-")

    effective_timeout = min(config.timeout_seconds, timeout_seconds) if timeout_seconds is not None else config.timeout_seconds
    ok = run_command_logged(command, artifact_path.parent, log_path, _file_review_prompt(prompt), timeout_seconds=effective_timeout)
    if not ok:
        return False
    if not output_path.exists():
        _append_log(log_path, "ERROR: codex_file did not write tik memo.\n")
        return False
    if not output_path.read_text(encoding="utf-8").strip():
        _append_log(log_path, "ERROR: codex_file wrote an empty tik memo.\n")
        return False
    return True


CLAUDE_CODE_DISALLOWED_TOOLS = "Write,Edit,MultiEdit,NotebookEdit,Bash"


def _claude_code_file_review(
    config: TikConfig,
    artifact_path: Path,
    prompt: str,
    output_path: Path,
    log_path: Path,
    timeout_seconds: float | None = None,
) -> bool:
    artifact_size = artifact_path.stat().st_size
    if artifact_size > config.max_file_size_bytes:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"ERROR: artifact is {artifact_size} bytes, larger than max_file_size_bytes={config.max_file_size_bytes}.\n",
            encoding="utf-8",
        )
        return False

    command = [
        "claude",
        "--print",
        "--output-format",
        "json",
        "--disallowedTools",
        CLAUDE_CODE_DISALLOWED_TOOLS,
    ]
    if config.model:
        command.extend(["--model", config.model])

    effective_timeout = min(config.timeout_seconds, timeout_seconds) if timeout_seconds is not None else config.timeout_seconds
    stdout = run_claude_print_logged(command, artifact_path.parent, log_path, _file_review_prompt(prompt), timeout_seconds=effective_timeout)
    if stdout is None:
        return False
    memo_text = _claude_code_result_text(stdout)
    if not memo_text.strip():
        _append_log(log_path, "\nERROR: claude_code_file returned no extractable result text.\n")
        return False
    output_path.write_text(memo_text, encoding="utf-8")
    return True


def run_claude_print_logged(
    command: list[str],
    cwd: Path,
    log_path: Path,
    stdin: str,
    timeout_seconds: float | None = None,
) -> str | None:
    """Run a claude --print command, keeping stdout apart from the log so the
    JSON envelope stays parseable. Returns stdout on success, None on failure."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(shlex.quote(part) for part in command)}\n# cwd: {cwd}\n\n")
        log_file.flush()
        if _timeout_exhausted(timeout_seconds, log_file):
            return None
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except OSError as exc:
            _log_launch_error(log_file, exc)
            return None
        try:
            stdout, stderr = process.communicate(input=stdin, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(process)
            stdout, stderr = process.communicate()
            if stdout:
                log_file.write(stdout)
            if stderr:
                log_file.write(stderr)
            timeout_label = f"{timeout_seconds:g}" if timeout_seconds is not None else "unknown"
            log_file.write(f"\nERROR: command timed out after {timeout_label} seconds.\n")
            return None
        if stdout:
            log_file.write(stdout)
        if stderr:
            log_file.write(stderr)
        if process.returncode != 0:
            log_file.write(f"\nERROR: claude exited with status {process.returncode}.\n")
            return None
        return stdout or ""


def claude_print_envelope(stdout: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or payload.get("is_error"):
        return None
    return payload


def _claude_code_result_text(stdout: str) -> str:
    payload = claude_print_envelope(stdout)
    if payload is None:
        return ""
    result = payload.get("result")
    if isinstance(result, str) and result.strip():
        return result.strip() + "\n"
    return ""


def _file_review_prompt(prompt: str) -> str:
    slash_command, body = _split_leading_slash_command(prompt)
    if slash_command:
        return f"{slash_command}\n\n{body}"
    return prompt


def _split_leading_slash_command(prompt: str) -> tuple[str | None, str]:
    lines = prompt.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("/") and " " not in stripped:
            return stripped, "\n".join(lines[index + 1 :]).lstrip()
        return None, prompt
    return None, prompt


def build_api_tik_prompt(config: TikConfig, root: Path, prompt: str) -> str:
    if not config.skill:
        return prompt
    skill_path = resolve_tik_skill_path(config.skill, root)
    if skill_path is None:
        raise ValueError(f"tik.skill could not be resolved to a SKILL.md file: {config.skill}")
    skill_text = skill_path.read_text(encoding="utf-8").strip()
    return (
        "Apply this local goal-cli tik skill while reviewing the attached artifact.\n\n"
        f"<goal-cli-tik-skill name=\"{config.skill}\">\n"
        f"Source: {skill_path}\n\n"
        f"{skill_text}\n"
        "</goal-cli-tik-skill>\n\n"
        "<goal-cli-tik-task>\n"
        f"{prompt.strip()}\n"
        "</goal-cli-tik-task>\n"
    )


def effective_api_tik_model(config: TikConfig) -> str:
    return config.model or DEFAULT_API_TIK_MODEL


def api_tik_client_options(config: TikConfig, timeout_seconds: float | None) -> tuple[dict[str, Any], str, str | None]:
    _, configured_base_url = api_tik_value_source(API_TIK_BASE_URL_ENV_VARS)
    base_url = config.base_url or configured_base_url or DEFAULT_API_TIK_BASE_URL
    api_key_source, api_key = api_tik_value_source(API_TIK_KEY_ENV_VARS)
    options: dict[str, Any] = {
        "timeout": timeout_seconds,
        "base_url": base_url,
    }
    if api_key:
        options["api_key"] = api_key
    return options, base_url, api_key_source


def _openai_review(
    config: TikConfig,
    artifact_path: Path,
    prompt: str,
    output_path: Path,
    log_path: Path,
    model: str,
    timeout_seconds: float | None = None,
) -> bool:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    uploaded_file_id: str | None = None
    client: Any | None = None
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("# OpenAI Responses API artifact tik\n")
        log_file.write(f"model={model}\nartifact={artifact_path}\noutput={output_path}\n\n")
        log_file.flush()
        if _timeout_exhausted(timeout_seconds, log_file):
            return False
        try:
            artifact_size = artifact_path.stat().st_size
            if artifact_size > config.max_file_size_bytes:
                log_file.write(f"ERROR: artifact is {artifact_size} bytes, larger than max_file_size_bytes={config.max_file_size_bytes}.\n")
                return False
            from openai import OpenAI

            effective_timeout = min(config.timeout_seconds, timeout_seconds) if timeout_seconds is not None else config.timeout_seconds
            client_options, base_url, api_key_env = api_tik_client_options(config, effective_timeout)
            log_file.write(f"base_url={base_url}\napi_key_env={api_key_env or 'unset'}\n")
            client = OpenAI(**client_options)
            uploaded_file = client.files.create(file=artifact_path, purpose="user_data")
            uploaded_file_id = uploaded_file.id
            response = client.responses.create(
                model=model,
                store=config.store,
                max_output_tokens=config.max_output_tokens,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": uploaded_file_id},
                            {"type": "input_text", "text": prompt},
                        ],
                    }
                ],
            )
            text = _extract_response_text(response)
            if not text.strip():
                log_file.write("ERROR: response contained no extractable output text.\n")
                return False
            output_path.write_text(text, encoding="utf-8")
            metadata = {
                "response_id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "status": getattr(response, "status", None),
                "uploaded_file_id": uploaded_file_id,
                "usage": _usage_dump(getattr(response, "usage", None)),
            }
            log_file.write(json.dumps(metadata, ensure_ascii=False, indent=2))
            log_file.write("\n")
            return True
        except Exception:
            log_file.write(traceback.format_exc())
            return False
        finally:
            if uploaded_file_id and client is not None:
                try:
                    client.files.delete(uploaded_file_id)
                    log_file.write(f"\ndeleted_uploaded_file_id={uploaded_file_id}\n")
                except Exception:
                    log_file.write("\nWARNING: failed to delete uploaded artifact file.\n")
                    log_file.write(traceback.format_exc())


def _append_log(log_path: Path, text: str) -> None:
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(text)


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip() + "\n"
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n\n".join(chunks).strip() + "\n" if chunks else ""


def _usage_dump(usage: object) -> object:
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    return str(usage)


def _stdout_without_header(log_text: str) -> str:
    marker = "\n\n"
    if marker in log_text:
        return log_text.split(marker, 1)[1]
    return log_text


def _timeout_exhausted(timeout_seconds: float | None, log_file: Any) -> bool:
    if timeout_seconds is not None and timeout_seconds <= 0:
        log_file.write("ERROR: time budget exhausted before command start.\n")
        return True
    return False


def _communicate_logged(process: subprocess.Popen[str], log_file: Any, stdin: str | None, timeout_seconds: float | None) -> bool:
    try:
        stdout, _ = process.communicate(input=stdin, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        stdout, _ = process.communicate()
        if stdout:
            log_file.write(stdout)
        timeout_label = f"{timeout_seconds:g}" if timeout_seconds is not None else "unknown"
        log_file.write(f"\nERROR: command timed out after {timeout_label} seconds.\n")
        return False
    if stdout:
        log_file.write(stdout)
    return process.returncode == 0


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    except OSError:
        process.kill()


def _log_launch_error(log_file: Any, exc: OSError) -> None:
    log_file.write(f"ERROR: failed to start command: {exc}\n")
