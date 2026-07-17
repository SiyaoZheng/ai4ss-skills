from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from .lease import FileMutation, FileOperation, path_identity, snapshot_tree, unsafe_repo_path_reason


FaultHook = Callable[[str, int], None]


class InjectedTransactionCrash(RuntimeError):
    pass


@dataclass(frozen=True)
class TransactionResult:
    committed: bool
    conflict: bool
    detail: str
    journal_path: Path


def prepare_transaction(
    canonical_root: Path,
    state_dir: Path,
    attempt_id: str,
    mutations: tuple[FileMutation, ...],
    isolated_root: Path,
    *,
    baseline: dict[str, str] | None = None,
) -> Path:
    canonical_root = canonical_root.resolve(strict=False)
    isolated_root = isolated_root.resolve(strict=False)
    transaction_dir = state_dir / "transactions" / attempt_id
    journal_path = transaction_dir / "journal.json"
    if journal_path.exists():
        journal = load_transaction(journal_path)
        if journal.get("attempt_id") != attempt_id:
            raise ValueError(f"transaction journal attempt mismatch: {journal_path}")
        return journal_path

    transaction_dir.mkdir(parents=True, exist_ok=False)
    staged_dir = transaction_dir / "staged"
    staged_dir.mkdir()
    serialized_mutations: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []

    for mutation_index, mutation in enumerate(mutations):
        _validate_mutation_paths(mutation)
        staged_path: str | None = None
        if mutation.operation in {FileOperation.CREATE, FileOperation.MODIFY, FileOperation.RENAME}:
            source = isolated_root / mutation.path
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"transaction payload must be a regular file: {mutation.path}")
            if path_identity(source) != mutation.after_identity:
                raise ValueError(f"isolated payload identity changed before staging: {mutation.path}")
            stage_target = staged_dir / f"{mutation_index:04d}.payload"
            _durable_copy(source, stage_target)
            staged_path = str(stage_target.relative_to(transaction_dir))

        serialized_mutations.append(
            {
                "operation": str(mutation.operation),
                "path": mutation.path,
                "source_path": mutation.source_path,
                "before_identity": mutation.before_identity,
                "after_identity": mutation.after_identity,
                "staged_path": staged_path,
            }
        )
        steps.extend(_mutation_steps(mutation, staged_path, isolated_root))

    state_relative = _relative_if_inside(canonical_root, state_dir)
    excluded = [".git"]
    if state_relative is not None:
        excluded.append(state_relative)
    baseline = dict(baseline) if baseline is not None else snapshot_tree(canonical_root, excluded=excluded)
    journal = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "status": "PREPARED",
        "canonical_root": str(canonical_root),
        "baseline": baseline,
        "mutations": serialized_mutations,
        "steps": steps,
        "applied_count": 0,
        "conflict": None,
    }
    _atomic_write_json(journal_path, journal)
    _fsync_directory(transaction_dir)
    return journal_path


def commit_transaction(
    canonical_root: Path,
    journal_path: Path,
    *,
    fault: FaultHook | None = None,
) -> TransactionResult:
    canonical_root = canonical_root.resolve(strict=False)
    journal_path = journal_path.resolve(strict=False)
    with _repository_lock(canonical_root):
        journal = load_transaction(journal_path)
        status = journal.get("status")
        if status in {"COMMITTED", "CHECKPOINTED"}:
            return TransactionResult(True, False, f"transaction is {status.lower()}", journal_path)
        if status == "CONFLICT":
            return TransactionResult(False, True, str(journal.get("conflict") or "transaction conflict"), journal_path)
        if status not in {"PREPARED", "APPLYING"}:
            raise ValueError(f"unsupported transaction status: {status}")

        steps = _journal_steps(journal)
        if status == "PREPARED":
            conflict = _preflight_conflict(canonical_root, steps)
            if conflict is not None:
                return _record_conflict(journal_path, journal, conflict)
            journal["status"] = "APPLYING"
            _atomic_write_json(journal_path, journal)

        applied_count = int(journal.get("applied_count", 0))
        for index in range(applied_count, len(steps)):
            step = steps[index]
            current_identity = path_identity(canonical_root / step["path"])
            if current_identity == step["after_identity"]:
                journal["applied_count"] = index + 1
                _atomic_write_json(journal_path, journal)
                if fault is not None:
                    fault("after_journal", index)
                continue
            if current_identity != step["before_identity"]:
                conflict = (
                    f"canonical content changed for {step['path']}: "
                    f"expected {step['before_identity']!r}, found {current_identity!r}"
                )
                return _record_conflict(journal_path, journal, conflict)

            _apply_step(canonical_root, journal_path.parent, step)
            if fault is not None:
                fault("after_apply_before_journal", index)
            journal["applied_count"] = index + 1
            _atomic_write_json(journal_path, journal)
            if fault is not None:
                fault("after_journal", index)

        journal["status"] = "COMMITTED"
        _atomic_write_json(journal_path, journal)
        return TransactionResult(True, False, "transaction committed", journal_path)


def mark_transaction_checkpointed(journal_path: Path) -> None:
    journal = load_transaction(journal_path)
    if journal.get("status") == "CHECKPOINTED":
        return
    if journal.get("status") != "COMMITTED":
        raise ValueError(f"cannot checkpoint transaction in status {journal.get('status')}")
    journal["status"] = "CHECKPOINTED"
    _atomic_write_json(journal_path, journal)


