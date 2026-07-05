from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .adapters import GoalProviderAdapters, ProductionGoalProviderAdapters
from .config import GoalConfig, TERMINAL_STATUSES, validate_config
from .no_mistakes import NO_MISTAKES_BUDGET_EXHAUSTED, NoMistakesGate, NoMistakesResult
from .observability import (
    GoalTelemetry,
    configure_observability,
    disabled_telemetry,
    record_no_mistakes_result,
    record_run_result,
    set_span_attributes,
)
from .template import render_template


@dataclass(frozen=True)
class RuntimeOptions:
    dry_run: bool = False
    review_only: bool = False
    max_minutes: float = 30.0


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    status: str
    run_dir: Path | None
    message: str


@dataclass(frozen=True)
class CleanupResult:
    actions: tuple[str, ...]
    warnings: tuple[str, ...] = ()


class HeartbeatLockError(RuntimeError):
    pass


@dataclass(frozen=True)
class HeartbeatRecorder:
    config: GoalConfig
    state: dict[str, Any]
    telemetry: GoalTelemetry

    def start(self, run_dir: Path) -> None:
        self.state["iteration"] = int(self.state.get("iteration", 0)) + 1
        self.state["last_run_dir"] = rel(self.config, run_dir)
        self.state["producer_command"] = self.config.producer.command
        save_state(self.config, self.state)

    def append_event(self, event: str, run_dir: Path, artifact: dict[str, Any] | None = None, **extra: Any) -> None:
        event_data: dict[str, Any] = {"event": event, "run_dir": rel(self.config, run_dir), **extra}
        if artifact is not None:
            event_data["artifact_sha256"] = artifact["sha256"]
        append_history(self.config, self.state, event_data)

    def finish_state(
        self,
        status: str,
        *,
        event: str,
        next_action: str | None,
        run_dir: Path,
        artifact: dict[str, Any] | None = None,
        blocked_reason: str | None = None,
    ) -> None:
        self.state["status"] = status
        self.state["next_action"] = next_action
        if blocked_reason is not None:
            self.state["blocked_reason"] = blocked_reason
        elif status in {"active", "complete"}:
            self.state.pop("blocked_reason", None)
        self.append_event(event, run_dir, artifact)
        save_state(self.config, self.state)

    def heartbeat(self, phase: str, run_dir: Path | None) -> None:
        update_heartbeat(self.config, self.state, phase, run_dir)
        attributes = {
            "goal.heartbeat.phase": phase,
            "goal.status": self.state.get("status"),
            "goal.iteration": self.state.get("iteration"),
            "goal.run_dir": rel(self.config, run_dir) if run_dir else None,
        }
        self.telemetry.add_event("goal_cli.heartbeat", attributes)
        self.telemetry.pulse("goal_cli.heartbeat", attributes)

    def record_no_mistakes(self, event: str, result: NoMistakesResult) -> None:
        self.state["last_no_mistakes"] = {
            "event": event,
            "status": result.status,
            "ok": result.ok,
            "skipped": result.skipped,
            "detail": result.detail,
            "repo_root": str(result.repo_root) if result.repo_root else None,
            "branch": result.branch,
            "commit": result.commit,
            "log_path": rel(self.config, result.log_path) if result.log_path else None,
        }


