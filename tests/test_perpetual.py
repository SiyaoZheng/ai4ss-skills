from __future__ import annotations

import datetime as dt
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from goal_cli.adapters import ProducerOutcome, TikOutcome
from goal_cli.config import load_config
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
            config = load_config(self._write_project(root, perpetual=True))
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
            config = load_config(self._write_project(root, perpetual=True))
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
            config = load_config(self._write_project(root, perpetual=True))
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

    def _write_project(self, root: Path, *, perpetual: bool = False) -> Path:
        (root / "src").mkdir(exist_ok=True)
        (root / "output").mkdir(exist_ok=True)
        perpetual_config = "\n[perpetual]\nenabled = true\n" if perpetual else ""
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
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return config_path


class RecordingAdapters:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        self.calls.append("produce")
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


if __name__ == "__main__":
    unittest.main()
