from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .adapters import run_tik
from .config import API_TIK_KEY_ENV_VARS, ConfigPolicyReport, GoalConfig, TikConfig, TokConfig, analyze_config_policy, api_tik_value_source
from .no_mistakes import no_mistakes_axi_run_help_command, no_mistakes_help_supports_required_flags, resolve_no_mistakes_binary
from .observability import plan_observability_export
from .tok_execution import execute_tok


_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SHELL_CONTROL_TOKENS = {"|", "||", "&&", ";", "&", ">", ">>", "<", "<<", "2>", "2>>", "(", ")"}
_SHELL_BUILTINS = {
    "alias",
    "bg",
    "cd",
    "command",
    "declare",
    "dirs",
    "echo",
    "eval",
    "exec",
    "exit",
    "export",
    "false",
    "fg",
    "hash",
    "history",
    "jobs",
    "popd",
    "printf",
    "pushd",
    "pwd",
    "read",
    "readonly",
    "set",
    "shift",
    "source",
    "test",
    "times",
    "trap",
    "true",
    "type",
    "ulimit",
    "umask",
    "unalias",
    "unset",
}


@dataclass(frozen=True)
class DoctorOptions:
    smoke_codex_goal: bool = False
    smoke_claude_code_goal: bool = False
    smoke_codex_file_tik: bool = False
    smoke_claude_code_file_tik: bool = False
    skip_openai_auth: bool = False
    timeout_seconds: float = 10.0
    smoke_timeout_seconds: float = 180.0


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    severity: str = "error"

    @property
    def blocks_readiness(self) -> bool:
        return not self.ok and self.severity == "error"


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    detail: str


class SetupProbeAdapter(Protocol):
    def which(self, binary: str) -> str | None:
        pass

    def run(self, command: list[str], cwd: Path, timeout_seconds: float) -> subprocess.CompletedProcess[str]:
        pass

    def package_available(self, package: str) -> bool:
        pass

    def env_has_value(self, name: str) -> bool:
        pass

    def path_writable(self, path: Path) -> bool:
        pass

    def tcp_connects(self, host: str, port: int, timeout_seconds: float) -> bool:
        pass

    def codex_goal_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        pass

    def claude_code_goal_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        pass

    def codex_file_tik_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        pass

    def claude_code_file_tik_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        pass


@dataclass(frozen=True)
class LocalSetupProbeAdapter:
    def which(self, binary: str) -> str | None:
        return shutil.which(binary)

    def run(self, command: list[str], cwd: Path, timeout_seconds: float) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )

    def package_available(self, package: str) -> bool:
        return importlib.util.find_spec(package) is not None

    def env_has_value(self, name: str) -> bool:
        return bool(os.environ.get(name))

    def path_writable(self, path: Path) -> bool:
        return os.access(path, os.W_OK | os.X_OK)

    def tcp_connects(self, host: str, port: int, timeout_seconds: float) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                return True
        except OSError:
            return False

    def codex_goal_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        return _tok_goal_smoke(config, options, "codex_goal")

    def claude_code_goal_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        return _tok_goal_smoke(config, options, "claude_code_goal")

    def codex_file_tik_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        return _local_file_tik_smoke(config, options, "codex_file")

    def claude_code_file_tik_smoke(self, config: GoalConfig, options: DoctorOptions) -> ProbeResult:
        return _local_file_tik_smoke(config, options, "claude_code_file")


def _tok_goal_smoke(config: GoalConfig, options: DoctorOptions, provider: str) -> ProbeResult:
    with tempfile.TemporaryDirectory(prefix="goal-cli-doctor-") as temp_dir:
        root = Path(temp_dir)
        write_dir = root / "src"
        run_dir = root / ".goal" / "doctor-smoke"
        write_dir.mkdir(parents=True)
        run_dir.mkdir(parents=True)
        smoke_config = TokConfig(
            provider=provider,
            prompt_template="",
            write_dirs=(write_dir,),
            sandbox=config.tok.sandbox,
            model=config.tok.model,
            codex_features=config.tok.codex_features,
        )
        prompt = (
            "Doctor smoke check for goal-cli setup readiness.\n"
            "Create doctor-smoke.txt in the current temporary writable directory, then return a JSON tok report with "
            "source_change_possible true and a concise remaining_artifact_bottleneck.\n"
        )
        result = execute_tok(smoke_config, prompt, run_dir, timeout_seconds=options.smoke_timeout_seconds)
        if not result.ok:
            detail = f"{provider} smoke failed: {result.detail}"
            if result.plan and result.plan.log_path.exists():
                detail += f"; see {result.plan.log_path}"
            return ProbeResult(False, detail)
        created_file = write_dir / "doctor-smoke.txt"
        if not created_file.exists():
            return ProbeResult(False, f"{provider} smoke returned a valid tok report but did not create the temporary smoke artifact")
        return ProbeResult(True, f"{provider} smoke produced a schema-valid tok report and temporary source change")


