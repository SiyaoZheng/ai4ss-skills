from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .adapters import GoalProviderAdapters, ProductionGoalProviderAdapters, mutation_containment_backend
from .config import GoalConfig, TERMINAL_STATUSES, TikConfig, tik_providers, validate_config
from .isolation import IsolatedAttemptResult, IsolatedWorkspace, rebase_goal_config
from .lifecycle import CallState, Clock, SystemClock, WorkState, normalized_utc, parse_timestamp, timestamp_after
from .no_mistakes import NoMistakesCheckpoint, NoMistakesResult
from .observability import (
    GoalTelemetry,
    configure_observability,
    disabled_telemetry,
    record_no_mistakes_result,
    record_run_result,
    set_span_attributes,
)
from .provider_contract import preflight_tok_provider, supervisor_transition
from .supervisor import (
    AttemptContext,
    AttemptOutcomeKind,
    ensure_goal_identity,
    prepare_attempt_context,
    record_attempt,
    render_attempt_guard,
)
from .template import render_template
from .transaction import load_transaction, mark_transaction_checkpointed, recover_transactions

IGNORED_RUNTIME_METADATA_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
IGNORED_RUNTIME_METADATA_DIRNAMES = {".Spotlight-V100", ".TemporaryItems", ".fseventsd"}
DEFAULT_MAX_MINUTES = 600.0
RETIRED_INVALID_REVIEW_STATUSES = {
    "blocked_producer_failed",
    "blocked_artifact_missing",
    "blocked_tik_failed",
    "blocked_unparseable_tik",
    "blocked_stale_tik_review",
}
RETIRED_ACTIVE_STATUSES = {
    "blocked_tok_failed",
    "blocked_tok_direct_artifact_mutation",
    "blocked_tok_unexpected_mutation",
    "blocked_tok_no_source_changes",
    "blocked_no_source_change_possible",
    "blocked_repeated_same_objection",
    "blocked_no_mistakes_failed",
    "budget_limited",
}


@dataclass(frozen=True)
class RuntimeOptions:
    dry_run: bool = False
    review_only: bool = False
    max_minutes: float = DEFAULT_MAX_MINUTES
    clock: Clock = field(default_factory=SystemClock, compare=False, repr=False)


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


