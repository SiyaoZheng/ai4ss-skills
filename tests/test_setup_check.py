from __future__ import annotations

import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.config import API_TIK_KEY_ENV_VARS, DEFAULT_API_TIK_MODEL, load_config
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

    def test_doctor_fails_when_codex_exec_lacks_goal_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root, include_goal_flags=False)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("does not show --enable", self._detail(checks, "codex.exec.--enable"))
            self.assertIn("codex.exec.--enable", self._detail(checks, "one_click_artifact_loop"))

    def test_doctor_fails_for_missing_producer_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, producer_command="missing-producer scripts/produce.py")
            self._install_fake_codex(root)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("command executable not found", self._detail(checks, "producer.command"))

    def test_doctor_checks_api_tik_package_and_auth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="api")
            self._install_fake_codex(root)
            self.assertEqual(load_config(root / "goal.toml").tik.model, DEFAULT_API_TIK_MODEL)

            old_api_keys = {name: os.environ.pop(name, None) for name in API_TIK_KEY_ENV_VARS}
            old_env_file = os.environ.get("GOAL_CLI_API_ENV_FILE")
            os.environ["GOAL_CLI_API_ENV_FILE"] = str(root / "missing-api.env")
            try:
                with mock.patch("goal_cli.setup_check.importlib.util.find_spec", return_value=None):
                    checks = run_doctor(load_config(root / "goal.toml"))
            finally:
                for name, value in old_api_keys.items():
                    if value is not None:
                        os.environ[name] = value
                if old_env_file is None:
                    os.environ.pop("GOAL_CLI_API_ENV_FILE", None)
                else:
                    os.environ["GOAL_CLI_API_ENV_FILE"] = old_env_file

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("not installed", self._detail(checks, "openai.package"))
            self.assertIn("no API key is set", self._detail(checks, "openai.auth"))

    def test_doctor_accepts_api_tik_key_from_user_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="api")
            self._install_fake_codex(root)
            env_file = root / "api.env"
            env_file.write_text("PACKYAPI_API_KEY=file-packy-key\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"GOAL_CLI_API_ENV_FILE": str(env_file)}, clear=False):
                with mock.patch("goal_cli.setup_check.importlib.util.find_spec", return_value=object()):
                    checks = run_doctor(load_config(root / "goal.toml"))

            self.assertIn("PACKYAPI_API_KEY is set", self._detail(checks, "openai.auth"))

    def test_doctor_requires_ephemeral_only_for_codex_file_tik(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root, include_ephemeral=False)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 0, checks)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="codex_file")
            self._install_fake_codex(root, include_ephemeral=False)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("does not show --ephemeral", self._detail(checks, "codex.exec.--ephemeral"))
            self.assertIn("codex.exec.--ephemeral", self._detail(checks, "one_click_artifact_loop"))

    def test_doctor_checks_every_parallel_oracle_tik_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root)
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    '[tik]\nprovider = "oracle"\ncommand = "python3 scripts/tik.py"',
                    textwrap.dedent(
                        """
                        [tik]

                        [[tik.providers]]
                        label = "alpha"
                        provider = "oracle"
                        command = "python3 scripts/tik.py"

                        [[tik.providers]]
                        label = "beta"
                        provider = "oracle"
                        command = "python3 scripts/missing_tik.py"
                        """
                    ).strip(),
                ),
                encoding="utf-8",
            )

            checks = run_doctor(load_config(config_path))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("command script does not exist", self._detail(checks, "tik.providers.beta.command"))

    def test_doctor_checks_checklist_tik_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="checklist")
            self._install_fake_codex(root)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("command executable found", self._detail(checks, "tik.command"))

    def test_codex_goal_smoke_uses_temp_workspace_and_edits_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(load_config(root / "goal.toml"), DoctorOptions(smoke_codex_goal=True))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("temporary source change", self._detail(checks, "codex_goal.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-prompt goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)

    def test_codex_app_server_smoke_uses_temp_workspace_and_edits_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tok_provider="codex_app_server")
            self._install_fake_codex(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(load_config(root / "goal.toml"), DoctorOptions(smoke_codex_app_server=True))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("codex app-server --help succeeded", self._detail(checks, "codex.app_server.help"))
            self.assertIn("codex app-server supports --stdio", self._detail(checks, "codex.app_server.--stdio"))
            self.assertIn("temporary source change", self._detail(checks, "codex_app_server.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-prompt goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)

    def test_codex_file_tik_smoke_uses_temp_artifact_and_validates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="codex_file")
            self._install_fake_codex(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(
                load_config(root / "goal.toml"),
                DoctorOptions(smoke_codex_goal=True, smoke_codex_file_tik=True),
            )

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("parseable current-artifact verdict", self._detail(checks, "codex_file_tik.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-prompt goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)

    def test_claude_code_file_tik_smoke_uses_temp_artifact_and_validates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="claude_code_file")
            self._install_fake_codex(root)
            self._install_fake_claude(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(
                load_config(root / "goal.toml"),
                DoctorOptions(smoke_codex_goal=True, smoke_claude_code_file_tik=True),
            )

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("claude found at", self._detail(checks, "claude.binary"))
            self.assertIn("claude supports --print", self._detail(checks, "claude.--print"))
            self.assertIn("parseable current-artifact verdict", self._detail(checks, "claude_code_file_tik.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-prompt goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)

    def test_claude_code_goal_smoke_uses_temp_workspace_and_edits_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tok_provider="claude_code_goal")
            self._install_fake_claude(root)
            project_source = root / "src" / "source.txt"
            before = project_source.read_text(encoding="utf-8")

            checks = run_doctor(
                load_config(root / "goal.toml"),
                DoctorOptions(smoke_claude_code_goal=True),
            )

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("claude found at", self._detail(checks, "claude.binary"))
            self.assertNotIn("claude.--json-schema", [check.name for check in checks])
            self.assertIn("temporary source change", self._detail(checks, "claude_code_goal.smoke"))
            self.assertEqual(self._detail(checks, "one_click_artifact_loop"), "ready for one-prompt goal-cli run")
            self.assertEqual(project_source.read_text(encoding="utf-8"), before)
            self.assertNotIn("codex.binary", [check.name for check in checks])

    def test_doctor_fails_when_claude_help_lacks_disallowed_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root, tik_provider="claude_code_file")
            self._install_fake_codex(root)
            self._install_fake_claude(root, include_disallowed_tools=False)

            checks = run_doctor(load_config(root / "goal.toml"))

            self.assertEqual(doctor_exit_code(checks), 1)
            self.assertIn("does not show --disallowedTools", self._detail(checks, "claude.--disallowedTools"))
            self.assertIn("claude.--disallowedTools", self._detail(checks, "one_click_artifact_loop"))

    def test_doctor_resolves_relative_no_mistakes_binary_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_project(root)
            self._install_fake_codex(root)
            tools_dir = root / "tools"
            tools_dir.mkdir()
            fake_no_mistakes = tools_dir / "no-mistakes"
            fake_no_mistakes.write_text(
                textwrap.dedent(
                    """
                    #!/usr/bin/env python3
                    import sys

                    if sys.argv[1:] == ["axi", "run", "--help"]:
                        print("--intent --yes --skip")
                        raise SystemExit(0)
                    raise SystemExit(2)
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            fake_no_mistakes.chmod(0o755)
            config_path = root / "goal.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8").replace(
                    "[no_mistakes]\nenabled = false",
                    '[no_mistakes]\nenabled = true\nbinary = "tools/no-mistakes"',
                ),
                encoding="utf-8",
            )

            checks = run_doctor(load_config(config_path))

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertIn("tools/no-mistakes", self._detail(checks, "no_mistakes.binary"))

    def _write_project(
        self,
        root: Path,
        producer_command: str = "python3 scripts/produce.py",
        tik_provider: str = "oracle",
        tok_provider: str = "codex_goal",
    ) -> None:
        (root / "src").mkdir()
        (root / "scripts").mkdir()
        (root / "output").mkdir()
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        (root / "scripts" / "produce.py").write_text("print('produce')\n", encoding="utf-8")
        (root / "scripts" / "tik.py").write_text("print('{}')\n", encoding="utf-8")
        if tik_provider == "api":
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "api"
                """
            ).strip()
        elif tik_provider == "codex_file":
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "codex_file"
                """
            ).strip()
        elif tik_provider == "claude_code_file":
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "claude_code_file"
                """
            ).strip()
        elif tik_provider == "checklist":
            tik_table = textwrap.dedent(
                """
                [tik]
                provider = "checklist"
                command = "python3 scripts/tik.py"
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
provider = "{tok_provider}"
write_dirs = ["src"]
sandbox = "workspace-write"

[tok.prompt]
template = "Goal {{goal_name}} review {{tik_review_path}}"

[no_mistakes]
enabled = false

[observability]
enabled = false

[safety]
generated_dirs = ["output", "build"]
'''
        (root / "goal.toml").write_text(config, encoding="utf-8")

    def _install_fake_codex(self, root: Path, include_goal_flags: bool = True, include_ephemeral: bool = True) -> None:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_codex = bin_dir / "codex"
        help_flags = ["--add-dir", "--sandbox", "--skip-git-repo-check", "--output-last-message"]
        if include_goal_flags:
            help_flags.append("--enable")
        if include_ephemeral:
            help_flags.append("--ephemeral")
        help_text = " ".join(help_flags)
        fake_codex.write_text(
            textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                import json
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                if args in (["exec", "--help"], ["exec", "--enable", "goals", "--help"]):
                    print({help_text!r})
                    raise SystemExit(0)
                if args == ["app-server", "--help"]:
                    print("--stdio generate-ts generate-json-schema")
                    raise SystemExit(0)
                if args == ["app-server", "--stdio"]:
                    def respond(request_id, result):
                        print(json.dumps({{"id": request_id, "result": result}}), flush=True)

                    for line in sys.stdin:
                        message = json.loads(line)
                        method = message["method"]
                        request_id = message["id"]
                        params = message.get("params") or {{}}
                        if method == "initialize":
                            respond(request_id, {{"userAgent": "fake-codex-app-server"}})
                        elif method == "thread/start":
                            assert params["approvalPolicy"] == "never"
                            assert params["ephemeral"] is False
                            respond(request_id, {{"thread": {{"id": "thread-1"}}}})
                        elif method == "thread/goal/set":
                            assert params["threadId"] == "thread-1"
                            respond(request_id, {{"goal": {{"threadId": "thread-1", "objective": params["objective"], "status": "active"}}}})
                        elif method == "turn/start":
                            assert "outputSchema" not in params
                            assert "Doctor smoke check for goal-cli setup readiness" in params["input"][0]["text"]
                            Path(params["cwd"], "doctor-smoke.txt").write_text("ok\\n", encoding="utf-8")
                            respond(request_id, {{"turn": {{"id": "turn-1", "status": "inProgress", "items": []}}}})
                            print(json.dumps({{
                                "method": "turn/completed",
                                "params": {{"threadId": "thread-1", "turn": {{"id": "turn-1", "status": "completed", "items": []}}}}
                            }}), flush=True)
                        else:
                            raise SystemExit(f"unexpected method: {{method}}")
                    raise SystemExit(0)

                workspace = Path(args[args.index("-C") + 1])
                assert args[0] == "exec"
                if "--enable" in args and "goals" in args:
                    assert "--output-schema" not in args
                    assert "--output-last-message" not in args
                    assert "--enable" in args and "goals" in args
                    prompt = sys.stdin.read()
                    assert prompt.startswith("/goal\\n")
                    assert "Doctor smoke check for goal-cli setup readiness" in prompt
                    (workspace / "doctor-smoke.txt").write_text("ok\\n", encoding="utf-8")
                    print("assistant final")
                    print("Done.")
                    print()
                    print("tokens used")
                    print("1")
                    raise SystemExit(0)

                output_path = Path(args[args.index("--output-last-message") + 1])
                assert "--skip-git-repo-check" in args
                assert args[args.index("--sandbox") + 1] == "read-only"
                assert "--ephemeral" in args
                assert sorted(path.name for path in workspace.iterdir()) == ["doctor-artifact.txt"]
                prompt = sys.stdin.read()
                assert "Doctor smoke check for goal-cli codex_file tik readiness" in prompt
                assert "doctor-artifact.txt" in prompt
                output_path.write_text(json.dumps({{
                    "artifact_ready": False
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

    def _install_fake_claude(self, root: Path, include_disallowed_tools: bool = True) -> None:
        bin_dir = root / "claude-bin"
        bin_dir.mkdir()
        fake_claude = bin_dir / "claude"
        help_flags = ["--print", "--output-format", "--model", "--add-dir", "--permission-mode"]
        if include_disallowed_tools:
            help_flags.append("--disallowedTools")
        help_text = " ".join(help_flags)
        fake_claude.write_text(
            textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                import json
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                if args == ["--help"]:
                    print({help_text!r})
                    raise SystemExit(0)

                assert "--print" in args
                assert args[args.index("--output-format") + 1] == "json"

                if "--permission-mode" in args:
                    assert "--json-schema" not in args
                    assert args[args.index("--permission-mode") + 1] == "acceptEdits"
                    add_dirs = [args[index + 1] for index, arg in enumerate(args) if arg == "--add-dir"]
                    assert any(path.endswith("attachments") for path in add_dirs)
                    prompt = sys.stdin.read()
                    assert "Doctor smoke check for goal-cli setup readiness" in prompt
                    (Path.cwd() / "doctor-smoke.txt").write_text("ok\\n", encoding="utf-8")
                    print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "result": "done"}}))
                    raise SystemExit(0)

                disallowed = args[args.index("--disallowedTools") + 1]
                assert "Write" in disallowed and "Edit" in disallowed and "Bash" in disallowed
                workspace = Path.cwd()
                assert sorted(path.name for path in workspace.iterdir()) == ["doctor-artifact.txt"]
                prompt = sys.stdin.read()
                assert "Doctor smoke check for goal-cli claude_code_file tik readiness" in prompt
                assert "doctor-artifact.txt" in prompt
                memo = json.dumps({{
                    "artifact_ready": False
                }})
                print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "result": memo}}))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old_path))

    def _detail(self, checks, name: str) -> str:
        matches = [check.detail for check in checks if check.name == name]
        self.assertTrue(matches, f"missing check {name}: {checks}")
        return matches[-1]


if __name__ == "__main__":
    unittest.main()
