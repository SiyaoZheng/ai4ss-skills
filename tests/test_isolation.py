from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from goal_cli.adapters import build_contained_shell_command, mutation_containment_backend, run_shell_logged
from goal_cli.isolation import IsolatedWorkspace, IsolationError
from goal_cli.lease import CapabilityLease, FileOperation, LeaseRule
from goal_cli.transaction import load_transaction


class IsolatedWorkspaceTests(unittest.TestCase):
    def test_contained_shell_plans_are_root_scoped(self) -> None:
        root = Path("/tmp/isolated-workspace")

        macos = build_contained_shell_command("python3 producer.py", root, backend="sandbox-exec")
        linux = build_contained_shell_command("python3 producer.py", root, backend="bwrap")

        assert macos is not None
        assert linux is not None
        self.assertEqual(macos[0], "/usr/bin/sandbox-exec")
        self.assertIn(str(root.resolve(strict=False)), macos[2])
        self.assertIn("(deny file-write*", macos[2])
        self.assertEqual(linux[0], "bwrap")
        self.assertIn("--ro-bind", linux)
        self.assertIn("--bind", linux)
        self.assertIn(str(root.resolve(strict=False)), linux)

    def test_macos_containment_blocks_child_write_to_canonical_path(self) -> None:
        if mutation_containment_backend() != "sandbox-exec":
            self.skipTest("macOS sandbox-exec is not available")
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            isolated = base / "isolated"
            canonical = base / "canonical"
            isolated.mkdir()
            canonical.mkdir()
            escaped = canonical / "escaped.txt"
            command = f"printf allowed > inside.txt; printf denied > {escaped}"

            ok = run_shell_logged(
                command,
                isolated,
                base / "command.log",
                containment_root=isolated,
            )

            self.assertFalse(ok)
            self.assertEqual((isolated / "inside.txt").read_text(encoding="utf-8"), "allowed")
            self.assertFalse(escaped.exists())

    def test_authorized_exact_file_modification_is_applied_from_dirty_untracked_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            self._write_repo(root)
            lease = self._lease(FileOperation.MODIFY, "src/source.txt")

            with IsolatedWorkspace(root, root / ".goal", "attempt-exact") as workspace:
                self.assertNotEqual(workspace.root, root)
                self.assertEqual((workspace.root / "src" / "dirty-untracked.txt").read_text(encoding="utf-8"), "untracked\n")
                self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")
                (workspace.root / "src" / "source.txt").write_text("revised\n", encoding="utf-8")
                result = workspace.finalize(lease)

            self.assertTrue(result.authorized)
            self.assertTrue(result.committed)
            self.assertEqual(result.attempt_id, "attempt-exact")
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "revised\n")
            self.assertIsNotNone(result.journal_path)
            assert result.journal_path is not None
            self.assertEqual(load_transaction(result.journal_path)["attempt_id"], "attempt-exact")

    def test_one_unauthorized_change_discards_the_entire_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            self._write_repo(root)
            lease = self._lease(FileOperation.MODIFY, "src/source.txt")

            with IsolatedWorkspace(root, root / ".goal", "attempt-denied") as workspace:
                (workspace.root / "src" / "source.txt").write_text("revised\n", encoding="utf-8")
                (workspace.root / "governance-checklist.md").write_text("substitute work\n", encoding="utf-8")
                result = workspace.finalize(lease)

            self.assertFalse(result.authorized)
            self.assertFalse(result.committed)
            self.assertFalse((root / "governance-checklist.md").exists())
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "draft\n")
            self.assertEqual(result.violations[0].path, "governance-checklist.md")
            self.assertIsNone(result.journal_path)

    def test_canonical_drift_rejects_attempt_without_overwriting_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            self._write_repo(root)
            lease = self._lease(FileOperation.MODIFY, "src/source.txt")

            with IsolatedWorkspace(root, root / ".goal", "attempt-drift") as workspace:
                (workspace.root / "src" / "source.txt").write_text("agent revision\n", encoding="utf-8")
                (root / "src" / "source.txt").write_text("user edit after baseline\n", encoding="utf-8")
                result = workspace.finalize(lease)

            self.assertTrue(result.authorized)
            self.assertFalse(result.committed)
            self.assertTrue(result.conflict)
            self.assertIn("src/source.txt", result.detail)
            self.assertEqual((root / "src" / "source.txt").read_text(encoding="utf-8"), "user edit after baseline\n")

    def test_isolated_workspace_rejects_baseline_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            self._write_repo(root)
            outside.mkdir()
            os.symlink(outside, root / "src" / "escape")

            with self.assertRaisesRegex(IsolationError, "symlink escapes"):
                with IsolatedWorkspace(root, root / ".goal", "attempt-symlink"):
                    pass

    def test_zero_delta_is_authorized_without_creating_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            self._write_repo(root)
            lease = self._lease(FileOperation.MODIFY, "src/source.txt")

            with IsolatedWorkspace(root, root / ".goal", "attempt-zero") as workspace:
                result = workspace.finalize(lease)

            self.assertTrue(result.authorized)
            self.assertTrue(result.committed)
            self.assertEqual(result.mutations, ())
            self.assertIsNone(result.journal_path)

    def _write_repo(self, root: Path) -> None:
        (root / ".git").mkdir(parents=True)
        (root / ".goal").mkdir()
        (root / "src").mkdir()
        (root / "src" / "source.txt").write_text("draft\n", encoding="utf-8")
        (root / "src" / "dirty-untracked.txt").write_text("untracked\n", encoding="utf-8")
        (root / ".goal" / "state.json").write_text("{}\n", encoding="utf-8")

    def _lease(self, operation: FileOperation, path: str) -> CapabilityLease:
        return CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", (operation,), (path,)),),
        )


if __name__ == "__main__":
    unittest.main()
