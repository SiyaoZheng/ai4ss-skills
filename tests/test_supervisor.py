from __future__ import annotations

import unittest

from goal_cli.supervisor import (
    AttemptOutcomeKind,
    ensure_goal_identity,
    prepare_attempt_context,
    record_attempt,
    render_attempt_guard,
)


ANGLES = (
    "repair the evidence chain",
    "restructure the argument",
    "revisit measurement",
    "add a robustness check",
    "sharpen literature positioning",
    "improve reader-facing exposition",
    "repair artifact generation",
)


class PerpetualSupervisorTests(unittest.TestCase):
    def test_reframe_avoids_six_most_recent_consumed_angles(self) -> None:
        state: dict[str, object] = {}
        ensure_goal_identity(state, "Write the paper", "lease-v1")
        for index, angle in enumerate(ANGLES[:6]):
            context = prepare_attempt_context(state, ANGLES, attempt_id=f"attempt-{index}")
            self.assertEqual(context.angle, angle)
            record_attempt(
                state,
                context,
                AttemptOutcomeKind.SELF_BLOCKED,
                provider="fake",
                detail=f"blocked {index}",
                failure_evidence=f"failure {index}",
            )

        next_context = prepare_attempt_context(state, ANGLES, attempt_id="attempt-7")

        self.assertEqual(next_context.angle, ANGLES[6])
        self.assertEqual(len(next_context.recent_attempts), 6)
        self.assertIn("self_blocked=6", next_context.aggregate_history)

    def test_provider_error_preserves_pending_angle_and_does_not_consume_it(self) -> None:
        state: dict[str, object] = {}
        ensure_goal_identity(state, "Write the paper", "lease-v1")
        first = prepare_attempt_context(state, ANGLES, attempt_id="attempt-1")

        record_attempt(
            state,
            first,
            AttemptOutcomeKind.PROVIDER_ERROR,
            provider="codex_goal",
            detail="provider unavailable",
            failure_evidence="",
        )
        retry = prepare_attempt_context(state, ANGLES, attempt_id="attempt-2")

        self.assertEqual(retry.angle, first.angle)
        supervisor = state["attempt_supervisor"]
        assert isinstance(supervisor, dict)
        self.assertEqual(supervisor["recent"], [])
        self.assertEqual(supervisor["angle_counts"], {})

    def test_substantive_blocker_and_resource_limit_consume_angles(self) -> None:
        state: dict[str, object] = {}
        ensure_goal_identity(state, "Write the paper", "lease-v1")
        first = prepare_attempt_context(state, ANGLES, attempt_id="attempt-1")
        record_attempt(
            state,
            first,
            AttemptOutcomeKind.RESOURCE_LIMIT,
            provider="claude_code_goal",
            detail="context limit",
            failure_evidence="review remains unresolved",
        )
        second = prepare_attempt_context(state, ANGLES, attempt_id="attempt-2")

        self.assertNotEqual(second.angle, first.angle)

    def test_prompt_guard_is_bounded_and_forbids_governance_substitutes(self) -> None:
        state: dict[str, object] = {}
        ensure_goal_identity(state, "Write the paper", "lease-v1")
        context = prepare_attempt_context(state, ANGLES, attempt_id="attempt-1")
        record_attempt(
            state,
            context,
            AttemptOutcomeKind.SELF_BLOCKED,
            provider="fake",
            detail="x" * 5000,
            failure_evidence="evidence " * 1000,
        )
        retry = prepare_attempt_context(state, ANGLES, attempt_id="attempt-2")

        guard = render_attempt_guard(retry)

        self.assertLess(len(guard), 5000)
        self.assertIn("Write the paper", guard)
        self.assertIn("lease-v1", guard)
        self.assertIn(retry.angle, guard)
        self.assertIn("recent failure evidence", guard.lower())
        self.assertIn("Do not create an audit, gate, score, checklist, process document, or CI configuration", guard)
        self.assertIn("Do not ask for human help", guard)

    def test_goal_or_lease_change_is_rejected_after_identity_is_bound(self) -> None:
        state: dict[str, object] = {}

        self.assertIsNone(ensure_goal_identity(state, "Write the paper", "lease-v1"))
        self.assertIsNone(ensure_goal_identity(state, "Write the paper", "lease-v1"))
        self.assertIn("substantive goal changed", ensure_goal_identity(state, "Write a different paper", "lease-v1") or "")
        self.assertIn("lease version changed", ensure_goal_identity(state, "Write the paper", "lease-v2") or "")

    def test_all_required_outcome_kinds_are_stable(self) -> None:
        self.assertEqual(
            {str(kind) for kind in AttemptOutcomeKind},
            {
                "applied",
                "zero_delta",
                "self_blocked",
                "lease_violation",
                "protocol_invalid",
                "resource_limit",
                "provider_error",
                "operator_cancel",
            },
        )


if __name__ == "__main__":
    unittest.main()
