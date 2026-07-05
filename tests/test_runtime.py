from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from goal_cli.adapters import run_tik
from goal_cli.config import ConfigError, TikConfig, load_config, validate_config
from goal_cli.runtime import HeartbeatLock, RuntimeOptions, cleanup_runtime, load_state, run_heartbeat, run_goal
from goal_cli.tok_execution import build_codex_goal_tok_plan, execute_tok


class GoalRuntimeTests(unittest.TestCase):
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
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "draft\n")
            heartbeat = json.loads((root / ".goal" / "heartbeat.json").read_text(encoding="utf-8"))
            self.assertEqual(heartbeat["phase"], "tok_completed")

            second_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(second_result.exit_code, 0)
            self.assertEqual(second_result.status, "complete")
            state = load_state(config)
            self.assertEqual(state["status"], "complete")
            self.assertEqual(state["iteration"], 2)
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

    def test_unparseable_tik_blocks_without_tok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            (root / "scripts" / "tik.py").write_text("print('not json')\n", encoding="utf-8")

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_unparseable_tik")
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
                        "central_bottleneck": "old review",
                        "blocking_objections": [{"severity": "blocking", "objection": "old PDF objection"}],
                        "required_next_artifact_changes": ["run a fresh review"],
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
            self.assertEqual(result.status, "blocked_stale_tik_review")
            state = load_state(config)
            self.assertEqual(state["status"], "blocked_stale_tik_review")
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

    def test_invalid_tok_report_blocks_before_next_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "invalid"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_tok_failed")
            self.assertEqual(load_state(config)["status"], "blocked_tok_failed")

            self._write_tok_behavior(root, {"mode": "success"})
            retry_result = run_goal(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(retry_result.exit_code, 0)
            self.assertEqual(retry_result.status, "active")
            self.assertEqual(load_state(config)["status"], "active")

    def test_tok_can_report_no_source_change_possible(self) -> None:
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

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_no_source_change_possible")
            state = load_state(config)
            self.assertEqual(state["status"], "blocked_no_source_change_possible")
            self.assertEqual(state["blocked_reason"], "verdict requires evidence absent from writable sources")

    def test_codex_goal_tok_uses_output_schema_and_goals_feature(self) -> None:
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
                    output_path = Path(args[args.index("--output-last-message") + 1])
                    schema_path = Path(args[args.index("--output-schema") + 1])
                    assert "--enable" in args and "goals" in args
                    assert schema_path.exists()
                    output_path.write_text(json.dumps({
                        "source_change_possible": True,
                        "revision_strategy": "edit source",
                        "sources_changed": ["src/source.txt"],
                        "expected_artifact_visible_improvement": ["artifact changes"],
                        "remaining_artifact_bottleneck": "none known"
                    }) + "\\n", encoding="utf-8")
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
            self.assertTrue((run_dir / "tok_report.schema.json").exists())
            log_text = (run_dir / "tok_codex.log").read_text(encoding="utf-8")
            self.assertIn("--output-schema", log_text)
            self.assertIn("--enable goals", log_text)
            self.assertIn("--add-dir", log_text)
            self.assertIn(str(run_dir / "attachments"), log_text)
            provider_prompt = (run_dir / "tok_codex_goal_prompt.md").read_text(encoding="utf-8")
            self.assertTrue(provider_prompt.startswith("/goal\n"))
            self.assertIn("Keep working according to the attached review", provider_prompt)
            self.assertIn("Return the required report", provider_prompt)
            self.assertNotIn("tik", provider_prompt.lower())
            self.assertNotIn("tok", provider_prompt.lower())
            self.assertNotIn("bounded", provider_prompt.lower())
            self.assertNotIn("writable scopes", provider_prompt.lower())

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
                    output_path = Path(args[args.index("--output-last-message") + 1])
                    add_dirs = [Path(args[index + 1]) for index, arg in enumerate(args) if arg == "--add-dir"]
                    (add_dirs[-1] / "tik_review.md").write_text("mutated review\\n", encoding="utf-8")
                    output_path.write_text(json.dumps({
                        "source_change_possible": True,
                        "revision_strategy": "edit source",
                        "sources_changed": ["src/source.txt"],
                        "expected_artifact_visible_improvement": ["artifact changes"],
                        "remaining_artifact_bottleneck": "none known"
                    }) + "\\n", encoding="utf-8")
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
            self.assertIn("## Review Text", tik_ledger)
            self.assertIn("## Parsed Verdict", tik_ledger)
            self.assertEqual(tik_review.read_text(encoding="utf-8").strip(), tik_ledger.strip())
            self.assertIn(str(tik_review), tok_prompt)
            self.assertNotIn(tik_ledger.strip(), tok_prompt)
            self.assertNotIn("tok", tok_prompt.lower())
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
                      "artifact_ready": false,
                      "central_bottleneck": "measurement is not validated",
                      "blocking_objections": [
                        {"severity": "blocking", "objection": "no validation evidence"}
                      ],
                      "required_next_artifact_changes": ["add validation evidence"]
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
            self.assertEqual(verdict["central_bottleneck"], "measurement is not validated")
            tok_prompt = (result.run_dir / "tok_prompt.md").read_text(encoding="utf-8")
            tik_review = result.run_dir / "attachments" / "tik_review.md"
            self.assertIn(str(tik_review), tok_prompt)
            self.assertNotIn("This manuscript is not ready for publication", tok_prompt)
            self.assertIn("This manuscript is not ready for publication", tik_review.read_text(encoding="utf-8"))

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
                    output_path.write_text(json.dumps({
                        "artifact_ready": False,
                        "central_bottleneck": "needs evidence",
                        "blocking_objections": [{"severity": "blocking", "objection": "thin evidence"}],
                        "required_next_artifact_changes": ["add evidence"]
                    }) + "\\n", encoding="utf-8")
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

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_tok_failed")
            state = load_state(config)
            self.assertEqual(state["status"], "blocked_tok_failed")
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
            self.assertEqual(result.status, "blocked_producer_failed")
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
        self.assertIn("APSR standard defined by the referee report at {tik_review_path}", prompt_text)
        self.assertIn("success means that PDF answers every blocking objection", prompt_text)
        self.assertIn("{tik_review_path}", prompt_text)
        self.assertIn("Manual edits are limited to:", config.tok.prompt_template)
        self.assertIn("Commands may run from {tok_run_cwd}", config.tok.prompt_template)
        self.assertIn("generated side effects may update", config.tok.prompt_template)
        self.assertIn("Do not hand-edit data/, scripts/, generated outputs, .goal/, or the manuscript", config.tok.prompt_template)
        rejected_tok_terms = [
            "keep working",
            "repair",
            "revise",
            "revision",
            "heartbeat",
            "strongest",
            "paper itself",
            "produce manuscript",
            "rebuilt PDF",
        ]
        lower_tok_prompt = config.tok.prompt_template.lower()
        for term in rejected_tok_terms:
            self.assertNotIn(term.lower(), lower_tok_prompt)
        self.assertIn("{writable_scopes}", prompt_text)
        self.assertIn("{runtime_writable_scopes}", prompt_text)
        self.assertIn("{tok_run_cwd}", prompt_text)

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
                print(json.dumps({
                    "artifact_ready": ready,
                    "central_bottleneck": "" if ready else "artifact still says draft",
                    "blocking_objections": [] if ready else [{"severity": "blocking", "objection": "draft artifact"}],
                    "required_next_artifact_changes": [] if ready else ["change artifact content to ready"]
                }))
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
blockers_field = "blocking_objections"
required_fields = ["artifact_ready", "blocking_objections"]
fingerprint_fields = ["blocking_objections", "central_bottleneck"]

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
                output_path = Path(args[args.index("--output-last-message") + 1])
                schema_path = Path(args[args.index("--output-schema") + 1])
                workspace = Path(args[args.index("-C") + 1])
                root = workspace.parent
                assert args[0] == "exec"
                assert "--enable" in args and "goals" in args
                assert schema_path.exists()
                behavior_path = root / "scripts" / "tok_behavior.json"
                behavior = json.loads(behavior_path.read_text(encoding="utf-8")) if behavior_path.exists() else {"mode": "success"}
                if behavior["mode"] == "invalid":
                    output_path.write_text("not json\\n", encoding="utf-8")
                    raise SystemExit(0)
                if behavior["mode"] == "no_source":
                    output_path.write_text(json.dumps({
                        "source_change_possible": False,
                        "revision_strategy": "no source change can address the verdict",
                        "sources_changed": [],
                        "expected_artifact_visible_improvement": [],
                        "remaining_artifact_bottleneck": behavior["remaining_artifact_bottleneck"]
                    }) + "\\n", encoding="utf-8")
                    raise SystemExit(0)
                (root / "src" / "source.txt").write_text("ready\\n", encoding="utf-8")
                output_path.write_text(json.dumps({
                    "source_change_possible": True,
                    "revision_strategy": "replace draft marker",
                    "sources_changed": ["src/source.txt"],
                    "expected_artifact_visible_improvement": ["artifact says ready"],
                    "remaining_artifact_bottleneck": "none known"
                }) + "\\n", encoding="utf-8")
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

    def _write_codex_goal_project(self, root: Path) -> Path:
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
'''
        config_path = root / "goal.toml"
        config_path.write_text(config, encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
