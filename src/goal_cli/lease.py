from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable


class FileOperation(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class DeltaError(ValueError):
    pass


@dataclass(frozen=True)
class LeaseRule:
    effect: str
    operations: tuple[FileOperation, ...]
    paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.effect not in {"allow", "deny"}:
            raise ValueError(f"unsupported lease rule effect: {self.effect}")
        if not self.operations:
            raise ValueError("lease rule must include at least one operation")
        if not self.paths:
            raise ValueError("lease rule must include at least one path")
        for pattern in self.paths:
            path_error = unsafe_repo_path_reason(pattern, allow_glob=True)
            if path_error is not None:
                raise ValueError(f"unsafe lease path pattern {pattern!r}: {path_error}")


@dataclass(frozen=True)
class CapabilityLease:
    version: str
    rules: tuple[LeaseRule, ...]
    allow_shell: bool = True
    allow_network: bool = False
    tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileMutation:
    operation: FileOperation
    path: str
    source_path: str | None = None
    before_identity: str | None = None
    after_identity: str | None = None


@dataclass(frozen=True)
class LeaseViolation:
    path: str
    operation: FileOperation
    reason: str


@dataclass(frozen=True)
class LeaseDecision:
    authorized: bool
    violations: tuple[LeaseViolation, ...]


def authorize_mutations(
    lease: CapabilityLease,
    mutations: Iterable[FileMutation],
    *,
    root: Path | None = None,
) -> LeaseDecision:
    violations: list[LeaseViolation] = []
    for mutation in mutations:
        paths = [mutation.path]
        if mutation.operation == FileOperation.RENAME:
            if mutation.source_path is None:
                violations.append(LeaseViolation(mutation.path, mutation.operation, "ambiguous rename without source path"))
                continue
            paths.insert(0, mutation.source_path)
        for path in paths:
            path_error = unsafe_repo_path_reason(path)
            if path_error is not None:
                violations.append(LeaseViolation(path, mutation.operation, f"unsafe repo-relative path: {path_error}"))
                continue
            if root is not None:
                symlink_error = symlink_path_reason(root, path)
                if symlink_error is not None:
                    violations.append(LeaseViolation(path, mutation.operation, symlink_error))
                    continue
            reason = _lease_rule_rejection(lease, mutation.operation, path)
            if reason is not None:
                violations.append(LeaseViolation(path, mutation.operation, reason))
    return LeaseDecision(not violations, tuple(violations))


def unsafe_repo_path_reason(path: str, *, allow_glob: bool = False) -> str | None:
    if not isinstance(path, str) or not path:
        return "path is empty"
    if "\x00" in path:
        return "path contains a NUL byte"
    if "\\" in path:
        return "backslash and device paths are not supported"
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return "absolute or device path"
    pure = PurePosixPath(path)
    if any(part in {"", ".", ".."} for part in pure.parts):
        return "path traversal or ambiguous segment"
    if not allow_glob and any(character in path for character in "*?["):
        return "mutation path contains glob syntax"
    return None


def symlink_path_reason(root: Path, repo_path: str) -> str | None:
    current = root.resolve(strict=False)
    for part in PurePosixPath(repo_path).parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            return f"path could not be inspected safely: {exc}"
        if stat.S_ISLNK(mode):
            return f"path traverses symlink: {current}"
    return None


def snapshot_tree(root: Path, *, excluded: Iterable[str] = ()) -> dict[str, str]:
    root = root.resolve(strict=False)
    excluded_paths = tuple(sorted(_normalized_excluded_path(path) for path in excluded))
    snapshot: dict[str, str] = {}
    if not root.exists():
        return snapshot

    for current_root, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_root)
        relative_dir = current.relative_to(root)
        retained_dirs: list[str] = []
        for name in sorted(dir_names):
            path = current / name
            relative = _repo_path(relative_dir / name)
            if _is_excluded(relative, excluded_paths):
                continue
            if path.is_symlink():
                snapshot[relative] = _path_identity(path)
                continue
            retained_dirs.append(name)
        dir_names[:] = retained_dirs

        for name in sorted(file_names):
            path = current / name
            relative = _repo_path(relative_dir / name)
            if _is_excluded(relative, excluded_paths):
                continue
            snapshot[relative] = _path_identity(path)
    return dict(sorted(snapshot.items()))


def detect_mutations(before: dict[str, str], after: dict[str, str]) -> tuple[FileMutation, ...]:
    before_paths = set(before)
    after_paths = set(after)
    deleted = before_paths - after_paths
    created = after_paths - before_paths
    modified = {path for path in before_paths & after_paths if before[path] != after[path]}

    deleted_by_identity = _paths_by_identity(deleted, before)
    created_by_identity = _paths_by_identity(created, after)
    renames: list[FileMutation] = []
    for identity in sorted(set(deleted_by_identity) & set(created_by_identity)):
        sources = deleted_by_identity[identity]
        destinations = created_by_identity[identity]
        if len(sources) != 1 or len(destinations) != 1:
            raise DeltaError(
                f"ambiguous rename for identity {identity}: "
                f"sources={','.join(sources)} destinations={','.join(destinations)}"
            )
        source = sources[0]
        destination = destinations[0]
        deleted.remove(source)
        created.remove(destination)
        renames.append(
            FileMutation(
                FileOperation.RENAME,
                destination,
                source_path=source,
                before_identity=identity,
                after_identity=identity,
            )
        )

    mutations = [
        *(FileMutation(FileOperation.CREATE, path, after_identity=after[path]) for path in sorted(created)),
        *(FileMutation(FileOperation.DELETE, path, before_identity=before[path]) for path in sorted(deleted)),
        *(
            FileMutation(
                FileOperation.MODIFY,
                path,
                before_identity=before[path],
                after_identity=after[path],
            )
            for path in sorted(modified)
        ),
        *sorted(renames, key=lambda mutation: (mutation.path, mutation.source_path or "")),
    ]
    return tuple(mutations)


def path_identity(path: Path) -> str | None:
    try:
        return _path_identity(path)
    except FileNotFoundError:
        return None


def _path_identity(path: Path) -> str:
    stat_result = path.lstat()
    if stat.S_ISLNK(stat_result.st_mode):
        return f"symlink:{os.readlink(path)}"
    if not stat.S_ISREG(stat_result.st_mode):
        raise DeltaError(f"unsupported special file in workspace: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    mode = stat.S_IMODE(stat_result.st_mode)
    return f"file:{digest.hexdigest()}:{mode:o}"


def _lease_rule_rejection(lease: CapabilityLease, operation: FileOperation, path: str) -> str | None:
    matching = [
        rule
        for rule in lease.rules
        if operation in rule.operations and any(fnmatch.fnmatchcase(path, pattern) for pattern in rule.paths)
    ]
    if any(rule.effect == "deny" for rule in matching):
        return "explicit deny rule"
    if not any(rule.effect == "allow" for rule in matching):
        return "no allow rule"
    return None


def _paths_by_identity(paths: Iterable[str], snapshot: dict[str, str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for path in sorted(paths):
        grouped.setdefault(snapshot[path], []).append(path)
    return grouped


def _normalized_excluded_path(path: str) -> str:
    normalized = path.strip("/")
    if unsafe_repo_path_reason(normalized) is not None:
        raise ValueError(f"invalid excluded repo path: {path}")
    return normalized


def _repo_path(path: Path) -> str:
    value = path.as_posix()
    return value.removeprefix("./")


def _is_excluded(path: str, excluded: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in excluded)