class HeartbeatLock:
    def __init__(self, lock_path: Path, stale_seconds: int) -> None:
        self.lock_path = lock_path
        self.stale_seconds = stale_seconds
        self.acquired = False
        self.payload: dict[str, Any] | None = None

    def __enter__(self) -> "HeartbeatLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                stat_result = self.lock_path.stat()
            except FileNotFoundError:
                break
            age = time.time() - stat_result.st_mtime
            if age > self.stale_seconds or _lock_process_is_dead(self.lock_path):
                stale_path = self.lock_path.with_name(f"{self.lock_path.name}.stale-{os.getpid()}-{uuid.uuid4().hex}")
                try:
                    os.rename(self.lock_path, stale_path)
                except FileNotFoundError:
                    break
                except OSError as exc:
                    raise HeartbeatLockError(f"heartbeat already running: {self.lock_path}") from exc
                try:
                    stale_path.unlink()
                except OSError:
                    pass
                break
            raise HeartbeatLockError(f"heartbeat already running: {self.lock_path}")
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise HeartbeatLockError(f"heartbeat already running: {self.lock_path}") from exc
        self.payload = {"pid": os.getpid(), "created_at": now_iso(), "token": uuid.uuid4().hex}
        with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
            lock_file.write(json.dumps(self.payload) + "\n")
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if not self.acquired or self.payload is None:
            return
        if _read_lock_payload(self.lock_path) != self.payload:
            return
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def _read_lock_payload(lock_path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _lock_process_is_dead(lock_path: Path) -> bool:
    payload = _read_lock_payload(lock_path)
    if payload is None:
        return False
    pid = payload.get("pid") if isinstance(payload, dict) else None
    if not isinstance(pid, int) or pid <= 0:
        return False
    if pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def run_goal(config: GoalConfig, options: RuntimeOptions | None = None, adapters: GoalProviderAdapters | None = None) -> RunResult:
    options = options or RuntimeOptions()
    adapters = adapters or ProductionGoalProviderAdapters()
    issues = validate_config(config)
    if issues:
        return RunResult(2, "invalid_config", None, "\n".join(issues))

    max_seconds = max(0.0, options.max_minutes) * 60.0
    deadline = time.monotonic() + max_seconds if max_seconds else None
    return run_heartbeat(config, options, deadline=deadline, adapters=adapters)


@dataclass
class HeartbeatRunner:
    config: GoalConfig
    options: RuntimeOptions
    adapters: GoalProviderAdapters
    deadline: float | None = None
    telemetry: GoalTelemetry = field(default_factory=disabled_telemetry)
    state: dict[str, Any] = field(default_factory=dict)
    run_dir: Path | None = None

    def run(self) -> RunResult:
        with HeartbeatLock(self.config.lock_path, self.config.safety.lock_stale_seconds):
            self.state = load_state(self.config)
            git_gate = self._git_gate()
            defer_heartbeat_start = git_gate.enabled and not self.options.dry_run
            if not defer_heartbeat_start:
                self._heartbeat("heartbeat_start", None)
            if self.state.get("status") in TERMINAL_STATUSES:
                save_state(self.config, self.state)
                self._heartbeat("terminal_state", None)
                return RunResult(0, str(self.state.get("status")), None, f"goal status is {self.state.get('status')}")

            self._start_heartbeat(emit_heartbeat=not defer_heartbeat_start)
            if self.options.dry_run:
                return self._dry_run()

            prepare_result = self._prepare_no_mistakes()
            if prepare_result is not None:
                return prepare_result
            if defer_heartbeat_start:
                self._heartbeat("heartbeat_ready", self._run_dir())

            producer_result = self._run_producer()
            if producer_result:
                return producer_result

            artifact_result = self._load_artifact()
            if isinstance(artifact_result, RunResult):
                return artifact_result
            artifact = artifact_result

            tik_result = self._run_tik(artifact)
            if isinstance(tik_result, RunResult):
                return tik_result
            verdict, verdict_path, memo_path, tik_path = tik_result

            ready = tik_is_ready(self.config, verdict)
            self.state["last_tik"] = tik_state(self.config, self._run_dir(), memo_path, verdict_path, tik_path, artifact, ready)
            if ready:
                if self.options.review_only:
                    return self._review_only_passed(artifact)
                self.state.pop("blocked_reason", None)
                return self._finish(
                    0,
                    "complete",
                    "artifact passed tik",
                    phase="complete",
                    event="complete",
                    next_action=None,
                    artifact=artifact,
                )

            if self.options.review_only:
                return self._review_only(artifact)
            blocker_result = self._record_blocker(verdict, artifact)
            if blocker_result:
                return blocker_result

            return self._run_tok(artifact, tik_path)

    def _start_heartbeat(self, emit_heartbeat: bool = True) -> None:
        run_dir = heartbeat_run_dir(self.config, self.state)
        run_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = run_dir
        self._recorder().start(run_dir)
        if emit_heartbeat:
            self._heartbeat("heartbeat_ready", run_dir)

    def _prepare_no_mistakes(self) -> RunResult | None:
        git_gate = self._git_gate()
        if not git_gate.enabled:
            return None
        with self.telemetry.span(
            "goal_cli.no_mistakes.prepare",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, self._run_dir()),
            },
        ) as span:
            result = git_gate.prepare(
                self._run_dir(),
                int(self.state.get("iteration", 0)),
                "heartbeat_start",
                deadline=self.deadline,
            )
            record_no_mistakes_result(span, result)
        self._record_no_mistakes("no_mistakes_prepare", result)
        save_state(self.config, self.state)
        if result.ok:
            return None
        if result.status == NO_MISTAKES_BUDGET_EXHAUSTED:
            return self._record_no_mistakes_budget_exhausted("no_mistakes_prepare_budget_exhausted", result)
        self.state["status"] = "blocked_no_mistakes_failed"
        self.state["next_action"] = None
        self.state["blocked_reason"] = result.detail
        append_history(self.config, self.state, {"event": "no_mistakes_prepare_failed", "detail": result.detail, "run_dir": rel(self.config, self._run_dir())})
        save_state(self.config, self.state)
        self._heartbeat("no_mistakes_failed", self._run_dir())
        return RunResult(1, "blocked_no_mistakes_failed", self._run_dir(), result.detail)

    def _dry_run(self) -> RunResult:
        run_dir = self._run_dir()
        render_prompts_to_run_dir(self.config, run_dir)
        self._event("dry_run")
        save_state(self.config, self.state)
        self._heartbeat("dry_run_complete", run_dir)
        return RunResult(0, "dry_run", run_dir, f"rendered prompts in {run_dir}")

    def _run_producer(self) -> RunResult | None:
        run_dir = self._run_dir()
        self._heartbeat("producer_running", run_dir)
        with self.telemetry.span(
            "goal_cli.producer",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, run_dir),
                "goal.producer.command": self.config.producer.command,
            },
        ) as span:
            outcome = self.adapters.produce_artifact(self.config, run_dir, timeout_seconds=remaining_seconds(self.deadline))
            span.set_attribute("goal.producer.ok", outcome.ok)
        if outcome.ok:
            return None
        return self._finish(
            1,
            "blocked_producer_failed",
            "producer command failed",
            phase="producer_failed",
            event="producer_failed",
            blocked_reason="producer command failed",
            next_action=None,
        )

    def _load_artifact(self) -> dict[str, Any] | RunResult:
        with self.telemetry.span(
            "goal_cli.artifact.load",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.artifact.path": rel(self.config, self.config.artifact.path),
            },
        ) as span:
            if not self.config.artifact.path.exists():
                span.set_attribute("goal.artifact.exists", False)
                return self._finish(
                    1,
                    "blocked_artifact_missing",
                    "artifact missing after producer",
                    phase="artifact_missing",
                    event="artifact_missing",
                    blocked_reason=f"artifact missing after producer: {self.config.artifact.path}",
                    next_action=None,
                )
            artifact = artifact_metadata(self.config, self.config.artifact.path)
            set_span_attributes(
                span,
                {
                    "goal.artifact.exists": True,
                    "goal.artifact.sha256": artifact["sha256"],
                    "goal.artifact.size_bytes": artifact["size_bytes"],
                },
            )
        self.state["last_artifact"] = artifact
        return artifact

    def _run_tik(self, artifact: dict[str, Any]) -> tuple[dict[str, Any], Path, Path, Path] | RunResult:
        run_dir = self._run_dir()
        tik_prompt = render_tik_prompt(self.config, artifact)
        self._heartbeat("tik_running", run_dir)
        with self.telemetry.span(
            "goal_cli.tik",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, run_dir),
                "goal.tik.provider": self.config.tik.provider,
                "goal.artifact.sha256": artifact["sha256"],
            },
        ) as span:
            outcome = self.adapters.run_tik(self.config, tik_prompt, run_dir, timeout_seconds=remaining_seconds(self.deadline))
            memo_path = outcome.memo_path
            if memo_path is None:
                span.set_attribute("goal.tik.ok", False)
                return self._finish(
                    1,
                    "blocked_tik_failed",
                    "tik provider failed",
                    phase="tik_failed",
                    event="tik_failed",
                    blocked_reason="tik provider failed",
                    next_action=None,
                    artifact=artifact,
                )

            verdict, parse_error = parse_tik_verdict(self.config, memo_path)
            verdict_path = run_dir / "tik_verdict.json"
            verdict_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tik_path = write_tik_ledger(self.config, run_dir, artifact, memo_path, verdict_path, verdict)
            blockers = verdict.get(self.config.tik.verdict.blockers_field)
            ready = tik_is_ready(self.config, verdict)
            set_span_attributes(
                span,
                {
                    "goal.tik.ok": not parse_error,
                    "goal.tik.memo_path": rel(self.config, memo_path),
                    "goal.tik.verdict_path": rel(self.config, verdict_path),
                    "goal.tik.ledger_path": rel(self.config, tik_path),
                    "goal.tik.parse_error": parse_error,
                    "goal.tik.ready": ready,
                    "goal.tik.blocker_count": len(blockers) if isinstance(blockers, list) else None,
                },
            )
            if parse_error:
                self.state["last_tik"] = tik_state(self.config, run_dir, memo_path, verdict_path, tik_path, artifact, False)
                return self._finish(
                    1,
                    "blocked_unparseable_tik",
                    "tik verdict was unparseable",
                    phase="tik_unparseable",
                    event="tik_unparseable",
                    blocked_reason="tik output was not parseable or did not match configured verdict fields",
                    next_action=None,
                    artifact=artifact,
                )
            freshness_error = tik_freshness_error(verdict, artifact)
            if freshness_error is not None:
                span.set_attribute("goal.tik.fresh", False)
                span.set_attribute("goal.tik.freshness_error", freshness_error)
                self.state["last_tik"] = tik_state(self.config, run_dir, memo_path, verdict_path, tik_path, artifact, False)
                return self._finish(
                    1,
                    "blocked_stale_tik_review",
                    "tik review does not match current artifact",
                    phase="tik_stale",
                    event="tik_stale",
                    blocked_reason=freshness_error,
                    next_action="tik",
                    artifact=artifact,
                )
            span.set_attribute("goal.tik.fresh", True)
            return verdict, verdict_path, memo_path, tik_path

    def _record_blocker(self, verdict: dict[str, Any], artifact: dict[str, Any]) -> RunResult | None:
        update_blocker_state(self.config, self.state, verdict)
        if self.state.get("status") != "blocked_repeated_same_objection":
            return None
        return self._finish(
            1,
            "blocked_repeated_same_objection",
            "same tik objection repeated",
            phase="blocked_repeated_same_objection",
            event="blocked_repeated_same_objection",
            next_action=None,
            artifact=artifact,
        )

    def _review_only(self, artifact: dict[str, Any]) -> RunResult:
        return self._finish(
            0,
            "active",
            "artifact did not pass tik; tok skipped by tik command",
            phase="review_only_complete",
            event="review_only_tik_failed",
            next_action="tok",
            artifact=artifact,
        )

    def _review_only_passed(self, artifact: dict[str, Any]) -> RunResult:
        return self._finish(
            0,
            "active",
            "artifact passed tik; goal completion skipped by tik command",
            phase="review_only_complete",
            event="review_only_tik_passed",
            next_action=None,
            artifact=artifact,
        )

    def _run_tok(self, artifact: dict[str, Any], tik_path: Path) -> RunResult:
        run_dir = self._run_dir()
        tok_prompt = render_tok_prompt(self.config, artifact, tik_path, run_dir)
        self._heartbeat("tok_running", run_dir)
        with self.telemetry.span(
            "goal_cli.tok",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, run_dir),
                "goal.tok.provider": self.config.tok.provider,
                "goal.tok.run_cwd": rel(self.config, self.config.tok.run_cwd or (self.config.tok.write_dirs[0] if self.config.tok.write_dirs else self.config.root)),
                "goal.tok.write_dirs": [rel(self.config, path) for path in self.config.tok.write_dirs],
                "goal.tok.runtime_write_dirs": [rel(self.config, path) for path in self.config.tok.runtime_write_dirs],
                "goal.tik.ledger_path": rel(self.config, tik_path),
                "goal.artifact.sha256": artifact["sha256"],
            },
        ) as span:
            outcome = self.adapters.execute_tok(self.config, tok_prompt, run_dir, timeout_seconds=remaining_seconds(self.deadline))
            tok_report_path = outcome.report_path
            if not outcome.ok or tok_report_path is None or outcome.report is None:
                set_span_attributes(
                    span,
                    {
                        "goal.tok.ok": False,
                        "goal.tok.report_path": rel(self.config, tok_report_path) if tok_report_path else None,
                        "goal.tok.error": outcome.detail,
                    },
                )
                return self._finish(
                    1,
                    "blocked_tok_failed",
                    "tok provider failed",
                    phase="tok_failed",
                    event="tok_failed",
                    blocked_reason="tok provider failed",
                    next_action=None,
                    artifact=artifact,
                )

            tok_report = outcome.report
            set_span_attributes(
                span,
                {
                    "goal.tok.ok": True,
                    "goal.tok.report_path": rel(self.config, tok_report_path),
                    "goal.tok.source_change_possible": tok_report.get("source_change_possible"),
                    "goal.tok.sources_changed": tok_report.get("sources_changed", []),
                },
            )
            self.state["last_tok"] = tok_state(self.config, run_dir, tok_report_path, artifact, tok_report)
            if tok_report.get("source_change_possible") is False:
                return self._finish(
                    1,
                    "blocked_no_source_change_possible",
                    "tok reported no source change possible",
                    phase="blocked_no_source_change_possible",
                    event="blocked_no_source_change_possible",
                    blocked_reason=str(tok_report.get("remaining_artifact_bottleneck") or "tok reported no source change possible"),
                    next_action=None,
                    artifact=artifact,
                )

            return self._finish(
                0,
                "active",
                "tok completed; next heartbeat must rebuild and run tik",
                phase="tok_completed",
                event="tok_completed",
                next_action="tik",
                artifact=artifact,
            )

    def _finish(
        self,
        exit_code: int,
        status: str,
        message: str,
        *,
        phase: str,
        event: str,
        next_action: str | None,
        artifact: dict[str, Any] | None = None,
        blocked_reason: str | None = None,
    ) -> RunResult:
        gate_result = self._gate_no_mistakes(exit_code, status)
        if gate_result is not None:
            return gate_result
        self._recorder().finish_state(
            status,
            event=event,
            next_action=next_action,
            run_dir=self._run_dir(),
            artifact=artifact,
            blocked_reason=blocked_reason,
        )
        self._heartbeat(phase, self._run_dir())
        return RunResult(exit_code, status, self._run_dir(), message)

    def _gate_no_mistakes(self, exit_code: int, status: str) -> RunResult | None:
        git_gate = self._git_gate()
        if not git_gate.enabled:
            return None
        if self.options.review_only or status not in {"active", "complete"}:
            return None

        self._heartbeat("no_mistakes_running", self._run_dir())
        with self.telemetry.span(
            "goal_cli.no_mistakes.gate",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, self._run_dir()),
                "goal.status.before_gate": status,
            },
        ) as span:
            result = git_gate.gate(
                self._run_dir(),
                int(self.state.get("iteration", 0)),
                status,
                deadline=self.deadline,
            )
            record_no_mistakes_result(span, result)
        self._record_no_mistakes("no_mistakes_gate", result)
        if result.ok:
            append_history(
                self.config,
                self.state,
                {
                    "event": "no_mistakes_gate",
                    "status": result.status,
                    "branch": result.branch,
                    "commit": result.commit,
                    "log_path": rel(self.config, result.log_path) if result.log_path else None,
                    "run_dir": rel(self.config, self._run_dir()),
                },
            )
            save_state(self.config, self.state)
            return None

        if result.status == NO_MISTAKES_BUDGET_EXHAUSTED:
            return self._record_no_mistakes_budget_exhausted("no_mistakes_gate_budget_exhausted", result)

        self.state["status"] = "blocked_no_mistakes_failed"
        self.state["next_action"] = None
        self.state["blocked_reason"] = result.detail
        append_history(
            self.config,
            self.state,
            {
                "event": "no_mistakes_gate_failed",
                "status": result.status,
                "detail": result.detail,
                "branch": result.branch,
                "commit": result.commit,
                "log_path": rel(self.config, result.log_path) if result.log_path else None,
                "run_dir": rel(self.config, self._run_dir()),
            },
        )
        save_state(self.config, self.state)
        self._heartbeat("no_mistakes_failed", self._run_dir())
        return RunResult(1, "blocked_no_mistakes_failed", self._run_dir(), result.detail)

    def _record_no_mistakes_budget_exhausted(self, event: str, result: NoMistakesResult) -> RunResult:
        self.state["status"] = "budget_limited"
        self.state["next_action"] = "tik"
        self.state.pop("blocked_reason", None)
        append_history(
            self.config,
            self.state,
            {
                "event": event,
                "status": result.status,
                "detail": result.detail,
                "branch": result.branch,
                "commit": result.commit,
                "log_path": rel(self.config, result.log_path) if result.log_path else None,
                "run_dir": rel(self.config, self._run_dir()),
            },
        )
        save_state(self.config, self.state)
        self._heartbeat("run_budget_exhausted", self._run_dir())
        return RunResult(1, "budget_limited", self._run_dir(), result.detail)

    def _record_no_mistakes(self, event: str, result: NoMistakesResult) -> None:
        self._recorder().record_no_mistakes(event, result)

    def _event(self, event: str, artifact: dict[str, Any] | None = None) -> None:
        self._recorder().append_event(event, self._run_dir(), artifact)

    def _heartbeat(self, phase: str, run_dir: Path | None) -> None:
        self._recorder().heartbeat(phase, run_dir)

    def _run_dir(self) -> Path:
        if self.run_dir is None:
            raise RuntimeError("heartbeat run directory has not been initialized")
        return self.run_dir

    def _recorder(self) -> HeartbeatRecorder:
        return HeartbeatRecorder(self.config, self.state, self.telemetry)

    def _git_gate(self) -> NoMistakesGate:
        return NoMistakesGate(self.config)


