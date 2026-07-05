from __future__ import annotations

import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.config import load_config
from goal_cli.setup_check import DoctorOptions, doctor_exit_code, run_doctor


class SetupCheckTests(unittest.TestCase):
    def test_doctor_reports_static_ready_but_not_one_click_without_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertEqual(self._detail(checks, "static_setup"), "static setup ready for goal-cli run")
            self.assertIn("not proven", self._detail(checks, "one_click_artifact_loop"))

    def test_doctor_fails_when_codex_exec_lacks_schema_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root, include_schema_flags=False)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("does not show --output-schema", self._detail(checks, "codex.exec.--output-schema"))
            self.assertIn("codex.exec.--output-schema", self._detail(checks, "one_click_artifact_loop"))

    def test_doctor_fails_for_missing_producer_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, producer_command="missing-producer scripts/produce.py")
            self._install_fake_codex(root)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("command executable not found", self._detail(checks, "producer.command"))

    def test_doctor_checks_agent_tik_openai_package_and_auth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="agent")
            self._install_fake_codex(root)

            old_api_key = os.environ.pop("OPENAI_API_KEY", None)
            try:
                with mock.patch("goal_cli.setup_check.importlib.util.find_spec", return_value=None):
                    checks = run_doctor(load_config(root / "goal.toml"))
            finally:
                if old_api_key is not None:
                    os.environ["OPENAI_API_KEY"] = old_api_key

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("not installed", self._detail(checks, "openai.package"))
            self.assertIn("not set", self._detail(checks, "openai.auth"))

    def test_codex_goal_smoke_uses_temp_workspace_and_validates_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(load_config(root / "goal.toml"), DoctorOptions(smoke_codex_goal=True))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("schema-valid tok report", self._detail(checks, "codex_goal.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-click goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)

    def _write_project(
        self,
        root: Path,
        producer_command: str = "python3 scripts/produce.py",
        tik_provider: str = "oracle",
    ) -> None:
        (root / "src").mkdir()
        (root / "scripts").mkdir()
        (root / "output").mkdir()
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        (root / "scripts" / "produce.py").write_text("print('produce')\n", encoding="utf-8")
        (root / "scripts" / "tik.py").write_text("print('{}')\n", encoding="utf-8")
        if tik_provider == "agent":
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "agent"
                model = "gpt-5.5-pro"
                """
            ).strip()
        else:
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "oracle"
                command = "python3 scripts/tik.py"
                """
            ).strip()
        config = f'''
name = "setup-check-test"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact"

[producer]
command = {json.dumps(producer_command)}

{tik_table}

[tik.prompt]
text = "Evaluate {{artifact_path}}."

[tok]
provider = "codex_goal"
write_dirs = ["src"]
sandbox = "workspace-write"

[tok.prompt]
template = "Goal {{goal_name}} verdict {{tik_ledger}}"

[no_mistakes]
enabled = false

[observability]
enabled = false

[safety]
generated_dirs = ["output", "build"]
'''
        (root / "goal.toml").write_text(config, encoding="utf-8")

    def _install_fake_codex(self, root: Path, include_schema_flags: bool = True) -> None:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_codex = bin_dir / "codex"
        help_flags = "--output-schema --output-last-message --enable --add-dir --sandbox" if include_schema_flags else "--enable --add-dir --sandbox"
        fake_codex.write_text(
            textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                import json
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                if args in (["exec", "--help"], ["exec", "--enable", "goals", "--help"]):
                    print({help_flags!r})
                    raise SystemExit(0)

                output_path = Path(args[args.index("--output-last-message") + 1])
                schema_path = Path(args[args.index("--output-schema") + 1])
                workspace = Path(args[args.index("-C") + 1])
                assert args[0] == "exec"
                assert "--enable" in args and "goals" in args
                assert schema_path.exists()
                (workspace / "doctor-smoke.txt").write_text("ok\\n", encoding="utf-8")
                output_path.write_text(json.dumps({{
                    "source_change_possible": True,
                    "revision_strategy": "write temporary smoke file",
                    "sources_changed": ["doctor-smoke.txt"],
                    "expected_artifact_visible_improvement": ["codex_goal can emit schema-shaped reports"],
                    "remaining_artifact_bottleneck": "none for setup smoke"
                }}) + "\\n", encoding="utf-8")
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old_path))

    def _detail(self, checks, name: str) -> str:
        matches = [check.detail for check in checks if check.name == name]
        self.assertTrue(matches, f"missing check {name}: {checks}")
        return matches[-1]


if __name__ == "__main__":
    unittest.main()
