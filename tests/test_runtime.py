from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.adapters import api_tik_client_options, build_api_tik_prompt, effective_api_tik_model, run_tik
from goal_cli.config import DEFAULT_API_TIK_BASE_URL, DEFAULT_API_TIK_MODEL, ConfigError, TikConfig, TokConfig, load_config, validate_config
from goal_cli.runtime import DEFAULT_MAX_MINUTES, HeartbeatLock, RuntimeOptions, cleanup_runtime, load_state, run_heartbeat, run_goal
from goal_cli.tok_execution import build_claude_code_goal_tok_plan, build_codex_app_server_tok_plan, build_codex_goal_tok_plan, execute_tok


class GoalRuntimeTests(unittest.TestCase):
    def test_runtime_options_default_to_ten_hour_budget(self) -> None:
        self.assertEqual(RuntimeOptions().max_minutes, DEFAULT_MAX_MINUTES)
        self.assertEqual(DEFAULT_MAX_MINUTES, 600.0)

    def test_heartbeat_lock_recovers_dead_pid_before_stale_age(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / ".goal" / ".heartbeat.lock"
            lock_path.parent.mkdir()
            lock_path.write_text(json.dumps({"pid": 999999999, "created_at": "2026-07-04T00:00:00+00:00"}) + "\n", encoding="utf-8")

            with HeartbeatLock(lock_path, stale_seconds=6 * 60 * 60):
                self.assertTrue(lock_path.exists())

            self.assertFalse(lock_path.exists())

    def test_heartbeat_lock_exit_only_releases_owned_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / ".goal" / ".heartbeat.lock"
            lock = HeartbeatLock(lock_path, stale_seconds=6 * 60 * 60)
            lock.__enter__()
            successor_payload = {"pid": os.getpid(), "created_at": "2026-07-04T00:00:00+00:00", "token": "successor"}
            lock_path.write_text(json.dumps(successor_payload) + "\n", encoding="utf-8")

            lock.__exit__(None, None, None)

            self.assertEqual(json.loads(lock_path.read_text(encoding="utf-8")), successor_payload)

    def test_run_goal_reports_active_lock_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")
            config.state_dir.mkdir(parents=True)
            config.lock_path.write_text(json.dumps({"pid": os.getpid(), "created_at": "2026-07-04T00:00:00+00:00"}) + "\n", encoding="utf-8")
            heartbeat_text = json.dumps({"phase": "tok_running", "run_dir": ".goal/runs/heartbeat-0001"}) + "\n"
            config.heartbeat_path.write_text(heartbeat_text, encoding="utf-8")

            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "locked")
            self.assertIn("heartbeat already running", result.message)
            self.assertEqual(config.heartbeat_path.read_text(encoding="utf-8"), heartbeat_text)

    def test_cleanup_removes_dead_lock_and_marks_interrupted_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")
            config.state_dir.mkdir(parents=True)
            config.lock_path.write_text(
                json.dumps({"pid": 999999999, "created_at": "2026-07-05T00:00:00+00:00", "token": "dead"}) + "\n",
                encoding="utf-8",
            )
            config.heartbeat_path.write_text(
                json.dumps(
                    {
                        "goal": config.name,
                        "phase": "tok_running",
                        "status": "active",
                        "iteration": 1,
                        "last_seen": "2026-07-05T00:00:00+00:00",
                        "run_dir": ".goal/runs/heartbeat-0001",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = cleanup_runtime(config)

            self.assertFalse(config.lock_path.exists())
            self.assertTrue(any("removed stale heartbeat lock" in action for action in result.actions))
            heartbeat = json.loads(config.heartbeat_path.read_text(encoding="utf-8"))
            self.assertEqual(heartbeat["phase"], "interrupted")
            self.assertEqual(heartbeat["previous_phase"], "tok_running")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tik")
            self.assertEqual(state["history"][-1]["event"], "cleanup_interrupted")

    def test_cleanup_leaves_live_lock_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")
            config.state_dir.mkdir(parents=True)
            config.lock_path.write_text(
                json.dumps({"pid": os.getpid(), "created_at": "2026-07-05T00:00:00+00:00", "token": "live"}) + "\n",
                encoding="utf-8",
            )

            result = cleanup_runtime(config)

            self.assertTrue(config.lock_path.exists())
            self.assertTrue(any("active" in warning for warning in result.warnings))

    def test_run_goal_advances_one_heartbeat_at_a_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)

            config = load_config(root / "goal.toml")
            first_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(first_result.exit_code, 0)
            self.assertEqual(first_result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["iteration"], 1)
            self.assertEqual(state["next_action"], "tik")
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])
            self.assertTrue((root / state["last_tok"]["source_changes_path"]).exists())
            self.assertFalse(state["last_tok"]["artifact_provenance"]["artifact_changed_during_tok"])
            first_reviewed_sha = state["last_tok"]["reviewed_artifact_sha256"]
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "draft\n")
            heartbeat = json.loads((root / ".goal" / "heartbeat.json").read_text(encoding="utf-8"))
            self.assertEqual(heartbeat["phase"], "tok_completed")

            second_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(second_result.exit_code, 0)
            self.assertEqual(second_result.status, "complete")
            state = load_state(config)
            self.assertEqual(state["status"], "complete")
            self.assertEqual(state["iteration"], 2)
            self.assertEqual(state["last_producer"]["previous_tok_reviewed_artifact_sha256"], first_reviewed_sha)
            self.assertTrue((root / state["last_producer"]["provenance_path"]).exists())
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "ready\n")

    def test_active_heartbeat_is_success_and_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)

            config = load_config(root / "goal.toml")
            first_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(first_result.exit_code, 0)
            self.assertEqual(first_result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tik")
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "draft\n")

            second_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(second_result.exit_code, 0)
            self.assertEqual(second_result.status, "complete")
            self.assertEqual(load_state(config)["status"], "complete")

    def test_retired_tok_blocked_status_resumes_as_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "success_no_change"})
            config = load_config(root / "goal.toml")
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "goal": config.name,
                        "status": "blocked_tok_unexpected_mutation",
                        "iteration": 0,
                        "created_at": "2026-07-04T00:00:00+00:00",
                        "updated_at": "2026-07-04T00:00:00+00:00",
                        "next_action": None,
                        "blocked_reason": "tok modified paths outside declared scopes: .DS_Store",
                        "history": [],
                        "last_tok_attempt": {"actual_sources_changed": ["src/.DS_Store"]},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertNotIn("blocked_reason", state)
            self.assertEqual(state["history"][0]["event"], "retired_status_migrated")
            self.assertEqual(state["history"][0]["previous_status"], "blocked_tok_unexpected_mutation")

    def test_multiple_tik_providers_run_in_parallel_and_tok_receives_aggregate_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_barrier_tik(root, "alpha", "beta", "alpha objection")
            self._write_barrier_tik(root, "beta", "alpha", "beta objection")
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    '[tik]\nprovider = "oracle"\ncommand = "python3 scripts/tik.py"',
                    textwrap.dedent(
                        """
                        [tik]
                        timeout_seconds = 5

                        [[tik.providers]]
                        label = "alpha"
                        provider = "oracle"
                        command = "python3 scripts/tik_alpha.py"

                        [[tik.providers]]
                        label = "beta"
                        provider = "oracle"
                        command = "python3 scripts/tik_beta.py"
                        """
                    ).strip(),
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0, result.message)
            self.assertEqual(result.status, "active")
            assert result.run_dir is not None
            tik_ledger = (result.run_dir / "tik.md").read_text(encoding="utf-8")
            tik_attachment = (result.run_dir / "attachments" / "tik_review.md").read_text(encoding="utf-8")
            self.assertIn("alpha objection", tik_ledger)
            self.assertIn("beta objection", tik_ledger)
            self.assertIn("## alpha (oracle)", tik_ledger)
            self.assertIn("## beta (oracle)", tik_ledger)
            self.assertNotIn("artifact_ready", tik_ledger)
            self.assertEqual(tik_attachment.strip(), tik_ledger.strip())
            self.assertTrue((result.run_dir / "alpha.md").exists())
            self.assertTrue((result.run_dir / "beta.md").exists())
            self.assertTrue((result.run_dir / "alpha_memo.md").exists())
            self.assertTrue((result.run_dir / "beta_memo.md").exists())
            state = load_state(config)
            self.assertEqual([provider["label"] for provider in state["last_tik"]["providers"]], ["alpha", "beta"])
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])

    def test_checklist_tik_provider_runs_command_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_barrier_tik(root, "alpha", "checklist", "alpha objection")
            self._write_barrier_tik(root, "checklist", "alpha", "checklist objection")
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    '[tik]\nprovider = "oracle"\ncommand = "python3 scripts/tik.py"',
                    textwrap.dedent(
                        """
                        [tik]
                        timeout_seconds = 5

                        [[tik.providers]]
                        label = "alpha"
                        provider = "oracle"
                        command = "python3 scripts/tik_alpha.py"

                        [[tik.providers]]
                        label = "checklist"
                        provider = "checklist"
                        command = "python3 scripts/tik_checklist.py"
                        """
                    ).strip(),
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0, result.message)
            self.assertEqual(result.status, "active")
            assert result.run_dir is not None
            tik_ledger = (result.run_dir / "tik.md").read_text(encoding="utf-8")
            self.assertIn("checklist objection", tik_ledger)
            self.assertIn("## checklist (checklist)", tik_ledger)
            self.assertTrue((result.run_dir / "checklist_memo.md").exists())
            state = load_state(config)
            self.assertEqual(state["last_tik"]["providers"][1]["provider"], "checklist")
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])

    def test_tok_success_without_source_diff_is_not_a_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "success_no_change"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_no_source_changes")
            self.assertEqual(state["last_tok"]["actual_sources_changed"], [])
            self.assertTrue((root / state["last_tok"]["source_changes_path"]).exists())

    def test_tok_artifact_mutation_is_observed_not_restored_by_goal_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "mutate_artifact"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tik")
            provenance = state["last_tok"]["artifact_provenance"]
            self.assertTrue(provenance["artifact_changed_during_tok"])
            self.assertNotEqual(
                provenance["artifact_before_tok"]["sha256"],
                provenance["artifact_after_tok"]["sha256"],
            )
            self.assertTrue((root / state["last_tok"]["artifact_provenance_path"]).exists())
            self.assertTrue((root / state["last_tok"]["mutation_audit_path"]).exists())
            self.assertEqual(state["last_tok"]["mutation_audit"]["artifact_changed_during_tok"], True)
            self.assertNotIn("artifact_restored_after_tok", state["last_tok"]["mutation_audit"])
            self.assertNotIn("artifact_restoration", provenance)
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "hand-edited artifact\n")

            second_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(second_result.exit_code, 0)
            self.assertEqual(second_result.status, "complete")
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "ready\n")

    def test_tok_generated_mutation_without_runtime_scope_is_observed_not_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "mutate_generated"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tik")
            audit = state["last_tok"]["mutation_audit"]
            self.assertIn("output/tok-side-effect.txt", audit["unexpected_changed_paths"])
            self.assertIn("output/tok-side-effect.txt", audit["protected_changed_paths"])
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])

    def test_tok_metadata_mutations_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "metadata_only"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_no_source_changes")
            self.assertEqual(state["last_tok"]["actual_sources_changed"], [])
            self.assertEqual(state["last_tok"]["mutation_audit"]["unexpected_changed_paths"], [])

    def test_tok_declared_runtime_write_dir_can_change_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    'write_dirs = ["src"]',
                    'write_dirs = ["src"]\nrun_cwd = "."\nruntime_write_dirs = ["output"]',
                ),
                encoding="utf-8",
            )
            self._write_tok_behavior(root, {"mode": "mutate_generated"})

            config = load_config(config_path)
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            audit = state["last_tok"]["mutation_audit"]
            self.assertEqual(audit["unexpected_changed_paths"], [])
            self.assertEqual(state["last_tok"]["actual_sources_changed"], ["src/source.txt"])

    def test_successful_tok_clears_stale_blocked_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")
            config.state_dir.mkdir(parents=True)
            config.state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "goal": config.name,
                        "status": "active",
                        "iteration": 0,
                        "created_at": "2026-07-04T00:00:00+00:00",
                        "updated_at": "2026-07-04T00:00:00+00:00",
                        "next_action": "tik",
                        "blocked_reason": "stale blocker",
                        "history": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.status, "active")
            self.assertNotIn("blocked_reason", load_state(config))

    def test_writable_scope_rejects_project_root_and_generated_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root, write_dirs=["."])
            config = load_config(root / "goal.toml")

            issues = validate_config(config)

            self.assertTrue(any("project root" in issue for issue in issues), issues)
            self.assertTrue(any("overlaps protected path" in issue for issue in issues), issues)

    def test_artifact_copy_as_must_be_plain_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace('copy_as = "artifact.txt"', 'copy_as = "../artifact.txt"'),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_config(config_path)

    def test_unparseable_tik_blocks_without_tok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "scripts" / "tik.py").write_text("print('not json')\n", encoding="utf-8")

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_invalid_review_evidence")
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")

    def test_stale_tik_review_blocks_without_tok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "scripts" / "tik.py").write_text(
                textwrap.dedent(
                    """
                    import json
                    print(json.dumps({
                        "artifact_ready": False,
                        "review_matches_current_pdf": False,
                        "current_pdf_sha256": "current-sha",
                        "reviewed_pdf_sha256": "old-sha"
                    }))
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_invalid_review_evidence")
            state = load_state(config)
            self.assertEqual(state["status"], "blocked_invalid_review_evidence")
            self.assertEqual(state["next_action"], "tik")
            self.assertIn("fresh artifact review", state["blocked_reason"])
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")
            self.assertFalse((root / state["last_run_dir"] / "tok_report.json").exists())

    def test_review_only_does_not_advance_repeated_blocker_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")

            for _ in range(3):
                result = run_heartbeat(config, RuntimeOptions(review_only=True, max_minutes=0))

            state = load_state(config)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            self.assertEqual(result.message, "artifact did not pass tik; tok skipped by tik command")
            self.assertEqual(state["status"], "active")
            self.assertNotIn("consecutive_blocker_count", state)
            self.assertNotIn("blocker_fingerprint", state)

    def test_repeated_blocker_is_observed_but_not_a_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "success_no_change"})
            config = load_config(root / "goal.toml")

            for _ in range(3):
                result = run_heartbeat(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["consecutive_blocker_count"], 3)
            self.assertTrue(state["repeated_blocker_ignored"])
            self.assertNotIn("blocked_reason", state)

    def test_review_only_tik_pass_does_not_complete_goal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "src" / "source.txt").write_text("ready\n", encoding="utf-8")
            config = load_config(root / "goal.toml")

            result = run_heartbeat(config, RuntimeOptions(review_only=True, max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["history"][-1]["event"], "review_only_tik_passed")

    def test_tok_report_is_runtime_owned_even_if_provider_writes_old_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "invalid"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_no_source_changes")
            self.assertEqual(state["last_tok"]["revision_strategy"], "tok provider completed")
            self.assertEqual((root / state["last_tok"]["report_path"]).read_text(encoding="utf-8").strip()[0], "{")

    def test_tok_no_source_change_claim_is_ignored_without_gating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(
                root,
                {
                    "mode": "no_source",
                    "remaining_artifact_bottleneck": "verdict requires evidence absent from writable sources",
                },
            )

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_no_source_changes")
            self.assertNotIn("blocked_reason", state)
            self.assertEqual(state["last_tok"]["source_change_possible"], True)
            self.assertEqual(state["last_tok"]["remaining_artifact_bottleneck"], "not reported by tok")

    def test_codex_goal_zero_exit_without_completion_marker_records_tok_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "no_completion_marker"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_failed_ignored")
            self.assertTrue(state["history"][-1]["run_dir"].startswith(".goal/runs/heartbeat-0001"))
            self.assertEqual(state["last_tok_attempt"]["error"], "codex_goal exited without a model completion marker")
            self.assertNotIn("last_tok", state)

    def test_codex_goal_tok_uses_goal_feature_without_structured_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            src_dir = root / "src"
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            bin_dir.mkdir()
            src_dir.mkdir()
            run_dir.mkdir(parents=True)
            fake_codex = bin_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys
                    from pathlib import Path

                    args = sys.argv[1:]
                    assert "--enable" in args and "goals" in args
                    assert "--output-last-message" not in args
                    assert "--output-schema" not in args
                    prompt = sys.stdin.read()
                    assert prompt == "/goal\\nrepair prompt\\n"
                    print("assistant final")
                    print("Done.")
                    print()
                    print("tokens used")
                    print("1")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                config = load_config(self._write_codex_goal_project(root))
                result = execute_tok(config.tok, "repair prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertTrue(result.ok, result.detail)
            self.assertEqual(result.report_path, run_dir / "tok_report.json")
            self.assertFalse((run_dir / "tok_report.schema.json").exists())
            self.assertEqual(result.report["revision_strategy"], "tok provider completed")
            log_text = (run_dir / "tok_codex.log").read_text(encoding="utf-8")
            self.assertNotIn("--output-schema", log_text)
            self.assertNotIn("--output-last-message", log_text)
            self.assertIn("--enable goals", log_text)
            self.assertIn("--add-dir", log_text)
            self.assertIn(str(run_dir / "attachments"), log_text)
            provider_prompt = (run_dir / "tok_codex_goal_prompt.md").read_text(encoding="utf-8")
            self.assertEqual(provider_prompt, "/goal\nrepair prompt\n")
            self.assertNotIn("Return the required report", provider_prompt)
            self.assertNotIn("Do not claim artifact completion", provider_prompt)
            self.assertNotIn("Keep working according to the attached review", provider_prompt)
            self.assertNotIn("tik", provider_prompt.lower())
            self.assertNotIn("tok", provider_prompt.lower())
            self.assertNotIn("bounded", provider_prompt.lower())
            self.assertNotIn("writable scopes", provider_prompt.lower())

    def test_codex_goal_tok_rejects_zero_exit_without_model_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            src_dir = root / "src"
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            bin_dir.mkdir()
            src_dir.mkdir()
            run_dir.mkdir(parents=True)
            fake_codex = bin_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import sys

                    sys.stdin.read()
                    print("OpenAI Codex v0.142.5")
                    print("user")
                    print("/goal")
                    print("2026-07-06T13:22:59Z ERROR rmcp::transport::worker: worker quit with fatal")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                config = load_config(self._write_codex_goal_project(root))
                result = execute_tok(config.tok, "repair prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertFalse(result.ok)
            self.assertIn("codex_goal exited without a model completion marker", result.detail)
            self.assertFalse((run_dir / "tok_report.json").exists())
            log_text = (run_dir / "tok_codex.log").read_text(encoding="utf-8")
            self.assertIn("codex_goal exited without a model completion marker", log_text)

    def test_claude_code_goal_tok_synthesizes_runtime_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            src_dir = root / "src"
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            bin_dir.mkdir()
            src_dir.mkdir()
            run_dir.mkdir(parents=True)
            fake_claude = bin_dir / "claude"
            fake_claude.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys

                    args = sys.argv[1:]
                    assert "--print" in args
                    assert args[args.index("--output-format") + 1] == "json"
                    assert "--json-schema" not in args
                    assert args[args.index("--permission-mode") + 1] == "acceptEdits"
                    assert args[args.index("--allowedTools") + 1] == "Bash"
                    add_dirs = [args[index + 1] for index, arg in enumerate(args) if arg == "--add-dir"]
                    assert any(path.endswith("attachments") for path in add_dirs)
                    prompt = sys.stdin.read()
                    assert prompt == "repair prompt\\n"
                    assert "/goal" not in prompt
                    assert "Return the required report as structured output" not in prompt
                    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done"}))
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                config = load_config(self._write_codex_goal_project(root, tok_provider="claude_code_goal"))
                result = execute_tok(config.tok, "repair prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertTrue(result.ok, result.detail)
            self.assertEqual(result.report_path, run_dir / "tok_report.json")
            report = json.loads((run_dir / "tok_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["source_change_possible"])
            self.assertEqual(report["revision_strategy"], "tok provider completed")
            self.assertFalse((run_dir / "tok_report.schema.json").exists())
            log_text = (run_dir / "tok_claude_code.log").read_text(encoding="utf-8")
            self.assertNotIn("--json-schema", log_text)
            self.assertIn("--permission-mode acceptEdits", log_text)
            provider_prompt = (run_dir / "tok_claude_code_goal_prompt.md").read_text(encoding="utf-8")
            self.assertEqual(provider_prompt, "repair prompt\n")
            self.assertNotIn("Do not claim artifact completion", provider_prompt)
            self.assertNotIn("/goal", provider_prompt)
            self.assertNotIn("tik", provider_prompt.lower())
            self.assertNotIn("bounded", provider_prompt.lower())

    def test_codex_app_server_tok_drives_thread_goal_without_schema_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            src_dir = root / "src"
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            bin_dir.mkdir()
            src_dir.mkdir()
            run_dir.mkdir(parents=True)
            fake_codex = bin_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys
                    from pathlib import Path

                    assert sys.argv[1:] == ["app-server", "--stdio"]
                    def respond(request_id, result):
                        print(json.dumps({"id": request_id, "result": result}), flush=True)

                    for line in sys.stdin:
                        message = json.loads(line)
                        method = message["method"]
                        request_id = message["id"]
                        params = message.get("params") or {}
                        if method == "initialize":
                            respond(request_id, {"userAgent": "fake-codex-app-server"})
                        elif method == "thread/start":
                            assert params["ephemeral"] is False
                            assert params["approvalPolicy"] == "never"
                            assert params["sandbox"] == "workspace-write"
                            respond(request_id, {"thread": {"id": "thread-1"}})
                        elif method == "thread/goal/set":
                            assert params["threadId"] == "thread-1"
                            assert params["status"] == "active"
                            assert params["objective"] == "repair prompt"
                            respond(request_id, {"goal": {"threadId": "thread-1", "objective": params["objective"], "status": "active"}})
                        elif method == "turn/start":
                            assert params["threadId"] == "thread-1"
                            assert params["approvalPolicy"] == "never"
                            assert "outputSchema" not in params
                            prompt = params["input"][0]["text"]
                            assert prompt == "repair prompt\\n"
                            assert "Return the required report" not in prompt
                            assert "/goal" not in prompt
                            sandbox_policy = params["sandboxPolicy"]
                            assert sandbox_policy["type"] == "workspaceWrite"
                            assert any(path.endswith("attachments") for path in sandbox_policy["writableRoots"])
                            Path(params["cwd"], "source.txt").write_text("ready\\n", encoding="utf-8")
                            respond(request_id, {"turn": {"id": "response-turn", "status": "inProgress", "items": []}})
                            print(json.dumps({
                                "method": "turn/completed",
                                "params": {"threadId": "thread-1", "turn": {"id": "turn-1", "status": "completed", "items": []}}
                            }), flush=True)
                        else:
                            raise SystemExit(f"unexpected method: {method}")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                config = load_config(self._write_codex_goal_project(root, tok_provider="codex_app_server"))
                plan = build_codex_app_server_tok_plan(config.tok, "repair prompt", run_dir)
                self.assertEqual(plan.command, ("codex", "app-server", "--stdio"))
                self.assertEqual(plan.cwd, src_dir.resolve())
                result = execute_tok(config.tok, "repair prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertTrue(result.ok, result.detail)
            self.assertEqual(result.report_path, run_dir / "tok_report.json")
            report = json.loads((run_dir / "tok_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["revision_strategy"], "tok provider completed")
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "ready\n")
            self.assertFalse((run_dir / "tok_report.schema.json").exists())
            log_text = (run_dir / "tok_codex_app_server.log").read_text(encoding="utf-8")
            self.assertIn("thread/goal/set", log_text)
            self.assertIn("turn/start", log_text)
            provider_prompt = (run_dir / "tok_codex_app_server_prompt.md").read_text(encoding="utf-8")
            self.assertFalse(provider_prompt.startswith("/goal"))
            self.assertEqual(provider_prompt, "repair prompt\n")
            self.assertNotIn("Return the required report", provider_prompt)

    def test_claude_code_goal_plan_maps_sandbox_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            base = dict(
                provider="claude_code_goal",
                prompt_template="",
                write_dirs=(root / "src", root / "data"),
                run_cwd=root,
                runtime_write_dirs=(root / "output",),
            )

            plan = build_claude_code_goal_tok_plan(TokConfig(sandbox="workspace-write", **base), "repair prompt", run_dir)
            args = list(plan.command)
            self.assertEqual(args[args.index("--permission-mode") + 1], "acceptEdits")
            self.assertEqual(args[args.index("--allowedTools") + 1], "Bash")
            self.assertIn(f"Write({run_dir / 'attachments'}/**)", args[args.index("--disallowedTools") + 1])
            self.assertNotIn("--json-schema", args)
            add_dirs = [Path(args[index + 1]) for index, arg in enumerate(args) if arg == "--add-dir"]
            self.assertEqual(
                add_dirs,
                [root / "src", root / "data", root / "output", run_dir / "attachments"],
            )
            self.assertEqual(plan.cwd, root)

            danger_plan = build_claude_code_goal_tok_plan(TokConfig(sandbox="danger-full-access", **base), "repair prompt", run_dir)
            self.assertIn("--dangerously-skip-permissions", danger_plan.command)
            self.assertNotIn("--permission-mode", danger_plan.command)

            read_only_plan = build_claude_code_goal_tok_plan(TokConfig(sandbox="read-only", **base), "repair prompt", run_dir)
            read_only_args = list(read_only_plan.command)
            disallowed = read_only_args[read_only_args.index("--disallowedTools") + 1]
            for tool in ("Write", "Edit", "NotebookEdit", "Bash"):
                self.assertIn(tool, disallowed)

    def test_codex_goal_tok_fails_if_attachment_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            src_dir = root / "src"
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            bin_dir.mkdir()
            src_dir.mkdir()
            (run_dir / "attachments").mkdir(parents=True)
            (run_dir / "attachments" / "tik_review.md").write_text("original review\n", encoding="utf-8")
            fake_codex = bin_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys
                    from pathlib import Path

                    args = sys.argv[1:]
                    assert "--output-last-message" not in args
                    assert "--output-schema" not in args
                    add_dirs = [Path(args[index + 1]) for index, arg in enumerate(args) if arg == "--add-dir"]
                    (add_dirs[-1] / "tik_review.md").write_text("mutated review\\n", encoding="utf-8")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                config = load_config(self._write_codex_goal_project(root))
                result = execute_tok(config.tok, "repair prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertFalse(result.ok)
            self.assertIn("modified tik_review.md", result.detail)
            self.assertTrue((run_dir / "tok_attachment_integrity.log").exists())

    def test_codex_goal_tok_separates_source_edits_from_runtime_write_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root, write_dirs=["src", "data"])
            for name in ("data", "build", "logs"):
                (root / name).mkdir()
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    'write_dirs = ["src", "data"]',
                    'write_dirs = ["src", "data"]\nrun_cwd = "."\nruntime_write_dirs = ["output", "build", "logs"]',
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)

            plan = build_codex_goal_tok_plan(config.tok, "repair prompt", root / ".goal" / "runs" / "heartbeat-0001")

            self.assertEqual(plan.cwd, root.resolve())
            args = list(plan.command)
            self.assertEqual(args[args.index("-C") + 1], str(root.resolve()))
            add_dirs = [Path(args[index + 1]).resolve() for index, arg in enumerate(args) if arg == "--add-dir"]
            self.assertEqual(
                add_dirs[:-1],
                [
                    (root / "src").resolve(),
                    (root / "data").resolve(),
                    (root / "output").resolve(),
                    (root / "build").resolve(),
                    (root / "logs").resolve(),
                ],
            )
            self.assertEqual(tuple(path.resolve() for path in config.tok.write_dirs), ((root / "src").resolve(), (root / "data").resolve()))
            self.assertEqual(
                tuple(path.resolve() for path in config.tok.runtime_write_dirs),
                ((root / "output").resolve(), (root / "build").resolve(), (root / "logs").resolve()),
            )

    def test_tik_review_is_attached_instead_of_inlined_into_tok_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            tik_ledger = (result.run_dir / "tik.md").read_text(encoding="utf-8")
            tik_review = result.run_dir / "attachments" / "tik_review.md"
            tok_prompt = (result.run_dir / "tok_prompt.md").read_text(encoding="utf-8")
            self.assertIn("# Referee Report", tik_ledger)
            self.assertIn("draft artifact", tik_ledger)
            self.assertNotIn("artifact_ready", tik_ledger)
            self.assertNotIn("## Parsed Verdict", tik_ledger)
            self.assertEqual(tik_review.read_text(encoding="utf-8").strip(), tik_ledger.strip())
            self.assertIn(str(tik_review), tok_prompt)
            self.assertNotIn("Artifact ownership rule:", tok_prompt)
            self.assertNotIn("edit prohibition is enforced by Codex/Claude hooks", tok_prompt)
            self.assertNotIn(tik_ledger.strip(), tok_prompt)
            self.assertNotIn("ledger", tok_prompt.lower())
            self.assertNotIn("bounded", tok_prompt.lower())
            self.assertNotIn("writable scopes", tok_prompt.lower())
            state = load_state(config)
            expected_ledger_path = result.run_dir.resolve().relative_to(root.resolve()) / "tik.md"
            self.assertEqual(state["last_tik"]["ledger_path"], str(expected_ledger_path))

    def test_rich_tik_report_can_end_with_json_verdict_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "scripts" / "tik.py").write_text(
                textwrap.dedent(
                    '''
                    print("""Referee report

                    This manuscript is not ready for publication because the measurement is not validated.

                    ```json
                    {
                      "artifact_ready": false
                    }
                    ```
                    """)
                    '''
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            config = load_config(root / "goal.toml")

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            self.assertIn("Referee report", (result.run_dir / "tik_memo.md").read_text(encoding="utf-8"))
            verdict = json.loads((result.run_dir / "tik_verdict.json").read_text(encoding="utf-8"))
            self.assertFalse(verdict["_parse_error"])
            self.assertFalse(verdict["artifact_ready"])
            tok_prompt = (result.run_dir / "tok_prompt.md").read_text(encoding="utf-8")
            tik_review = result.run_dir / "attachments" / "tik_review.md"
            self.assertIn(str(tik_review), tok_prompt)
            self.assertNotIn("This manuscript is not ready for publication", tok_prompt)
            tik_review_text = tik_review.read_text(encoding="utf-8")
            self.assertIn("This manuscript is not ready for publication", tik_review_text)
            self.assertNotIn("artifact_ready", tik_review_text)

    def test_codex_file_tik_uses_single_artifact_read_only_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            run_dir.mkdir(parents=True)
            artifact = root / "output" / "artifact.pdf"
            artifact.parent.mkdir()
            artifact.write_text("fake pdf content\n", encoding="utf-8")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake_codex = bin_dir / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys
                    from pathlib import Path

                    args = sys.argv[1:]
                    output_path = Path(args[args.index("--output-last-message") + 1])
                    workspace = Path(args[args.index("-C") + 1])
                    assert args[0] == "exec"
                    assert "--skip-git-repo-check" in args
                    assert args[args.index("--sandbox") + 1] == "read-only"
                    assert "--ephemeral" in args
                    assert sorted(path.name for path in workspace.iterdir()) == ["full_paper.pdf"]
                    prompt = sys.stdin.read()
                    assert prompt.startswith("/apsr-review\\n")
                    assert "Only inspect this local artifact file" not in prompt
                    assert "temporary directory" not in prompt
                    assert "configured review prompt" in prompt
                    output_path.write_text(
                        "Review: thin evidence.\\n" +
                        json.dumps({"artifact_ready": False}) + "\\n",
                        encoding="utf-8"
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                memo_path = run_tik(
                    TikConfig(provider="codex_file", prompt=""),
                    root,
                    artifact,
                    "/apsr-review\n\nconfigured review prompt",
                    run_dir,
                    "tik",
                    "full_paper.pdf",
                )
            finally:
                os.environ["PATH"] = old_path

            self.assertEqual(memo_path, run_dir / "tik_memo.md")
            self.assertIn("thin evidence", memo_path.read_text(encoding="utf-8"))
            log_text = (run_dir / "tik_codex_file.log").read_text(encoding="utf-8")
            self.assertIn("--sandbox read-only", log_text)
            self.assertIn("--ephemeral", log_text)

    def test_claude_code_file_tik_uses_single_artifact_write_disallowed_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".goal" / "runs" / "heartbeat-0001"
            run_dir.mkdir(parents=True)
            artifact = root / "output" / "artifact.pdf"
            artifact.parent.mkdir()
            artifact.write_text("fake pdf content\n", encoding="utf-8")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake_claude = bin_dir / "claude"
            fake_claude.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import json
                    import sys
                    from pathlib import Path

                    args = sys.argv[1:]
                    assert "--print" in args
                    assert args[args.index("--output-format") + 1] == "json"
                    disallowed = args[args.index("--disallowedTools") + 1]
                    for tool in ("Write", "Edit", "NotebookEdit", "Bash"):
                        assert tool in disallowed
                    workspace = Path.cwd()
                    assert sorted(path.name for path in workspace.iterdir()) == ["full_paper.pdf"]
                    prompt = sys.stdin.read()
                    assert prompt.startswith("/apsr-review\\n")
                    assert "configured review prompt" in prompt
                    memo = "Review: thin evidence.\\n" + json.dumps({"artifact_ready": False})
                    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": memo}))
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
            try:
                memo_path = run_tik(
                    TikConfig(provider="claude_code_file", prompt=""),
                    root,
                    artifact,
                    "/apsr-review\n\nconfigured review prompt",
                    run_dir,
                    "tik",
                    "full_paper.pdf",
                )
            finally:
                os.environ["PATH"] = old_path

            self.assertEqual(memo_path, run_dir / "tik_memo.md")
            self.assertIn("thin evidence", memo_path.read_text(encoding="utf-8"))
            log_text = (run_dir / "tik_claude_code_file.log").read_text(encoding="utf-8")
            self.assertIn("--output-format json", log_text)
            self.assertIn("--disallowedTools", log_text)

    def test_api_tik_expands_named_skill_into_provider_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skills" / "apsr-review"
            skill_dir.mkdir(parents=True)
            skill_path = skill_dir / "SKILL.md"
            skill_path.write_text(
                textwrap.dedent(
                    """
                    ---
                    name: apsr-review
                    ---

                    Judge the artifact as an APSR referee.
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            prompt = build_api_tik_prompt(
                TikConfig(provider="api", prompt="", skill="apsr-review"),
                root,
                "Review the attached PDF.",
            )

            self.assertIn('<goal-cli-tik-skill name="apsr-review">', prompt)
            self.assertIn(f"Source: {skill_path.resolve(strict=False)}", prompt)
            self.assertIn("Judge the artifact as an APSR referee.", prompt)
            self.assertIn("<goal-cli-tik-task>", prompt)
            self.assertIn("Review the attached PDF.", prompt)

    def test_api_tik_defaults_to_packy_fable5(self) -> None:
        config = TikConfig(provider="api", prompt="")

        self.assertEqual(effective_api_tik_model(config), DEFAULT_API_TIK_MODEL)

        with tempfile.TemporaryDirectory() as temp_dir:
            missing_env_file = str(Path(temp_dir) / "missing.env")
            with mock.patch.dict(os.environ, {"GOAL_CLI_API_ENV_FILE": missing_env_file}, clear=True):
                options, base_url, api_key_env = api_tik_client_options(config, 30)

        self.assertEqual(base_url, DEFAULT_API_TIK_BASE_URL)
        self.assertEqual(options["base_url"], DEFAULT_API_TIK_BASE_URL)
        self.assertEqual(options["timeout"], 30)
        self.assertNotIn("api_key", options)
        self.assertIsNone(api_key_env)

    def test_api_tik_prefers_packy_key_env(self) -> None:
        config = TikConfig(provider="api", prompt="")

        with mock.patch.dict(
            os.environ,
            {
                "PACKYCODE_CODEX_KEY": "test-packy-key",
                "OPENAI_API_KEY": "test-openai-key",
            },
            clear=True,
        ):
            options, base_url, api_key_env = api_tik_client_options(config, 30)

        self.assertEqual(base_url, DEFAULT_API_TIK_BASE_URL)
        self.assertEqual(options["api_key"], "test-packy-key")
        self.assertEqual(api_key_env, "PACKYCODE_CODEX_KEY")

    def test_api_tik_reads_packy_key_from_user_env_file(self) -> None:
        config = TikConfig(provider="api", prompt="")
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "api.env"
            env_file.write_text("PACKYAPI_API_KEY=file-packy-key\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"GOAL_CLI_API_ENV_FILE": str(env_file)}, clear=True):
                options, base_url, api_key_source = api_tik_client_options(config, 30)

        self.assertEqual(base_url, DEFAULT_API_TIK_BASE_URL)
        self.assertEqual(options["api_key"], "file-packy-key")
        self.assertEqual(api_key_source, f"{env_file}:PACKYAPI_API_KEY")

    def test_api_tik_rejects_slash_skill_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace(
                'provider = "oracle"\ncommand = "python3 scripts/tik.py"',
                'provider = "api"',
            )
            text = text.replace("Evaluate {artifact_path}.", "/apsr-review\n\nEvaluate {artifact_path}.")
            config_path.write_text(text, encoding="utf-8")

            issues = validate_config(load_config(config_path))

            self.assertTrue(any("cannot execute slash skill commands" in issue for issue in issues), issues)

    def test_api_tik_validates_missing_skill_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace(
                'provider = "oracle"\ncommand = "python3 scripts/tik.py"',
                'provider = "api"\nskill = "missing-skill"',
            )
            config_path.write_text(text, encoding="utf-8")

            issues = validate_config(load_config(config_path))

            self.assertTrue(any("tik.skill could not be resolved" in issue for issue in issues), issues)

    def test_missing_codex_blocks_without_uncaught_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace("python3 scripts/produce.py", f"{sys.executable} scripts/produce.py")
            text = text.replace("python3 scripts/tik.py", f"{sys.executable} scripts/tik.py")
            config_path.write_text(text, encoding="utf-8")
            no_codex_bin = root / "no-codex-bin"
            no_codex_bin.mkdir()
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = str(no_codex_bin)
            try:
                config = load_config(config_path)
                result = run_goal(config, RuntimeOptions(max_minutes=0))
            finally:
                os.environ["PATH"] = old_path

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            state = load_state(config)
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["next_action"], "tok")
            self.assertEqual(state["history"][-1]["event"], "tok_failed_ignored")
            log_text = Path(state["last_run_dir"], "tok_codex.log")
            self.assertIn("failed to start command", (root / log_text).read_text(encoding="utf-8"))

    def test_run_time_budget_kills_hung_producer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "scripts" / "produce.py").write_text(
                "import time\ntime.sleep(5)\n",
                encoding="utf-8",
            )
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace("python3 scripts/produce.py", f"{sys.executable} scripts/produce.py")
            config_path.write_text(text, encoding="utf-8")

            config = load_config(config_path)
            started = time.monotonic()
            result = run_goal(config, RuntimeOptions(max_minutes=0.001))
            elapsed = time.monotonic() - started

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_invalid_review_evidence")
            self.assertLess(elapsed, 2.0)
            self.assertIn("timed out", (result.run_dir / "producer.log").read_text(encoding="utf-8"))

    def test_scientificity_example_uses_codex_file_tik_and_codex_goal_tok(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = load_config(repo_root / "examples" / "scientificity" / "goal.toml")

        self.assertEqual(config.tik.provider, "codex_file")
        self.assertEqual(config.tok.provider, "codex_goal")
        prompt_text = config.tik.prompt + "\n" + config.tok.prompt_template
        banned = ["Adrian", "user", "human", "approval", "decision_required", "ask", "bounded", "Writable scopes", "{tik_ledger}"]
        for term in banned:
            self.assertNotIn(term, prompt_text)
        self.assertTrue(config.tik.prompt.startswith("/apsr-review\n"))
        self.assertIn("Review full_paper.pdf", config.tik.prompt)
        self.assertIn("IMPORTANT: Do not assume", config.tik.prompt)
        self.assertIn("automatic pipeline output", config.tik.prompt)
        self.assertIn("blocking publication problems", config.tik.prompt)
        self.assertIn("Make the editable source yield", prompt_text)
        self.assertIn("via `{producer_command}`", prompt_text)
        self.assertIn("manuscript PDF", prompt_text)
        self.assertIn("meets the APSR standards. Your work should address the concerns raised in {tik_review_path}.", prompt_text)
        self.assertNotIn("success means", prompt_text)
        self.assertNotIn("publication standards defined by the report", prompt_text)
        self.assertIn("{tik_review_path}", prompt_text)
        rejected_tok_terms = [
            "keep working",
            "repair",
            "revise",
            "revision",
            "heartbeat",
            "strongest",
            "aggregate tik",
            "dp16276 checklist standards",
            "manual edits",
            "commands may run",
            "generated side effects",
            "runtime writes",
            "do not hand-edit",
            "edit prohibition",
            "paper itself",
            "produce manuscript",
            "rebuilt PDF",
        ]
        lower_tok_prompt = config.tok.prompt_template.lower()
        for term in rejected_tok_terms:
            self.assertNotIn(term.lower(), lower_tok_prompt)
        self.assertNotIn("{writable_scopes}", prompt_text)
        self.assertNotIn("{runtime_writable_scopes}", prompt_text)
        self.assertNotIn("{tok_run_cwd}", prompt_text)

    def test_scientificity_example_validates_after_copy_to_project_root(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        example_text = (repo_root / "examples" / "scientificity" / "goal.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "output").mkdir()
            (root / "build").mkdir()
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "data").mkdir()
            (root / "writing").mkdir()
            config_path = root / "goal.toml"
            config_path.write_text(example_text, encoding="utf-8")

            config = load_config(config_path)

            self.assertEqual(validate_config(config), [])
            self.assertEqual(config.tik.provider, "codex_file")
            self.assertEqual(
                tuple(path.resolve() for path in config.tok.write_dirs),
                ((root / "writing").resolve(), (root / "src").resolve()),
            )
            self.assertNotIn((root / "data").resolve(), tuple(path.resolve() for path in config.tok.write_dirs))
            self.assertEqual(config.tok.run_cwd, root.resolve())
            self.assertEqual(
                tuple(path.resolve() for path in config.tok.runtime_write_dirs),
                ((root / "output").resolve(), (root / "build").resolve(), (root / "logs").resolve()),
            )

    def test_scientificity_claude_example_matches_codex_example_with_claude_providers(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        codex_config = load_config(repo_root / "examples" / "scientificity" / "goal.toml")
        claude_config = load_config(repo_root / "examples" / "scientificity-claude" / "goal.toml")

        self.assertEqual(claude_config.tik.provider, "claude_code_file")
        self.assertEqual(claude_config.tok.provider, "claude_code_goal")
        self.assertTrue(claude_config.tik.prompt.startswith("/apsr-review\n"))
        self.assertEqual(claude_config.tik.prompt, codex_config.tik.prompt)
        self.assertEqual(claude_config.tik.verdict, codex_config.tik.verdict)
        self.assertEqual(claude_config.tok.prompt_template, codex_config.tok.prompt_template)
        self.assertEqual(claude_config.tok.sandbox, codex_config.tok.sandbox)
        self.assertEqual(claude_config.artifact.copy_as, codex_config.artifact.copy_as)
        self.assertEqual(
            [path.name for path in claude_config.tok.write_dirs],
            [path.name for path in codex_config.tok.write_dirs],
        )
        self.assertEqual(
            [path.name for path in claude_config.tok.runtime_write_dirs],
            [path.name for path in codex_config.tok.runtime_write_dirs],
        )

    def test_scientificity_claude_example_validates_after_copy_to_project_root(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        example_text = (repo_root / "examples" / "scientificity-claude" / "goal.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "output").mkdir()
            (root / "build").mkdir()
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "data").mkdir()
            (root / "writing").mkdir()
            config_path = root / "goal.toml"
            config_path.write_text(example_text, encoding="utf-8")

            config = load_config(config_path)

            self.assertEqual(validate_config(config), [])
            self.assertEqual(config.tik.provider, "claude_code_file")
            self.assertEqual(config.tok.provider, "claude_code_goal")

    def test_validate_rejects_wrong_tok_provider_and_runtime_prompt_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace('provider = "codex_goal"', 'provider = "codex_exec"')
            text = text.replace("Use {tik_review_path}.", "Use {tik_review_path}.\nAsk a human for approval before editing source files.")
            config_path.write_text(text, encoding="utf-8")

            issues = validate_config(load_config(config_path))

            self.assertTrue(any("unsupported tok provider" in issue and "codex_exec" in issue for issue in issues), issues)
            self.assertTrue(any("forbidden runtime prompt term" in issue for issue in issues), issues)

    def test_load_rejects_old_tok_command_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace('sandbox = "workspace-write"', 'command = "python3 scripts/tok.py"\nsandbox = "workspace-write"')
            config_path.write_text(text, encoding="utf-8")

            with self.assertRaises(ConfigError):
                load_config(config_path)

    def test_validate_rejects_unknown_prompt_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace("{tik_review_path}", "{missing_field}"),
                encoding="utf-8",
            )

            issues = validate_config(load_config(config_path))

            self.assertTrue(any("unknown tok prompt placeholder" in issue for issue in issues), issues)

    def _write_basic_project(self, root: Path, write_dirs: list[str] | None = None) -> None:
        (root / "src").mkdir()
        (root / "scripts").mkdir()
        (root / "output").mkdir()
        self._install_fake_codex(root)
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        (root / "scripts" / "produce.py").write_text(
            textwrap.dedent(
                """
                from pathlib import Path
                root = Path(__file__).resolve().parents[1]
                (root / "output").mkdir(exist_ok=True)
                source = (root / "src" / "source.txt").read_text(encoding="utf-8")
                (root / "output" / "artifact.txt").write_text(source, encoding="utf-8")
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (root / "scripts" / "tik.py").write_text(
            textwrap.dedent(
                """
                import json
                import os
                from pathlib import Path
                artifact = Path(os.environ["GOAL_ARTIFACT"]).read_text(encoding="utf-8")
                ready = artifact.strip() == "ready"
                if ready:
                    print("Review: artifact is ready.")
                else:
                    print("Review: draft artifact remains.")
                print(json.dumps({"artifact_ready": ready}))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        config = f'''
name = "test-artifact-goal"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"
copy_as = "artifact.txt"

[producer]
command = "python3 scripts/produce.py"

[tik]
provider = "oracle"
command = "python3 scripts/tik.py"

[tik.verdict]
ready_field = "artifact_ready"
required_fields = ["artifact_ready"]

[tik.prompt]
text = """
Evaluate {{artifact_path}}.
"""

[tok]
provider = "codex_goal"
sandbox = "workspace-write"
write_dirs = {json.dumps(write_dirs or ["src"])}

[tok.prompt]
template = """
The artifact is produced by {{producer_command}}.
Use {{tik_review_path}}.
"""

[no_mistakes]
enabled = false

[observability]
enabled = false

[safety]
generated_dirs = ["output", "build"]
max_blocker_repeats = 3
'''
        (root / "goal.toml").write_text(config, encoding="utf-8")

    def _install_fake_codex(self, root: Path) -> None:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_codex = bin_dir / "codex"
        fake_codex.write_text(
            textwrap.dedent(
                """
                #!/usr/bin/env python3
                import json
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                workspace = Path(args[args.index("-C") + 1])
                root = workspace if (workspace / "goal.toml").exists() else workspace.parent
                assert args[0] == "exec"
                assert "--enable" in args and "goals" in args
                assert "--output-last-message" not in args
                assert "--output-schema" not in args
                prompt = sys.stdin.read()
                assert prompt.startswith("/goal\\n")
                assert "Return the required report" not in prompt
                def finish():
                    print("assistant final")
                    print("Done.")
                    print()
                    print("tokens used")
                    print("1")
                attachment_dirs = [Path(args[index + 1]) for index, arg in enumerate(args) if arg == "--add-dir" and args[index + 1].endswith("attachments")]
                run_dir = attachment_dirs[0].parent if attachment_dirs else root / ".goal" / "runs" / "unknown"
                output_path = run_dir / "tok_report.json"
                behavior_path = root / "scripts" / "tok_behavior.json"
                behavior = json.loads(behavior_path.read_text(encoding="utf-8")) if behavior_path.exists() else {"mode": "success"}
                if behavior["mode"] == "no_completion_marker":
                    print("OpenAI Codex v0.142.5")
                    print("user")
                    print("/goal")
                    print("2026-07-06T13:22:59Z ERROR rmcp::transport::worker: worker quit with fatal")
                    raise SystemExit(0)
                if behavior["mode"] == "invalid":
                    output_path.write_text("not json\\n", encoding="utf-8")
                    finish()
                    raise SystemExit(0)
                if behavior["mode"] == "no_source":
                    output_path.write_text(json.dumps({
                        "source_change_possible": False,
                        "revision_strategy": "no source change can address the verdict",
                        "expected_artifact_visible_improvement": [],
                        "remaining_artifact_bottleneck": behavior["remaining_artifact_bottleneck"]
                    }) + "\\n", encoding="utf-8")
                    finish()
                    raise SystemExit(0)
                if behavior["mode"] == "success_no_change":
                    finish()
                    raise SystemExit(0)
                if behavior["mode"] == "metadata_only":
                    (root / ".DS_Store").write_bytes(b"root metadata")
                    (root / "src" / ".DS_Store").write_bytes(b"source metadata")
                    finish()
                    raise SystemExit(0)
                if behavior["mode"] == "mutate_artifact":
                    (root / "output" / "artifact.txt").write_text("hand-edited artifact\\n", encoding="utf-8")
                if behavior["mode"] == "mutate_generated":
                    (root / "output" / "tok-side-effect.txt").write_text("runtime side effect\\n", encoding="utf-8")
                if behavior["mode"] == "mutate_unexpected":
                    (root / "scripts" / "tok-side-effect.txt").write_text("unexpected side effect\\n", encoding="utf-8")
                (root / "src" / "source.txt").write_text("ready\\n", encoding="utf-8")
                finish()
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old_path))

    def _write_tok_behavior(self, root: Path, behavior: dict[str, object]) -> None:
        (root / "scripts" / "tok_behavior.json").write_text(json.dumps(behavior), encoding="utf-8")

    def _write_barrier_tik(self, root: Path, label: str, other_label: str, objection: str) -> None:
        (root / "scripts" / f"tik_{label}.py").write_text(
            textwrap.dedent(
                f"""
                import json
                import os
                import time
                from pathlib import Path

                run_dir = Path(os.environ["GOAL_RUN_DIR"])
                (run_dir / "{label}.started").write_text("started\\n", encoding="utf-8")
                deadline = time.time() + 3
                while time.time() < deadline:
                    if (run_dir / "{other_label}.started").exists():
                        break
                    time.sleep(0.05)
                else:
                    raise SystemExit("timed out waiting for {other_label}")

                print("Review: {objection}.")
                print(json.dumps({{"artifact_ready": False}}))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def _write_codex_goal_project(self, root: Path, tok_provider: str = "codex_goal") -> Path:
        config = '''
name = "codex-goal-test"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"

[producer]
command = "true"

[tik]
provider = "oracle"
command = "true"

[tik.prompt]
text = "Evaluate {artifact_path}."

[tok]
provider = "codex_goal"
write_dirs = ["src"]
sandbox = "workspace-write"

[tok.prompt]
template = "Goal {goal_name} review {tik_review_path}"

[no_mistakes]
enabled = false

[observability]
enabled = false
'''.replace('provider = "codex_goal"', f'provider = "{tok_provider}"')
        config_path = root / "goal.toml"
        config_path.write_text(config, encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
