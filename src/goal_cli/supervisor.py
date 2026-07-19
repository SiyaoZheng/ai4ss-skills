from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


DEFAULT_REFRAME_ANGLES = (
    "repair the evidence chain",
    "restructure the substantive argument",
    "revisit measurement or analysis",
    "add a targeted robustness check",
    "sharpen literature positioning",
    "improve reader-facing exposition",
    "repair direct artifact generation",
)


class AttemptOutcomeKind(StrEnum):
    APPLIED = "applied"
    ZERO_DELTA = "zero_delta"
    SELF_BLOCKED = "self_blocked"
    LEASE_VIOLATION = "lease_violation"
    PROTOCOL_INVALID = "protocol_invalid"
    RESOURCE_LIMIT = "resource_limit"
    PROVIDER_ERROR = "provider_error"
    OPERATOR_CANCEL = "operator_cancel"


@dataclass(frozen=True)
class AttemptContext:
    attempt_id: str
    substantive_goal: str
    goal_identity: str
    lease_version: str
    angle: str
    recent_attempts: tuple[dict[str, str], ...]
    aggregate_history: str


def ensure_goal_identity(state: dict[str, Any], substantive_goal: str, lease_version: str) -> str | None:
    goal = substantive_goal.strip()
    version = lease_version.strip()
    identity = hashlib.sha256(goal.encode("utf-8")).hexdigest()
    binding = state.get("goal_binding")
    if binding is None:
        state["goal_binding"] = {
            "substantive_goal": goal,
            "goal_identity": identity,
            "lease_version": version,
        }
        return None
    if not isinstance(binding, dict):
        return "stored perpetual goal binding is invalid"
    if binding.get("goal_identity") != identity or binding.get("substantive_goal") != goal:
        return "substantive goal changed after perpetual execution began"
    if binding.get("lease_version") != version:
        return "capability lease version changed after perpetual execution began"
    return None


def prepare_attempt_context(
    state: dict[str, Any],
    angles: tuple[str, ...],
    *,
    attempt_id: str,
) -> AttemptContext:
    if not angles:
        raise ValueError("at least one substantive reframe angle is required")
    binding = state.get("goal_binding")
    if not isinstance(binding, dict):
        raise ValueError("perpetual goal identity must be bound before preparing an attempt")
    supervisor = _supervisor_state(state)
    pending_angle = supervisor.get("pending_angle")
    if isinstance(pending_angle, str) and pending_angle in angles:
        angle = pending_angle
    else:
        angle = _select_angle(supervisor, angles)
        supervisor["pending_angle"] = angle
    recent = supervisor.get("recent")
    recent_attempts = tuple(
        {
            "attempt_id": str(item.get("attempt_id", "")),
            "angle": str(item.get("angle", "")),
            "outcome": str(item.get("outcome", "")),
            "provider": str(item.get("provider", "")),
            "detail": str(item.get("detail", "")),
            "failure_evidence": str(item.get("failure_evidence", "")),
        }
        for item in recent
        if isinstance(item, dict)
    ) if isinstance(recent, list) else ()
    return AttemptContext(
        attempt_id=attempt_id,
        substantive_goal=str(binding["substantive_goal"]),
        goal_identity=str(binding["goal_identity"]),
        lease_version=str(binding["lease_version"]),
        angle=angle,
        recent_attempts=recent_attempts,
        aggregate_history=_aggregate_history(supervisor),
    )