def run_heartbeat(
    config: GoalConfig,
    options: RuntimeOptions | None = None,
    deadline: float | None = None,
    adapters: GoalProviderAdapters | None = None,
) -> RunResult:
    options = options or RuntimeOptions()
    issues = validate_config(config)
    if issues:
        return RunResult(2, "invalid_config", None, "\n".join(issues))
    if deadline is None and options.max_minutes > 0:
        deadline = time.monotonic() + options.max_minutes * 60.0
    telemetry = configure_observability(config)
    with telemetry.span(
        "goal_cli.heartbeat.run",
        {
            "goal.name": config.name,
            "goal.root": str(config.root),
            "goal.config": str(config.path),
            "goal.command": "heartbeat",
            "goal.dry_run": options.dry_run,
            "goal.review_only": options.review_only,
            "goal.deadline_set": deadline is not None,
            "goal.no_mistakes.enabled": NoMistakesGate(config).enabled,
        },
    ) as span:
        runner = HeartbeatRunner(config, options, adapters or ProductionGoalProviderAdapters(), deadline, telemetry)
        try:
            result = runner.run()
        except HeartbeatLockError as exc:
            result = RunResult(1, "locked", None, str(exc))
        record_run_result(span, result)
    telemetry.flush()
    return result


def run_producer(config: GoalConfig, run_dir: Path, timeout_seconds: float | None = None) -> bool:
    return ProductionGoalProviderAdapters().produce_artifact(config, run_dir, timeout_seconds=timeout_seconds).ok


