from __future__ import annotations

import hashlib
import json
import os
import queue
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters import CLAUDE_CODE_DISALLOWED_TOOLS, claude_print_envelope, run_claude_print_logged, run_command_logged
from .config import TokConfig
from .supervisor import AttemptOutcomeKind


@dataclass(frozen=True)
class TokExecutionPlan:
    command: tuple[str, ...]
    cwd: Path
    prompt: str
    report_path: Path
    prompt_path: Path
    provider_prompt_path: Path
    log_path: Path
    audit_log_path: Path


@dataclass(frozen=True)
class TokExecutionResult:
    ok: bool
    report_path: Path | None
    report: dict[str, Any] | None
    errors: tuple[str, ...]
    plan: TokExecutionPlan | None = None
    outcome_kind: AttemptOutcomeKind | None = None

    @property
    def detail(self) -> str:
        return "; ".join(self.errors) if self.errors else "tok completed"


def execute_tok(config: TokConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> TokExecutionResult:
    if config.provider not in {"codex_goal", "codex_app_server", "claude_code_goal"}:
        raise ValueError(f"unsupported tok provider: {config.provider}")

    run_dir.mkdir(parents=True, exist_ok=True)
    if not config.write_dirs:
        failed_path = run_dir / "tok_FAILED.txt"
        failed_path.write_text("tok.write_dirs is empty\n", encoding="utf-8")
        return TokExecutionResult(False, None, None, ("tok.write_dirs is empty",), outcome_kind=AttemptOutcomeKind.PROTOCOL_INVALID)

    attachment_dir = _attachments_dir(config, run_dir)
    attachment_dir.mkdir(parents=True, exist_ok=True)
    attachment_snapshot = _snapshot_attachment_files(attachment_dir)
    if config.provider == "claude_code_goal":
        plan = build_claude_code_goal_tok_plan(config, prompt, run_dir)
    elif config.provider == "codex_app_server":
        plan = build_codex_app_server_tok_plan(config, prompt, run_dir)
    else:
        plan = build_codex_goal_tok_plan(config, prompt, run_dir)
    plan.prompt_path.write_text(prompt, encoding="utf-8")
    plan.provider_prompt_path.write_text(plan.prompt, encoding="utf-8")

    provider_errors: list[str] = []
    if config.provider == "claude_code_goal":
        ok = _run_claude_code_goal(config, plan, timeout_seconds)
    elif config.provider == "codex_app_server":
        ok = _run_codex_app_server_goal(config, plan, timeout_seconds)
    else:
        ok = run_command_logged(list(plan.command), plan.cwd, plan.log_path, plan.prompt, timeout_seconds=timeout_seconds)
        if ok:
            completion_error = _codex_goal_completion_error(plan.log_path)
            if completion_error is not None:
                with plan.log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(f"\nERROR: {completion_error}\n")
                provider_errors.append(completion_error)
                ok = False
    attachment_errors = _attachment_integrity_errors(attachment_snapshot, _snapshot_attachment_files(attachment_dir))
    if attachment_errors:
        (run_dir / "tok_attachment_integrity.log").write_text("\n".join(attachment_errors) + "\n", encoding="utf-8")
        return TokExecutionResult(False, None, None, tuple(attachment_errors), plan, AttemptOutcomeKind.LEASE_VIOLATION)
    if not ok:
        errors = tuple(provider_errors) or ("tok provider failed",)
        kind = AttemptOutcomeKind.PROTOCOL_INVALID if provider_errors else _provider_failure_kind(plan.log_path)
        return TokExecutionResult(False, None, None, errors, plan, kind)

    report = runtime_tok_report()
    plan.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plan.audit_log_path.write_text("tok completed; runtime synthesized audit report\n", encoding="utf-8")
    return TokExecutionResult(True, plan.report_path, report, (), plan, AttemptOutcomeKind.APPLIED)


def build_codex_goal_tok_plan(config: TokConfig, prompt: str, run_dir: Path) -> TokExecutionPlan:
    final_prompt = _codex_goal_prompt(prompt)
    output_path = run_dir / "tok_report.json"
    run_cwd = config.run_cwd or config.write_dirs[0]
    command = [
        "codex",
        "exec",
        "-C",
        str(run_cwd),
        "--skip-git-repo-check",
        "--sandbox",
        config.sandbox,
    ]
    enabled_features = list(config.codex_features)
    if "goals" not in enabled_features:
        enabled_features.append("goals")
    for feature in enabled_features:
        command.extend(["--enable", feature])
    if config.model:
        command.extend(["-m", config.model])
    for write_dir in _dedupe_paths((*config.write_dirs, *config.runtime_write_dirs), skip=(run_cwd,)):
        command.extend(["--add-dir", str(write_dir)])
    command.extend(["--add-dir", str(_attachments_dir(config, run_dir))])
    command.append("-")
    return TokExecutionPlan(
        command=tuple(command),
        cwd=run_cwd,
        prompt=final_prompt,
        report_path=output_path,
        prompt_path=run_dir / "tok_prompt.md",
        provider_prompt_path=run_dir / "tok_codex_goal_prompt.md",
        log_path=run_dir / "tok_codex.log",
        audit_log_path=run_dir / "tok_report_audit.log",
    )


def build_codex_app_server_tok_plan(config: TokConfig, prompt: str, run_dir: Path) -> TokExecutionPlan:
    final_prompt = _codex_app_server_goal_prompt(prompt)
    output_path = run_dir / "tok_report.json"
    run_cwd = config.run_cwd or config.write_dirs[0]
    command = [
        "codex",
        "app-server",
        "--stdio",
    ]
    return TokExecutionPlan(
        command=tuple(command),
        cwd=run_cwd,
        prompt=final_prompt,
        report_path=output_path,
        prompt_path=run_dir / "tok_prompt.md",
        provider_prompt_path=run_dir / "tok_codex_app_server_prompt.md",
        log_path=run_dir / "tok_codex_app_server.log",
        audit_log_path=run_dir / "tok_report_audit.log",
    )


def build_claude_code_goal_tok_plan(config: TokConfig, prompt: str, run_dir: Path) -> TokExecutionPlan:
    attachments_dir = _attachments_dir(config, run_dir)
    final_prompt = _claude_code_goal_prompt(prompt)
    output_path = run_dir / "tok_report.json"
    run_cwd = config.run_cwd or config.write_dirs[0]
    command = [
        "claude",
        "--print",
        "--output-format",
        "json",
    ]
    command.extend(_claude_code_sandbox_args(config.sandbox, attachments_dir))
    if config.model:
        command.extend(["--model", config.model])
    for write_dir in _dedupe_paths((*config.write_dirs, *config.runtime_write_dirs), skip=(run_cwd,)):
        command.extend(["--add-dir", str(write_dir)])
    command.extend(["--add-dir", str(attachments_dir)])
    return TokExecutionPlan(
        command=tuple(command),
        cwd=run_cwd,
        prompt=final_prompt,
        report_path=output_path,
        prompt_path=run_dir / "tok_prompt.md",
        provider_prompt_path=run_dir / "tok_claude_code_goal_prompt.md",
        log_path=run_dir / "tok_claude_code.log",
        audit_log_path=run_dir / "tok_report_audit.log",
    )


def _claude_code_sandbox_args(sandbox: str, attachments_dir: Path) -> list[str]:
    if sandbox == "read-only":
        return ["--disallowedTools", CLAUDE_CODE_DISALLOWED_TOOLS]
    protect_attachments = f"Write({attachments_dir}/**),Edit({attachments_dir}/**)"
    if sandbox == "danger-full-access":
        return ["--dangerously-skip-permissions"]
    return ["--permission-mode", "acceptEdits", "--allowedTools", "Bash", "--disallowedTools", protect_attachments]


def _run_claude_code_goal(config: TokConfig, plan: TokExecutionPlan, timeout_seconds: float | None) -> bool:
    stdout = run_claude_print_logged(
        list(plan.command),
        plan.cwd,
        plan.log_path,
        plan.prompt,
        timeout_seconds=timeout_seconds,
        containment_root=config.containment_root,
        containment_allow_network=config.network_access,
    )
    if stdout is None:
        return False
    envelope = claude_print_envelope(stdout)
    if envelope is None:
        with plan.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("\nERROR: claude_code_goal returned no parseable JSON envelope.\n")
        return False
    return True


def _run_codex_app_server_goal(config: TokConfig, plan: TokExecutionPlan, timeout_seconds: float | None) -> bool:
    deadline = time.monotonic() + timeout_seconds if timeout_seconds and timeout_seconds > 0 else None
    try:
        with _JsonRpcStdioClient(plan.command, plan.cwd, plan.log_path, deadline) as client:
            client.request(
                "initialize",
                {"clientInfo": {"name": "goal-cli", "version": "0"}, "capabilities": {}},
            )
            thread_start: dict[str, Any] = {
                "cwd": str(plan.cwd),
                "approvalPolicy": "never",
                "sandbox": config.sandbox,
                "ephemeral": False,
                "serviceName": "goal-cli",
                "threadSource": "goal-cli-tok",
            }
            if config.model:
                thread_start["model"] = config.model
            thread_response = client.request("thread/start", thread_start)
            thread = thread_response.get("thread") if isinstance(thread_response, dict) else None
            thread_id = thread.get("id") if isinstance(thread, dict) else None
            if not isinstance(thread_id, str) or not thread_id:
                client.log_error("thread/start response did not include thread.id")
                return False

            client.request(
                "thread/goal/set",
                {
                    "threadId": thread_id,
                    "objective": _codex_app_server_goal_objective(plan.prompt),
                    "status": "active",
                },
            )
            turn_response = client.request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": plan.prompt, "text_elements": []}],
                    "cwd": str(plan.cwd),
                    "approvalPolicy": "never",
                    "sandboxPolicy": _codex_app_server_sandbox_policy(config, plan),
                    "model": config.model,
                },
            )
            turn = turn_response.get("turn") if isinstance(turn_response, dict) else None
            turn_id = turn.get("id") if isinstance(turn, dict) else None
            if not isinstance(turn_id, str) or not turn_id:
                client.log_error("turn/start response did not include turn.id")
                return False
            completed = client.wait_for_turn_completed(thread_id, turn_id)
            return completed
    except _CodexAppServerError as exc:
        with plan.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\nERROR: {exc}\n")
        return False


