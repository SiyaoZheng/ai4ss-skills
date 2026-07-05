from __future__ import annotations

import json
import os
import signal
import shlex
import shutil
import subprocess
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .config import GoalConfig, TikConfig


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
        return ProducerOutcome(run_shell_logged(config.producer.command, config.root, run_dir / "producer.log", timeout_seconds=timeout_seconds))

    def run_tik(self, config: GoalConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> TikOutcome:
        return TikOutcome(
            run_tik(
                config.tik,
                config.root,
                config.artifact.path,
                prompt,
                run_dir,
                "tik",
                config.artifact.copy_as,
                timeout_seconds=timeout_seconds,
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
        try:
            process = subprocess.Popen(
                command_text,
                cwd=cwd,
                shell=True,
                executable="/bin/bash",
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
) -> Path | None:
    output_path = run_dir / f"{label}_memo.md"
    (run_dir / f"{label}_prompt.md").write_text(prompt, encoding="utf-8")
    if config.provider == "oracle":
        env = {
            "GOAL_ARTIFACT": str(artifact_path),
            "GOAL_TIK_PROMPT": prompt,
            "GOAL_RUN_DIR": str(run_dir),
        }
        ok = run_shell_logged(config.command or "", root, run_dir / f"{label}_command.log", env=env, timeout_seconds=timeout_seconds)
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
        if config.provider == "agent":
            model = config.model
            if not model:
                raise ValueError("tik provider agent requires tik.model")
            ok = _openai_review(config, tik_artifact, prompt, output_path, run_dir / f"{label}_openai.log", model, timeout_seconds)
        elif config.provider == "codex_file":
            ok = _codex_file_review(config, tik_artifact, prompt, output_path, run_dir / f"{label}_codex_file.log", timeout_seconds)
        else:
            raise ValueError(f"unsupported tik provider: {config.provider}")

    if not ok:
        (run_dir / f"{label}_FAILED.txt").write_text("tik provider failed\n", encoding="utf-8")
        return None
    return output_path


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
    ok = run_command_logged(command, artifact_path.parent, log_path, _codex_file_prompt(prompt), timeout_seconds=effective_timeout)
    if not ok:
        return False
    if not output_path.exists():
        _append_log(log_path, "ERROR: codex_file did not write tik memo.\n")
        return False
    if not output_path.read_text(encoding="utf-8").strip():
        _append_log(log_path, "ERROR: codex_file wrote an empty tik memo.\n")
        return False
    return True


def _codex_file_prompt(prompt: str) -> str:
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
            client = OpenAI(timeout=effective_timeout)
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
