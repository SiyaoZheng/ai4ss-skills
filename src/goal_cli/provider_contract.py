from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import TokConfig
from .lease import CapabilityLease
from .lifecycle import CallState, WorkState
from .supervisor import AttemptOutcomeKind


@dataclass(frozen=True)
class ProviderPreflight:
    ok: bool
    provider: str
    filesystem_boundary: str
    shell_access: bool
    network_access: bool
    detail: str


@dataclass(frozen=True)
class SupervisorTransition:
    work_state: WorkState
    call_state: CallState
    consumes_angle: bool
    next_action: str | None


def preflight_tok_provider(
    config: TokConfig,
    lease: CapabilityLease,
    *,
    run_dir: Path,
    containment_backend: str | None,
    which: Callable[[str], str | None],
) -> ProviderPreflight:
    boundary = config.containment_root.resolve(strict=False) if config.containment_root is not None else None
    run_dir = run_dir.resolve(strict=False)
    errors: list[str] = []
    if boundary is None:
        errors.append("isolated filesystem containment root is missing")
    if config.sandbox != "workspace-write":
        errors.append(f"perpetual provider sandbox must be workspace-write, not {config.sandbox}")
    if not lease.allow_shell:
        errors.append("tok provider requires shell capability but the lease denies it")
    if config.network_access != lease.allow_network:
        errors.append(
            f"provider network policy {config.network_access} does not match lease network policy {lease.allow_network}"
        )
    if config.provider == "codex_goal" and lease.allow_network:
        errors.append("codex_goal cannot explicitly enforce a network-enabled workspace-write lease")
    if config.provider == "claude_code_goal" and containment_backend is None:
        errors.append("claude_code_goal requires an OS containment backend")
    if boundary is not None:
        if not _inside(boundary, run_dir):
            errors.append(f"provider run directory escapes isolated boundary: {run_dir}")
        attachment_root = config.attachments_dir or (run_dir / "attachments")
        for path in (*config.write_dirs, *config.runtime_write_dirs, config.run_cwd, attachment_root):
            if path is None:
                continue
            if not _inside(boundary, path.resolve(strict=False)):
                errors.append(f"provider writable path escapes isolated boundary: {path}")
    for tool in lease.tools:
        if which(tool) is None:
            errors.append(f"required tool is unavailable: {tool}")
    provider_policy = native_provider_policy(
        config,
        run_dir=run_dir,
        containment_backend=containment_backend,
    )
    return ProviderPreflight(
        not errors,
        config.provider,
        str(boundary) if boundary is not None else "",
        lease.allow_shell,
        bool(provider_policy["network_access"]),
        "; ".join(errors) if errors else "provider capabilities match the task lease",
    )


def native_provider_policy(
    config: TokConfig,
    *,
    run_dir: Path,
    containment_backend: str | None,
) -> dict[str, object]:
    writable_paths = [
        *config.write_dirs,
        *config.runtime_write_dirs,
        *((config.run_cwd,) if config.run_cwd is not None else ()),
        config.attachments_dir or (run_dir / "attachments"),
    ]
    writable_roots = list(
        dict.fromkeys(str(path.resolve(strict=False)) for path in writable_paths)
    )
    return {
        "provider": config.provider,
        "sandbox": config.sandbox,
        "filesystem_boundary": str(config.containment_root.resolve(strict=False)) if config.containment_root is not None else "",
        "network_access": config.network_access,
        "containment_backend": containment_backend if config.provider == "claude_code_goal" else "native",
        "writable_roots": writable_roots,
    }


def supervisor_transition(outcome: AttemptOutcomeKind) -> SupervisorTransition:
    if outcome == AttemptOutcomeKind.OPERATOR_CANCEL:
        return SupervisorTransition(WorkState.STOPPED, CallState.CANCELLED, False, None)
    if outcome == AttemptOutcomeKind.PROVIDER_ERROR:
        return SupervisorTransition(WorkState.ACTIVE, CallState.FAILED, False, "retry_provider")
    if outcome in {AttemptOutcomeKind.LEASE_VIOLATION, AttemptOutcomeKind.PROTOCOL_INVALID}:
        return SupervisorTransition(WorkState.BLOCKED, CallState.FAILED, False, "retry_blocked")
    if outcome in {AttemptOutcomeKind.SELF_BLOCKED, AttemptOutcomeKind.RESOURCE_LIMIT}:
        return SupervisorTransition(WorkState.BLOCKED, CallState.FAILED, True, "reframe")
    if outcome == AttemptOutcomeKind.ZERO_DELTA:
        return SupervisorTransition(WorkState.ACTIVE, CallState.SUCCEEDED, True, "inspect")
    return SupervisorTransition(WorkState.ACTIVE, CallState.SUCCEEDED, True, "inspect")


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