@dataclass(frozen=True)
class TikProviderReview:
    label: str
    provider: str
    memo_path: Path | None
    verdict_path: Path | None
    ledger_path: Path | None
    verdict: dict[str, Any] | None
    ready: bool
    parse_error: bool = False
    freshness_error: str | None = None
    error: str | None = None


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
    pending_transaction_journal: Path | None = None
    current_attempt_context: AttemptContext | None = None

    def run(self) -> RunResult:
        with HeartbeatLock(self.config.lock_path, self.config.safety.lock_stale_seconds):
            self.state = load_state(self.config)
            recovery_result = self._recover_transactions()
            if recovery_result is not None:
                return recovery_result
            normalize_retired_status(self.config, self.state)
            self._normalize_perpetual_state()
            identity_result = self._bind_perpetual_identity()
            if identity_result is not None:
                return identity_result
            if self.state.get("operator_stopped") is True:
                save_state(self.config, self.state)
                self._heartbeat("operator_stopped", None)
                return RunResult(0, WorkState.STOPPED, None, "perpetual goal is stopped; run goal-cli resume to continue")
            checkpoint = self._no_mistakes_checkpoint()
            defer_heartbeat_start = checkpoint.enabled and not self.options.dry_run
            if not defer_heartbeat_start:
                self._heartbeat("heartbeat_start", None)
            scheduled_result = self._scheduled_result()
            if scheduled_result is not None:
                return scheduled_result
            if self.state.get("status") in TERMINAL_STATUSES:
                save_state(self.config, self.state)
                self._heartbeat("terminal_state", None)
                return RunResult(0, str(self.state.get("status")), None, f"goal status is {self.state.get('status')}")

            if self.config.perpetual.enabled:
                self.state["call_state"] = CallState.DUE
                save_state(self.config, self.state)
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
            verdict, verdict_path, memo_path, tik_path, reviews = tik_result

            ready = tik_is_ready(self.config, verdict)
            self.state["last_tik"] = tik_state(self.config, self._run_dir(), memo_path, verdict_path, tik_path, artifact, ready, reviews)
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
            blocker_result = self._record_blocker(tik_path, artifact)
            if blocker_result:
                return blocker_result

            return self._run_tok(artifact, tik_path)

    def _bind_perpetual_identity(self) -> RunResult | None:
        if not self.config.perpetual.enabled:
            return None
        if self.config.lease is None:
            reason = "capability lease is required before perpetual execution begins"
            self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
            self.state["status"] = WorkState.BLOCKED
            self.state["call_state"] = CallState.FAILED
            self.state["blocked_reason"] = reason
            self.state["next_action"] = "configure_lease"
            self.state["next_due_at"] = timestamp_after(
                self.options.clock,
                self.config.perpetual.active_interval_seconds,
            )
            save_state(self.config, self.state)
            self._heartbeat("capability_lease_missing", None)
            return RunResult(0, WorkState.BLOCKED, None, reason)
        substantive_goal = self.config.perpetual.substantive_goal or self.config.name
        lease_version = self.config.lease.version
        error = ensure_goal_identity(self.state, substantive_goal, lease_version)
        if error is None:
            save_state(self.config, self.state)
            return None
        self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
        self.state["status"] = WorkState.BLOCKED
        self.state["call_state"] = CallState.FAILED
        self.state["blocked_reason"] = error
        self.state["next_action"] = "restore_goal_binding"
        save_state(self.config, self.state)
        self._heartbeat("goal_binding_violation", None)
        return RunResult(2, WorkState.BLOCKED, None, error)

    def _recover_transactions(self) -> RunResult | None:
        for result in recover_transactions(self.config.root, self.config.state_dir):
            journal = load_transaction(result.journal_path)
            attempt_id = str(journal.get("attempt_id"))
            history = self.state.get("history")
            if result.conflict:
                already_recorded = isinstance(history, list) and any(
                    isinstance(entry, dict)
                    and entry.get("event") == "transaction_conflict"
                    and entry.get("attempt_id") == attempt_id
                    for entry in history
                )
                self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
                self.state["status"] = WorkState.BLOCKED
                self.state["call_state"] = CallState.FAILED
                self.state["next_action"] = "resolve_transaction_conflict"
                self.state["next_due_at"] = timestamp_after(
                    self.options.clock,
                    self.config.perpetual.active_interval_seconds,
                )
                self.state["blocked_reason"] = result.detail
                self.state["last_transaction"] = {
                    "attempt_id": attempt_id,
                    "status": "conflict",
                    "journal_path": rel(self.config, result.journal_path),
                    "mutations": journal.get("mutations", []),
                    "detail": result.detail,
                }
                if not already_recorded:
                    append_history(
                        self.config,
                        self.state,
                        {
                            "event": "transaction_conflict",
                            "attempt_id": attempt_id,
                            "journal_path": rel(self.config, result.journal_path),
                            "detail": result.detail,
                        },
                    )
                save_state(self.config, self.state)
                self._heartbeat("transaction_conflict", None)
                return RunResult(0, WorkState.BLOCKED, None, result.detail)
            if not result.committed:
                continue
            already_recorded = isinstance(history, list) and any(
                isinstance(entry, dict)
                and entry.get("event") == "transaction_recovered"
                and entry.get("attempt_id") == attempt_id
                for entry in history
            )
            self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
            self.state["status"] = WorkState.ACTIVE
            self.state["call_state"] = CallState.SUCCEEDED
            self.state["next_action"] = "tik"
            self.state["next_due_at"] = timestamp_after(self.options.clock, 0)
            self.state["last_transaction"] = {
                "attempt_id": attempt_id,
                "status": "recovered",
                "journal_path": rel(self.config, result.journal_path),
                "mutations": journal.get("mutations", []),
            }
            if not already_recorded:
                append_history(
                    self.config,
                    self.state,
                    {
                        "event": "transaction_recovered",
                        "attempt_id": attempt_id,
                        "journal_path": rel(self.config, result.journal_path),
                    },
                )
            save_state(self.config, self.state)
            mark_transaction_checkpointed(result.journal_path)
        return None

    def _normalize_perpetual_state(self) -> None:
        if not self.config.perpetual.enabled or self.state.get("status") != "complete":
            return
        self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
        self.state["status"] = WorkState.HEALTHY
        self.state["call_state"] = CallState.NOT_DUE
        self.state["next_action"] = "inspect"
        self.state["next_due_at"] = timestamp_after(self.options.clock, self.config.perpetual.healthy_interval_seconds)
        append_history(
            self.config,
            self.state,
            {
                "event": "perpetual_complete_migrated",
                "previous_status": "complete",
                "status": WorkState.HEALTHY,
                "next_due_at": self.state["next_due_at"],
            },
        )
        save_state(self.config, self.state)

    def _scheduled_result(self) -> RunResult | None:
        if not self.config.perpetual.enabled:
            return None
        due_at = parse_timestamp(self.state.get("next_due_at"))
        if due_at is None or normalized_utc(self.options.clock.now()) >= due_at:
            return None
        self.state["call_state"] = CallState.NOT_DUE
        save_state(self.config, self.state)
        self._heartbeat("not_due", None)
        return RunResult(
            0,
            str(self.state.get("status", WorkState.ACTIVE)),
            None,
            f"next perpetual heartbeat is due at {due_at.replace(microsecond=0).isoformat()}",
        )

    def _start_heartbeat(self, emit_heartbeat: bool = True) -> None:
        run_dir = heartbeat_run_dir(self.config, self.state)
        run_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = run_dir
        self._recorder().start(run_dir)
        if emit_heartbeat:
            self._heartbeat("heartbeat_ready", run_dir)

    def _prepare_no_mistakes(self) -> RunResult | None:
        checkpoint = self._no_mistakes_checkpoint()
        if not checkpoint.enabled:
            return None
        with self.telemetry.span(
            "goal_cli.no_mistakes.prepare",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, self._run_dir()),
            },
        ) as span:
            result = checkpoint.prepare(
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
        append_history(
            self.config,
            self.state,
            {
                "event": "no_mistakes_prepare_failed_ignored",
                "status": result.status,
                "detail": result.detail,
                "run_dir": rel(self.config, self._run_dir()),
            },
        )
        save_state(self.config, self.state)
        return None

    def _dry_run(self) -> RunResult:
        run_dir = self._run_dir()
        render_prompts_to_run_dir(self.config, run_dir)
        self._event("dry_run")
        save_state(self.config, self.state)
        self._heartbeat("dry_run_complete", run_dir)
        return RunResult(0, "dry_run", run_dir, f"rendered prompts in {run_dir}")

    def _run_producer(self) -> RunResult | None:
        run_dir = self._run_dir()
        artifact_before = artifact_snapshot(self.config)
        self.state["last_producer"] = producer_state(self.config, run_dir, artifact_before, self.state.get("last_tok"))
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
            if self.config.perpetual.enabled:
                preflight_error = self._mutation_capability_preflight()
                if preflight_error is not None:
                    span.set_attribute("goal.producer.ok", False)
                    return self._finish(
                        0,
                        WorkState.BLOCKED,
                        preflight_error,
                        phase="producer_preflight_blocked",
                        event="producer_preflight_blocked",
                        blocked_reason=preflight_error,
                        next_action="producer",
                        call_state=CallState.FAILED,
                    )
                assert self.config.lease is not None
                attempt_id = f"{run_dir.name}-producer"
                with IsolatedWorkspace(self.config.root, self.config.state_dir, attempt_id) as workspace:
                    isolated_config = rebase_goal_config(self.config, workspace.root)
                    outcome = self.adapters.produce_artifact(
                        isolated_config,
                        run_dir,
                        timeout_seconds=remaining_seconds(self.deadline),
                    )
                    isolated_result = workspace.finalize(self.config.lease) if outcome.ok else None
                if isolated_result is not None and (not isolated_result.authorized or not isolated_result.committed):
                    reason = (
                        f"producer lease violation: {isolated_result.detail}"
                        if not isolated_result.authorized
                        else f"producer canonical drift: {isolated_result.detail}"
                    )
                    span.set_attribute("goal.producer.ok", False)
                    return self._finish(
                        0,
                        WorkState.BLOCKED,
                        reason,
                        phase="producer_delta_rejected",
                        event="producer_delta_rejected",
                        blocked_reason=reason,
                        next_action="producer",
                        call_state=CallState.FAILED,
                    )
                if isolated_result is not None:
                    self._record_committed_transaction(isolated_result, stage="producer", checkpoint=True)
            else:
                outcome = self.adapters.produce_artifact(self.config, run_dir, timeout_seconds=remaining_seconds(self.deadline))
            span.set_attribute("goal.producer.ok", outcome.ok)
        if outcome.ok:
            return None
        if self.config.perpetual.enabled:
            return self._finish(
                0,
                WorkState.BLOCKED,
                "producer command failed",
                phase="producer_failed",
                event="producer_failed",
                blocked_reason="producer command failed",
                next_action="producer",
                call_state=CallState.FAILED,
            )
        return self._finish(
            1,
            "blocked_invalid_review_evidence",
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
                    0 if self.config.perpetual.enabled else 1,
                    WorkState.BLOCKED if self.config.perpetual.enabled else "blocked_invalid_review_evidence",
                    "artifact missing after producer",
                    phase="artifact_missing",
                    event="artifact_missing",
                    blocked_reason=f"artifact missing after producer: {self.config.artifact.path}",
                    next_action="producer" if self.config.perpetual.enabled else None,
                    call_state=CallState.FAILED if self.config.perpetual.enabled else None,
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
        last_producer = self.state.get("last_producer")
        if isinstance(last_producer, dict) and last_producer.get("run_dir") == rel(self.config, self._run_dir()):
            before = last_producer.get("artifact_before_producer")
            before_sha = before.get("sha256") if isinstance(before, dict) else None
            last_producer["artifact_after_producer"] = {**artifact, "exists": True}
            last_producer["artifact_hash_changed_by_producer"] = before_sha != artifact.get("sha256")
            provenance_path = self._run_dir() / "producer_artifact_provenance.json"
            last_producer["provenance_path"] = rel(self.config, provenance_path)
            provenance_path.write_text(json.dumps(last_producer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return artifact

    def _run_tik(self, artifact: dict[str, Any]) -> tuple[dict[str, Any], Path, Path, Path, tuple[TikProviderReview, ...]] | RunResult:
        run_dir = self._run_dir()
        providers = tik_providers(self.config.tik)
        self._heartbeat("tik_running", run_dir)
        with self.telemetry.span(
            "goal_cli.tik",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, run_dir),
                "goal.tik.provider": self.config.tik.provider,
                "goal.tik.providers": [provider.label for provider in providers],
                "goal.tik.provider_count": len(providers),
                "goal.artifact.sha256": artifact["sha256"],
            },
        ) as span:
            reviews = self._run_tik_providers(providers, artifact, run_dir)
            verdict, verdict_path, memo_path, tik_path = aggregate_tik_reviews(self.config, run_dir, artifact, reviews)
            ready = tik_is_ready(self.config, verdict)
            failures = [review for review in reviews if review.error]
            parse_errors = [review for review in reviews if review.parse_error]
            stale_reviews = [review for review in reviews if review.freshness_error is not None]
            set_span_attributes(
                span,
                {
                    "goal.tik.ok": not failures and not parse_errors and not stale_reviews,
                    "goal.tik.memo_path": rel(self.config, memo_path),
                    "goal.tik.verdict_path": rel(self.config, verdict_path),
                    "goal.tik.ledger_path": rel(self.config, tik_path),
                    "goal.tik.parse_error": bool(parse_errors),
                    "goal.tik.ready": ready,
                    "goal.tik.failed_providers": [review.label for review in failures],
                    "goal.tik.stale_providers": [review.label for review in stale_reviews],
                },
            )
            if failures:
                span.set_attribute("goal.tik.ok", False)
                self.state["last_tik"] = tik_state(self.config, run_dir, memo_path, verdict_path, tik_path, artifact, False, reviews)
                return self._finish(
                    0 if self.config.perpetual.enabled else 1,
                    WorkState.BLOCKED if self.config.perpetual.enabled else "blocked_invalid_review_evidence",
                    "tik provider failed",
                    phase="tik_failed",
                    event="tik_failed",
                    blocked_reason="tik provider failed: " + ", ".join(review.label for review in failures),
                    next_action="tik" if self.config.perpetual.enabled else None,
                    artifact=artifact,
                    call_state=CallState.FAILED if self.config.perpetual.enabled else None,
                )
            if parse_errors:
                self.state["last_tik"] = tik_state(self.config, run_dir, memo_path, verdict_path, tik_path, artifact, False, reviews)
                return self._finish(
                    0 if self.config.perpetual.enabled else 1,
                    WorkState.BLOCKED if self.config.perpetual.enabled else "blocked_invalid_review_evidence",
                    "tik verdict was unparseable",
                    phase="tik_unparseable",
                    event="tik_unparseable",
                    blocked_reason="tik output was not parseable or did not match configured verdict fields: "
                    + ", ".join(review.label for review in parse_errors),
                    next_action="tik" if self.config.perpetual.enabled else None,
                    artifact=artifact,
                    call_state=CallState.FAILED if self.config.perpetual.enabled else None,
                )
            if stale_reviews:
                freshness_error = "; ".join(f"{review.label}: {review.freshness_error}" for review in stale_reviews)
                span.set_attribute("goal.tik.fresh", False)
                span.set_attribute("goal.tik.freshness_error", freshness_error)
                self.state["last_tik"] = tik_state(self.config, run_dir, memo_path, verdict_path, tik_path, artifact, False, reviews)
                return self._finish(
                    0 if self.config.perpetual.enabled else 1,
                    WorkState.BLOCKED if self.config.perpetual.enabled else "blocked_invalid_review_evidence",
                    "tik review does not match current artifact",
                    phase="tik_stale",
                    event="tik_stale",
                    blocked_reason=freshness_error,
                    next_action="tik",
                    artifact=artifact,
                    call_state=CallState.FAILED if self.config.perpetual.enabled else None,
                )
            span.set_attribute("goal.tik.fresh", True)
            return verdict, verdict_path, memo_path, tik_path, reviews

    def _run_tik_providers(self, providers: tuple[TikConfig, ...], artifact: dict[str, Any], run_dir: Path) -> tuple[TikProviderReview, ...]:
        if len(providers) == 1:
            return (self._run_tik_provider(providers[0], artifact, run_dir, single_provider=True),)
        results: dict[str, TikProviderReview] = {}
        with ThreadPoolExecutor(max_workers=len(providers), thread_name_prefix="goal-cli-tik") as executor:
            futures = {
                executor.submit(self._run_tik_provider, provider, artifact, run_dir, False): provider.label
                for provider in providers
            }
            for future in as_completed(futures):
                label = futures[future]
                try:
                    results[label] = future.result()
                except Exception as exc:  # defensive; provider failures should be captured inside _run_tik_provider.
                    results[label] = TikProviderReview(label, "unknown", None, None, None, None, False, error=f"tik provider raised {type(exc).__name__}: {exc}")
        return tuple(results[provider.label] for provider in providers)

    def _run_tik_provider(self, tik_provider: TikConfig, artifact: dict[str, Any], run_dir: Path, single_provider: bool) -> TikProviderReview:
        provider_config = replace(tik_provider, verdict=self.config.tik.verdict, providers=())
        provider_goal_config = replace(self.config, tik=provider_config)
        tik_prompt = render_tik_prompt(provider_goal_config, artifact)
        verdict_path = run_dir / ("tik_verdict.json" if single_provider else f"{tik_provider.label}_verdict.json")
        ledger_path = run_dir / ("tik.md" if single_provider else f"{tik_provider.label}.md")
        try:
            if self.config.perpetual.enabled and tik_provider.provider in {"oracle", "checklist"}:
                preflight_error = self._mutation_capability_preflight()
                if preflight_error is not None:
                    raise RuntimeError(preflight_error)
                attempt_id = f"{run_dir.name}-tik-{tik_provider.label}"
                with IsolatedWorkspace(self.config.root, self.config.state_dir, attempt_id) as workspace:
                    isolated_config = rebase_goal_config(provider_goal_config, workspace.root)
                    isolated_prompt = render_tik_prompt(isolated_config, artifact)
                    outcome = self.adapters.run_tik(
                        isolated_config,
                        isolated_prompt,
                        run_dir,
                        timeout_seconds=remaining_seconds(self.deadline),
                    )
            else:
                outcome = self.adapters.run_tik(provider_goal_config, tik_prompt, run_dir, timeout_seconds=remaining_seconds(self.deadline))
        except Exception as exc:
            failure_path = run_dir / f"{tik_provider.label}_FAILED.txt"
            failure_path.write_text(f"tik provider raised {type(exc).__name__}: {exc}\n", encoding="utf-8")
            return TikProviderReview(tik_provider.label, tik_provider.provider, None, None, None, None, False, error=str(exc))
        memo_path = outcome.memo_path
        if memo_path is None:
            return TikProviderReview(tik_provider.label, tik_provider.provider, None, None, None, None, False, error="tik provider failed")

        verdict, parse_error = parse_tik_verdict(self.config, memo_path)
        verdict_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ledger_path = write_tik_ledger(
            provider_goal_config,
            run_dir,
            artifact,
            memo_path,
            verdict_path,
            verdict,
            tik_path=ledger_path,
            title="Referee Report" if single_provider else f"Referee Report: {tik_provider.label}",
        )
        freshness_error = None if parse_error else tik_freshness_error(verdict, artifact)
        ready = False if parse_error or freshness_error else tik_is_ready(self.config, verdict)
        return TikProviderReview(
            tik_provider.label,
            tik_provider.provider,
            memo_path,
            verdict_path,
            ledger_path,
            verdict,
            ready,
            parse_error=parse_error,
            freshness_error=freshness_error,
        )

    def _mutation_capability_preflight(self) -> str | None:
        lease = self.config.lease
        if lease is None:
            return "capability lease is required before perpetual mutation-capable command"
        if not lease.allow_shell:
            return "capability preflight failed: shell execution is not authorized by the lease"
        if isinstance(self.adapters, ProductionGoalProviderAdapters) and mutation_containment_backend() is None:
            return "capability preflight failed: no supported child-process write containment backend is available"
        return None

    def _record_blocker(self, tik_path: Path, artifact: dict[str, Any]) -> RunResult | None:
        update_blocker_state(self.config, self.state, tik_path.read_text(encoding="utf-8") if tik_path.exists() else "")
        return None

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
        source_before = snapshot_file_scope(self.config, self.config.tok.write_dirs)
        mutation_before = snapshot_tok_offlimits(self.config)
        artifact_before_tok = artifact_snapshot(self.config)
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
            outcome = self._execute_tok_attempt(artifact, tik_path, run_dir)
            tok_report_path = outcome.report_path
            source_after = snapshot_file_scope(self.config, self.config.tok.write_dirs)
            source_changes = source_change_summary(self.config, source_before, source_after, self.config.tok.write_dirs)
            artifact_after_tok = artifact_snapshot(self.config)
            artifact_provenance = tok_artifact_provenance(self.config, artifact_before_tok, artifact_after_tok)
            mutation_after = snapshot_tok_offlimits(self.config)
            mutation_audit = tok_mutation_audit(self.config, mutation_before, mutation_after, artifact_provenance)
            source_changes_path = run_dir / "tok_source_changes.json"
            artifact_provenance_path = run_dir / "tok_artifact_provenance.json"
            mutation_audit_path = run_dir / "tok_mutation_audit.json"
            source_changes_path.write_text(json.dumps(source_changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            artifact_provenance_path.write_text(json.dumps(artifact_provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            mutation_audit_path.write_text(json.dumps(mutation_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if not outcome.ok or tok_report_path is None or outcome.report is None:
                failure_kind = outcome.outcome_kind or (
                    AttemptOutcomeKind.PROTOCOL_INVALID if outcome.ok else AttemptOutcomeKind.PROVIDER_ERROR
                )
                self._record_tok_outcome(
                    failure_kind,
                    outcome.detail,
                    tik_path,
                    provider_succeeded=outcome.report_path is not None and outcome.report is not None,
                )
                transition = supervisor_transition(failure_kind)
                set_span_attributes(
                    span,
                    {
                        "goal.tok.ok": False,
                        "goal.tok.report_path": rel(self.config, tok_report_path) if tok_report_path else None,
                        "goal.tok.error": outcome.detail,
                        "goal.tok.local_source_change_count": len(source_changes["changed_paths"]),
                        "goal.tok.artifact_changed_during_tok": artifact_provenance["artifact_changed_during_tok"],
                        "goal.tok.unexpected_mutation_count": len(mutation_audit["unexpected_changed_paths"]),
                    },
                )
                self.state["last_tok_attempt"] = tok_attempt_state(
                    self.config,
                    run_dir,
                    tok_report_path,
                    artifact,
                    source_changes_path,
                    source_changes,
                    artifact_provenance_path,
                    artifact_provenance,
                    mutation_audit_path,
                    mutation_audit,
                    outcome.detail,
                )
                next_action: str | None = "tik" if source_changes["changed_paths"] else "tok"
                phase = "tok_failed_with_source_changes" if source_changes["changed_paths"] else "tok_failed"
                if self.config.perpetual.enabled:
                    next_action = transition.next_action
                    phase = f"tok_{failure_kind}"
                return self._finish(
                    0,
                    transition.work_state if self.config.perpetual.enabled else "active",
                    "tok provider failed; recorded for retry",
                    phase=phase,
                    event="tok_failed_ignored",
                    next_action=next_action,
                    artifact=artifact,
                    blocked_reason=outcome.detail if transition.work_state == WorkState.BLOCKED else None,
                    call_state=transition.call_state if self.config.perpetual.enabled else None,
                    schedule_seconds=(
                        float(self.state["provider_backoff_seconds"])
                        if self.config.perpetual.enabled
                        and failure_kind == AttemptOutcomeKind.PROVIDER_ERROR
                        else None
                    ),
                )

            tok_report = outcome.report
            set_span_attributes(
                span,
                {
                    "goal.tok.ok": True,
                    "goal.tok.report_path": rel(self.config, tok_report_path),
                    "goal.tok.source_change_possible": tok_report.get("source_change_possible"),
                    "goal.tok.local_source_change_count": len(source_changes["changed_paths"]),
                    "goal.tok.local_sources_changed": source_changes["changed_paths"],
                    "goal.tok.artifact_changed_during_tok": artifact_provenance["artifact_changed_during_tok"],
                    "goal.tok.unexpected_mutation_count": len(mutation_audit["unexpected_changed_paths"]),
                },
            )
            self.state["last_tok"] = tok_state(
                self.config,
                run_dir,
                tok_report_path,
                artifact,
                tok_report,
                source_changes_path,
                source_changes,
                artifact_provenance_path,
                artifact_provenance,
                mutation_audit_path,
                mutation_audit,
            )
            if not source_changes["changed_paths"]:
                outcome_kind = (
                    AttemptOutcomeKind.SELF_BLOCKED
                    if tok_report.get("source_change_possible") is False
                    else AttemptOutcomeKind.ZERO_DELTA
                )
                self._record_tok_outcome(outcome_kind, "tok completed without source delta", tik_path)
                transition = supervisor_transition(outcome_kind)
                return self._finish(
                    0,
                    transition.work_state if self.config.perpetual.enabled else "active",
                    "tok completed without changing configured source files",
                    phase="tok_no_source_changes",
                    event="tok_no_source_changes",
                    next_action=transition.next_action if self.config.perpetual.enabled else "tok",
                    artifact=artifact,
                    blocked_reason=(
                        str(tok_report.get("remaining_artifact_bottleneck") or "substantive attempt was blocked")
                        if transition.work_state == WorkState.BLOCKED
                        else None
                    ),
                    call_state=transition.call_state if self.config.perpetual.enabled else None,
                )

            self._record_tok_outcome(AttemptOutcomeKind.APPLIED, "authorized source delta committed", tik_path)
            return self._finish(
                0,
                "active",
                "tok completed; next heartbeat must rebuild and run tik",
                phase="tok_completed",
                event="tok_completed",
                next_action="tik",
                artifact=artifact,
            )

    def _record_tok_outcome(
        self,
        outcome: AttemptOutcomeKind,
        detail: str,
        tik_path: Path,
        *,
        provider_succeeded: bool = False,
    ) -> None:
        context = self.current_attempt_context
        if context is None:
            return
        failure_evidence = tik_path.read_text(encoding="utf-8") if tik_path.exists() else ""
        record_attempt(
            self.state,
            context,
            outcome,
            provider=self.config.tok.provider,
            detail=detail,
            failure_evidence=failure_evidence,
        )
        if outcome == AttemptOutcomeKind.PROVIDER_ERROR:
            failures = int(self.state.get("provider_backoff_failures", 0)) + 1
            schedule = self.config.perpetual.provider_backoff_seconds
            seconds = schedule[min(failures - 1, len(schedule) - 1)]
            self.state["provider_backoff_failures"] = failures
            self.state["provider_backoff_seconds"] = seconds
        elif provider_succeeded or outcome in {
            AttemptOutcomeKind.APPLIED,
            AttemptOutcomeKind.ZERO_DELTA,
            AttemptOutcomeKind.SELF_BLOCKED,
        }:
            self.state["provider_backoff_failures"] = 0
            self.state.pop("provider_backoff_seconds", None)
        self.state["last_attempt_outcome"] = {
            "attempt_id": context.attempt_id,
            "kind": str(outcome),
            "provider": self.config.tok.provider,
            "angle": context.angle,
            "detail": detail,
        }
        self.current_attempt_context = None

    def _execute_tok_attempt(self, artifact: dict[str, Any], tik_path: Path, run_dir: Path):
        from .tok_execution import TokExecutionResult

        if not self.config.perpetual.enabled:
            tok_prompt = render_tok_prompt(self.config, artifact, tik_path, run_dir)
            return self.adapters.execute_tok(
                self.config,
                tok_prompt,
                run_dir,
                timeout_seconds=remaining_seconds(self.deadline),
            )

        lease = self.config.lease
        if lease is None:
            return TokExecutionResult(
                False,
                None,
                None,
                ("capability lease is required before perpetual tok invocation",),
                outcome_kind=AttemptOutcomeKind.LEASE_VIOLATION,
            )
        if not lease.allow_shell:
            return TokExecutionResult(
                False,
                None,
                None,
                ("capability preflight failed: tok provider shell capability is not authorized by the lease",),
                outcome_kind=AttemptOutcomeKind.LEASE_VIOLATION,
            )

        attempt_id = f"{run_dir.name}-tok"
        self.current_attempt_context = prepare_attempt_context(
            self.state,
            self.config.perpetual.reframe_angles,
            attempt_id=attempt_id,
        )
        save_state(self.config, self.state)
        with IsolatedWorkspace(self.config.root, self.config.state_dir, attempt_id) as workspace:
            isolated_config = rebase_goal_config(self.config, workspace.root)
            provider_run_dir = _isolated_provider_run_dir(
                self.config,
                isolated_config,
                run_dir,
            )
            provider_run_dir.mkdir(parents=True, exist_ok=True)
            isolated_config = replace(
                isolated_config,
                tok=replace(
                    isolated_config.tok,
                    attachments_dir=provider_run_dir / "attachments",
                ),
            )
            preflight = preflight_tok_provider(
                isolated_config.tok,
                lease,
                run_dir=provider_run_dir,
                containment_backend=mutation_containment_backend(),
                which=shutil.which,
            )
            if not preflight.ok:
                return TokExecutionResult(
                    False,
                    None,
                    None,
                    (f"capability preflight failed: {preflight.detail}",),
                    outcome_kind=AttemptOutcomeKind.LEASE_VIOLATION,
                )
            tok_prompt = render_tok_prompt(
                isolated_config,
                artifact,
                tik_path,
                provider_run_dir,
                self.current_attempt_context,
            )
            outcome = self.adapters.execute_tok(
                isolated_config,
                tok_prompt,
                run_dir,
                timeout_seconds=remaining_seconds(self.deadline),
            )
            write_tik_review_attachment(
                run_dir,
                tik_path.read_text(encoding="utf-8") if tik_path.exists() else "",
            )
            if not outcome.ok:
                return outcome
            isolated_result = workspace.finalize(lease)

        return self._finalize_isolated_tok(outcome, isolated_result)

    def _finalize_isolated_tok(self, outcome, isolated_result: IsolatedAttemptResult):
        from .tok_execution import TokExecutionResult

        if not isolated_result.authorized:
            return TokExecutionResult(
                False,
                outcome.report_path,
                outcome.report,
                (f"lease violation: {isolated_result.detail}",),
                outcome.plan,
                AttemptOutcomeKind.LEASE_VIOLATION,
            )
        if not isolated_result.committed:
            prefix = "canonical drift" if isolated_result.conflict else "transaction failed"
            return TokExecutionResult(
                False,
                outcome.report_path,
                outcome.report,
                (f"{prefix}: {isolated_result.detail}",),
                outcome.plan,
                AttemptOutcomeKind.LEASE_VIOLATION,
            )
        if isolated_result.journal_path is not None:
            self._record_committed_transaction(isolated_result, stage="tok", checkpoint=False)
        return outcome

    def _record_committed_transaction(
        self,
        isolated_result: IsolatedAttemptResult,
        *,
        stage: str,
        checkpoint: bool,
    ) -> None:
        journal_path = isolated_result.journal_path
        if journal_path is None:
            return
        self.state["last_transaction"] = {
            "attempt_id": isolated_result.attempt_id,
            "stage": stage,
            "status": "committed",
            "journal_path": rel(self.config, journal_path),
            "mutations": [
                {
                    "operation": str(mutation.operation),
                    "path": mutation.path,
                    "source_path": mutation.source_path,
                    "before_identity": mutation.before_identity,
                    "after_identity": mutation.after_identity,
                }
                for mutation in isolated_result.mutations
            ],
        }
        if checkpoint:
            save_state(self.config, self.state)
            mark_transaction_checkpointed(journal_path)
        else:
            self.pending_transaction_journal = journal_path

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
        call_state: CallState | None = None,
        schedule_seconds: float | None = None,
    ) -> RunResult:
        if self.config.perpetual.enabled:
            if status == "complete":
                status = WorkState.HEALTHY
                phase = "healthy"
                event = "healthy"
                next_action = "inspect"
            interval = schedule_seconds
            if interval is None:
                interval = (
                    self.config.perpetual.healthy_interval_seconds
                    if status == WorkState.HEALTHY
                    else self.config.perpetual.active_interval_seconds
                )
            self.state["schema_version"] = max(2, int(self.state.get("schema_version", 1)))
            self.state["call_state"] = call_state or (CallState.SUCCEEDED if exit_code == 0 else CallState.FAILED)
            self.state["next_due_at"] = timestamp_after(self.options.clock, interval)
        checkpoint_result = self._checkpoint_no_mistakes(exit_code, status)
        if checkpoint_result is not None:
            return checkpoint_result
        self._recorder().finish_state(
            status,
            event=event,
            next_action=next_action,
            run_dir=self._run_dir(),
            artifact=artifact,
            blocked_reason=blocked_reason,
        )
        if self.pending_transaction_journal is not None:
            mark_transaction_checkpointed(self.pending_transaction_journal)
            self.pending_transaction_journal = None
        self._heartbeat(phase, self._run_dir())
        return RunResult(exit_code, status, self._run_dir(), message)

    def _checkpoint_no_mistakes(self, exit_code: int, status: str) -> RunResult | None:
        checkpoint = self._no_mistakes_checkpoint()
        if not checkpoint.enabled:
            return None
        if self.options.review_only or status not in {"active", "complete"}:
            return None

        self._heartbeat("no_mistakes_running", self._run_dir())
        with self.telemetry.span(
            "goal_cli.no_mistakes.checkpoint",
            {
                "goal.name": self.config.name,
                "goal.iteration": int(self.state.get("iteration", 0)),
                "goal.run_dir": rel(self.config, self._run_dir()),
                "goal.status.before_checkpoint": status,
            },
        ) as span:
            result = checkpoint.checkpoint(
                self._run_dir(),
                int(self.state.get("iteration", 0)),
                status,
                deadline=self.deadline,
            )
            record_no_mistakes_result(span, result)
        self._record_no_mistakes("no_mistakes_checkpoint", result)
        if result.ok:
            append_history(
                self.config,
                self.state,
                {
                    "event": "no_mistakes_checkpoint",
                    "status": result.status,
                    "branch": result.branch,
                    "commit": result.commit,
                    "log_path": rel(self.config, result.log_path) if result.log_path else None,
                    "run_dir": rel(self.config, self._run_dir()),
                },
            )
            save_state(self.config, self.state)
            return None

        append_history(
            self.config,
            self.state,
            {
                "event": "no_mistakes_checkpoint_failed_ignored",
                "status": result.status,
                "detail": result.detail,
                "branch": result.branch,
                "commit": result.commit,
                "log_path": rel(self.config, result.log_path) if result.log_path else None,
                "run_dir": rel(self.config, self._run_dir()),
            },
        )
        save_state(self.config, self.state)
        return None

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

    def _no_mistakes_checkpoint(self) -> NoMistakesCheckpoint:
        return NoMistakesCheckpoint(self.config)


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
            "goal.no_mistakes.enabled": NoMistakesCheckpoint(config).enabled,
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
    providers = tik_providers(config.tik)
    if len(providers) == 1:
        (run_dir / "tik_prompt.md").write_text(render_tik_prompt(replace(config, tik=providers[0]), artifact), encoding="utf-8")
    else:
        (run_dir / "tik_prompt.md").write_text(
            "Dry run placeholder. This goal has multiple tik providers; provider-specific prompts are rendered next to this file.\n",
            encoding="utf-8",
        )
        for provider in providers:
            provider_config = replace(config, tik=replace(provider, providers=()))
            (run_dir / f"{provider.label}_prompt.md").write_text(render_tik_prompt(provider_config, artifact), encoding="utf-8")
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


def _isolated_provider_run_dir(
    canonical_config: GoalConfig,
    isolated_config: GoalConfig,
    canonical_run_dir: Path,
) -> Path:
    try:
        relative = canonical_run_dir.resolve(strict=False).relative_to(
            canonical_config.runs_dir.resolve(strict=False)
        )
    except ValueError:
        relative = Path(canonical_run_dir.name)
    return (isolated_config.runs_dir / relative).resolve(strict=False)


def render_tok_prompt(
    config: GoalConfig,
    artifact: dict[str, Any],
    tik_path: Path,
    run_dir: Path,
    attempt_context: AttemptContext | None = None,
) -> str:
    tik_ledger = tik_path.read_text(encoding="utf-8") if tik_path.exists() else ""
    tik_review_path = write_tik_review_attachment(run_dir, tik_ledger)
    artifact_path = str(artifact.get("path", rel(config, config.artifact.path)))
    values = {
        "goal_name": config.name,
        "producer_command": config.producer.command,
        "artifact_path": artifact_path,
        "artifact_sha256": str(artifact.get("sha256", "")),
        "tik_review_path": str(tik_review_path),
        "writable_scopes": "\n".join(f"- {path}" for path in config.tok.write_dirs),
        "runtime_writable_scopes": "\n".join(f"- {path}" for path in config.tok.runtime_write_dirs),
        "tok_run_cwd": str(config.tok.run_cwd or (config.tok.write_dirs[0] if config.tok.write_dirs else config.root)),
        "run_dir": str(run_dir),
    }
    prompt = render_template(config.tok.prompt_template, values)
    if attempt_context is not None:
        prompt = f"{prompt.rstrip()}\n{render_attempt_guard(attempt_context)}"
    return prompt


def write_tik_review_attachment(run_dir: Path, report_text: str) -> Path:
    attachment_dir = run_dir / "attachments"
    attachment_dir.mkdir(parents=True, exist_ok=True)
    report_path = attachment_dir / "tik_review.md"
    report_path.write_text(report_text.strip() + "\n", encoding="utf-8")
    return report_path


def aggregate_tik_reviews(
    config: GoalConfig,
    run_dir: Path,
    artifact: dict[str, Any],
    reviews: tuple[TikProviderReview, ...],
) -> tuple[dict[str, Any], Path, Path, Path]:
    if len(reviews) == 1:
        review = reviews[0]
        if review.verdict is not None and review.verdict_path is not None and review.memo_path is not None and review.ledger_path is not None:
            return review.verdict, review.verdict_path, review.memo_path, review.ledger_path

    verdict = aggregate_tik_verdict(config, reviews)
    memo_path = write_aggregate_tik_memo(config, run_dir, reviews)
    verdict_path = run_dir / "tik_verdict.json"
    verdict_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tik_path = write_tik_ledger(config, run_dir, artifact, memo_path, verdict_path, verdict)
    return verdict, verdict_path, memo_path, tik_path


def aggregate_tik_verdict(config: GoalConfig, reviews: tuple[TikProviderReview, ...]) -> dict[str, Any]:
    provider_results: list[dict[str, Any]] = []

    for review in reviews:
        provider_results.append(tik_provider_review_state(config, review))

    ready = bool(reviews) and all(review.ready for review in reviews)
    return {
        config.tik.verdict.ready_field: ready,
        "tik_provider_count": len(reviews),
        "tik_provider_results": provider_results,
        "_parse_error": any(review.parse_error for review in reviews),
    }


def write_aggregate_tik_memo(config: GoalConfig, run_dir: Path, reviews: tuple[TikProviderReview, ...]) -> Path:
    memo_path = run_dir / "tik_memo.md"
    lines = ["# Tik Provider Results", ""]
    for review in reviews:
        lines.extend(
            [
                f"## {review.label} ({review.provider})",
                "",
            ]
        )
        if review.memo_path and review.memo_path.exists():
            lines.append(tik_handoff_text(config, review.memo_path.read_text(encoding="utf-8")))
        else:
            lines.append("No narrative review was provided.")
        lines.append("")
    memo_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return memo_path


def write_tik_ledger(
    config: GoalConfig,
    run_dir: Path,
    artifact: dict[str, Any],
    memo_path: Path,
    verdict_path: Path,
    verdict: dict[str, Any],
    tik_path: Path | None = None,
    title: str = "Referee Report",
) -> Path:
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
    tik_path = tik_path or run_dir / "tik.md"
    body = "\n".join(
        [
            f"# {title}",
            "",
            tik_handoff_text(config, memo),
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


def normalize_retired_status(config: GoalConfig, state: dict[str, Any]) -> None:
    status = state.get("status")
    if status in RETIRED_INVALID_REVIEW_STATUSES:
        state["status"] = "blocked_invalid_review_evidence"
        state["next_action"] = "tik"
        append_history(
            config,
            state,
            {
                "event": "retired_status_migrated",
                "previous_status": status,
                "status": "blocked_invalid_review_evidence",
            },
        )
        save_state(config, state)
        return

    if status not in RETIRED_ACTIVE_STATUSES:
        return

    state["status"] = "active"
    state["next_action"] = next_action_after_retired_active_status(state)
    state.pop("blocked_reason", None)
    append_history(
        config,
        state,
        {
            "event": "retired_status_migrated",
            "previous_status": status,
            "status": "active",
            "next_action": state["next_action"],
        },
    )
    save_state(config, state)


def next_action_after_retired_active_status(state: dict[str, Any]) -> str:
    source_changes = retired_status_source_changes(state)
    if any(not is_ignored_runtime_metadata(Path(path)) for path in source_changes):
        return "tik"
    return "tok"


def retired_status_source_changes(state: dict[str, Any]) -> list[str]:
    for key in ("last_tok", "last_tok_attempt"):
        candidate = state.get(key)
        if not isinstance(candidate, dict):
            continue
        changes = candidate.get("actual_sources_changed")
        if isinstance(changes, list):
            return [str(path) for path in changes if isinstance(path, str)]
    return []


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


def stop_perpetual(config: GoalConfig, *, clock: Clock | None = None) -> RunResult:
    if not config.perpetual.enabled:
        return RunResult(2, "invalid_config", None, "operator stop requires [perpetual] enabled = true")
    try:
        with HeartbeatLock(config.lock_path, config.safety.lock_stale_seconds):
            state = load_state(config)
            state["schema_version"] = max(2, int(state.get("schema_version", 1)))
            state["status"] = WorkState.STOPPED
            state["call_state"] = CallState.CANCELLED
            state["operator_stopped"] = True
            state["next_action"] = "resume"
            append_history(config, state, {"event": "operator_stopped"})
            save_state(config, state)
            update_heartbeat(config, state, "operator_stopped", None)
    except HeartbeatLockError as exc:
        return RunResult(1, "locked", None, str(exc))
    return RunResult(0, WorkState.STOPPED, None, "perpetual goal stopped without terminal completion")


def resume_perpetual(config: GoalConfig, *, clock: Clock | None = None) -> RunResult:
    if not config.perpetual.enabled:
        return RunResult(2, "invalid_config", None, "operator resume requires [perpetual] enabled = true")
    effective_clock = clock or SystemClock()
    try:
        with HeartbeatLock(config.lock_path, config.safety.lock_stale_seconds):
            state = load_state(config)
            state["schema_version"] = max(2, int(state.get("schema_version", 1)))
            state["status"] = WorkState.ACTIVE
            state["call_state"] = CallState.DUE
            state["operator_stopped"] = False
            state["next_action"] = "inspect"
            state["next_due_at"] = timestamp_after(effective_clock, 0)
            state.pop("blocked_reason", None)
            append_history(config, state, {"event": "operator_resumed"})
            save_state(config, state)
            update_heartbeat(config, state, "operator_resumed", None)
    except HeartbeatLockError as exc:
        return RunResult(1, "locked", None, str(exc))
    return RunResult(0, WorkState.ACTIVE, None, "perpetual goal resumed from durable state")


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
        if "codex exec" not in command and "claude --print" not in command and "goal_cli.cli" not in command and "-m goal_cli" not in command:
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
    for required_field in config.tik.verdict.required_fields:
        if required_field not in parsed:
            return _parse_error_verdict(config, f"Tik JSON missing required field: {required_field}", memo_path), True
    ready = parsed.get(config.tik.verdict.ready_field)
    if not isinstance(ready, bool):
        return _parse_error_verdict(config, f"{config.tik.verdict.ready_field} must be boolean", memo_path), True
    verdict = {config.tik.verdict.ready_field: ready, "_parse_error": False}
    for verdict_field in (
        "review_matches_current_pdf",
        "review_matches_current_artifact",
        "reviewed_pdf_sha256",
        "reviewed_artifact_sha256",
        "reviewed_sha256",
        "current_pdf_sha256",
        "current_artifact_sha256",
        "current_sha256",
    ):
        if verdict_field in parsed:
            verdict[verdict_field] = parsed[verdict_field]
    return verdict, False


def extract_json_object(text: str) -> dict[str, Any] | None:
    extracted = extract_json_object_with_span(text)
    return extracted[0] if extracted else None


def extract_json_object_with_span(text: str) -> tuple[dict[str, Any], tuple[int, int]] | None:
    candidates: list[tuple[str, int, int]] = []
    for match in re.finditer(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE):
        candidates.append((match.group(1).strip(), match.start(0), match.end(0)))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        start = text.find(stripped)
        candidates.append((stripped, start, start + len(stripped)))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append((text[start : end + 1], start, end + 1))
    for candidate, span_start, span_end in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, (span_start, span_end)
    return None


def tik_handoff_text(config: GoalConfig, text: str) -> str:
    _ = config
    extracted = extract_json_object_with_span(text)
    if extracted:
        _, (start, end) = extracted
        text = f"{text[:start]}{text[end:]}"
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned or "No narrative review was provided."


def tik_is_ready(config: GoalConfig, verdict: dict[str, Any]) -> bool:
    return verdict.get(config.tik.verdict.ready_field) is True


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


def update_blocker_state(config: GoalConfig, state: dict[str, Any], review_text: str) -> None:
    fingerprint = blocker_fingerprint(review_text)
    if state.get("blocker_fingerprint") == fingerprint:
        repeats = int(state.get("consecutive_blocker_count", 0)) + 1
    else:
        repeats = 1
    state["blocker_fingerprint"] = fingerprint
    state["consecutive_blocker_count"] = repeats
    state["repeated_blocker_ignored"] = repeats >= config.safety.max_blocker_repeats
    state["status"] = "active"
    state["next_action"] = "tok"
    state.pop("blocked_reason", None)


def blocker_fingerprint(review_text: str) -> str:
    normalized = re.sub(r"\s+", " ", tik_handoff_text_for_fingerprint(review_text).lower()).strip() or "tik-not-ready"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def tik_handoff_text_for_fingerprint(review_text: str) -> str:
    extracted = extract_json_object_with_span(review_text)
    if not extracted:
        return review_text
    _, (start, end) = extracted
    return f"{review_text[:start]}{review_text[end:]}"


def artifact_metadata(config: GoalConfig, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": rel(config, path),
        "sha256": sha256_file(path),
        "size_bytes": stat.st_size,
        "mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.UTC).replace(microsecond=0).isoformat(),
    }


def artifact_snapshot(config: GoalConfig) -> dict[str, Any]:
    path = config.artifact.path
    if not path.exists():
        return {"path": rel(config, path), "exists": False}
    return {**artifact_metadata(config, path), "exists": True}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_file_scope(config: GoalConfig, scopes: tuple[Path, ...]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for scope in scopes:
        if not scope.exists():
            continue
        paths = [scope] if scope.is_file() else sorted(scope.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if is_ignored_runtime_metadata(path):
                continue
            stat = path.stat()
            snapshot[rel(config, path)] = {
                "sha256": sha256_file(path),
                "size_bytes": stat.st_size,
                "mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.UTC).replace(microsecond=0).isoformat(),
            }
    return snapshot


def snapshot_tok_offlimits(config: GoalConfig) -> dict[str, dict[str, Any]]:
    root = config.root.resolve(strict=False)
    allowed_scopes = _resolved_scopes(
        (
            *config.tok.write_dirs,
            *config.tok.runtime_write_dirs,
            config.state_dir,
            config.runs_dir,
        )
    )
    skipped_scopes = (*allowed_scopes, (root / ".git").resolve(strict=False))
    snapshot: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return snapshot
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        current_resolved = current_path.resolve(strict=False)
        if _path_in_any_scope(current_resolved, skipped_scopes):
            dirnames[:] = []
            continue
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in IGNORED_RUNTIME_METADATA_DIRNAMES
            and not _path_in_any_scope((current_path / dirname).resolve(strict=False), skipped_scopes)
        ]
        for filename in sorted(filenames):
            path = current_path / filename
            if not path.is_file():
                continue
            if is_ignored_runtime_metadata(path):
                continue
            stat = path.stat()
            snapshot[rel(config, path)] = {
                "sha256": sha256_file(path),
                "size_bytes": stat.st_size,
                "mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.UTC).replace(microsecond=0).isoformat(),
            }
    return snapshot


def source_change_summary(
    config: GoalConfig,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    scopes: tuple[Path, ...],
) -> dict[str, Any]:
    before_paths = set(before)
    after_paths = set(after)
    added = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(path for path in before_paths & after_paths if before[path].get("sha256") != after[path].get("sha256"))
    files: list[dict[str, Any]] = []
    for path in added:
        files.append({"path": path, "change": "added", "after": after[path]})
    for path in modified:
        files.append({"path": path, "change": "modified", "before": before[path], "after": after[path]})
    for path in deleted:
        files.append({"path": path, "change": "deleted", "before": before[path]})
    changed_paths = sorted(added + modified + deleted)
    return {
        "scopes": [rel(config, scope) for scope in scopes],
        "changed_paths": changed_paths,
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "files": files,
    }


def tok_mutation_audit(
    config: GoalConfig,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    artifact_provenance: dict[str, Any],
) -> dict[str, Any]:
    changes = source_change_summary(config, before, after, ())
    protected_scopes = _tok_protected_scopes(config)
    protected_changed = [
        path
        for path in changes["changed_paths"]
        if _path_in_any_scope((config.root / path).resolve(strict=False), protected_scopes)
    ]
    unexpected_changed = changes["changed_paths"]
    return {
        "allowed_scopes": [rel(config, path) for path in _tok_allowed_scopes(config)],
        "protected_scopes": [rel(config, path) for path in protected_scopes],
        "artifact_changed_during_tok": bool(artifact_provenance.get("artifact_changed_during_tok")),
        "unexpected_changed_paths": unexpected_changed,
        "protected_changed_paths": protected_changed,
        "changes": changes,
    }


def tok_artifact_provenance(config: GoalConfig, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_sha = before.get("sha256") if before.get("exists") else None
    after_sha = after.get("sha256") if after.get("exists") else None
    return {
        "artifact_before_tok": before,
        "artifact_after_tok": after,
        "artifact_changed_during_tok": before.get("exists") != after.get("exists") or before_sha != after_sha,
    }


def tik_state(
    config: GoalConfig,
    run_dir: Path,
    memo_path: Path,
    verdict_path: Path,
    tik_path: Path,
    artifact: dict[str, Any],
    ready: bool,
    reviews: tuple[TikProviderReview, ...] = (),
) -> dict[str, Any]:
    state = {
        "run_dir": rel(config, run_dir),
        "memo_path": rel(config, memo_path),
        "verdict_path": rel(config, verdict_path),
        "ledger_path": rel(config, tik_path),
        "artifact_sha256": artifact["sha256"],
        "artifact_ready": ready,
    }
    if reviews:
        state["providers"] = [tik_provider_review_state(config, review) for review in reviews]
    return state


def tik_provider_review_state(config: GoalConfig, review: TikProviderReview) -> dict[str, Any]:
    return {
        "label": review.label,
        "provider": review.provider,
        "memo_path": rel(config, review.memo_path) if review.memo_path else None,
        "verdict_path": rel(config, review.verdict_path) if review.verdict_path else None,
        "ledger_path": rel(config, review.ledger_path) if review.ledger_path else None,
        "artifact_ready": review.ready,
        "parse_error": review.parse_error,
        "freshness_error": review.freshness_error,
        "error": review.error,
    }


def producer_state(config: GoalConfig, run_dir: Path, artifact_before: dict[str, Any], previous_tok: object) -> dict[str, Any]:
    state: dict[str, Any] = {
        "run_dir": rel(config, run_dir),
        "artifact_before_producer": artifact_before,
    }
    if isinstance(previous_tok, dict):
        provenance = previous_tok.get("artifact_provenance")
        if isinstance(provenance, dict):
            after_tok = provenance.get("artifact_after_tok")
            state["previous_tok_artifact_after_sha256"] = after_tok.get("sha256") if isinstance(after_tok, dict) else None
            state["previous_tok_artifact_changed_during_tok"] = provenance.get("artifact_changed_during_tok")
        state["previous_tok_reviewed_artifact_sha256"] = previous_tok.get("reviewed_artifact_sha256")
    return state


def tok_state(
    config: GoalConfig,
    run_dir: Path,
    report_path: Path,
    artifact: dict[str, Any],
    report: dict[str, Any],
    source_changes_path: Path,
    source_changes: dict[str, Any],
    artifact_provenance_path: Path,
    artifact_provenance: dict[str, Any],
    mutation_audit_path: Path,
    mutation_audit: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_dir": rel(config, run_dir),
        "report_path": rel(config, report_path),
        "reviewed_artifact_sha256": artifact["sha256"],
        "source_change_possible": report.get("source_change_possible"),
        "source_changes_path": rel(config, source_changes_path),
        "source_changes": source_changes,
        "actual_sources_changed": source_changes["changed_paths"],
        "artifact_provenance_path": rel(config, artifact_provenance_path),
        "artifact_provenance": artifact_provenance,
        "mutation_audit_path": rel(config, mutation_audit_path),
        "mutation_audit": mutation_audit,
        "revision_strategy": report.get("revision_strategy", ""),
        "expected_artifact_visible_improvement": report.get("expected_artifact_visible_improvement", []),
        "remaining_artifact_bottleneck": report.get("remaining_artifact_bottleneck", ""),
    }


def tok_attempt_state(
    config: GoalConfig,
    run_dir: Path,
    report_path: Path | None,
    artifact: dict[str, Any],
    source_changes_path: Path,
    source_changes: dict[str, Any],
    artifact_provenance_path: Path,
    artifact_provenance: dict[str, Any],
    mutation_audit_path: Path,
    mutation_audit: dict[str, Any],
    error: str,
) -> dict[str, Any]:
    return {
        "run_dir": rel(config, run_dir),
        "report_path": rel(config, report_path) if report_path else None,
        "reviewed_artifact_sha256": artifact["sha256"],
        "source_changes_path": rel(config, source_changes_path),
        "source_changes": source_changes,
        "actual_sources_changed": source_changes["changed_paths"],
        "artifact_provenance_path": rel(config, artifact_provenance_path),
        "artifact_provenance": artifact_provenance,
        "mutation_audit_path": rel(config, mutation_audit_path),
        "mutation_audit": mutation_audit,
        "error": error,
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


def _tok_allowed_scopes(config: GoalConfig) -> tuple[Path, ...]:
    return _resolved_scopes(
        (
            *config.tok.write_dirs,
            *config.tok.runtime_write_dirs,
            config.state_dir,
            config.runs_dir,
        )
    )


def _tok_protected_scopes(config: GoalConfig) -> tuple[Path, ...]:
    return _resolved_scopes(
        (
            config.root / ".git",
            config.path,
            config.artifact.path,
            *config.safety.generated_dirs,
        )
    )


def _resolved_scopes(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        candidate = path.resolve(strict=False)
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(candidate)
    return tuple(resolved)


def _path_in_any_scope(path: Path, scopes: tuple[Path, ...]) -> bool:
    resolved = path.resolve(strict=False)
    for scope in scopes:
        scope_resolved = scope.resolve(strict=False)
        if resolved == scope_resolved:
            return True
        try:
            resolved.relative_to(scope_resolved)
            return True
        except ValueError:
            continue
    return False


def is_ignored_runtime_metadata(path: Path) -> bool:
    name = path.name
    return name in IGNORED_RUNTIME_METADATA_FILENAMES or name.startswith("._")


def remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _parse_error_verdict(config: GoalConfig, message: str, memo_path: Path) -> dict[str, Any]:
    return {
        config.tik.verdict.ready_field: False,
        "error": message,
        "memo_path": str(memo_path),
        "_parse_error": True,
    }
