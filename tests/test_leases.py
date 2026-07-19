from __future__ import annotations

import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from goal_cli.config import ConfigError, load_config
from goal_cli.lease import (
    CapabilityLease,
    DeltaError,
    FileMutation,
    FileOperation,
    LeaseRule,
    authorize_mutations,
    detect_mutations,
    snapshot_tree,
)


class CapabilityLeaseTests(unittest.TestCase):
    def test_config_loads_typed_capability_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "output").mkdir()
            config_path = self._write_config(
                root,
                """
                [lease]
                version = "lease-v7"
                allow_shell = true
                allow_network = false
                tools = ["git"]

                [[lease.rules]]
                effect = "allow"
                operations = ["modify", "rename"]
                paths = ["src/source.txt", "src/archive/**"]

                [[lease.rules]]
                effect = "deny"
                operations = ["rename"]
                paths = ["src/archive/frozen/**"]
                """,
            )

            config = load_config(config_path)

            assert config.lease is not None
            self.assertEqual(config.lease.version, "lease-v7")
            self.assertEqual(config.lease.tools, ("git",))
            self.assertTrue(config.lease.allow_shell)
            self.assertFalse(config.lease.allow_network)
            self.assertEqual(config.lease.rules[0].operations, (FileOperation.MODIFY, FileOperation.RENAME))

    def test_config_rejects_unknown_lease_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "output").mkdir()
            config_path = self._write_config(
                root,
                """
                [lease]
                version = "lease-v1"

                [[lease.rules]]
                effect = "allow"
                operations = ["overwrite"]
                paths = ["src/source.txt"]
                """,
            )

            with self.assertRaisesRegex(ConfigError, "unsupported lease operation"):
                load_config(config_path)

    def test_exact_modify_rule_denies_every_other_mutation(self) -> None:
        lease = CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", (FileOperation.MODIFY,), ("paper/manuscript.qmd",)),),
        )

        allowed = authorize_mutations(
            lease,
            (FileMutation(FileOperation.MODIFY, "paper/manuscript.qmd", before_identity="old", after_identity="new"),),
        )
        denied = authorize_mutations(
            lease,
            (FileMutation(FileOperation.MODIFY, "paper/appendix.qmd", before_identity="old", after_identity="new"),),
        )

        self.assertTrue(allowed.authorized)
        self.assertFalse(denied.authorized)
        self.assertEqual(denied.violations[0].path, "paper/appendix.qmd")
        self.assertEqual(denied.violations[0].operation, FileOperation.MODIFY)
        self.assertIn("no allow rule", denied.violations[0].reason)

    def test_create_modify_delete_are_separate_and_deny_overrides_allow(self) -> None:
        lease = CapabilityLease(
            version="lease-v1",
            rules=(
                LeaseRule("allow", (FileOperation.CREATE, FileOperation.MODIFY), ("paper/**",)),
                LeaseRule("deny", (FileOperation.MODIFY,), ("paper/frozen.qmd",)),
            ),
        )
        mutations = (
            FileMutation(FileOperation.CREATE, "paper/new.qmd", after_identity="new"),
            FileMutation(FileOperation.MODIFY, "paper/frozen.qmd", before_identity="old", after_identity="new"),
            FileMutation(FileOperation.DELETE, "paper/old.qmd", before_identity="old"),
        )

        decision = authorize_mutations(lease, mutations)

        self.assertFalse(decision.authorized)
        self.assertEqual(
            [(violation.path, violation.operation, violation.reason) for violation in decision.violations],
            [
                ("paper/frozen.qmd", FileOperation.MODIFY, "explicit deny rule"),
                ("paper/old.qmd", FileOperation.DELETE, "no allow rule"),
            ],
        )

    def test_rename_requires_source_and_destination_authorization(self) -> None:
        mutation = FileMutation(
            FileOperation.RENAME,
            "paper/new.qmd",
            source_path="drafts/old.qmd",
            before_identity="same",
            after_identity="same",
        )
        source_only = CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", (FileOperation.RENAME,), ("drafts/**",)),),
        )
        both = CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", (FileOperation.RENAME,), ("drafts/**", "paper/**")),),
        )

        denied = authorize_mutations(source_only, (mutation,))
        allowed = authorize_mutations(both, (mutation,))

        self.assertFalse(denied.authorized)
        self.assertEqual(denied.violations[0].path, "paper/new.qmd")
        self.assertTrue(allowed.authorized)

    def test_unsafe_paths_are_rejected_deterministically(self) -> None:
        lease = CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", tuple(FileOperation), ("**",)),),
        )
        unsafe_paths = (
            "/tmp/escape",
            "../escape",
            "paper/../../escape",
            r"C:\device.txt",
            r"\\server\share",
            "paper/\x00bad",
        )

        for path in unsafe_paths:
            with self.subTest(path=path):
                decision = authorize_mutations(
                    lease,
                    (FileMutation(FileOperation.CREATE, path, after_identity="new"),),
                )
                self.assertFalse(decision.authorized)
                self.assertIn("unsafe repo-relative path", decision.violations[0].reason)

    def test_batch_with_one_unauthorized_mutation_is_not_authorized(self) -> None:
        lease = CapabilityLease(
            version="lease-v1",
            rules=(LeaseRule("allow", (FileOperation.MODIFY,), ("paper/allowed.qmd",)),),
        )
        mutations = (
            FileMutation(FileOperation.MODIFY, "paper/allowed.qmd", before_identity="a", after_identity="b"),
            FileMutation(FileOperation.CREATE, "governance/checklist.md", after_identity="c"),
        )

        decision = authorize_mutations(lease, mutations)

        self.assertFalse(decision.authorized)
        self.assertEqual(len(decision.violations), 1)
        self.assertEqual(decision.violations[0].path, "governance/checklist.md")

    def test_snapshot_rejects_symlink_escape_in_mutated_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root.parent / f"{root.name}-outside"
            outside.mkdir()
            self.addCleanup(lambda: outside.rmdir())
            os.symlink(outside, root / "escape")
            lease = CapabilityLease(
                version="lease-v1",
                rules=(LeaseRule("allow", (FileOperation.CREATE,), ("escape/**",)),),
            )

            decision = authorize_mutations(
                lease,
                (FileMutation(FileOperation.CREATE, "escape/paper.qmd", after_identity="new"),),
                root=root,
            )

            self.assertFalse(decision.authorized)
            self.assertIn("symlink", decision.violations[0].reason)
            self.assertEqual(snapshot_tree(root), {"escape": f"symlink:{outside}"})

    def test_detect_mutations_supports_create_modify_delete_and_unique_rename(self) -> None:
        before = {
            "modify.txt": "file:old",
            "delete.txt": "file:delete",
            "old-name.txt": "file:rename",
        }
        after = {
            "modify.txt": "file:new",
            "create.txt": "file:create",
            "new-name.txt": "file:rename",
        }

        mutations = detect_mutations(before, after)

        self.assertEqual(
            [(mutation.operation, mutation.path, mutation.source_path) for mutation in mutations],
            [
                (FileOperation.CREATE, "create.txt", None),
                (FileOperation.DELETE, "delete.txt", None),
                (FileOperation.MODIFY, "modify.txt", None),
                (FileOperation.RENAME, "new-name.txt", "old-name.txt"),
            ],
        )

    def test_ambiguous_rename_is_rejected(self) -> None:
        before = {"a.txt": "file:same", "b.txt": "file:same"}
        after = {"c.txt": "file:same", "d.txt": "file:same"}

        with self.assertRaisesRegex(DeltaError, "ambiguous rename"):
            detect_mutations(before, after)

    def _write_config(self, root: Path, lease_config: str) -> Path:
        config_path = root / "goal.toml"
        config_path.write_text(
            textwrap.dedent(
                f"""
                name = "lease-config-test"

                [artifact]
                path = "output/artifact.txt"

                [producer]
                command = "unused"

                [tik]
                provider = "oracle"
                command = "unused"

                [tik.prompt]
                text = "Review {{artifact_path}}"

                [tok]
                provider = "codex_goal"
                write_dirs = ["src"]
                run_cwd = "."

                [tok.prompt]
                template = "Use {{tik_review_path}}"

                [no_mistakes]
                enabled = false

                [observability]
                enabled = false

                {textwrap.dedent(lease_config).strip()}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return config_path


if __name__ == "__main__":
    unittest.main()
