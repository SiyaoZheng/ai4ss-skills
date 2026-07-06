from __future__ import annotations

import os
import signal
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .config import GoalConfig


PIPELINE_STEP_ORDER = ("intent", "rebase", "review", "test", "document", "lint", "push", "pr", "ci")
REQUIRED_AXI_RUN_FLAGS = ("--intent", "--yes", "--skip")
NO_MISTAKES_BUDGET_EXHAUSTED = "no_mistakes_budget_exhausted"
MODE_SKIP_STEPS = {
    "full": (),
    "fast": ("push", "pr", "ci"),
    "lightspeed": ("review", "test", "document", "lint", "push", "pr", "ci"),
}


class _NoMistakesBudgetExhausted(RuntimeError):
    pass


class _NoMistakesGitTimedOut(RuntimeError):
    pass


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
class NoMistakesCheckpoint:
    config: GoalConfig

    @property
    def enabled(self) -> bool:
        return self.config.no_mistakes.enabled

    def prepare(self, run_dir: Path, iteration: int, phase: str, *, deadline: float | None = None) -> NoMistakesResult:
        if not self.enabled:
            return NoMistakesResult(True, "no_mistakes_off", "no-mistakes disabled", skipped=True)
        if resolve_no_mistakes_binary(self.config) is None:
            return _unavailable("no_mistakes_binary_missing", f"no-mistakes binary not found: {self.config.no_mistakes.binary}")
        return _prepare_committed_worktree(self.config, run_dir, iteration, phase, deadline)

    def checkpoint(self, run_dir: Path, iteration: int, phase: str, *, deadline: float | None = None) -> NoMistakesResult:
        if not self.enabled:
            return NoMistakesResult(True, "no_mistakes_off", "no-mistakes disabled", skipped=True)

        prepared = _prepare_committed_worktree(self.config, run_dir, iteration, phase, deadline)
        if not prepared.ok:
            return prepared

        binary = resolve_no_mistakes_binary(self.config)
        if binary is None:
            return _unavailable("no_mistakes_binary_missing", f"no-mistakes binary not found: {self.config.no_mistakes.binary}")

        repo = prepared.repo_root
        if repo is None:
            return _unavailable("no_mistakes_no_git_repository", "project is not inside a Git repository")

        log_path = run_dir / f"no_mistakes_{phase}.log"
        try:
            branch_is_default = _branch_is_default(self.config, repo, prepared.branch, deadline)
        except _NoMistakesBudgetExhausted as exc:
            return _budget_exhausted(str(exc), repo, prepared.branch, prepared.commit, log_path)
        if branch_is_default:
            detail = (
                "no-mistakes axi run skipped on the default branch; goal-cli "
                "kept the current branch as the single-person mainline and "
                f"checkpointed commit {prepared.commit}"
            )
            _append_log_message(log_path, detail)
            return NoMistakesResult(
                True,
                "no_mistakes_default_branch_skipped",
                detail,
                repo,
                prepared.branch,
                prepared.commit,
                log_path,
                skipped=True,
            )

        if _deadline_exhausted(deadline):
            return _budget_exhausted("run budget exhausted before no-mistakes checkpoint", repo, prepared.branch, prepared.commit, log_path)
        init_timeout = _effective_no_mistakes_timeout(self.config, deadline)
        init_result = _run_logged([binary, "init"], repo, log_path, init_timeout)
        if init_result.returncode != 0:
            if _timed_out_on_run_budget(init_result, deadline):
                return _budget_exhausted("run budget exhausted during no-mistakes init", repo, prepared.branch, prepared.commit, log_path)
            return _failed("no_mistakes_failed", "no-mistakes init failed", repo, prepared.branch, prepared.commit, log_path, init_result)

        command = self.axi_run_command(binary)
        if _deadline_exhausted(deadline):
            return _budget_exhausted("run budget exhausted before no-mistakes axi run", repo, prepared.branch, prepared.commit, log_path)
        run_timeout = _effective_no_mistakes_timeout(self.config, deadline)
        result = _run_logged(command, repo, log_path, run_timeout)
        if result.returncode != 0:
            if _timed_out_on_run_budget(result, deadline):
                return _budget_exhausted("run budget exhausted during no-mistakes axi run", repo, prepared.branch, prepared.commit, log_path)
            return _failed("no_mistakes_failed", "no-mistakes axi run failed", repo, prepared.branch, prepared.commit, log_path, result)
        return NoMistakesResult(
            True,
            "no_mistakes_passed",
            "no-mistakes checkpoint passed",
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
            _checkpoint_intent(self.config),
            "--yes",
        ]
        skip_steps = _effective_skip_steps(self.config)
        if skip_steps:
            command.extend(["--skip", ",".join(skip_steps)])
        return command