def render_prompts_to_run_dir(config: GoalConfig, run_dir: Path, tik_path: Path | None = None) -> None:
    artifact = {"path": rel(config, config.artifact.path), "sha256": "", "size_bytes": 0, "mtime": ""}
    (run_dir / "tik_prompt.md").write_text(render_tik_prompt(config, artifact), encoding="utf-8")
    if tik_path is None:
        tik_path = run_dir / "tik.md"
        tik_path.write_text(
            "# Referee Report\n\n"
            "Dry run placeholder. A real heartbeat writes this file after the finished thing is reviewed.\n",
            encoding="utf-8",
        )
    (run_dir / "tok_prompt.md").write_text(render_tok_prompt(config, artifact, tik_path, run_dir), encoding="utf-8")


def render_tik_prompt(config: GoalConfig, artifact: dict[str, Any]) -> str:
    values = {
        "goal_name": config.name,
        "artifact_path": str(artifact.get("path", rel(config, config.artifact.path))),
        "artifact_sha256": str(artifact.get("sha256", "")),
        "producer_command": config.producer.command,
    }
    return render_template(config.tik.prompt, values)


def render_tok_prompt(config: GoalConfig, artifact: dict[str, Any], tik_path: Path, run_dir: Path) -> str:
    tik_ledger = tik_path.read_text(encoding="utf-8") if tik_path.exists() else ""
    tik_review_path = write_tik_review_attachment(run_dir, tik_ledger)
    values = {
        "goal_name": config.name,
        "producer_command": config.producer.command,
        "artifact_path": str(artifact.get("path", rel(config, config.artifact.path))),
        "artifact_sha256": str(artifact.get("sha256", "")),
        "tik_review_path": str(tik_review_path),
        "writable_scopes": "\n".join(f"- {path}" for path in config.tok.write_dirs),
        "runtime_writable_scopes": "\n".join(f"- {path}" for path in config.tok.runtime_write_dirs),
        "tok_run_cwd": str(config.tok.run_cwd or (config.tok.write_dirs[0] if config.tok.write_dirs else config.root)),
        "run_dir": str(run_dir),
    }
    return render_template(config.tok.prompt_template, values)