def record_attempt(
    state: dict[str, Any],
    context: AttemptContext,
    outcome: AttemptOutcomeKind,
    *,
    provider: str,
    detail: str,
    failure_evidence: str,
) -> None:
    supervisor = _supervisor_state(state)
    outcome_counts = _string_int_dict(supervisor, "outcome_counts")
    outcome_counts[str(outcome)] = outcome_counts.get(str(outcome), 0) + 1
    supervisor["total_attempts"] = int(supervisor.get("total_attempts", 0)) + 1

    if outcome == AttemptOutcomeKind.PROVIDER_ERROR:
        supervisor["last_provider_error"] = _clip(detail, 800)
        return
    if outcome in {
        AttemptOutcomeKind.OPERATOR_CANCEL,
        AttemptOutcomeKind.LEASE_VIOLATION,
        AttemptOutcomeKind.PROTOCOL_INVALID,
    }:
        return

    angle_counts = _string_int_dict(supervisor, "angle_counts")
    angle_counts[context.angle] = angle_counts.get(context.angle, 0) + 1
    recent = supervisor.setdefault("recent", [])
    if not isinstance(recent, list):
        recent = []
        supervisor["recent"] = recent
    recent.append(
        {
            "attempt_id": context.attempt_id,
            "angle": context.angle,
            "outcome": str(outcome),
            "provider": provider,
            "detail": _clip(detail, 600),
            "failure_evidence": _clip(failure_evidence, 900),
        }
    )
    del recent[:-6]
    supervisor.pop("pending_angle", None)


def render_attempt_guard(context: AttemptContext) -> str:
    recent_lines: list[str] = []
    for item in context.recent_attempts:
        evidence = item.get("failure_evidence") or item.get("detail") or "no evidence recorded"
        recent_lines.append(
            f"- {item.get('outcome', 'unknown')} via {item.get('angle', 'unknown angle')}: {_clip(evidence, 350)}"
        )
    if not recent_lines:
        recent_lines.append("- no prior substantive attempt evidence")
    return "\n".join(
        [
            "",
            "## Perpetual attempt boundary",
            f"Substantive goal: {context.substantive_goal}",
            f"Goal identity: {context.goal_identity}",
            f"Capability lease version: {context.lease_version}",
            f"Current substantive angle: {context.angle}",
            f"Deterministic aggregate attempt history: {context.aggregate_history}",
            "Recent failure evidence:",
            *recent_lines,
            "",
            "Keep the exact substantive goal and capability lease.",
            "Use the current angle materially; do not repeat the same recent approach.",
            "Do not create an audit, gate, score, checklist, process document, or CI configuration as substitute output.",
            "Do not ask for human help, permission expansion, or a new goal.",
            "If blocked, preserve concrete failure evidence for the next unattended heartbeat.",
            "",
        ]
    )


def _select_angle(supervisor: dict[str, Any], angles: tuple[str, ...]) -> str:
    recent = supervisor.get("recent")
    recent_angles = {
        str(item.get("angle"))
        for item in recent[-6:]
        if isinstance(recent, list) and isinstance(item, dict) and item.get("angle") is not None
    } if isinstance(recent, list) else set()
    counts = supervisor.get("angle_counts")
    angle_counts = counts if isinstance(counts, dict) else {}
    unused = [angle for angle in angles if angle not in recent_angles]
    candidates = unused or list(angles)
    return min(candidates, key=lambda angle: (int(angle_counts.get(angle, 0)), angles.index(angle)))


def _supervisor_state(state: dict[str, Any]) -> dict[str, Any]:
    supervisor = state.setdefault(
        "attempt_supervisor",
        {
            "total_attempts": 0,
            "outcome_counts": {},
            "angle_counts": {},
            "recent": [],
        },
    )
    if not isinstance(supervisor, dict):
        raise ValueError("attempt_supervisor state must be an object")
    return supervisor


def _string_int_dict(supervisor: dict[str, Any], key: str) -> dict[str, int]:
    value = supervisor.setdefault(key, {})
    if not isinstance(value, dict):
        value = {}
        supervisor[key] = value
    return value


def _aggregate_history(supervisor: dict[str, Any]) -> str:
    total = int(supervisor.get("total_attempts", 0))
    outcomes = supervisor.get("outcome_counts")
    angles = supervisor.get("angle_counts")
    outcome_text = ",".join(f"{key}={int(value)}" for key, value in sorted(outcomes.items())) if isinstance(outcomes, dict) else ""
    angle_text = ",".join(f"{key}={int(value)}" for key, value in sorted(angles.items())) if isinstance(angles, dict) else ""
    return f"total={total}; outcomes={outcome_text or 'none'}; angles={angle_text or 'none'}"


def _clip(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."
