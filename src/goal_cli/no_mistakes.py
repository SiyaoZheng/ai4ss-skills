from __future__ import annotations

import datetime as dt
import os
import re
import signal
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import GoalConfig


DEFAULT_BRANCH_NAMES = {"main", "master", "trunk", "develop"}
PIPELINE_STEP_ORDER = ("intent", "rebase", "review", "test", "document", "lint", "push", "pr", "ci")
REQUIRED_AXI_RUN_FLAGS = ("--intent", "--yes", "--skip")
MODE_SKIP_STEPS = {
    "full": (),
    "fast": ("push", "pr", "ci"),
    "lightspeed": ("review", "test", "document", "lint", "push", "pr", "ci"),
}


@dataclass(frozen=True)
class NoMistakesResult:
    ok: bool
    status: str
    detail: str
    repo_root: Path | None = None
    branch: str | None = None
    commit: str | None = None
    log_path: Path | None = None
    skipped: bool = False


@dataclass(frozen=True)
class NoMistakesGate:
    config: GoalConfig

    @property
    def enabled(self) -> bool:
        return self.config.no_mistakes.enabled

    def prepare(self, run_dir: Path, iteration: int, phase: str) -> NoMistakesResult:
        if not self.enabled:
            return NoMistakesResult(True, "no_mistakes_off", "no-mistakes disabled", skipped=True)
        if resolve_no_mistakes_binary(self.config) is None:
            return _unavailable("no_mistakes_binary_missing", f"no-mistakes binary not found: {self.config.no_mistakes.binary}")
        return _prepare_committed_feature_branch(self.config, run_dir, iteration, phase)

    def gate(self, run_dir: Path, iteration: int, phase: str, *, deadline: float | None = None) -> NoMistakesResult:
        if not self.enabled:
            return NoMistakesResult(True, "no_mistakes_off", "no-mistakes disabled", skipped=True)

        prepared = _prepare_committed_feature_branch(self.config, run_dir, iteration, phase)
        if not prepared.ok:
            return prepared

        binary = resolve_no_mistakes_binary(self.config)
        if binary is None:
            return _unavailable("no_mistakes_binary_missing", f"no-mistakes binary not found: {self.config.no_mistakes.binary}")

        repo = prepared.repo_root
        if repo is None:
            return _unavailable("no_mistakes_no_git_repository", "project is not inside a Git repository")

        log_path = run_dir / f"no_mistakes_{phase}.log"
        if _deadline_exhausted(deadline):
            return NoMistakesResult(False, "blocked_no_mistakes_failed", "run budget exhausted before no-mistakes gate", repo, prepared.branch, prepared.commit, log_path)
        init_result = _run_logged([binary, "init"], repo, log_path, _effective_no_mistakes_timeout(self.config, deadline))
        if init_result.returncode != 0:
            return _failed("blocked_no_mistakes_failed", "no-mistakes init failed", repo, prepared.branch, prepared.commit, log_path, init_result)

        command = self.axi_run_command(binary)
        if _deadline_exhausted(deadline):
            return NoMistakesResult(False, "blocked_no_mistakes_failed", "run budget exhausted before no-mistakes axi run", repo, prepared.branch, prepared.commit, log_path)
        result = _run_logged(command, repo, log_path, _effective_no_mistakes_timeout(self.config, deadline))
        if result.returncode != 0:
            return _failed("blocked_no_mistakes_failed", "no-mistakes axi run failed", repo, prepared.branch, prepared.commit, log_path, result)
        return NoMistakesResult(
            True,
            "no_mistakes_passed",
            "no-mistakes gate passed",
            repo,
            prepared.branch,
            prepared.commit,
            log_path,
        )

    def axi_run_command(self, binary: str) -> list[str]:
        command = [
            binary,
            "axi",
            "run",
            "--intent",
            _gate_intent(self.config),
            "--yes",
        ]
        skip_steps = _effective_skip_steps(self.config)
        if skip_steps:
            command.extend(["--skip", ",".join(skip_steps)])
        return command


def resolve_no_mistakes_binary(config: GoalConfig) -> str | None:
    return _resolve_binary(config.no_mistakes.binary)


def no_mistakes_axi_run_help_command(binary: str) -> list[str]:
    return [binary, "axi", "run", "--help"]


def no_mistakes_help_supports_required_flags(help_text: str) -> bool:
    return all(flag in help_text for flag in REQUIRED_AXI_RUN_FLAGS)


