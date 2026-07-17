from __future__ import annotations

import datetime as dt
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from goal_cli.adapters import ProducerOutcome, TikOutcome
from goal_cli.config import load_config
from goal_cli.isolation import IsolatedWorkspace
from goal_cli.lifecycle import CallState, FrozenClock, WorkState
from goal_cli.runtime import RuntimeOptions, load_state, run_goal
from goal_cli.tok_execution import TokExecutionResult


UTC = dt.timezone.utc


class PerpetualLifecycleTests(unittest.TestCase):
    def test_perpetual_mode_is_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            ordinary = load_config(self._write_project(root))
            self.assertFalse(ordinary.perpetual.enabled)

            perpetual = load_config(self._write_project(root, perpetual=True))
            self.assertTrue(perpetual.perpetual.enabled)
            self.assertEqual(perpetual.perpetual.healthy_interval_seconds, 6 * 60 * 60)
            self.assertEqual(perpetual.perpetual.active_interval_seconds, 30 * 60)

    def test_old_complete_checkpoint_migrates_to_healthy_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "goal": config.name,
                        "status": "complete",
                        "iteration": 7,
                        "created_at": "2026-07-01T00:00:00+00:00",
                        "updated_at": "2026-07-01T00:00:00+00:00",
                        "next_action": None,
                        "history": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            adapters = RecordingAdapters()
            now = dt.datetime(2026, 7, 17, 0, 0, tzinfo=UTC)

            result = run_goal(config, RuntimeOptions(max_minutes=0, clock=FrozenClock(now)), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertEqual(result.run_dir, None)
            self.assertEqual(adapters.calls, [])
            state = load_state(config)
            self.assertEqual(state["status"], WorkState.HEALTHY)
            self.assertEqual(state["call_state"], CallState.NOT_DUE)
            self.assertEqual(state["iteration"], 7)
            self.assertEqual(state["next_due_at"], "2026-07-17T06:00:00+00:00")
            self.assertEqual([entry["event"] for entry in state["history"]], ["perpetual_complete_migrated"])

            second = run_goal(config, RuntimeOptions(max_minutes=0, clock=FrozenClock(now)), adapters=adapters)
            self.assertEqual(second.status, WorkState.HEALTHY)
            self.assertEqual(adapters.calls, [])
            self.assertEqual([entry["event"] for entry in load_state(config)["history"]], ["perpetual_complete_migrated"])

    def test_healthy_checkpoint_before_due_time_skips_all_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "goal": config.name,
                        "status": "healthy",
                        "call_state": "not_due",
                        "iteration": 3,
                        "created_at": "2026-07-17T00:00:00+00:00",
                        "updated_at": "2026-07-17T00:00:00+00:00",
                        "next_due_at": "2026-07-17T06:00:00+00:00",
                        "next_action": "inspect",
                        "history": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            adapters = RecordingAdapters()
            now = dt.datetime(2026, 7, 17, 5, 59, 59, tzinfo=UTC)

            result = run_goal(config, RuntimeOptions(max_minutes=0, clock=FrozenClock(now)), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertEqual(result.run_dir, None)
            self.assertEqual(adapters.calls, [])
            self.assertEqual(load_state(config)["iteration"], 3)

    def test_due_healthy_checkpoint_runs_inspection_and_schedules_next_due_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "goal": config.name,
                        "status": "healthy",
                        "call_state": "not_due",
                        "iteration": 3,
                        "created_at": "2026-07-17T00:00:00+00:00",
                        "updated_at": "2026-07-17T00:00:00+00:00",
                        "next_due_at": "2026-07-17T06:00:00+00:00",
                        "next_action": "inspect",
                        "history": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            adapters = RecordingAdapters()
            now = dt.datetime(2026, 7, 17, 6, 0, tzinfo=UTC)

            result = run_goal(config, RuntimeOptions(max_minutes=0, clock=FrozenClock(now)), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertEqual(adapters.calls, ["produce", "tik"])
            state = load_state(config)
            self.assertEqual(state["iteration"], 4)
            self.assertEqual(state["call_state"], CallState.SUCCEEDED)
            self.assertEqual(state["next_due_at"], "2026-07-17T12:00:00+00:00")
            self.assertEqual(state["next_action"], "inspect")

    def test_non_perpetual_complete_checkpoint_stays_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root))
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "goal": config.name,
                        "status": "complete",
                        "iteration": 2,
                        "created_at": "2026-07-17T00:00:00+00:00",
                        "updated_at": "2026-07-17T00:00:00+00:00",
                        "next_action": None,
                        "history": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            adapters = RecordingAdapters()

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, "complete")
            self.assertEqual(adapters.calls, [])
            self.assertEqual(load_state(config)["status"], "complete")

    def test_lifecycle_states_are_typed_and_stable(self) -> None:
        self.assertEqual(WorkState.ACTIVE, "active")
        self.assertEqual(WorkState.HEALTHY, "healthy")
        self.assertEqual(WorkState.BLOCKED, "blocked")
        self.assertEqual(CallState.NOT_DUE, "not_due")
        self.assertEqual(CallState.SUCCEEDED, "succeeded")

    def test_tok_modification_runs_in_isolated_root_and_commits_through_exact_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = EditingAdapters(config.root)

            result = run_goal(
                config,
                RuntimeOptions(max_minutes=0, clock=FrozenClock(dt.datetime(2026, 7, 17, tzinfo=UTC))),
                adapters=adapters,
            )

            self.assertEqual(result.status, WorkState.ACTIVE)
            self.assertEqual(adapters.calls, ["produce", "tik", "tok"])
            self.assertIsNotNone(adapters.tok_root)
            self.assertNotEqual(adapters.tok_root, root)
            self.assertFalse(str(adapters.tok_root).startswith(str(root)))
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "revised in isolation\n")
            state = load_state(config)
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])
            self.assertEqual(state["last_transaction"]["status"], "committed")
            journal_path = root / state["last_transaction"]["journal_path"]
            self.assertTrue(journal_path.exists())
            self.assertEqual(json.loads(journal_path.read_text(encoding="utf-8"))["status"], "CHECKPOINTED")

    def test_unauthorized_isolated_mutation_rejects_entire_tok_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = EditingAdapters(config.root, unauthorized=True)

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.ACTIVE)
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")
            self.assertFalse((root / "governance-checklist.md").exists())
            state = load_state(config)
            self.assertIn("lease violation", state["last_tok_attempt"]["error"])
            self.assertIn("governance-checklist.md", state["last_tok_attempt"]["error"])
            self.assertEqual(state["last_transaction"]["stage"], "producer")

    def test_canonical_drift_during_tok_preserves_user_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = EditingAdapters(config.root, drift=True)

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.ACTIVE)
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "user edit during tok\n")
            state = load_state(config)
            self.assertIn("canonical drift", state["last_tok_attempt"]["error"])
            self.assertIn("src/source.txt", state["last_tok_attempt"]["error"])

    def test_missing_lease_fails_closed_before_tok_provider_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True))
            adapters = EditingAdapters(config.root)

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.BLOCKED)
            self.assertEqual(adapters.calls, [])
            state = load_state(config)
            self.assertIn("capability lease is required", state["blocked_reason"])

    def test_producer_runs_isolated_and_commits_only_authorized_artifact_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = RecordingAdapters()

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertIsNotNone(adapters.producer_root)
            self.assertNotEqual(adapters.producer_root, config.root)
            self.assertFalse(str(adapters.producer_root).startswith(str(config.root)))
            self.assertEqual(config.artifact.path.read_text(encoding="utf-8"), "ready\n")

    def test_unauthorized_producer_mutation_rejects_whole_delta_before_canonical_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = ProducerMutationAdapters()

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.BLOCKED)
            self.assertEqual(adapters.calls, ["produce"])
            self.assertFalse(config.artifact.path.exists())
            self.assertEqual((config.root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")
            self.assertIn("governance-checklist.md", load_state(config)["blocked_reason"])

    def test_command_tik_side_effects_are_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            adapters = TikSideEffectAdapters()

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertIsNotNone(adapters.tik_root)
            self.assertNotEqual(adapters.tik_root, config.root)
            self.assertEqual((config.root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")

    def test_restart_recovers_committed_transaction_state_before_new_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True, lease=True))
            assert config.lease is not None
            with IsolatedWorkspace(config.root, config.state_dir, "attempt-before-state") as workspace:
                (workspace.root / "src" / "source.txt").write_text("committed before crash\n", encoding="utf-8")
                isolated_result = workspace.finalize(config.lease)
            assert isolated_result.journal_path is not None
            self.assertEqual(json.loads(isolated_result.journal_path.read_text(encoding="utf-8"))["status"], "COMMITTED")
            adapters = RecoveryAwareAdapters(config)

            result = run_goal(config, RuntimeOptions(max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, WorkState.HEALTHY)
            self.assertTrue(adapters.recovery_seen_before_producer)
            self.assertEqual((config.root / "src" / "source.txt").read_text(encoding="utf-8"), "committed before crash\n")
            self.assertEqual(json.loads(isolated_result.journal_path.read_text(encoding="utf-8"))["status"], "CHECKPOINTED")
            state = load_state(config)
            self.assertTrue(any(entry["event"] == "transaction_recovered" for entry in state["history"]))

    def _write_project(self, root: Path, *, perpetual: bool = False, lease: bool = False) -> Path:
        (root / "src").mkdir(exist_ok=True)
        (root / "output").mkdir(exist_ok=True)
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        perpetual_config = "\n[perpetual]\nenabled = true\n" if perpetual else ""
        lease_config = (
            """

            [lease]
            version = "lease-v1"
            allow_shell = true
            allow_network = false

            [[lease.rules]]
            effect = "allow"
            operations = ["modify"]
            paths = ["src/source.txt"]

            [[lease.rules]]
            effect = "allow"
            operations = ["create", "modify"]
            paths = ["output/artifact.txt"]
            """
            if lease
            else ""
        )
        config_path = root / "goal.toml"
        config_path.write_text(
            textwrap.dedent(
                f"""
                name = "perpetual-lifecycle-test"
                state_dir = ".goal"
                runs_dir = ".goal/runs"

                [artifact]
                path = "output/artifact.txt"

                [producer]
                command = "unused-producer"

                [tik]
                provider = "oracle"
                command = "unused-tik"

                [tik.prompt]
                text = "Evaluate {{artifact_path}}."

                [tok]
                provider = "codex_goal"
                write_dirs = ["src"]
                run_cwd = "."
                sandbox = "workspace-write"

                [tok.prompt]
                template = "Goal {{goal_name}} review {{tik_review_path}}"

                [no_mistakes]
                enabled = false

                [observability]
                enabled = false

                [safety]
                generated_dirs = ["output"]
                {perpetual_config}
                {lease_config}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return config_path


class RecordingAdapters:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.producer_root: Path | None = None

    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        self.calls.append("produce")
        self.producer_root = config.root
        config.artifact.path.write_text("ready\n", encoding="utf-8")
        return ProducerOutcome(True)

    def run_tik(self, config, prompt, run_dir, timeout_seconds=None) -> TikOutcome:
        self.calls.append("tik")
        memo_path = run_dir / "tik_memo.md"
        memo_path.write_text('{"artifact_ready": true}\n', encoding="utf-8")
        return TikOutcome(memo_path)

    def execute_tok(self, config, prompt, run_dir, timeout_seconds=None) -> TokExecutionResult:
        self.calls.append("tok")
        return TokExecutionResult(False, None, None, ("unused",))


class EditingAdapters(RecordingAdapters):
    def __init__(self, canonical_root: Path, *, unauthorized: bool = False, drift: bool = False) -> None:
        super().__init__()
        self.canonical_root = canonical_root
        self.unauthorized = unauthorized
        self.drift = drift
        self.tok_root: Path | None = None

    def run_tik(self, config, prompt, run_dir, timeout_seconds=None) -> TikOutcome:
        self.calls.append("tik")
        memo_path = run_dir / "tik_memo.md"
        memo_path.write_text('{"artifact_ready": false}\n', encoding="utf-8")
        return TikOutcome(memo_path)

    def execute_tok(self, config, prompt, run_dir, timeout_seconds=None) -> TokExecutionResult:
        self.calls.append("tok")
        self.tok_root = config.root
        (config.root / "src" / "source.txt").write_text("revised in isolation\n", encoding="utf-8")
        if self.unauthorized:
            (config.root / "governance-checklist.md").write_text("substitute work\n", encoding="utf-8")
        if self.drift:
            (self.canonical_root / "src" / "source.txt").write_text("user edit during tok\n", encoding="utf-8")
        report = {
            "source_change_possible": True,
            "revision_strategy": "revise manuscript",
            "expected_artifact_visible_improvement": ["clearer argument"],
            "remaining_artifact_bottleneck": "",
        }
        report_path = run_dir / "tok_report.json"
        report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")
        return TokExecutionResult(True, report_path, report, ())


class RecoveryAwareAdapters(RecordingAdapters):
    def __init__(self, canonical_config) -> None:
        super().__init__()
        self.canonical_config = canonical_config
        self.recovery_seen_before_producer = False

    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        state = load_state(self.canonical_config)
        self.recovery_seen_before_producer = any(entry["event"] == "transaction_recovered" for entry in state["history"])
        return super().produce_artifact(config, run_dir, timeout_seconds)


class ProducerMutationAdapters(RecordingAdapters):
    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        super().produce_artifact(config, run_dir, timeout_seconds)
        (config.root / "governance-checklist.md").write_text("producer substitute work\n", encoding="utf-8")
        return ProducerOutcome(True)


class TikSideEffectAdapters(RecordingAdapters):
    def __init__(self) -> None:
        super().__init__()
        self.tik_root: Path | None = None

    def run_tik(self, config, prompt, run_dir, timeout_seconds=None) -> TikOutcome:
        self.calls.append("tik")
        self.tik_root = config.root
        (config.root / "src" / "source.txt").write_text("tik side effect\n", encoding="utf-8")
        memo_path = run_dir / "tik_memo.md"
        memo_path.write_text('{"artifact_ready": true}\n', encoding="utf-8")
        return TikOutcome(memo_path)


if __name__ == "__main__":
    unittest.main()