def write_tik_review_attachment(run_dir: Path, report_text: str) -> Path:
    attachment_dir = run_dir / "attachments"
    attachment_dir.mkdir(parents=True, exist_ok=True)
    report_path = attachment_dir / "tik_review.md"
    report_path.write_text(report_text.strip() + "\n", encoding="utf-8")
    return report_path


def write_tik_ledger(
    config: GoalConfig,
    run_dir: Path,
    artifact: dict[str, Any],
    memo_path: Path,
    verdict_path: Path,
    verdict: dict[str, Any],
) -> Path:
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
    parsed_tik_json = json.dumps(verdict, ensure_ascii=False, indent=2)
    tik_path = run_dir / "tik.md"
    body = "\n".join(
        [
            "# Referee Report",
            "",
            f"Goal: {config.name}",
            f"Run directory: {rel(config, run_dir)}",
            "",
            "## Artifact",
            "",
            f"- path: {artifact.get('path', rel(config, config.artifact.path))}",
            f"- sha256: {artifact.get('sha256', '')}",
            f"- size_bytes: {artifact.get('size_bytes', '')}",
            f"- mtime: {artifact.get('mtime', '')}",
            "",
            "## Review Text",
            "",
            memo.strip() or "(empty)",
            "",
            "## Parsed Verdict",
            "",
            "```json",
            parsed_tik_json,
            "```",
            "",
        ]
    )
    tik_path.write_text(body, encoding="utf-8")
    return tik_path