def _local_file_tik_smoke(config: GoalConfig, options: DoctorOptions, provider: str) -> ProbeResult:
    with tempfile.TemporaryDirectory(prefix="goal-cli-doctor-tik-") as temp_dir:
        from .runtime import parse_tik_verdict

        root = Path(temp_dir)
        run_dir = root / ".goal" / f"doctor-{provider.replace('_', '-')}-tik"
        run_dir.mkdir(parents=True)
        artifact = root / "doctor-artifact.txt"
        artifact.write_text(f"goal-cli doctor {provider} tik smoke artifact\n", encoding="utf-8")
        smoke_config = TikConfig(
            provider=provider,
            prompt="",
            model=config.tik.model,
            timeout_seconds=options.smoke_timeout_seconds,
            max_file_size_bytes=max(config.tik.max_file_size_bytes, artifact.stat().st_size),
            verdict=config.tik.verdict,
        )
        example = _tik_smoke_example(config)
        prompt = (
            f"Doctor smoke check for goal-cli {provider} tik readiness.\n"
            "Inspect the only local artifact file and return only a JSON object that matches this example:\n"
            f"{json.dumps(example, ensure_ascii=False, indent=2)}\n"
        )
        label = f"{provider}_smoke"
        memo_path = run_tik(
            smoke_config,
            root,
            artifact,
            prompt,
            run_dir,
            label,
            "doctor-artifact.txt",
            timeout_seconds=options.smoke_timeout_seconds,
        )
        if memo_path is None:
            log_path = run_dir / f"{label}_{provider}.log"
            detail = f"{provider} tik smoke failed"
            if log_path.exists():
                detail += f"; see {log_path}"
            return ProbeResult(False, detail)
        verdict, parse_error = parse_tik_verdict(config, memo_path)
        if parse_error:
            return ProbeResult(False, f"{provider} tik smoke returned an invalid tik verdict: {verdict.get('_parse_error')}")
        return ProbeResult(True, f"{provider} tik smoke produced a parseable current-artifact verdict")


