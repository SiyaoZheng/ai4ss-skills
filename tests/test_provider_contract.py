from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from goal_cli.config import TokConfig
from goal_cli.lease import CapabilityLease
from goal_cli.lifecycle import CallState, WorkState
from goal_cli.provider_contract import (
    native_provider_policy,
    preflight_tok_provider,
    supervisor_transition,
)
from goal_cli.supervisor import AttemptOutcomeKind
from goal_cli.tok_execution import (
    build_claude_code_goal_tok_plan,
    build_codex_app_server_tok_plan,
    build_codex_goal_tok_plan,
)


class ProviderContractTests(unittest.TestCase):
    def test_all_three_providers_pass_same_isolated_lease_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            lease = CapabilityLease("lease-v1", (), allow_shell=True, allow_network=False)

            reports = [
                preflight_tok_provider(
                    self._config(provider, root),
                    lease,
                    run_dir=root / "run",
                    containment_backend="sandbox-exec",
                    which=lambda tool: f"/bin/{tool}",
                )
                for provider in ("claude_code_goal", "codex_goal", "codex_app_server")
            ]

            self.assertTrue(all(report.ok for report in reports), reports)
            self.assertEqual({report.filesystem_boundary for report in reports}, {str(root.resolve())})
            self.assertEqual({report.network_access for report in reports}, {False})

    def test_preflight_fails_closed_for_widened_or_unenforceable_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            lease = CapabilityLease("lease-v1", (), allow_shell=True, allow_network=False, tools=("git",))

            danger = preflight_tok_provider(
                self._config("codex_goal", root, sandbox="danger-full-access"),
                lease,
                run_dir=root / "run",
                containment_backend="sandbox-exec",
                which=lambda tool: f"/bin/{tool}",
            )
            no_claude_containment = preflight_tok_provider(
                self._config("claude_code_goal", root),
                lease,
                run_dir=root / "run",
                containment_backend=None,
                which=lambda tool: f"/bin/{tool}",
            )
            network_mismatch = preflight_tok_provider(
                self._config("codex_app_server", root, network_access=True),
                lease,
                run_dir=root / "run",
                containment_backend="sandbox-exec",
                which=lambda tool: f"/bin/{tool}",
            )
            missing_tool = preflight_tok_provider(
                self._config("codex_goal", root),
                lease,
                run_dir=root / "run",
                containment_backend="sandbox-exec",
                which=lambda tool: None,
            )

            self.assertIn("danger-full-access", danger.detail)
            self.assertIn("containment backend", no_claude_containment.detail)
            self.assertIn("network", network_mismatch.detail)
            self.assertIn("required tool is unavailable: git", missing_tool.detail)

            escaped_attachments = preflight_tok_provider(
                self._config("codex_goal", root),
                lease,
                run_dir=root.parent / "canonical-run",
                containment_backend="sandbox-exec",
                which=lambda tool: f"/bin/{tool}",
            )
            self.assertIn("provider run directory escapes isolated boundary", escaped_attachments.detail)

    def test_provider_specific_plans_keep_common_isolated_root_and_safe_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            run_dir = root / "run"
            run_dir.mkdir()

            claude_config = self._config("claude_code_goal", root)
            codex_config = self._config("codex_goal", root)
            app_config = self._config("codex_app_server", root)
            plans = (
                build_claude_code_goal_tok_plan(claude_config, "prompt", run_dir),
                build_codex_goal_tok_plan(codex_config, "prompt", run_dir),
                build_codex_app_server_tok_plan(app_config, "prompt", run_dir),
            )

            self.assertEqual({plan.cwd for plan in plans}, {root.resolve()})
            self.assertNotIn("--dangerously-skip-permissions", plans[0].command)
            self.assertIn("--sandbox", plans[1].command)
            self.assertEqual(plans[2].command[:2], ("codex", "app-server"))
            policies = [
                native_provider_policy(config, run_dir=run_dir, containment_backend="sandbox-exec")
                for config in (claude_config, codex_config, app_config)
            ]
            self.assertTrue(all(policy["filesystem_boundary"] == str(root.resolve()) for policy in policies))
            self.assertTrue(all(policy["network_access"] is False for policy in policies))
            self.assertTrue(
                all(
                    all(Path(path).resolve().is_relative_to(root.resolve()) for path in policy["writable_roots"])
                    for policy in policies
                )
            )

    def test_equivalent_outcomes_have_provider_independent_supervisor_transitions(self) -> None:
        for outcome in AttemptOutcomeKind:
            with self.subTest(outcome=outcome):
                transitions = {
                    provider: supervisor_transition(outcome)
                    for provider in ("claude_code_goal", "codex_goal", "codex_app_server")
                }
                self.assertEqual(len(set(transitions.values())), 1)

        self.assertEqual(supervisor_transition(AttemptOutcomeKind.PROVIDER_ERROR).work_state, WorkState.ACTIVE)
        self.assertEqual(supervisor_transition(AttemptOutcomeKind.PROVIDER_ERROR).call_state, CallState.FAILED)
        self.assertFalse(supervisor_transition(AttemptOutcomeKind.PROVIDER_ERROR).consumes_angle)
        self.assertEqual(supervisor_transition(AttemptOutcomeKind.SELF_BLOCKED).work_state, WorkState.BLOCKED)
        self.assertTrue(supervisor_transition(AttemptOutcomeKind.SELF_BLOCKED).consumes_angle)

    def test_parent_evidence_paths_are_separate_from_model_controlled_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            isolated = base / "isolated"
            canonical_run = base / "canonical-run"
            attachments = isolated / ".goal" / "runs" / "attempt" / "attachments"
            victim = base / "victim.txt"
            (isolated / "src").mkdir(parents=True)
            attachments.mkdir(parents=True)
            canonical_run.mkdir()
            victim.write_text("preserve me\n", encoding="utf-8")
            malicious_report = attachments.parent / "tok_report.json"
            malicious_report.symlink_to(victim)

            plans = []
            for provider, builder in (
                ("claude_code_goal", build_claude_code_goal_tok_plan),
                ("codex_goal", build_codex_goal_tok_plan),
                ("codex_app_server", build_codex_app_server_tok_plan),
            ):
                config = replace(
                    self._config(provider, isolated),
                    attachments_dir=attachments,
                )
                plans.append(builder(config, "prompt", canonical_run))

            self.assertTrue(all(plan.report_path.parent == canonical_run for plan in plans))
            self.assertTrue(all(not plan.report_path.is_relative_to(isolated) for plan in plans))
            plans[0].report_path.write_text("trusted report\n", encoding="utf-8")
            self.assertEqual(victim.read_text(encoding="utf-8"), "preserve me\n")

    def _config(
        self,
        provider: str,
        root: Path,
        *,
        sandbox: str = "workspace-write",
        network_access: bool = False,
    ) -> TokConfig:
        resolved = root.resolve()
        return TokConfig(
            provider=provider,
            prompt_template="",
            write_dirs=(resolved / "src",),
            sandbox=sandbox,
            run_cwd=resolved,
            containment_root=resolved,
            network_access=network_access,
        )


if __name__ == "__main__":
    unittest.main()
