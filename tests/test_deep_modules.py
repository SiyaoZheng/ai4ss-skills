from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from goal_cli.adapters import TikOutcome, ProducerOutcome
from goal_cli.config import analyze_config_policy, load_config
from goal_cli.runtime import RuntimeOptions, run_goal
from goal_cli.setup_check import DoctorOptions, ProbeResult, doctor_exit_code, run_doctor
from goal_cli.tok_execution import TokExecutionResult


class DeepModuleInterfaceTests(unittest.TestCase):
    def test_runtime_cycle_can_complete_through_provider_adapter_seam(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root))
            adapters = PassingProviderAdapters()

            result = run_goal(config, RuntimeOptions(max_cycles=1, max_minutes=0), adapters=adapters)

            self.assertEqual(result.status, "complete")
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(adapters.calls, ["produce", "tik"])

    def test_config_policy_exposes_writable_scope_facts_and_issue_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, write_dirs=["."]))

            policy = analyze_config_policy(config)

            self.assertTrue(any(issue.code == "tok.write_dir.project_root" for issue in policy.issues))
            self.assertTrue(any(issue.code == "tok.write_dir.protected_overlap" for issue in policy.issues))
            self.assertEqual(len(policy.writable_scopes), 1)
            self.assertFalse(policy.writable_scopes[0].valid)
            self.assertIn(config.artifact.path, policy.protected_paths)

    def test_config_policy_rejects_writable_scope_that_can_edit_goal_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "configs"
            config_dir.mkdir()
            (root / "output").mkdir()
            config_path = config_dir / "goal.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    name = "config-protection-test"
                    state_dir = ".goal"
                    runs_dir = ".goal/runs"

                    [project]
                    root = ".."

                    [artifact]
                    path = "output/artifact.txt"

                    [producer]
                    command = "ignored-producer"

                    [tik]
                    provider = "oracle"
                    command = "ignored-tik"

                    [tik.prompt]
                    text = "Evaluate {artifact_path}."

                    [tok]
                    provider = "codex_goal"
                    write_dirs = ["configs"]
                    sandbox = "workspace-write"

                    [tok.prompt]
                    template = "Goal {goal_name} verdict {tik_ledger}"

                    [no_mistakes]
                    enabled = false

                    [observability]
                    enabled = false

                    [safety]
                    generated_dirs = ["output", "build"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            policy = analyze_config_policy(load_config(config_path))

            self.assertTrue(any(issue.code == "tok.write_dir.protected_overlap" for issue in policy.issues), policy.issues)
            self.assertIn(config_path.resolve(), policy.protected_paths)

    def test_doctor_can_use_probe_adapter_without_path_or_environment_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root))
            probes = ReadyProbeAdapter()

            checks = run_doctor(config, DoctorOptions(smoke_codex_goal=True), probes=probes)

            self.assertEqual(doctor_exit_code(checks), 0, checks)
            self.assertEqual(probes.commands, [("codex", "exec", "--help"), ("codex", "exec", "--enable", "goals", "--help")])
            self.assertTrue(any(check.name == "codex_goal.smoke" and check.ok for check in checks))

    def _write_project(self, root: Path, write_dirs: list[str] | None = None) -> Path:
        (root / "src").mkdir()
        (root / "scripts").mkdir()
        (root / "output").mkdir()
        config = f'''
name = "deep-module-test"
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
write_dirs = {json.dumps(write_dirs or ["src"])}
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
        config_path = root / "goal.toml"
        config_path.write_text(config, encoding="utf-8")
        return config_path


class PassingProviderAdapters:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def produce_artifact(self, config, run_dir, timeout_seconds=None) -> ProducerOutcome:
        self.calls.append("produce")
        config.artifact.path.parent.mkdir(parents=True, exist_ok=True)
        config.artifact.path.write_text("ready\n", encoding="utf-8")
        return ProducerOutcome(True)

    def run_tik(self, config, prompt, run_dir, timeout_seconds=None) -> TikOutcome:
        self.calls.append("tik")
        memo_path = run_dir / "tik_memo.md"
        memo_path.write_text(
            textwrap.dedent(
                """
                {
                  "artifact_ready": true,
                  "central_bottleneck": "",
                  "blocking_objections": [],
                  "required_next_artifact_changes": []
                }
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return TikOutcome(memo_path)

    def execute_tok(self, config, prompt, run_dir, timeout_seconds=None) -> TokExecutionResult:
        self.calls.append("execute")
        return TokExecutionResult(False, None, None, ("unused in passing tik test",))


class ReadyProbeAdapter:
    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def which(self, binary: str) -> str | None:
        return f"/fake/bin/{binary}"

    def run(self, command: list[str], cwd: Path, timeout_seconds: float) -> subprocess.CompletedProcess[str]:
        self.commands.append(tuple(command))
        return subprocess.CompletedProcess(command, 0, "--output-schema --output-last-message --enable --add-dir --sandbox\n", "")

    def package_available(self, package: str) -> bool:
        return True

    def env_has_value(self, name: str) -> bool:
        return True

    def path_writable(self, path: Path) -> bool:
        return True

    def codex_goal_smoke(self, config, options) -> ProbeResult:
        return ProbeResult(True, "fake smoke ok")


if __name__ == "__main__":
    unittest.main()
