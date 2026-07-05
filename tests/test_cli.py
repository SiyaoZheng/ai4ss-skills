from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from goal_cli.cli import main


class CliTests(unittest.TestCase):
    def test_run_help_has_no_multi_cycle_flag(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["run", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertNotIn("--max-cycles", help_text)
        self.assertIn("The thing decides success", help_text)
        self.assertIn("source changes are only a step", help_text)
        self.assertIn("Maximum wall-clock minutes for the heartbeat", help_text)
        self.assertIn("including providers and no-mistakes", help_text)

    def test_init_starter_prompt_uses_goal_style_source_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "goal.toml"
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(["-c", str(config_path), "init"])

            self.assertEqual(exit_code, 0)
            text = config_path.read_text(encoding="utf-8")
            self.assertIn("Make the editable source yield", text)
            self.assertIn("success\nmeans that artifact answers every blocking objection", text)
            self.assertIn("Manual edits are limited to:", text)
            self.assertIn("{writable_scopes}", text)
            self.assertIn("{runtime_writable_scopes}", text)
            lower_text = text.lower()
            for term in ("keep working", "repair", "revise", "revision", "strongest"):
                self.assertNotIn(term, lower_text)

    def test_top_level_help_has_no_cycle_alias(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertNotIn("cycle", help_text)
        self.assertIn("Omitting the command defaults to run", help_text)
        self.assertIn("Validate config, prompt placeholders, and writable", help_text)

    def test_doctor_help_exposes_separate_smoke_timeout(self) -> None:
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["doctor", "--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("--timeout-seconds", help_text)
        self.assertIn("--smoke-timeout-seconds", help_text)
        self.assertIn("except optional Codex", help_text)
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


if __name__ == "__main__":
    unittest.main()
