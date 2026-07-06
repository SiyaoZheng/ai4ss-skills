from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.cli import main
from goal_cli.runtime import DEFAULT_MAX_MINUTES, RunResult


class CliTests(unittest.TestCase):
    def test_run_help_has_no_multi_cycle_flag(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["run", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertNotIn("--max-cycles", help_text)
        self.assertIn("Run exactly one heartbeat", help_text)
        self.assertIn("producer rebuild, tik review", help_text)
        self.assertIn("review fails", help_text)
        self.assertIn("Maximum wall-clock minutes for the heartbeat", help_text)
        self.assertIn("including providers and no-mistakes", help_text)

    def test_run_uses_default_ten_hour_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = self._write_project(Path(temp_dir))
            output = io.StringIO()

            with (
                mock.patch("goal_cli.cli.run_goal", return_value=RunResult(0, "active", None, "ok")) as run_goal,
                contextlib.redirect_stdout(output),
            ):
                exit_code = main(["-c", str(config_path), "run"])

            self.assertEqual(exit_code, 0)
            self.assertEqual(run_goal.call_args.args[1].max_minutes, DEFAULT_MAX_MINUTES)

    def test_init_starter_prompt_keeps_tok_goal_to_two_plain_sentences(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "goal.toml"
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(["-c", str(config_path), "init"])

            self.assertEqual(exit_code, 0)
            text = config_path.read_text(encoding="utf-8")
            self.assertIn("Make the editable source yield", text)
            self.assertIn("Your work should address the concerns raised in {tik_review_path}.", text)
            self.assertNotIn("success means", text)
            lower_text = text.lower()
            for term in (
                "keep working",
                "repair",
                "revise",
                "revision",
                "strongest",
                "manual edits",
                "{writable_scopes}",
                "{runtime_writable_scopes}",
                "{tok_run_cwd}",
                "runtime writes",
                "do not hand-edit",
            ):
                self.assertNotIn(term, lower_text)

    def test_top_level_help_has_no_cycle_alias(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertNotIn("cycle", help_text)
        self.assertIn("Omitting the command defaults to run", help_text)
        self.assertIn("Validate goal.toml, prompt placeholders, and writable", help_text)

    def test_doctor_help_exposes_separate_smoke_timeout(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["doctor", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("source-change smoke check", help_text)
        self.assertNotIn("schema-output", help_text)
        self.assertNotIn("structured-output", help_text)
        self.assertIn("--timeout-seconds", help_text)
        self.assertIn("--smoke-timeout-seconds", help_text)
        self.assertIn("except optional provider", help_text)
        self.assertIn("smoke checks", help_text)

    def test_cleanup_help_exposes_orphan_cleanup_boundary(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["cleanup", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("--kill-orphans", help_text)
        self.assertIn("when no live heartbeat lock exists", help_text)

    def test_heartbeat_help_exposes_system_timer_commands(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["heartbeat", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("OS-level timer", help_text)
        self.assertIn("install", help_text)
        self.assertIn("status", help_text)
        self.assertIn("uninstall", help_text)
        self.assertIn("tick", help_text)

    def test_heartbeat_install_help_exposes_launchd_and_systemd(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["heartbeat", "install", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("--every-minutes", help_text)
        self.assertIn("--max-minutes", help_text)
        self.assertIn("--no-start", help_text)
        self.assertIn("launchd", help_text)
        self.assertIn("systemd-user", help_text)

    def _write_project(self, root: Path) -> Path:
        (root / "src").mkdir()
        (root / "output").mkdir()
        (root / "build").mkdir()
        (root / "scripts").mkdir()
        config_path = root / "goal.toml"
        config_path.write_text(
            """name = "cli-test"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"

[producer]
command = "python3 scripts/produce.py"

[tik]
provider = "oracle"
command = "python3 scripts/tik.py"

[tik.prompt]
text = "Review {artifact_path}."

[tok]
provider = "codex_goal"
write_dirs = ["src"]

[tok.prompt]
template = "Use {tik_review_path}."

[observability]
enabled = false
""",
            encoding="utf-8",
        )
        return config_path


if __name__ == "__main__":
    unittest.main()