def run_doctor(config: GoalConfig, options: DoctorOptions | None = None, probes: SetupProbeAdapter | None = None) -> list[DoctorCheck]:
    options = options or DoctorOptions()
    probes = probes or LocalSetupProbeAdapter()
    checks: list[DoctorCheck] = []
    policy = analyze_config_policy(config)

    config_issues = policy.messages()
    checks.append(_check("config", not config_issues, "config valid", "; ".join(config_issues)))
    checks.extend(_filesystem_checks(config, policy, probes))
    checks.extend(_configured_command_checks(config, probes))
    checks.extend(_no_mistakes_checks(config, options, probes))
    checks.extend(_observability_checks(config, options, probes))

    codex_available = False
    if config.tok.provider == "codex_goal" or config.tik.provider == "codex_file":
        codex_path = probes.which("codex")
        codex_available = codex_path is not None
        checks.append(_check("codex.binary", codex_available, f"codex found at {codex_path}", "codex executable not found on PATH"))
        if codex_available:
            checks.extend(_codex_capability_checks(config, options, probes))

    if config.tik.provider == "api":
        checks.extend(_api_tik_checks(options, probes))

    claude_available = False
    if config.tik.provider == "claude_code_file" or config.tok.provider == "claude_code_goal":
        claude_path = probes.which("claude")
        claude_available = claude_path is not None
        checks.append(_check("claude.binary", claude_available, f"claude found at {claude_path}", "claude executable not found on PATH"))
        if claude_available:
            checks.extend(_claude_code_capability_checks(config, options, probes))

    if config.tok.sandbox == "read-only":
        checks.append(
            DoctorCheck(
                "tok.sandbox",
                False,
                "tok sandbox is read-only; source-improvement loops can only complete if the producer already emits a passing artifact",
                "warning",
            )
        )

    if options.smoke_codex_goal and codex_available:
        if config.tok.provider == "codex_goal":
            smoke_result = probes.codex_goal_smoke(config, options)
            checks.append(DoctorCheck("codex_goal.smoke", smoke_result.ok, smoke_result.detail))
        else:
            checks.append(
                DoctorCheck(
                    "codex_goal.smoke",
                    True,
                    f"codex_goal smoke skipped because tok.provider is {config.tok.provider}",
                    "warning",
                )
            )

    if options.smoke_claude_code_goal and claude_available:
        if config.tok.provider == "claude_code_goal":
            smoke_result = probes.claude_code_goal_smoke(config, options)
            checks.append(DoctorCheck("claude_code_goal.smoke", smoke_result.ok, smoke_result.detail))
        else:
            checks.append(
                DoctorCheck(
                    "claude_code_goal.smoke",
                    True,
                    f"claude_code_goal smoke skipped because tok.provider is {config.tok.provider}",
                    "warning",
                )
            )

    if options.smoke_codex_file_tik and codex_available:
        if config.tik.provider == "codex_file":
            smoke_result = probes.codex_file_tik_smoke(config, options)
            checks.append(DoctorCheck("codex_file_tik.smoke", smoke_result.ok, smoke_result.detail))
        else:
            checks.append(
                DoctorCheck(
                    "codex_file_tik.smoke",
                    True,
                    f"codex_file tik smoke skipped because tik.provider is {config.tik.provider}",
                    "warning",
                )
            )

    if options.smoke_claude_code_file_tik:
        if config.tik.provider == "claude_code_file" and claude_available:
            smoke_result = probes.claude_code_file_tik_smoke(config, options)
            checks.append(DoctorCheck("claude_code_file_tik.smoke", smoke_result.ok, smoke_result.detail))
        elif config.tik.provider != "claude_code_file":
            checks.append(
                DoctorCheck(
                    "claude_code_file_tik.smoke",
                    True,
                    f"claude_code_file tik smoke skipped because tik.provider is {config.tik.provider}",
                    "warning",
                )
            )

    checks.append(_static_setup_summary(checks))
    checks.append(_one_click_summary(config, checks))
    return checks


def format_doctor_checks(checks: list[DoctorCheck]) -> str:
    lines = []
    for check in checks:
        prefix = "OK" if check.ok else ("WARN" if check.severity == "warning" else "FAIL")
        lines.append(f"[{prefix}] {check.name}: {check.detail}")
    return "\n".join(lines) + "\n"


def doctor_exit_code(checks: list[DoctorCheck]) -> int:
    return 1 if any(check.blocks_readiness for check in checks) else 0