def load_state(config: GoalConfig) -> dict[str, Any]:
    if not config.state_path.exists():
        return {
            "schema_version": 1,
            "goal": config.name,
            "status": "active",
            "iteration": 0,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "next_action": "tik",
            "history": [],
        }
    with config.state_path.open("r", encoding="utf-8") as state_file:
        state = json.load(state_file)
    if not isinstance(state, dict):
        raise ValueError(f"{config.state_path} must contain a JSON object")
    state.setdefault("history", [])
    return state


def save_state(config: GoalConfig, state: dict[str, Any]) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now_iso()
    temp_path = config.state_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(config.state_path)


def reset_state(config: GoalConfig) -> None:
    if config.state_path.exists():
        config.state_path.unlink()
    if config.lock_path.exists():
        config.lock_path.unlink()


def append_history(config: GoalConfig, state: dict[str, Any], event: dict[str, Any]) -> None:
    history = state.setdefault("history", [])
    if not isinstance(history, list):
        history = []
        state["history"] = history
    history.append({"at": now_iso(), **event})
    del history[:-config.safety.max_history_items]


def cleanup_runtime(config: GoalConfig, kill_orphans: bool = False) -> CleanupResult:
    actions: list[str] = []
    warnings: list[str] = []
    live_lock = False
    removed_lock = False

    if config.lock_path.exists():
        payload = _read_lock_payload(config.lock_path)
        if _lock_process_is_dead(config.lock_path):
            config.lock_path.unlink()
            removed_lock = True
            pid = payload.get("pid") if isinstance(payload, dict) else None
            actions.append(f"removed stale heartbeat lock for dead pid {pid}: {rel(config, config.lock_path)}")
        elif payload is None:
            warnings.append(f"heartbeat lock exists but is not parseable; left untouched: {rel(config, config.lock_path)}")
        else:
            live_lock = True
            warnings.append(f"heartbeat lock is active for pid {payload.get('pid')}; left untouched")

    if removed_lock or (not live_lock and _heartbeat_looks_interrupted(config)):
        previous_phase = _mark_heartbeat_interrupted(config)
        if previous_phase:
            actions.append(f"marked heartbeat interrupted: {previous_phase} -> interrupted")

    if kill_orphans:
        if live_lock:
            warnings.append("skipped orphan process cleanup because an active heartbeat lock exists")
        else:
            actions.extend(_terminate_orphan_goal_processes(config))

    if not actions and not warnings:
        actions.append("cleanup found nothing to do")
    return CleanupResult(tuple(actions), tuple(warnings))