def _prepare_committed_feature_branch(config: GoalConfig, run_dir: Path, iteration: int, phase: str) -> NoMistakesResult:
    repo = _git_repo_root(config)
    if repo is None:
        return _unavailable("no_mistakes_no_git_repository", "project is not inside a Git repository")

    _ensure_runtime_paths_ignored(config, repo)
    branch = _current_branch(repo)
    if branch is None:
        return NoMistakesResult(False, "blocked_no_mistakes_failed", "Git worktree is detached; cannot create a no-mistakes feature branch", repo)

    if _is_default_branch(repo, branch):
        branch_result = _switch_to_feature_branch(config, repo)
        if not branch_result.ok:
            return branch_result
        branch = branch_result.branch or branch

    return _checkpoint_dirty_worktree(config, repo, run_dir, iteration, phase, branch)


def _checkpoint_dirty_worktree(
    config: GoalConfig,
    repo: Path,
    run_dir: Path,
    iteration: int,
    phase: str,
    branch: str | None,
) -> NoMistakesResult:
    head_exists = _has_head(repo)
    dirty_before = _git_dirty_entries(repo)
    if not dirty_before and head_exists:
        return NoMistakesResult(True, "no_mistakes_checkpoint_clean", "Git worktree already clean", repo, branch, _short_head(repo))

    pathspec = _relative_pathspec(repo, config.root)
    add_result = _run_git(repo, ["add", "-A", "--", pathspec])
    if add_result.returncode != 0:
        return _failed("blocked_no_mistakes_failed", "git add failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", add_result)

    staged_result = _run_git(repo, ["diff", "--cached", "--quiet", "--exit-code"])
    has_staged_changes = staged_result.returncode == 1
    if staged_result.returncode not in (0, 1):
        return _failed("blocked_no_mistakes_failed", "git diff --cached failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", staged_result)

    if has_staged_changes or not head_exists:
        commit_result = _run_git(
            repo,
            ["commit", *([] if has_staged_changes else ["--allow-empty"]), "-m", _checkpoint_message(config, iteration, phase)],
            env={
                "GIT_AUTHOR_NAME": "goal-cli",
                "GIT_AUTHOR_EMAIL": "goal-cli@localhost",
                "GIT_COMMITTER_NAME": "goal-cli",
                "GIT_COMMITTER_EMAIL": "goal-cli@localhost",
            },
        )
        if commit_result.returncode != 0:
            return _failed("blocked_no_mistakes_failed", "git commit failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", commit_result)

    dirty_after = _git_dirty_entries(repo)
    if dirty_after:
        detail = "Git worktree is still dirty after checkpoint; refusing to run no-mistakes on a dirty tree: " + "; ".join(dirty_after[:20])
        return NoMistakesResult(False, "blocked_no_mistakes_failed", detail, repo, branch, _short_head(repo), run_dir / f"no_mistakes_{phase}.log")

    commit = _short_head(repo)
    detail = f"created Git checkpoint {commit}" if has_staged_changes or not head_exists else "Git worktree already clean"
    return NoMistakesResult(True, "no_mistakes_checkpoint_ready", detail, repo, branch, commit)


