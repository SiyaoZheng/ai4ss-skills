from __future__ import annotations

import os
import plistlib
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from goal_cli.config import load_config
from goal_cli.runtime import DEFAULT_MAX_MINUTES, CleanupResult, RunResult
from goal_cli.system_heartbeat import (
    DEFAULT_EVERY_MINUTES,
    DEFAULT_PERPETUAL_WAKE_MINUTES,
    SystemHeartbeatOptions,
    build_system_heartbeat_layout,
    install_system_heartbeat,
    run_system_heartbeat_tick,
)


class SystemHeartbeatTests(unittest.TestCase):
    def test_default_layout_uses_ten_hour_tick_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xdg_config = root / "xdg"
            config = load_config(self._write_project(root))

            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_config)}):
                layout = build_system_heartbeat_layout(
                    config,
                    SystemHeartbeatOptions(
                        manager="systemd-user",
                        label="goal-cli-test",
                    ),
                )

            self.assertEqual(layout.max_minutes, DEFAULT_MAX_MINUTES)
            self.assertEqual(layout.interval_seconds, 1800)
            self.assertEqual(DEFAULT_EVERY_MINUTES, 30.0)
            self.assertEqual(DEFAULT_PERPETUAL_WAKE_MINUTES, 5.0)
            self.assertEqual(layout.tick_args[-2:], ("--max-minutes", "600"))

    def test_perpetual_layout_defaults_to_five_minute_wakeups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root, perpetual=True))

            layout = build_system_heartbeat_layout(
                config,
                SystemHeartbeatOptions(manager="launchd", label="goal-cli-test"),
            )

            self.assertEqual(layout.interval_seconds, 300)

    def test_launchd_layout_runs_one_absolute_tick(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root))

            layout = build_system_heartbeat_layout(
                config,
                SystemHeartbeatOptions(
                    manager="launchd",
                    label="com.goal-cli.test",
                    every_minutes=15,
                    max_minutes=7,
                ),
            )

            plist = plistlib.loads(layout.files[0].content.encode("utf-8"))
            self.assertEqual(plist["Label"], "com.goal-cli.test")
            self.assertEqual(plist["StartInterval"], 900)
            self.assertTrue(plist["RunAtLoad"])
            self.assertEqual(plist["WorkingDirectory"], str(root.resolve()))
            args = plist["ProgramArguments"]
            self.assertEqual(args[1:3], ["-m", "goal_cli.cli"])
            self.assertEqual(args[args.index("-c") + 1], str((root / "goal.toml").resolve()))
            self.assertEqual(args[args.index("heartbeat") :], ["heartbeat", "tick", "--max-minutes", "7"])
            self.assertEqual(plist["StandardOutPath"], str((root / ".goal" / "system-heartbeat" / "launchd.out.log").resolve()))

    def test_systemd_layout_has_service_and_persistent_timer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xdg_config = root / "xdg"
            config = load_config(self._write_project(root))

            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_config)}):
                layout = build_system_heartbeat_layout(
                    config,
                    SystemHeartbeatOptions(
                        manager="systemd-user",
                        label="goal-cli-test",
                        every_minutes=2.5,
                        max_minutes=4.5,
                    ),
                )

            service, timer = layout.files
            self.assertEqual(service.path, xdg_config / "systemd" / "user" / "goal-cli-test.service")
            self.assertEqual(timer.path, xdg_config / "systemd" / "user" / "goal-cli-test.timer")
            self.assertIn("WorkingDirectory=" + str(root.resolve()), service.content)
            self.assertIn("-m goal_cli.cli", service.content)
            self.assertIn("heartbeat tick --max-minutes 4.5", service.content)
            self.assertIn("StandardOutput=append:", service.content)
            self.assertIn("OnUnitActiveSec=150s", timer.content)
            self.assertIn("Persistent=true", timer.content)
            self.assertIn("Unit=goal-cli-test.service", timer.content)

    def test_install_dry_run_does_not_write_service_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xdg_config = root / "xdg"
            config = load_config(self._write_project(root))

            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_config)}):
                result = install_system_heartbeat(
                    config,
                    SystemHeartbeatOptions(
                        manager="systemd-user",
                        label="goal-cli-test",
                        every_minutes=5,
                        max_minutes=1,
                        dry_run=True,
                    ),
                )

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(any("would write" in message for message in result.messages))
            self.assertTrue(any("would run: systemctl --user enable --now goal-cli-test.timer" in message for message in result.messages))
            self.assertFalse((xdg_config / "systemd" / "user" / "goal-cli-test.service").exists())

    def test_install_refuses_to_overwrite_unmanaged_service_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xdg_config = root / "xdg"
            unit_dir = xdg_config / "systemd" / "user"
            unit_dir.mkdir(parents=True)
            service_path = unit_dir / "goal-cli-test.service"
            service_path.write_text("[Service]\nExecStart=/bin/true\n", encoding="utf-8")
            config = load_config(self._write_project(root))

            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_config)}):
                result = install_system_heartbeat(
                    config,
                    SystemHeartbeatOptions(
                        manager="systemd-user",
                        label="goal-cli-test",
                        every_minutes=5,
                        max_minutes=1,
                        start=False,
                    ),
                )

            self.assertEqual(result.exit_code, 1)
            self.assertIn("refusing to overwrite unmanaged service file", "\n".join(result.errors))
            self.assertEqual(service_path.read_text(encoding="utf-8"), "[Service]\nExecStart=/bin/true\n")

    def test_tick_treats_active_lock_as_skipped_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = load_config(self._write_project(root))

            with (
                mock.patch("goal_cli.system_heartbeat.cleanup_runtime", return_value=CleanupResult(("cleanup found nothing to do",), ("heartbeat lock is active",))),
                mock.patch("goal_cli.system_heartbeat.run_goal", return_value=RunResult(1, "locked", None, "heartbeat already running")) as run_goal,
            ):
                result = run_system_heartbeat_tick(config, max_minutes=3)

            self.assertEqual(result.exit_code, 0)
            self.assertIn("heartbeat already running", result.messages)
            self.assertIn("heartbeat tick skipped because another heartbeat is active", result.messages)
            self.assertIn("warning: heartbeat lock is active", result.errors)
            self.assertEqual(run_goal.call_args.args[1].max_minutes, 3)

    def _write_project(self, root: Path, *, perpetual: bool = False) -> Path:
        (root / "src").mkdir()
        (root / "output").mkdir()
        (root / "build").mkdir()
        (root / "scripts").mkdir()
        config = textwrap.dedent(
            """
            name = "system-heartbeat-test"
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

            [no_mistakes]
            enabled = false

            [observability]
            enabled = false

            [safety]
            generated_dirs = ["output", "build"]
            """
        ).strip()
        if perpetual:
            config += "\n\n[perpetual]\nenabled = true"
        config_path = root / "goal.toml"
        config_path.write_text(config + "\n", encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