def _heartbeat_looks_interrupted(config: GoalConfig) -> bool:
    heartbeat = _read_heartbeat(config)
    phase = heartbeat.get("phase") if isinstance(heartbeat, dict) else None
    return isinstance(phase, str) and phase.endswith("_running")


def _read_heartbeat(config: GoalConfig) -> dict[str, Any]:
    if not config.heartbeat_path.exists():
        return {}
    try:
        heartbeat = json.loads(config.heartbeat_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return heartbeat if isinstance(heartbeat, dict) else {}


def _mark_heartbeat_interrupted(config: GoalConfig) -> str | None:
    heartbeat = _read_heartbeat(config)
    previous_phase = heartbeat.get("phase")
    if not isinstance(previous_phase, str) or not previous_phase.endswith("_running"):
        return None
    heartbeat["phase"] = "interrupted"
    heartbeat["previous_phase"] = previous_phase
    heartbeat["last_seen"] = now_iso()
    temp_path = config.heartbeat_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(heartbeat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(config.heartbeat_path)

    state = load_state(config)
    state["status"] = "active"
    state["next_action"] = "tik"
    append_history(
        config,
        state,
        {
            "event": "cleanup_interrupted",
            "previous_phase": previous_phase,
            "run_dir": heartbeat.get("run_dir"),
        },
    )
    save_state(config, state)
    return previous_phase


def _terminate_orphan_goal_processes(config: GoalConfig) -> list[str]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return [f"could not list processes for orphan cleanup: {result.stderr.strip() or result.returncode}"]

    actions: list[str] = []
    current_pid = os.getpid()
    for line in result.stdout.splitlines():
        match = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)", line)
        if not match:
            continue
        pid = int(match.group(1))
        command = match.group(3)
        if pid == current_pid or str(config.root) not in command:
            continue
        if "codex exec" not in command and "goal_cli.cli" not in command and "-m goal_cli" not in command:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError:
            actions.append(f"permission denied terminating orphan process {pid}")
            continue
        actions.append(f"terminated orphan process {pid}: {_clip(command, 160)}")
    if not actions:
        actions.append("no orphan goal-cli/Codex processes found for this project")
    return actions


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def update_heartbeat(config: GoalConfig, state: dict[str, Any], phase: str, run_dir: Path | None) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    heartbeat = {
        "goal": config.name,
        "phase": phase,
        "status": state.get("status"),
        "iteration": state.get("iteration"),
        "last_seen": now_iso(),
        "run_dir": rel(config, run_dir) if run_dir else None,
    }
    temp_path = config.heartbeat_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(heartbeat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(config.heartbeat_path)


def parse_tik_verdict(config: GoalConfig, memo_path: Path) -> tuple[dict[str, Any], bool]:
    memo_text = memo_path.read_text(encoding="utf-8")
    parsed = extract_json_object(memo_text)
    if parsed is None:
        return _parse_error_verdict(config, "Tik did not return parseable JSON.", memo_path), True
    for field in config.tik.verdict.required_fields:
        if field not in parsed:
            return _parse_error_verdict(config, f"Tik JSON missing required field: {field}", memo_path), True
    ready = parsed.get(config.tik.verdict.ready_field)
    blockers = parsed.get(config.tik.verdict.blockers_field)
    if not isinstance(ready, bool):
        return _parse_error_verdict(config, f"{config.tik.verdict.ready_field} must be boolean", memo_path), True
    if not isinstance(blockers, list):
        return _parse_error_verdict(config, f"{config.tik.verdict.blockers_field} must be a list", memo_path), True
    parsed["_parse_error"] = False
    return parsed, False


def extract_json_object(text: str) -> dict[str, Any] | None:
    candidates: list[str] = []
    for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE):
        candidates.append(match.group(1))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def tik_is_ready(config: GoalConfig, verdict: dict[str, Any]) -> bool:
    blockers = verdict.get(config.tik.verdict.blockers_field)
    return verdict.get(config.tik.verdict.ready_field) is True and isinstance(blockers, list) and not blockers


def tik_freshness_error(verdict: dict[str, Any], artifact: dict[str, Any]) -> str | None:
    artifact_sha = str(artifact.get("sha256") or "")
    if verdict.get("review_matches_current_pdf") is False:
        reviewed_sha = _optional_str(verdict.get("reviewed_pdf_sha256") or verdict.get("reviewed_artifact_sha256") or verdict.get("reviewed_sha256"))
        current_sha = _optional_str(verdict.get("current_pdf_sha256") or verdict.get("current_artifact_sha256") or verdict.get("current_sha256"))
        return _freshness_message(artifact_sha, reviewed_sha, current_sha)

    current_sha = _optional_str(verdict.get("current_pdf_sha256") or verdict.get("current_artifact_sha256") or verdict.get("current_sha256"))
    if current_sha and artifact_sha and current_sha != artifact_sha:
        return f"tik current artifact hash {current_sha} does not match runtime artifact hash {artifact_sha}"

    reviewed_sha = _optional_str(verdict.get("reviewed_pdf_sha256") or verdict.get("reviewed_artifact_sha256") or verdict.get("reviewed_sha256"))
    if reviewed_sha and artifact_sha and reviewed_sha != artifact_sha:
        return _freshness_message(artifact_sha, reviewed_sha, current_sha)
    return None


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _freshness_message(artifact_sha: str, reviewed_sha: str | None, current_sha: str | None) -> str:
    parts = ["tik review does not match the current artifact"]
    if artifact_sha:
        parts.append(f"runtime_artifact_sha256={artifact_sha}")
    if current_sha:
        parts.append(f"tik_current_sha256={current_sha}")
    if reviewed_sha:
        parts.append(f"reviewed_sha256={reviewed_sha}")
    parts.append("run a fresh artifact review before tok")
    return "; ".join(parts)


def update_blocker_state(config: GoalConfig, state: dict[str, Any], verdict: dict[str, Any]) -> None:
    fingerprint = blocker_fingerprint(config, verdict)
    if state.get("blocker_fingerprint") == fingerprint:
        repeats = int(state.get("consecutive_blocker_count", 0)) + 1
    else:
        repeats = 1
    state["blocker_fingerprint"] = fingerprint
    state["consecutive_blocker_count"] = repeats
    if repeats >= config.safety.max_blocker_repeats:
        state["status"] = "blocked_repeated_same_objection"
        state["next_action"] = None
        state["blocked_reason"] = "same tik objection repeated across heartbeats"
    else:
        state["status"] = "active"
        state["next_action"] = "tok"


def blocker_fingerprint(config: GoalConfig, verdict: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in config.tik.verdict.fingerprint_fields:
        value = verdict.get(field)
        if value is not None:
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if not parts:
        parts.append(json.dumps(verdict, ensure_ascii=False, sort_keys=True))
    normalized = re.sub(r"\s+", " ", "\n".join(parts).lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def artifact_metadata(config: GoalConfig, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": rel(config, path),
        "sha256": sha256_file(path),
        "size_bytes": stat.st_size,
        "mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.UTC).replace(microsecond=0).isoformat(),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tik_state(config: GoalConfig, run_dir: Path, memo_path: Path, verdict_path: Path, tik_path: Path, artifact: dict[str, Any], ready: bool) -> dict[str, Any]:
    return {
        "run_dir": rel(config, run_dir),
        "memo_path": rel(config, memo_path),
        "verdict_path": rel(config, verdict_path),
        "ledger_path": rel(config, tik_path),
        "artifact_sha256": artifact["sha256"],
        "artifact_ready": ready,
    }


def tok_state(config: GoalConfig, run_dir: Path, report_path: Path, artifact: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": rel(config, run_dir),
        "report_path": rel(config, report_path),
        "reviewed_artifact_sha256": artifact["sha256"],
        "source_change_possible": report.get("source_change_possible"),
        "sources_changed": report.get("sources_changed", []),
        "expected_artifact_visible_improvement": report.get("expected_artifact_visible_improvement", []),
        "remaining_artifact_bottleneck": report.get("remaining_artifact_bottleneck", ""),
    }


def heartbeat_run_dir(config: GoalConfig, state: dict[str, Any]) -> Path:
    iteration = int(state.get("iteration", 0)) + 1
    return config.runs_dir / f"heartbeat-{iteration:04d}-{timestamp()}"


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def rel(config: GoalConfig, path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(config.root))
    except ValueError:
        return str(path)


def remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _parse_error_verdict(config: GoalConfig, message: str, memo_path: Path) -> dict[str, Any]:
    return {
        config.tik.verdict.ready_field: False,
        config.tik.verdict.blockers_field: [
            {
                "severity": "blocking",
                "objection": message,
                "artifact_evidence": f"See raw tik memo: {memo_path}",
            }
        ],
        "central_bottleneck": "Tik output could not be used by the runtime.",
        "_parse_error": True,
    }