def _git_repo_root(config: GoalConfig) -> Path | None:
    result = _run_git(config.root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return Path(output).resolve() if output else None


def _current_branch(repo: Path) -> str | None:
    result = _run_git(repo, ["branch", "--show-current"])
    branch = result.stdout.strip()
    return branch or None


def _has_head(repo: Path) -> bool:
    return _run_git(repo, ["rev-parse", "--verify", "HEAD"]).returncode == 0


def _short_head(repo: Path) -> str | None:
    result = _run_git(repo, ["rev-parse", "--short", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _is_default_branch(repo: Path, branch: str) -> bool:
    remote_default = _remote_default_branch(repo)
    if remote_default:
        return branch == remote_default
    return branch in DEFAULT_BRANCH_NAMES


def _remote_default_branch(repo: Path) -> str | None:
    result = _run_git(repo, ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"])
    if result.returncode != 0:
        return None
    ref = result.stdout.strip()
    if not ref:
        return None
    return ref.split("/", 1)[1] if "/" in ref else ref


def _switch_to_feature_branch(config: GoalConfig, repo: Path) -> NoMistakesResult:
    base = f"{config.no_mistakes.branch_prefix}/{_slug(config.name)}-{_timestamp()}"
    for suffix in ["", "-2", "-3", "-4", "-5"]:
        branch = base + suffix
        result = _run_git(repo, ["switch", "-c", branch])
        if result.returncode == 0:
            return NoMistakesResult(True, "no_mistakes_feature_branch", f"created feature branch {branch}", repo, branch)
    return _failed("blocked_no_mistakes_failed", "failed to create no-mistakes feature branch", repo, None, None, None, result)


def _git_dirty_entries(repo: Path) -> tuple[str, ...]:
    result = _run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])
    if result.returncode != 0:
        return (f"git status failed: {_combined_output(result)}",)
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def _ensure_runtime_paths_ignored(config: GoalConfig, repo: Path) -> None:
    exclude_result = _run_git(repo, ["rev-parse", "--git-path", "info/exclude"])
    if exclude_result.returncode != 0:
        return
    exclude_path = (repo / exclude_result.stdout.strip()).resolve()
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    existing_lines = set(existing.splitlines())
    additions = []
    for path in (config.state_dir, config.runs_dir):
        pattern = _git_exclude_pattern(repo, path)
        if pattern and pattern not in existing_lines:
            additions.append(pattern)
    if not additions:
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    exclude_path.write_text(existing + prefix + "\n".join(additions) + "\n", encoding="utf-8")


def _git_exclude_pattern(repo: Path, path: Path) -> str | None:
    try:
        relative = path.resolve(strict=False).relative_to(repo.resolve(strict=False))
    except ValueError:
        return None
    text = relative.as_posix().rstrip("/")
    return f"/{text}/" if text else None


def _relative_pathspec(repo: Path, path: Path) -> str:
    try:
        relative = path.resolve(strict=False).relative_to(repo.resolve(strict=False))
    except ValueError:
        return str(path)
    text = relative.as_posix()
    return text or "."


def _resolve_binary(binary: str) -> str | None:
    if "/" in binary:
        path = Path(binary).expanduser()
        return str(path) if path.exists() and os.access(path, os.X_OK) else None
    return shutil.which(binary)


def _gate_intent(config: GoalConfig) -> str:
    if config.no_mistakes.intent:
        return config.no_mistakes.intent
    return (
        f"Run the autonomous artifact loop for {config.name}. "
        "Each cycle continues from the previous cycle, rebuilds the canonical artifact, "
        "evaluates it, and applies one bounded source revision when needed. "
        "The workspace must stay clean between cycles."
    )


def _effective_skip_steps(config: GoalConfig) -> tuple[str, ...]:
    requested = set(MODE_SKIP_STEPS.get(config.no_mistakes.mode, ()))
    requested.update(config.no_mistakes.skip_steps)
    return tuple(step for step in PIPELINE_STEP_ORDER if step in requested)


def _effective_no_mistakes_timeout(config: GoalConfig, deadline: float | None) -> float:
    configured_timeout = config.no_mistakes.timeout_seconds if config.no_mistakes.timeout_seconds > 0 else None
    remaining = _remaining_deadline_seconds(deadline)
    if configured_timeout is None and remaining is None:
        return 0.0
    if configured_timeout is None:
        return remaining if remaining is not None else 0.0
    if remaining is None:
        return configured_timeout
    return min(configured_timeout, remaining)


def _remaining_deadline_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _deadline_exhausted(deadline: float | None) -> bool:
    return deadline is not None and time.monotonic() >= deadline


def _checkpoint_message(config: GoalConfig, iteration: int, phase: str) -> str:
    return config.no_mistakes.checkpoint_message.format(
        goal_name=config.name,
        iteration=iteration,
        phase=phase,
    )


def _run_git(
    cwd: Path,
    args: list[str],
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=run_env,
    )


def _run_logged(command: list[str], cwd: Path, log_path: Path, timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timeout = timeout_seconds if timeout_seconds > 0 else None
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(command)}\n")
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as exc:
            result = subprocess.CompletedProcess(command, 127, "", f"failed to start command: {exc}")
        else:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                result = subprocess.CompletedProcess(command, process.returncode, stdout or "", stderr or "")
            except subprocess.TimeoutExpired as exc:
                _terminate_process_tree(process)
                stdout, stderr = process.communicate()
                captured_stdout = stdout if isinstance(stdout, str) else (exc.stdout if isinstance(exc.stdout, str) else "")
                captured_stderr = stderr if isinstance(stderr, str) else (exc.stderr if isinstance(exc.stderr, str) else "")
                result = subprocess.CompletedProcess(command, 124, captured_stdout, captured_stderr + f"\ntimed out after {timeout_seconds:g}s")
        log_file.write(result.stdout or "")
        if result.stderr:
            log_file.write(result.stderr)
        log_file.write(f"\nexit_code={result.returncode}\n")
    return result


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass
    except OSError:
        process.kill()


def _unavailable(status: str, detail: str) -> NoMistakesResult:
    return NoMistakesResult(False, "blocked_no_mistakes_failed", detail)


def _failed(
    status: str,
    detail: str,
    repo: Path,
    branch: str | None,
    commit: str | None,
    log_path: Path | None,
    result: subprocess.CompletedProcess[str],
) -> NoMistakesResult:
    return NoMistakesResult(False, status, f"{detail}: {_combined_output(result)}", repo, branch, commit, log_path)


def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
    return text or f"exit code {result.returncode}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug or "goal"


def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")