class _CodexAppServerError(RuntimeError):
    pass


class _JsonRpcStdioClient:
    def __init__(self, command: tuple[str, ...], cwd: Path, log_path: Path, deadline: float | None) -> None:
        self.command = command
        self.cwd = cwd
        self.log_path = log_path
        self.deadline = deadline
        self.process: subprocess.Popen[str] | None = None
        self.lines: queue.Queue[tuple[str, str | None]] = queue.Queue()
        self.reader_threads: list[threading.Thread] = []
        self.next_id = 1
        self.pending: dict[int, dict[str, Any]] = {}
        self.notifications: list[dict[str, Any]] = []
        self.last_agent_message_text: str | None = None

    def __enter__(self) -> "_JsonRpcStdioClient":
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"$ {' '.join(self.command)}\n# cwd: {self.cwd}\n\n")
        try:
            self.process = subprocess.Popen(
                list(self.command),
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,
            )
        except OSError as exc:
            raise _CodexAppServerError(f"failed to start codex app-server: {exc}") from exc
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        for name, stream in (("stdout", self.process.stdout), ("stderr", self.process.stderr)):
            thread = threading.Thread(target=self._read_stream, args=(name, stream), daemon=True)
            thread.start()
            self.reader_threads.append(thread)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is None:
                continue
            try:
                stream.close()
            except OSError:
                pass

    def request(self, method: str, params: dict[str, Any] | None) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        while True:
            if request_id in self.pending:
                response = self.pending.pop(request_id)
                if "error" in response:
                    raise _CodexAppServerError(f"{method} failed: {response['error']}")
                result = response.get("result", {})
                return result if isinstance(result, dict) else {"value": result}
            self._read_next_message()

    def wait_for_turn_completed(self, thread_id: str, turn_id: str) -> bool:
        while True:
            fallback_completed: dict[str, Any] | None = None
            for notification in self.notifications:
                if notification.get("method") != "turn/completed":
                    continue
                params = notification.get("params")
                if not isinstance(params, dict) or params.get("threadId") != thread_id:
                    continue
                turn = params.get("turn")
                if not isinstance(turn, dict):
                    continue
                if turn.get("id") != turn_id:
                    if fallback_completed is None:
                        fallback_completed = turn
                    continue
                if turn.get("status") == "completed":
                    return True
                self.log_error(f"turn completed with non-success status: {turn.get('status')}")
                return False
            if fallback_completed is not None:
                if fallback_completed.get("status") == "completed":
                    self.log_error(
                        "turn/start response id did not match completed notification; "
                        f"using completed turn {fallback_completed.get('id')}"
                    )
                    return True
                self.log_error(f"turn completed with non-success status: {fallback_completed.get('status')}")
                return False
            self._read_next_message()

    def log_error(self, message: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\nERROR: {message}\n")

    def _send(self, message: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise _CodexAppServerError("codex app-server process is not running")
        self._log_json(">", message)
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
        except OSError as exc:
            raise _CodexAppServerError(f"failed to write to codex app-server: {exc}") from exc

    def _read_next_message(self) -> None:
        if self.process is None:
            raise _CodexAppServerError("codex app-server process is not running")
        while True:
            timeout = self._queue_timeout()
            try:
                stream, line = self.lines.get(timeout=timeout)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise _CodexAppServerError(f"codex app-server exited with code {self.process.returncode}")
                self._remaining_timeout()
                continue
            if line is None:
                if stream == "stdout" and self.process.poll() is not None:
                    raise _CodexAppServerError(f"codex app-server exited with code {self.process.returncode}")
                continue
            if stream == "stderr":
                self._log_raw("!", line)
                continue
            self._log_raw("<", line)
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self.log_error(f"codex app-server emitted non-JSON stdout line: {line.strip()}")
                continue
            self._handle_message(message)
            return

    def _read_stream(self, name: str, stream: Any) -> None:
        try:
            for line in stream:
                self.lines.put((name, line))
        finally:
            self.lines.put((name, None))

    def _handle_message(self, message: dict[str, Any]) -> None:
        if "id" in message and ("result" in message or "error" in message):
            try:
                response_id = int(message["id"])
            except (TypeError, ValueError):
                self.log_error(f"codex app-server returned non-integer response id: {message.get('id')!r}")
                return
            self.pending[response_id] = message
            return
        method = message.get("method")
        if isinstance(method, str) and "id" in message:
            self._deny_server_request(message)
            return
        if isinstance(method, str):
            self.notifications.append(message)
            self._remember_agent_message(message)
            return
        self.log_error(f"codex app-server emitted unknown message: {message}")

    def _deny_server_request(self, message: dict[str, Any]) -> None:
        response = {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32000,
                "message": "goal-cli tok app-server client does not support interactive approvals or input requests",
            },
        }
        self._send(response)

    def _remember_agent_message(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        params = message.get("params")
        if method != "item/completed" or not isinstance(params, dict):
            return
        item = params.get("item")
        if isinstance(item, dict) and item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
            self.last_agent_message_text = item["text"]

    def _remaining_timeout(self) -> float | None:
        if self.deadline is None:
            return None
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise _CodexAppServerError("codex app-server timed out")
        return remaining

    def _queue_timeout(self) -> float:
        remaining = self._remaining_timeout()
        if remaining is None:
            return 0.1
        return min(0.1, remaining)

    def _log_json(self, prefix: str, message: dict[str, Any]) -> None:
        self._log_raw(prefix, json.dumps(message, ensure_ascii=False) + "\n")

    def _log_raw(self, prefix: str, text: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{prefix} {text}")


def _codex_app_server_sandbox_policy(config: TokConfig, plan: TokExecutionPlan) -> dict[str, Any]:
    if config.sandbox == "danger-full-access":
        return {"type": "dangerFullAccess"}
    if config.sandbox == "read-only":
        return {"type": "readOnly", "networkAccess": config.network_access}
    writable_roots = [
        str(path)
        for path in _dedupe_paths(
            (
                *config.write_dirs,
                *config.runtime_write_dirs,
                _attachments_dir(config, plan.report_path.parent),
            )
        )
    ]
    return {
        "type": "workspaceWrite",
        "writableRoots": writable_roots,
        "networkAccess": config.network_access,
        "excludeTmpdirEnvVar": False,
        "excludeSlashTmp": False,
    }


def _dedupe_paths(paths: tuple[Path, ...], skip: tuple[Path, ...] = ()) -> tuple[Path, ...]:
    skipped = {_path_key(path) for path in skip}
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = _path_key(path)
        if key in skipped or key in seen:
            continue
        seen.add(key)
        result.append(path)
    return tuple(result)


def _path_key(path: Path) -> str:
    return str(path.resolve(strict=False))


def _attachments_dir(config: TokConfig, run_dir: Path) -> Path:
    return config.attachments_dir or (run_dir / "attachments")


def runtime_tok_report() -> dict[str, Any]:
    return {
        "source_change_possible": True,
        "revision_strategy": "tok provider completed",
        "expected_artifact_visible_improvement": [],
        "remaining_artifact_bottleneck": "not reported by tok",
    }


def _codex_goal_prompt(prompt: str) -> str:
    return f"/goal\n{_plain_tok_prompt(prompt)}"


def _codex_app_server_goal_prompt(prompt: str) -> str:
    return _plain_tok_prompt(prompt)


def _codex_app_server_goal_objective(prompt: str) -> str:
    return prompt.rstrip()


def _claude_code_goal_prompt(prompt: str) -> str:
    return _plain_tok_prompt(prompt)


def _plain_tok_prompt(prompt: str) -> str:
    return f"{prompt.rstrip()}\n"


def _codex_goal_completion_error(log_path: Path) -> str | None:
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"tok provider log could not be read: {exc}"
    if _codex_goal_log_has_completion_marker(log_text):
        return None
    return "codex_goal exited without a model completion marker"


def _codex_goal_log_has_completion_marker(log_text: str) -> bool:
    return any(line.strip() == "tokens used" for line in log_text.splitlines())


def _provider_failure_kind(log_path: Path) -> AttemptOutcomeKind:
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return AttemptOutcomeKind.PROVIDER_ERROR
    if "timed out" in log_text or "timeout" in log_text or "resource limit" in log_text:
        return AttemptOutcomeKind.RESOURCE_LIMIT
    return AttemptOutcomeKind.PROVIDER_ERROR


def _snapshot_attachment_files(attachment_dir: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not attachment_dir.exists():
        return snapshot
    for path in sorted(attachment_dir.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[path.relative_to(attachment_dir).as_posix()] = digest
    return snapshot


def _attachment_integrity_errors(before: dict[str, str], after: dict[str, str]) -> list[str]:
    errors: list[str] = []
    before_paths = set(before)
    after_paths = set(after)
    for path in sorted(before_paths - after_paths):
        errors.append(f"tok attachment changed during execution: removed {path}")
    for path in sorted(after_paths - before_paths):
        errors.append(f"tok attachment changed during execution: added {path}")
    for path in sorted(before_paths & after_paths):
        if before[path] != after[path]:
            errors.append(f"tok attachment changed during execution: modified {path}")
    return errors
