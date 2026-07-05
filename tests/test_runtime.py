from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from goal_cli.config import ConfigError, load_config, validate_config
from goal_cli.runtime import HeartbeatLock, RuntimeOptions, load_state, run_cycle, run_goal
from goal_cli.tok_execution import execute_tok


class GoalRuntimeTests(unittest.TestCase):
    def test_heartbeat_lock_recovers_dead_pid_before_stale_age(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / ".goal" / ".heartbeat.lock"
            lock_path.parent.mkdir()
            lock_path.write_text(json.dumps({"pid": 999999999, "created_at": "2026-07-04T00:00:00+00:00"}) + "\n", encoding="utf-8")

            with HeartbeatLock(lock_path, stale_seconds=6 * 60 * 60):
                self.assertTrue(lock_path.exists())

            self.assertFalse(lock_path.exists())

    def test_run_rebuilds_artifact_until_tik_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_cycles=3, max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "complete")
            state = load_state(config)
            self.assertEqual(state["status"], "complete")
            self.assertEqual(state["iteration"], 2)
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "ready\n")
            self.assertTrue((root / ".goal" / "heartbeat.json").exists())

    def test_cycle_budget_exhaustion_is_not_reported_as_success_and_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)

            config = load_config(root / "goal.toml")
            first_result = run_goal(config, RuntimeOptions(max_cycles=1, max_minutes=0))

            self.assertEqual(first_result.exit_code, 1)
            self.assertEqual(first_result.status, "budget_limited")
            state = load_state(config)
            self.assertEqual(state["status"], "budget_limited")
            self.assertEqual(state["next_action"], "tik")
            self.assertEqual((root / "output" / "artifact.txt").read_text(encoding="utf-8"), "draft\n")

            second_result = run_goal(config, RuntimeOptions(max_cycles=2, max_minutes=0))

            self.assertEqual(second_result.exit_code, 0)
            self.assertEqual(second_result.status, "complete")
            self.assertEqual(load_state(config)["status"], "complete")

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
            result = run_goal(config, RuntimeOptions(max_cycles=2, max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_unparseable_tik")
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")

    def test_review_only_does_not_advance_repeated_blocker_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")

            for _ in range(3):
                result = run_cycle(config, RuntimeOptions(review_only=True, max_minutes=0))

            state = load_state(config)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            self.assertEqual(result.message, "artifact did not pass tik; tok skipped by tik command")
            self.assertEqual(state["status"], "active")
            self.assertNotIn("consecutive_blocker_count", state)
            self.assertNotIn("blocker_fingerprint", state)

    def test_invalid_tok_report_blocks_before_next_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            self._write_tok_behavior(root, {"mode": "invalid"})

            config = load_config(root / "goal.toml")
            result = run_goal(config, RuntimeOptions(max_cycles=2, max_minutes=0))

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_tok_failed")
            self.assertEqual(load_state(config)["status"], "blocked_tok_failed")

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
            result = run_goal(config, RuntimeOptions(max_cycles=2, max_minutes=0))

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
            run_dir = root / ".goal" / "runs" / "cycle-0001"
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
                result = execute_tok(config.tok, "bounded prompt", run_dir)
            finally:
                os.environ["PATH"] = old_path

            self.assertTrue(result.ok, result.detail)
            self.assertEqual(result.report_path, run_dir / "tok_report.json")
            self.assertTrue((run_dir / "tok_report.schema.json").exists())
            log_text = (run_dir / "tok_codex.log").read_text(encoding="utf-8")
            self.assertIn("--output-schema", log_text)
            self.assertIn("--enable goals", log_text)

    def test_tik_ledger_is_passed_whole_into_tok_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config = load_config(root / "goal.toml")

            result = run_cycle(config, RuntimeOptions(max_minutes=0))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            tik_ledger = (result.run_dir / "tik.md").read_text(encoding="utf-8")
            tok_prompt = (result.run_dir / "tok_prompt.md").read_text(encoding="utf-8")
            self.assertIn("# Tik Ledger", tik_ledger)
            self.assertIn("draft artifact", tik_ledger)
            self.assertIn("## Raw Tik Memo", tik_ledger)
            self.assertIn("## Parsed Tik Verdict", tik_ledger)
            self.assertIn(tik_ledger.strip(), tok_prompt)
            state = load_state(config)
            expected_ledger_path = result.run_dir.resolve().relative_to(root.resolve()) / "tik.md"
            self.assertEqual(state["last_tik"]["ledger_path"], str(expected_ledger_path))

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
                result = run_goal(config, RuntimeOptions(max_cycles=1, max_minutes=0))
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
            result = run_goal(config, RuntimeOptions(max_cycles=1, max_minutes=0.001))
            elapsed = time.monotonic() - started

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_producer_failed")
            self.assertLess(elapsed, 2.0)
            self.assertIn("timed out", (result.run_dir / "producer.log").read_text(encoding="utf-8"))

    def test_scientificity_example_uses_agent_tik_and_codex_goal_tok(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = load_config(repo_root / "examples" / "scientificity" / "goal.toml")

        self.assertEqual(config.tik.provider, "agent")
        self.assertEqual(config.tok.provider, "codex_goal")
        prompt_text = config.tik.prompt + "\n" + config.tok.prompt_template
        banned = ["Adrian", "user", "human", "approval", "decision_required", "ask"]
        for term in banned:
            self.assertNotIn(term, prompt_text)

    def test_validate_rejects_wrong_tok_provider_and_runtime_prompt_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_basic_project(root)
            config_path = root / "goal.toml"
            text = config_path.read_text(encoding="utf-8")
            text = text.replace('provider = "codex_goal"', 'provider = "codex_exec"')
            text = text.replace("Goal: {goal_name}", "Goal: {goal_name}\nAsk a human for approval before making one bounded source change.")
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
                config_path.read_text(encoding="utf-8").replace("{tik_ledger}", "{missing_field}"),
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
Goal: {{goal_name}}
Producer: {{producer_command}}
Verdict:
{{tik_ledger}}
Writable scopes:
{{writable_scopes}}
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
                        "revision_strategy": "no bounded source change can address the verdict",
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
template = "Goal {goal_name} verdict {tik_ledger}"

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