def resolve_no_mistakes_binary(config: GoalConfig, which: Callable[[str], str | None] = shutil.which) -> str | None:
    return _resolve_binary(config.no_mistakes.binary, config.root, which)


def no_mistakes_axi_run_help_command(binary: str) -> list[str]:
    return [binary, "axi", "run", "--help"]


def no_mistakes_help_supports_required_flags(help_text: str) -> bool:
    return all(flag in help_text for flag in REQUIRED_AXI_RUN_FLAGS)


def _prepare_committed_worktree(config: GoalConfig, run_dir: Path, iteration: int, phase: str, deadline: float | None) -> NoMistakesResult:
    repo: Path | None = None
    branch: str | None = None
    log_path = run_dir / f"no_mistakes_{phase}.log"
    try:
        _raise_if_deadline_exhausted(deadline, "no-mistakes prepare")
        repo = _git_repo_root(config, deadline)
        if repo is None:
            return _unavailable("no_mistakes_no_git_repository", "project is not inside a Git repository")

        _ensure_runtime_paths_ignored(config, repo, deadline)
        branch = _current_branch(config, repo, deadline)
        if branch is None:
            return NoMistakesResult(False, "no_mistakes_failed", "Git worktree is detached; cannot checkpoint no-mistakes on a detached HEAD", repo)

        return _checkpoint_dirty_worktree(config, repo, run_dir, iteration, phase, branch, deadline)
    except _NoMistakesBudgetExhausted as exc:
        return _budget_exhausted(str(exc), repo, branch, None, log_path)
    except _NoMistakesGitTimedOut as exc:
        return NoMistakesResult(False, "no_mistakes_failed", str(exc), repo, branch, None, log_path)


