from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from goal_cli.adapters import TikOutcome, ProducerOutcome
from goal_cli import no_mistakes
from goal_cli.config import ConfigError, load_config
from goal_cli.runtime import RuntimeOptions, load_state, run_heartbeat, run_goal
from goal_cli.tok_execution import TokExecutionResult


class NoMistakesIntegrationTests(unittest.TestCase):
    def test_no_mistakes_is_default_and_unsupported_semi_automatic_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = self._write_project(root)

            config = load_config(config_path)

            self.assertTrue(config.no_mistakes.enabled)
            self.assertEqual(config.no_mistakes.mode, "lightspeed")
            self.assertTrue(config.observability.enabled)
            self.assertEqual(config.observability.endpoint, "http://localhost:4318/v1/traces")

            config_path.write_text(config_path.read_text(encoding="utf-8") + "\n[no_mistakes]\nyes = false\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(config_path)

    def test_heartbeat_auto_checkpoints_and_runs_no_mistakes_on_current_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            self._install_fake_no_mistakes(root, fake_log)
            config = load_config(self._write_project(root, disable_observability=True))
            self._git(root, "init")
            starting_branch = self._git(root, "branch", "--show-current").stdout.strip()

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0), adapters=RevisionAdapters())

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.status, "active")
            branch = self._git(root, "branch", "--show-current").stdout.strip()
            self.assertEqual(branch, starting_branch)
            self.assertEqual(self._git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip(), "")
            state = load_state(config)
            self.assertEqual(state["last_no_mistakes"]["status"], "no_mistakes_passed")
            exclude_text = (root / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("/.goal/", exclude_text)
            self.assertIn("/output/", exclude_text)
            self.assertIn("/build/", exclude_text)

            events = [json.loads(line) for line in fake_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["command"] for event in events], ["init", "axi run"])
            axi_args = events[-1]["args"]
            self.assertIn("--intent", axi_args)
            self.assertIn("--yes", axi_args)
            self.assertIn("--skip", axi_args)
            self.assertEqual(
                axi_args[axi_args.index("--skip") + 1],
                "review,test,document,lint,push,pr,ci",
            )
            self.assertEqual(events[-1]["git_status"], "")

    def test_lightspeed_mode_pre_skips_high_latency_no_mistakes_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            self._install_fake_no_mistakes(root, fake_log)
            config = load_config(
                self._write_project(
                    root,
                    disable_observability=True,
                    no_mistakes_table='\n[no_mistakes]\nmode = "lightspeed"\nskip_steps = ["rebase"]\n',
                )
            )
            self._git(root, "init")

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0), adapters=RevisionAdapters())

            self.assertEqual(result.exit_code, 0)
            events = [json.loads(line) for line in fake_log.read_text(encoding="utf-8").splitlines()]
            axi_args = events[-1]["args"]
            self.assertIn("--skip", axi_args)
            self.assertEqual(
                axi_args[axi_args.index("--skip") + 1],
                "rebase,review,test,document,lint,push,pr,ci",
            )

    def test_no_mistakes_gate_is_capped_by_run_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            child_marker = root / ".goal" / "child-survived.txt"
            self._install_fake_no_mistakes(root, fake_log, axi_sleep_seconds=5.0, child_marker=child_marker)
            config = load_config(self._write_project(root, disable_observability=True))
            self._git(root, "init")

            started = time.monotonic()
            result = run_heartbeat(config, RuntimeOptions(max_minutes=0.005), adapters=RevisionAdapters())
            elapsed = time.monotonic() - started

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "budget_limited")
            self.assertLess(elapsed, 2.0)
            self.assertRegex(result.message, r"timed out|run budget exhausted")
            state = load_state(config)
            self.assertEqual(state["status"], "budget_limited")
            self.assertEqual(state["last_no_mistakes"]["status"], "no_mistakes_budget_exhausted")
            time.sleep(1.0)
            self.assertFalse(child_marker.exists())

    def test_no_mistakes_prepare_budget_exhaustion_is_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            self._install_fake_no_mistakes(root, fake_log)
            config = load_config(self._write_project(root, disable_observability=True))
            self._git(root, "init")

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0), deadline=time.monotonic() - 1, adapters=RevisionAdapters())

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "budget_limited")
            self.assertIn("run budget exhausted", result.message)
            state = load_state(config)
            self.assertEqual(state["status"], "budget_limited")
            self.assertEqual(state["last_no_mistakes"]["status"], "no_mistakes_budget_exhausted")

    def test_run_goal_preserves_no_mistakes_budget_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            self._install_fake_no_mistakes(root, fake_log, axi_sleep_seconds=5.0)
            config = load_config(self._write_project(root, disable_observability=True))
            self._git(root, "init")

            result = run_goal(config, RuntimeOptions(max_minutes=0.005), adapters=RevisionAdapters())

            self.assertEqual(result.status, "budget_limited")
            heartbeat = json.loads(config.heartbeat_path.read_text(encoding="utf-8"))
            self.assertEqual(heartbeat["phase"], "run_budget_exhausted")

    def test_no_mistakes_prepare_records_granular_non_git_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_log = root / ".goal" / "fake-no-mistakes.jsonl"
            self._install_fake_no_mistakes(root, fake_log)
            config = load_config(self._write_project(root, disable_observability=True))

            result = run_heartbeat(config, RuntimeOptions(max_minutes=0), adapters=RevisionAdapters())

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.status, "blocked_no_mistakes_failed")
            self.assertEqual(load_state(config)["last_no_mistakes"]["status"], "no_mistakes_no_git_repository")

    def test_git_diff_cached_timeout_is_classified_as_budget_exhaustion(self) -> None:
        result = subprocess.CompletedProcess(
            ["git", "diff", "--cached"],
            124,
            "",
            "time budget exhausted before git command start",
        )

        with self.assertRaises(no_mistakes._NoMistakesBudgetExhausted):
            no_mistakes._raise_if_git_timed_out(result, time.monotonic() - 1, "git diff --cached before no-mistakes")

    def _write_project(self, root: Path, disable_observability: bool = False, no_mistakes_table: str = "") -> Path:
        (root / "src").mkdir()
        (root / "output").mkdir()
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        observability_table = '\n[observability]\nenabled = false\n' if disable_observability else ""
        config = f"""
name = "test-artifact-goal"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"

[producer]
command = "ignored-producer"

[tik]
provider = "oracle"
command = "ignored-tik"

[tik.prompt]
text = "Evaluate {{artifact_path}}."

[tok]
provider = "codex_goal"
write_dirs = ["src"]
sandbox = "workspace-write"

[tok.prompt]
template = "Goal {{goal_name}} review {{tik_review_path}}"
{observability_table}
{no_mistakes_table}

[safety]
generated_dirs = ["output", "build"]
"""
        config_path = root / "goal.toml"
        config_path.write_text(config, encoding="utf-8")
        return config_path

    def _install_fake_no_mistakes(self, root: Path, fake_log: Path, axi_sleep_seconds: float = 0.0, child_marker: Path | None = None) -> None:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "no-mistakes"
        fake.write_text(
            textwrap.dedent(
                """
                #!/usr/bin/env python3
                import json
                import os
                import subprocess
                import sys
                import time
                from pathlib import Path

                log = Path(os.environ["FAKE_NO_MISTAKES_LOG"])
                args = sys.argv[1:]

                if args == ["axi", "run", "--help"]:
                    print("--intent --yes --skip")
                    raise SystemExit(0)

                if args == ["init"]:
                    log.open("a", encoding="utf-8").write(json.dumps({"command": "init", "args": args}) + "\\n")
                    raise SystemExit(0)

                if args[:2] == ["axi", "run"]:
                    child_marker = os.environ.get("FAKE_NO_MISTAKES_CHILD_MARKER")
                    if child_marker:
                        subprocess.Popen([
                            sys.executable,
                            "-c",
                            "import sys, time; from pathlib import Path; time.sleep(0.7); Path(sys.argv[1]).write_text('survived\\n', encoding='utf-8')",
                            child_marker,
                        ])
                    sleep_seconds = float(os.environ.get("FAKE_NO_MISTAKES_AXI_SLEEP", "0"))
                    if sleep_seconds:
                        time.sleep(sleep_seconds)
                    git_status = subprocess.check_output(
                        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                        text=True,
                    ).strip()
                    if git_status:
                        print(git_status, file=sys.stderr)
                        raise SystemExit(1)
                    if "--intent" not in args or "--yes" not in args:
                        print("missing required non-interactive flags", file=sys.stderr)
                        raise SystemExit(1)
                    log.open("a", encoding="utf-8").write(
                        json.dumps({"command": "axi run", "args": args, "git_status": git_status}) + "\\n"
                    )
                    print("outcome: passed")
                    raise SystemExit(0)

                print(f"unexpected args: {args}", file=sys.stderr)
                raise SystemExit(2)
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        old_path = os.environ.get("PATH", "")
        old_log = os.environ.get("FAKE_NO_MISTAKES_LOG")
        old_sleep = os.environ.get("FAKE_NO_MISTAKES_AXI_SLEEP")
        old_child_marker = os.environ.get("FAKE_NO_MISTAKES_CHILD_MARKER")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
        os.environ["FAKE_NO_MISTAKES_LOG"] = str(fake_log)
        os.environ["FAKE_NO_MISTAKES_AXI_SLEEP"] = str(axi_sleep_seconds)
        if child_marker is None:
            os.environ.pop("FAKE_NO_MISTAKES_CHILD_MARKER", None)
        else:
            os.environ["FAKE_NO_MISTAKES_CHILD_MARKER"] = str(child_marker)
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old_path))
        if old_log is None:
            self.addCleanup(lambda: os.environ.pop("FAKE_NO_MISTAKES_LOG", None))
        else:
            self.addCleanup(lambda: os.environ.__setitem__("FAKE_NO_MISTAKES_LOG", old_log))
        if old_sleep is None:
            self.addCleanup(lambda: os.environ.pop("FAKE_NO_MISTAKES_AXI_SLEEP", None))
        else:
            self.addCleanup(lambda: os.environ.__setitem__("FAKE_NO_MISTAKES_AXI_SLEEP", old_sleep))
        if old_child_marker is None:
            self.addCleanup(lambda: os.environ.pop("FAKE_NO_MISTAKES_CHILD_MARKER", None))
        else:
            self.addCleanup(lambda: os.environ.__setitem__("FAKE_NO_MISTAKES_CHILD_MARKER", old_child_marker))

    def _git(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result


class RevisionAdapters:
    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        config.artifact.path.parent.mkdir(parents=True, exist_ok=True)
        config.artifact.path.write_text((config.root / "src" / "source.txt").read_text(encoding="utf-8"), encoding="utf-8")
        return ProducerOutcome(True)

    def run_tik(self, config, prompt, run_dir, timeout_seconds=None) -> TikOutcome:
        memo_path = run_dir / "tik_memo.md"
        memo_path.write_text(
            json.dumps(
                {
                    "artifact_ready": False,
                    "central_bottleneck": "artifact still says draft",
                    "blocking_objections": [{"severity": "blocking", "objection": "draft artifact"}],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return TikOutcome(memo_path)

    def execute_tok(self, config, prompt, run_dir, timeout_seconds=None) -> TokExecutionResult:
        (config.root / "src" / "source.txt").write_text("ready\n", encoding="utf-8")
        report_path = run_dir / "tok_report.json"
        report = {
            "source_change_possible": True,
            "revision_strategy": "replace draft marker",
            "sources_changed": ["src/source.txt"],
            "expected_artifact_visible_improvement": ["artifact says ready"],
            "remaining_artifact_bottleneck": "none known",
        }
        report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")
        return TokExecutionResult(True, report_path, report, ())


if __name__ == "__main__":
    unittest.main()
