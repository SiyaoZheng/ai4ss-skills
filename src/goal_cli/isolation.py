from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from .config import GoalConfig
from .lease import CapabilityLease, DeltaError, FileMutation, LeaseViolation, authorize_mutations, detect_mutations, snapshot_tree
from .transaction import TransactionResult, commit_transaction, prepare_transaction


class IsolationError(RuntimeError):
    pass


@dataclass(frozen=True)
class IsolatedAttemptResult:
    attempt_id: str
    authorized: bool
    committed: bool
    conflict: bool
    detail: str
    mutations: tuple[FileMutation, ...]
    violations: tuple[LeaseViolation, ...] = ()
    journal_path: Path | None = None


class IsolatedWorkspace:
    def __init__(self, canonical_root: Path, state_dir: Path, attempt_id: str) -> None:
        self.canonical_root = canonical_root.resolve(strict=False)
        self.state_dir = state_dir.resolve(strict=False)
        self.attempt_id = attempt_id
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self.root: Path = Path()
        self.baseline: dict[str, str] = {}
        self._excluded: tuple[str, ...] = ()
        self._finalized = False

    def __enter__(self) -> "IsolatedWorkspace":
        if not self.canonical_root.is_dir():
            raise IsolationError(f"canonical root does not exist: {self.canonical_root}")
        self._temporary = tempfile.TemporaryDirectory(prefix=f"goal-cli-{self.attempt_id}-")
        self.root = Path(self._temporary.name) / "workspace"
        self.root.mkdir()
        excluded = [".git"]
        state_relative = _relative_if_inside(self.canonical_root, self.state_dir)
        if state_relative is not None:
            excluded.append(state_relative)
        self._excluded = tuple(excluded)
        self.baseline = snapshot_tree(self.canonical_root, excluded=excluded)
        self._copy_baseline()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def finalize(self, lease: CapabilityLease) -> IsolatedAttemptResult:
        if self._finalized:
            raise IsolationError(f"isolated attempt already finalized: {self.attempt_id}")
        self._finalized = True
        after = snapshot_tree(self.root)
        try:
            mutations = detect_mutations(self.baseline, after)
        except DeltaError as exc:
            raise IsolationError(str(exc)) from exc
        decision = authorize_mutations(lease, mutations, root=self.canonical_root)
        if not decision.authorized:
            detail = "; ".join(
                f"{violation.operation}:{violation.path}: {violation.reason}"
                for violation in decision.violations
            )
            return IsolatedAttemptResult(
                self.attempt_id,
                False,
                False,
                False,
                detail,
                mutations,
                decision.violations,
            )
        if not mutations:
            return IsolatedAttemptResult(
                self.attempt_id,
                True,
                True,
                False,
                "isolated attempt produced zero delta",
                (),
            )

        journal_path = prepare_transaction(
            self.canonical_root,
            self.state_dir,
            self.attempt_id,
            mutations,
            self.root,
            baseline=self.baseline,
        )
        transaction = commit_transaction(self.canonical_root, journal_path)
        return _attempt_result(self.attempt_id, mutations, journal_path, transaction)

    def _copy_baseline(self) -> None:
        for current_root, dir_names, _ in os.walk(self.canonical_root, topdown=True, followlinks=False):
            current = Path(current_root)
            relative_dir = current.relative_to(self.canonical_root)
            retained: list[str] = []
            for name in sorted(dir_names):
                source = current / name
                relative = (relative_dir / name).as_posix().removeprefix("./")
                if _is_excluded(relative, self._excluded) or source.is_symlink():
                    continue
                (self.root / relative).mkdir(parents=True, exist_ok=True)
                retained.append(name)
            dir_names[:] = retained
        for repo_path, identity in self.baseline.items():
            source = self.canonical_root / repo_path
            destination = self.root / repo_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if identity.startswith("symlink:"):
                resolved = source.resolve(strict=False)
                if not _inside(self.canonical_root, resolved):
                    raise IsolationError(f"baseline symlink escapes canonical root: {repo_path} -> {os.readlink(source)}")
                target = os.readlink(source)
                if os.path.isabs(target):
                    raise IsolationError(f"baseline symlink escapes isolated root through absolute target: {repo_path} -> {target}")
                os.symlink(target, destination)
                continue
            shutil.copy2(source, destination, follow_symlinks=False)


def rebase_goal_config(config: GoalConfig, isolated_root: Path) -> GoalConfig:
    canonical_root = config.root.resolve(strict=False)
    isolated_root = isolated_root.resolve(strict=False)

    def rebase(path: Path) -> Path:
        try:
            relative = path.resolve(strict=False).relative_to(canonical_root)
        except ValueError as exc:
            raise IsolationError(f"configured path is outside canonical root: {path}") from exc
        return (isolated_root / relative).resolve(strict=False)

    tok = replace(
        config.tok,
        write_dirs=tuple(rebase(path) for path in config.tok.write_dirs),
        run_cwd=rebase(config.tok.run_cwd) if config.tok.run_cwd is not None else None,
        runtime_write_dirs=tuple(rebase(path) for path in config.tok.runtime_write_dirs),
    )
    return replace(
        config,
        root=isolated_root,
        path=rebase(config.path),
        state_dir=rebase(config.state_dir),
        runs_dir=rebase(config.runs_dir),
        artifact=replace(config.artifact, path=rebase(config.artifact.path)),
        tok=tok,
        safety=replace(
            config.safety,
            generated_dirs=tuple(rebase(path) for path in config.safety.generated_dirs),
        ),
    )


def _attempt_result(
    attempt_id: str,
    mutations: tuple[FileMutation, ...],
    journal_path: Path,
    transaction: TransactionResult,
) -> IsolatedAttemptResult:
    return IsolatedAttemptResult(
        attempt_id,
        True,
        transaction.committed,
        transaction.conflict,
        transaction.detail,
        mutations,
        journal_path=journal_path,
    )


def _relative_if_inside(root: Path, path: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_excluded(path: str, excluded: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in excluded)