def _filesystem_checks(config: GoalConfig, policy: ConfigPolicyReport, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    checks.append(_path_parent_check("artifact.path", config.artifact.path, target_is_file=True))
    checks.append(_path_parent_check("state_dir", config.state_dir))
    checks.append(_path_parent_check("runs_dir", config.runs_dir))
    run_cwd = config.tok.run_cwd or (config.tok.write_dirs[0] if config.tok.write_dirs else config.root)
    checks.append(_path_parent_check("tok.run_cwd", run_cwd))
    for fact in policy.writable_scopes:
        ok = fact.valid and probes.path_writable(fact.resolved)
        checks.append(
            _check(
                "tok.write_dir",
                ok,
                f"writable source scope: {fact.path}",
                f"source scope is not a valid writable directory: {fact.path}",
            )
        )
    for fact in policy.runtime_writable_scopes:
        ok = fact.valid and probes.path_writable(fact.resolved)
        checks.append(
            _check(
                "tok.runtime_write_dir",
                ok,
                f"runtime writable scope: {fact.path}",
                f"runtime scope is not a valid writable directory: {fact.path}",
            )
        )
    return checks


def _configured_command_checks(config: GoalConfig, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    checks = [_command_check("producer.command", config.producer.command, config.root, probes)]
    if config.tik.provider == "oracle":
        checks.append(_command_check("tik.command", config.tik.command or "", config.root, probes))
    return checks


def _observability_checks(config: GoalConfig, options: DoctorOptions, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    if not config.observability.enabled:
        return []

    package_names = [
        "opentelemetry",
        "opentelemetry.sdk",
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    ]
    missing = [package for package in package_names if not probes.package_available(package)]
    checks = [
        DoctorCheck(
            "observability.opentelemetry_packages",
            not missing,
            "OpenTelemetry API, SDK, and OTLP HTTP exporter are importable"
            if not missing
            else f"missing OpenTelemetry package(s): {', '.join(missing)}",
        )
    ]

    plan = plan_observability_export(config, connect_probe=probes.tcp_connects, timeout_seconds=min(options.timeout_seconds, 2.0))
    if not plan.endpoint_valid:
        checks.append(DoctorCheck("observability.otlp_endpoint", False, f"invalid OTLP HTTP endpoint: {plan.endpoint}"))
        return checks

    checks.append(DoctorCheck("observability.otlp_endpoint", True, f"OTLP traces endpoint: {plan.endpoint}"))
    checks.append(
        DoctorCheck(
            "observability.otlp_receiver",
            plan.kind == "otlp" and (plan.reachable or plan.explicit_env),
            f"OTLP receiver is reachable at {plan.host}:{plan.port}"
            if plan.reachable
            else "OTLP receiver is configured by environment; runtime will use the OpenTelemetry exporter"
            if plan.explicit_env
            else (
                f"OTLP receiver is not reachable at {plan.host}:{plan.port}; "
                f"goal-cli will write local fallback traces to {plan.path}"
            ),
            "warning",
        )
    )
    return checks


def _no_mistakes_checks(config: GoalConfig, options: DoctorOptions, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    if not config.no_mistakes.enabled:
        return []

    resolved = resolve_no_mistakes_binary(config, probes.which)
    if resolved is None:
        return [
            DoctorCheck(
                "no_mistakes.binary",
                False,
                f"no-mistakes executable not found: {config.no_mistakes.binary}",
            )
        ]

    checks = [DoctorCheck("no_mistakes.binary", True, f"no-mistakes found at {resolved}")]
    try:
        help_result = probes.run(no_mistakes_axi_run_help_command(resolved), config.root, options.timeout_seconds)
    except OSError as exc:
        return checks + [DoctorCheck("no_mistakes.axi_run_help", False, f"failed to start no-mistakes axi run --help: {exc}")]
    except subprocess.TimeoutExpired:
        return checks + [DoctorCheck("no_mistakes.axi_run_help", False, f"no-mistakes axi run --help timed out after {options.timeout_seconds:g}s")]

    help_text = (help_result.stdout or "") + (help_result.stderr or "")
    ok = help_result.returncode == 0 and no_mistakes_help_supports_required_flags(help_text)
    checks.append(
        DoctorCheck(
            "no_mistakes.axi_run_help",
            ok,
            "no-mistakes axi run supports --intent, --yes, and --skip" if ok else "no-mistakes axi run --help did not show required non-interactive flags",
        )
    )
    return checks

def _codex_capability_checks(config: GoalConfig, options: DoctorOptions, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    try:
        help_result = probes.run(["codex", "exec", "--help"], config.root, options.timeout_seconds)
    except OSError as exc:
        return [DoctorCheck("codex.exec.help", False, f"failed to start codex exec --help: {exc}")]
    except subprocess.TimeoutExpired:
        return [DoctorCheck("codex.exec.help", False, f"codex exec --help timed out after {options.timeout_seconds:g}s")]

    help_text = (help_result.stdout or "") + (help_result.stderr or "")
    checks = [_check("codex.exec.help", help_result.returncode == 0, "codex exec --help succeeded", "codex exec --help failed")]
    required_flags: list[str] = []
    if config.tok.provider == "codex_goal":
        required_flags.extend(["--output-schema", "--output-last-message", "--enable", "--add-dir", "--sandbox", "--skip-git-repo-check"])
    if config.tik.provider == "codex_file":
        for flag in ("--output-last-message", "--sandbox", "--skip-git-repo-check", "--ephemeral"):
            if flag not in required_flags:
                required_flags.append(flag)
    for flag in required_flags:
        checks.append(_check(f"codex.exec.{flag}", flag in help_text, f"codex exec supports {flag}", f"codex exec help does not show {flag}"))
    if config.tok.provider != "codex_goal":
        return checks
    if "--enable" in help_text:
        try:
            goals_result = probes.run(["codex", "exec", "--enable", "goals", "--help"], config.root, options.timeout_seconds)
            checks.append(
                _check(
                    "codex.goal_feature",
                    goals_result.returncode == 0,
                    "codex exec accepts --enable goals",
                    "codex exec did not accept --enable goals",
                )
            )
        except OSError as exc:
            checks.append(DoctorCheck("codex.goal_feature", False, f"failed to start codex exec --enable goals --help: {exc}"))
        except subprocess.TimeoutExpired:
            checks.append(DoctorCheck("codex.goal_feature", False, f"codex exec --enable goals --help timed out after {options.timeout_seconds:g}s"))
    else:
        checks.append(DoctorCheck("codex.goal_feature", False, "codex goals feature cannot be requested because --enable is unavailable"))
    return checks


def _claude_code_capability_checks(config: GoalConfig, options: DoctorOptions, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    try:
        help_result = probes.run(["claude", "--help"], config.root, options.timeout_seconds)
    except OSError as exc:
        return [DoctorCheck("claude.help", False, f"failed to start claude --help: {exc}")]
    except subprocess.TimeoutExpired:
        return [DoctorCheck("claude.help", False, f"claude --help timed out after {options.timeout_seconds:g}s")]

    help_text = (help_result.stdout or "") + (help_result.stderr or "")
    checks = [_check("claude.help", help_result.returncode == 0, "claude --help succeeded", "claude --help failed")]
    required_flags = ["--print", "--output-format", "--disallowedTools", "--model"]
    if config.tok.provider == "claude_code_goal":
        required_flags.extend(["--json-schema", "--add-dir", "--permission-mode"])
    for flag in required_flags:
        checks.append(_check(f"claude.{flag}", flag in help_text, f"claude supports {flag}", f"claude help does not show {flag}"))
    return checks


def _api_tik_checks(options: DoctorOptions, probes: SetupProbeAdapter) -> list[DoctorCheck]:
    checks = [
        _check(
            "openai.package",
            probes.package_available("openai"),
            "openai Python package importable",
            "openai Python package is not installed; install goal-cli[openai] or openai",
        )
    ]
    if options.skip_openai_auth:
        checks.append(DoctorCheck("openai.auth", True, "API auth check skipped"))
    else:
        key_source, _ = api_tik_value_source(API_TIK_KEY_ENV_VARS)
        accepted = ", ".join(API_TIK_KEY_ENV_VARS)
        checks.append(
            _check(
                "openai.auth",
                key_source is not None,
                f"{key_source} is set",
                f"no API key is set for the api tik provider; set one of {accepted} or write ~/.config/goal-cli/api.env",
            )
        )
    return checks


def _static_setup_summary(checks: list[DoctorCheck]) -> DoctorCheck:
    blocking = _blocking_checks(checks)
    if blocking:
        names = ", ".join(check.name for check in blocking)
        return DoctorCheck("static_setup", False, f"not ready for goal-cli run; blocking checks: {names}")
    warnings = [check.name for check in checks if not check.ok and check.severity == "warning"]
    detail = "static setup ready for goal-cli run"
    if warnings:
        detail += f"; warnings: {', '.join(warnings)}"
    return DoctorCheck("static_setup", True, detail)


def _one_click_summary(config: GoalConfig, checks: list[DoctorCheck]) -> DoctorCheck:
    blocking = _blocking_checks(checks)
    if blocking:
        names = ", ".join(check.name for check in blocking)
        return DoctorCheck("one_click_artifact_loop", False, f"not ready for one-prompt goal-cli run; blocking checks: {names}")
    required_smokes = []
    if config.tok.provider == "codex_goal":
        required_smokes.append("codex_goal.smoke")
    if config.tok.provider == "claude_code_goal":
        required_smokes.append("claude_code_goal.smoke")
    if config.tik.provider == "codex_file":
        required_smokes.append("codex_file_tik.smoke")
    if config.tik.provider == "claude_code_file":
        required_smokes.append("claude_code_file_tik.smoke")
    missing_smokes = [name for name in required_smokes if not any(check.name == name for check in checks)]
    if missing_smokes:
        flags = []
        if config.tok.provider == "codex_goal":
            flags.append("--smoke-codex-goal")
        if config.tok.provider == "claude_code_goal":
            flags.append("--smoke-claude-code-goal")
        if config.tik.provider == "codex_file":
            flags.append("--smoke-codex-file-tik")
        if config.tik.provider == "claude_code_file":
            flags.append("--smoke-claude-code-file-tik")
        return DoctorCheck(
            "one_click_artifact_loop",
            False,
            f"one-prompt path not proven; run goal-cli doctor {' '.join(flags)}",
            "warning",
        )
    return DoctorCheck("one_click_artifact_loop", True, "ready for one-prompt goal-cli run")


def _blocking_checks(checks: list[DoctorCheck]) -> list[DoctorCheck]:
    summary_names = {"static_setup", "one_click_artifact_loop"}
    return [check for check in checks if check.name not in summary_names and check.blocks_readiness]


def _path_parent_check(name: str, path: Path, target_is_file: bool = False) -> DoctorCheck:
    target = path.parent if target_is_file else path
    ancestor = target
    missing_parts: list[str] = []
    while not ancestor.exists() and ancestor.parent != ancestor:
        missing_parts.append(ancestor.name)
        ancestor = ancestor.parent
    ok = ancestor.exists() and ancestor.is_dir() and os.access(ancestor, os.W_OK | os.X_OK)
    if ok:
        if missing_parts:
            return DoctorCheck(name, True, f"{path} can be created under writable ancestor {ancestor}")
        return DoctorCheck(name, True, f"{path} is under writable directory {ancestor}")
    return DoctorCheck(name, False, f"{path} cannot be created; nearest existing ancestor is not writable: {ancestor}")


def _command_check(name: str, command: str, cwd: Path, probes: SetupProbeAdapter) -> DoctorCheck:
    binary, reason = _first_command_binary(command)
    if binary is None:
        return DoctorCheck(name, False, f"{reason}: {command}", "warning")
    resolved = _resolve_executable(binary, cwd, probes)
    if resolved is None:
        return DoctorCheck(name, False, f"command executable not found: {binary}")
    script_issue = _script_argument_issue(command, cwd)
    if script_issue:
        return DoctorCheck(name, False, script_issue)
    return DoctorCheck(name, True, f"command executable found: {binary} ({resolved})")


def _first_command_binary(command: str) -> tuple[str | None, str]:
    if any(token in command for token in ("&&", "||", "|", ";", "\n")):
        return None, "complex shell command cannot be fully checked statically"
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return None, f"command could not be parsed: {exc}"
    while tokens and _ENV_ASSIGNMENT.match(tokens[0]):
        tokens.pop(0)
    if tokens and tokens[0] == "env":
        tokens.pop(0)
        while tokens and (_ENV_ASSIGNMENT.match(tokens[0]) or tokens[0].startswith("-")):
            tokens.pop(0)
    if not tokens:
        return None, "empty command"
    if tokens[0] in _SHELL_CONTROL_TOKENS:
        return None, "command starts with shell control syntax"
    if tokens[0] in _SHELL_BUILTINS:
        return tokens[0], "shell builtin"
    return tokens[0], "command executable"


def _resolve_executable(binary: str, cwd: Path, probes: SetupProbeAdapter) -> str | None:
    if binary in _SHELL_BUILTINS:
        return "shell builtin"
    if "/" in binary:
        path = Path(binary)
        if not path.is_absolute():
            path = cwd / path
        return str(path) if path.exists() and os.access(path, os.X_OK) else None
    return probes.which(binary)


def _script_argument_issue(command: str, cwd: Path) -> str | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    while tokens and _ENV_ASSIGNMENT.match(tokens[0]):
        tokens.pop(0)
    if tokens and tokens[0] == "env":
        tokens.pop(0)
        while tokens and (_ENV_ASSIGNMENT.match(tokens[0]) or tokens[0].startswith("-")):
            tokens.pop(0)
    if len(tokens) < 2:
        return None
    binary = Path(tokens[0]).name
    if not (binary.startswith("python") or binary in {"ruby", "node", "bash", "sh"}):
        return None
    script = tokens[1]
    if script.startswith("-"):
        return None
    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = cwd / script_path
    if not script_path.exists():
        return f"command script does not exist: {script}"
    return None


def _check(name: str, ok: bool, ok_detail: str, fail_detail: str) -> DoctorCheck:
    return DoctorCheck(name, ok, ok_detail if ok else fail_detail)


def _tik_smoke_example(config: GoalConfig) -> dict[str, object]:
    example: dict[str, object] = {field: "doctor smoke" for field in config.tik.verdict.required_fields}
    example[config.tik.verdict.ready_field] = False
    example[config.tik.verdict.blockers_field] = [
        {
            "severity": "blocking",
            "objection": "doctor smoke objection",
            "artifact_evidence": "doctor-artifact.txt",
        }
    ]
    example.setdefault("central_bottleneck", "doctor smoke bottleneck")
    example.setdefault("required_next_artifact_changes", ["doctor smoke change"])
    return example