def _checkpoint_dirty_worktree(
    config: GoalConfig,
    repo: Path,
    run_dir: Path,
    iteration: int,
    phase: str,
    branch: str | None,
    deadline: float | None,
) -> NoMistakesResult:
    head_exists = _has_head(config, repo, deadline)
    dirty_before = _git_dirty_entries(config, repo, deadline)
    if not dirty_before and head_exists:
        return NoMistakesResult(True, "no_mistakes_checkpoint_clean", "Git worktree already clean", repo, branch, _short_head(config, repo, deadline))

    pathspec = _relative_pathspec(repo, config.root)
    _raise_if_deadline_exhausted(deadline, "git add before no-mistakes")
    add_result = _run_git(repo, ["add", "-A", "--", pathspec], read_only=False)
    if add_result.returncode != 0:
        return _failed("no_mistakes_failed", "git add failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", add_result)

    staged_result = _run_git(repo, ["diff", "--cached", "--quiet", "--exit-code"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(staged_result, deadline, "git diff --cached before no-mistakes")
    has_staged_changes = staged_result.returncode == 1
    if staged_result.returncode not in (0, 1):
        return _failed("no_mistakes_failed", "git diff --cached failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", staged_result)

    if has_staged_changes or not head_exists:
        _raise_if_deadline_exhausted(deadline, "git commit before no-mistakes")
        commit_result = _run_git(
            repo,
            ["commit", "--no-verify", *([] if has_staged_changes else ["--allow-empty"]), "-m", _checkpoint_message(config, iteration, phase)],
            env={
                "GIT_AUTHOR_NAME": "goal-cli",
                "GIT_AUTHOR_EMAIL": "goal-cli@localhost",
                "GIT_COMMITTER_NAME": "goal-cli",
                "GIT_COMMITTER_EMAIL": "goal-cli@localhost",
            },
            read_only=False,
        )
        if commit_result.returncode != 0:
            return _failed("no_mistakes_failed", "git commit failed before no-mistakes", repo, branch, None, run_dir / f"no_mistakes_{phase}.log", commit_result)

    dirty_after = _git_dirty_entries(config, repo, deadline)
    if dirty_after:
        detail = "Git worktree is still dirty after checkpoint; refusing to run no-mistakes on a dirty tree: " + "; ".join(dirty_after[:20])
        return NoMistakesResult(False, "no_mistakes_failed", detail, repo, branch, _short_head(config, repo, deadline), run_dir / f"no_mistakes_{phase}.log")

    commit = _short_head(config, repo, deadline)
    detail = f"created Git checkpoint {commit}" if has_staged_changes or not head_exists else "Git worktree already clean"
    return NoMistakesResult(True, "no_mistakes_checkpoint_ready", detail, repo, branch, commit)


def _git_repo_root(config: GoalConfig, deadline: float | None) -> Path | None:
    result = _run_git(config.root, ["rev-parse", "--show-toplevel"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(result, deadline, "git repo discovery before no-mistakes")
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return Path(output).resolve() if output else None


def _current_branch(config: GoalConfig, repo: Path, deadline: float | None) -> str | None:
    result = _run_git(repo, ["branch", "--show-current"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(result, deadline, "git branch discovery before no-mistakes")
    branch = result.stdout.strip()
    return branch or None


def _has_head(config: GoalConfig, repo: Path, deadline: float | None) -> bool:
    result = _run_git(repo, ["rev-parse", "--verify", "HEAD"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(result, deadline, "git HEAD check before no-mistakes")
    return result.returncode == 0


def _short_head(config: GoalConfig, repo: Path, deadline: float | None) -> str | None:
    result = _run_git(repo, ["rev-parse", "--short", "HEAD"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(result, deadline, "git HEAD summary before no-mistakes")
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _branch_is_default(config: GoalConfig, repo: Path, branch: str | None, deadline: float | None) -> bool:
    if branch is None:
        return False
    default_names = {"main", "master"}
    remote_default = _origin_default_branch(config, repo, deadline)
    if remote_default:
        default_names.add(remote_default)
    return branch in default_names


def _origin_default_branch(config: GoalConfig, repo: Path, deadline: float | None) -> str | None:
    result = _run_git(
        repo,
        ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        timeout_seconds=_effective_no_mistakes_timeout(config, deadline),
    )
    _raise_if_git_timed_out(result, deadline, "git origin default branch discovery before no-mistakes")
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    return text.rsplit("/", 1)[-1]


def _git_dirty_entries(config: GoalConfig, repo: Path, deadline: float | None) -> tuple[str, ...]:
    result = _run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(result, deadline, "git status before no-mistakes")
    if result.returncode != 0:
        return (f"git status failed: {_combined_output(result)}",)
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def _ensure_runtime_paths_ignored(config: GoalConfig, repo: Path, deadline: float | None) -> None:
    exclude_result = _run_git(repo, ["rev-parse", "--git-path", "info/exclude"], timeout_seconds=_effective_no_mistakes_timeout(config, deadline))
    _raise_if_git_timed_out(exclude_result, deadline, "git exclude discovery before no-mistakes")
    if exclude_result.returncode != 0:
        return
    exclude_path = (repo / exclude_result.stdout.strip()).resolve()
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    existing_lines = set(existing.splitlines())
    additions = []
    for path in (config.state_dir, config.runs_dir, *config.safety.generated_dirs):
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


def _resolve_binary(binary: str, root: Path, which: Callable[[str], str | None]) -> str | None:
    if "/" in binary:
        path = Path(binary).expanduser()
        if not path.is_absolute():
            path = root / path
        return str(path) if path.exists() and os.access(path, os.X_OK) else None
    return which(binary)


def _checkpoint_intent(config: GoalConfig) -> str:
    if config.no_mistakes.intent:
        return config.no_mistakes.intent
    return (
        f"Run {config.name}: rebuild artifact, evaluate it, apply source changes, keep Git clean."
    )


def _effective_skip_steps(config: GoalConfig) -> tuple[str, ...]:
    requested = set(MODE_SKIP_STEPS.get(config.no_mistakes.mode, ()))
    requested.update(config.no_mistakes.skip_steps)
    return tuple(step for step in PIPELINE_STEP_ORDER if step in requested)


def _effective_no_mistakes_timeout(config: GoalConfig, deadline: float | None) -> float | None:
    configured_timeout = config.no_mistakes.timeout_seconds if config.no_mistakes.timeout_seconds > 0 else None
    remaining = _remaining_deadline_seconds(deadline)
    if configured_timeout is None and remaining is None:
        return None
    if configured_timeout is None:
        return remaining
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
    timeout_seconds: float | None = None,
    read_only: bool = True,
) -> subprocess.CompletedProcess[str]:
    if timeout_seconds is not None and timeout_seconds <= 0:
        return subprocess.CompletedProcess(["git", *args], 124, "", "time budget exhausted before git command start")
    run_env = os.environ.copy()
    if read_only:
        run_env.setdefault("GIT_OPTIONAL_LOCKS", "0")
    if env:
        run_env.update(env)
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=run_env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return subprocess.CompletedProcess(["git", *args], 124, stdout, stderr + f"\ntimed out after {timeout_seconds:g}s")


def _run_logged(command: list[str], cwd: Path, log_path: Path, timeout_seconds: float | None) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(command)}\n")
        if timeout_seconds is not None and timeout_seconds <= 0:
            result = subprocess.CompletedProcess(command, 124, "", "time budget exhausted before command start")
            log_file.write(result.stderr)
            log_file.write(f"\nexit_code={result.returncode}\n")
            return result
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
                stdout, stderr = process.communicate(timeout=timeout_seconds)
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


def _append_log_message(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(message)
        log_file.write("\n")


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
    return NoMistakesResult(False, status, detail)


def _budget_exhausted(
    detail: str,
    repo: Path | None = None,
    branch: str | None = None,
    commit: str | None = None,
    log_path: Path | None = None,
) -> NoMistakesResult:
    return NoMistakesResult(False, NO_MISTAKES_BUDGET_EXHAUSTED, detail, repo, branch, commit, log_path)


def _raise_if_deadline_exhausted(deadline: float | None, action: str) -> None:
    if _deadline_exhausted(deadline):
        raise _NoMistakesBudgetExhausted(f"run budget exhausted before {action}")


def _raise_if_git_timed_out(result: subprocess.CompletedProcess[str], deadline: float | None, action: str) -> None:
    if not _is_timeout_result(result):
        return
    if _deadline_exhausted(deadline):
        raise _NoMistakesBudgetExhausted(f"run budget exhausted during {action}")
    raise _NoMistakesGitTimedOut(f"{action} timed out: {_combined_output(result)}")


def _timed_out_on_run_budget(result: subprocess.CompletedProcess[str], deadline: float | None) -> bool:
    return _is_timeout_result(result) and _deadline_exhausted(deadline)


def _is_timeout_result(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode != 124:
        return False
    output = _combined_output(result)
    return "time budget exhausted" in output or "timed out after" in output


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