def recover_transactions(canonical_root: Path, state_dir: Path) -> tuple[TransactionResult, ...]:
    transactions_dir = state_dir / "transactions"
    if not transactions_dir.is_dir():
        return ()
    results: list[TransactionResult] = []
    for journal_path in sorted(transactions_dir.glob("*/journal.json")):
        journal = load_transaction(journal_path)
        if journal.get("status") in {"CHECKPOINTED", "CONFLICT"}:
            continue
        results.append(commit_transaction(canonical_root, journal_path))
    return tuple(results)


def load_transaction(journal_path: Path) -> dict[str, Any]:
    with journal_path.open("r", encoding="utf-8") as journal_file:
        journal = json.load(journal_file)
    if not isinstance(journal, dict):
        raise ValueError(f"transaction journal must contain a JSON object: {journal_path}")
    return journal


def repository_lock_path(canonical_root: Path) -> Path:
    canonical_root = canonical_root.resolve(strict=False)
    dot_git = canonical_root / ".git"
    if dot_git.is_dir():
        return dot_git / "goal-cli-repository.lock"
    digest = hashlib.sha256(str(canonical_root).encode("utf-8")).hexdigest()
    return Path.home() / ".cache" / "goal-cli" / "repository-locks" / f"{digest}.lock"


def _mutation_steps(mutation: FileMutation, staged_path: str | None, isolated_root: Path) -> list[dict[str, Any]]:
    if mutation.operation == FileOperation.RENAME:
        if mutation.source_path is None:
            raise ValueError(f"rename is missing source path: {mutation.path}")
        return [
            {
                "operation": "rename_destination",
                "path": mutation.path,
                "before_identity": None,
                "after_identity": mutation.after_identity,
                "staged_path": staged_path,
                "mode": _file_mode(isolated_root / mutation.path),
            },
            {
                "operation": "rename_source",
                "path": mutation.source_path,
                "before_identity": mutation.before_identity,
                "after_identity": None,
                "staged_path": None,
                "mode": None,
            },
        ]
    if mutation.operation in {FileOperation.CREATE, FileOperation.MODIFY}:
        return [
            {
                "operation": str(mutation.operation),
                "path": mutation.path,
                "before_identity": mutation.before_identity,
                "after_identity": mutation.after_identity,
                "staged_path": staged_path,
                "mode": _file_mode(isolated_root / mutation.path),
            }
        ]
    return [
        {
            "operation": "delete",
            "path": mutation.path,
            "before_identity": mutation.before_identity,
            "after_identity": None,
            "staged_path": None,
            "mode": None,
        }
    ]


def _journal_steps(journal: dict[str, Any]) -> list[dict[str, Any]]:
    steps = journal.get("steps")
    if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
        raise ValueError("transaction journal steps are invalid")
    return steps


def _preflight_conflict(canonical_root: Path, steps: list[dict[str, Any]]) -> str | None:
    for step in steps:
        current_identity = path_identity(canonical_root / step["path"])
        if current_identity != step["before_identity"]:
            return (
                f"canonical content changed for {step['path']}: "
                f"expected {step['before_identity']!r}, found {current_identity!r}"
            )
    return None


def _record_conflict(
    journal_path: Path,
    journal: dict[str, Any],
    conflict: str,
) -> TransactionResult:
    journal["status"] = "CONFLICT"
    journal["conflict"] = conflict
    _atomic_write_json(journal_path, journal)
    return TransactionResult(False, True, conflict, journal_path)


def _apply_step(canonical_root: Path, transaction_dir: Path, step: dict[str, Any]) -> None:
    destination = canonical_root / step["path"]
    if step["after_identity"] is None:
        destination.unlink()
        _fsync_directory(destination.parent)
        return

    staged_relative = step.get("staged_path")
    if not isinstance(staged_relative, str):
        raise ValueError(f"transaction step has no staged payload: {step['path']}")
    staged_path = transaction_dir / staged_relative
    if path_identity(staged_path) != step["after_identity"]:
        raise ValueError(f"staged payload identity mismatch: {step['path']}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.parent / f".{destination.name}.goal-cli-{uuid.uuid4().hex}.tmp"
    shutil.copyfile(staged_path, temp_path)
    mode = step.get("mode")
    if isinstance(mode, int):
        temp_path.chmod(mode)
    with temp_path.open("rb") as temp_file:
        os.fsync(temp_file.fileno())
    os.replace(temp_path, destination)
    _fsync_directory(destination.parent)


@contextmanager
def _repository_lock(canonical_root: Path) -> Iterator[None]:
    lock_path = repository_lock_path(canonical_root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _validate_mutation_paths(mutation: FileMutation) -> None:
    paths = [mutation.path]
    if mutation.source_path is not None:
        paths.append(mutation.source_path)
    for path in paths:
        reason = unsafe_repo_path_reason(path)
        if reason is not None:
            raise ValueError(f"unsafe transaction path {path!r}: {reason}")


def _durable_copy(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination, follow_symlinks=False)
    with destination.open("rb") as copied_file:
        os.fsync(copied_file.fileno())


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as temp_file:
        json.dump(value, temp_file, ensure_ascii=False, indent=2)
        temp_file.write("\n")
        temp_file.flush()
        os.fsync(temp_file.fileno())
    os.replace(temp_path, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _relative_if_inside(root: Path, path: Path) -> str | None:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return None
