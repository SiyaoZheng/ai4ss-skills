from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import os
import re
import tomllib

from .template import template_placeholders


TERMINAL_STATUSES = {
    "complete",
    "blocked_unparseable_tik",
    "blocked_repeated_same_objection",
    "blocked_no_source_change_possible",
    "blocked_tok_no_source_changes",
}

NO_MISTAKES_SKIP_STEPS = {
    "intent",
    "rebase",
    "review",
    "test",
    "document",
    "lint",
    "push",
    "pr",
    "ci",
}
NO_MISTAKES_MODES = {"full", "fast", "lightspeed"}
NO_MISTAKES_FIELDS = {
    "enabled",
    "binary",
    "mode",
    "branch_prefix",
    "intent",
    "skip_steps",
    "timeout_seconds",
    "checkpoint_message",
}
OBSERVABILITY_FIELDS = {
    "enabled",
    "service_name",
    "endpoint",
    "timeout_seconds",
}
DEFAULT_API_TIK_MODEL = "claude-fable-5"
DEFAULT_API_TIK_BASE_URL = "https://www.packyapi.com/v1"
API_TIK_KEY_ENV_VARS = ("PACKYAPI_API_KEY", "PACKYCODE_CODEX_KEY", "OPENAI_API_KEY")
API_TIK_BASE_URL_ENV_VARS = ("PACKYAPI_BASE_URL", "OPENAI_BASE_URL")
API_TIK_ENV_FILE_ENV_VAR = "GOAL_CLI_API_ENV_FILE"

TIK_PROMPT_PLACEHOLDERS = {
    "goal_name",
    "artifact_path",
    "artifact_sha256",
    "producer_command",
}

TOK_PROMPT_PLACEHOLDERS = {
    "goal_name",
    "producer_command",
    "artifact_path",
    "artifact_sha256",
    "tik_review_path",
    "writable_scopes",
    "runtime_writable_scopes",
    "tok_run_cwd",
    "run_dir",
}

FORBIDDEN_RUNTIME_PROMPT_PATTERNS = {
    "Adrian": re.compile(r"\bAdrian\b", re.IGNORECASE),
    "user": re.compile(r"\buser\b", re.IGNORECASE),
    "human": re.compile(r"\bhuman\b", re.IGNORECASE),
    "approval": re.compile(r"\bapproval\b", re.IGNORECASE),
    "approve": re.compile(r"\bapprove\b", re.IGNORECASE),
    "ask": re.compile(r"\bask\b", re.IGNORECASE),
    "decision_required": re.compile(r"\bdecision_required\b", re.IGNORECASE),
    "scholarly decision": re.compile(r"\bscholarly\s+decision\b", re.IGNORECASE),
    "human judgment": re.compile(r"\bhuman\s+judg(?:e)?ment\b", re.IGNORECASE),
}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactConfig:
    path: Path
    copy_as: str | None = None


@dataclass(frozen=True)
class ProducerConfig:
    command: str


@dataclass(frozen=True)
class VerdictConfig:
    ready_field: str = "artifact_ready"
    blockers_field: str = "blocking_objections"
    required_fields: tuple[str, ...] = ("artifact_ready", "blocking_objections")
    fingerprint_fields: tuple[str, ...] = ("blocking_objections", "central_bottleneck")


@dataclass(frozen=True)
class TikConfig:
    provider: str
    prompt: str
    model: str | None = None
    command: str | None = None
    skill: str | None = None
    base_url: str | None = None
    binary: str = "oracle"
    engine: str = "browser"
    timeout: str = "auto"
    timeout_seconds: float = 1800
    max_file_size_bytes: int = 25_000_000
    max_output_tokens: int = 4096
    store: bool = False
    verdict: VerdictConfig = field(default_factory=VerdictConfig)


@dataclass(frozen=True)
class TokConfig:
    provider: str
    prompt_template: str
    write_dirs: tuple[Path, ...]
    sandbox: str = "workspace-write"
    run_cwd: Path | None = None
    runtime_write_dirs: tuple[Path, ...] = ()
    model: str | None = None
    codex_features: tuple[str, ...] = ()


@dataclass(frozen=True)
class SafetyConfig:
    generated_dirs: tuple[Path, ...] = (Path("output"), Path("build"))
    max_blocker_repeats: int = 3
    lock_stale_seconds: int = 6 * 60 * 60
    max_history_items: int = 50


@dataclass(frozen=True)
class NoMistakesConfig:
    enabled: bool = True
    binary: str = "no-mistakes"
    mode: str = "lightspeed"
    branch_prefix: str = "goal-cli"
    intent: str | None = None
    skip_steps: tuple[str, ...] = ()
    timeout_seconds: float = 0.0
    checkpoint_message: str = "goal-cli checkpoint: {goal_name} heartbeat {iteration} {phase}"


@dataclass(frozen=True)
class ObservabilityConfig:
    enabled: bool = True
    service_name: str = "goal-cli"
    endpoint: str = "http://localhost:4318/v1/traces"
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class GoalConfig:
    path: Path
    root: Path
    name: str
    state_dir: Path
    runs_dir: Path
    artifact: ArtifactConfig
    producer: ProducerConfig
    tik: TikConfig
    tok: TokConfig
    safety: SafetyConfig
    no_mistakes: NoMistakesConfig
    observability: ObservabilityConfig

    @property
    def state_path(self) -> Path:
        return self.state_dir / "state.json"

    @property
    def lock_path(self) -> Path:
        return self.state_dir / ".heartbeat.lock"

    @property
    def heartbeat_path(self) -> Path:
        return self.state_dir / "heartbeat.json"


@dataclass(frozen=True)
class ConfigIssue:
    code: str
    message: str


@dataclass(frozen=True)
class WritableScopeFact:
    path: Path
    resolved: Path
    inside_root: bool
    is_project_root: bool
    exists: bool
    is_dir: bool
    protected_overlap: Path | None

    @property
    def valid(self) -> bool:
        return self.inside_root and not self.is_project_root and self.exists and self.is_dir and self.protected_overlap is None


@dataclass(frozen=True)
class ConfigPolicyReport:
    root: Path
    protected_paths: tuple[Path, ...]
    writable_scopes: tuple[WritableScopeFact, ...]
    runtime_writable_scopes: tuple[WritableScopeFact, ...]
    issues: tuple[ConfigIssue, ...]

    def messages(self) -> list[str]:
        return [issue.message for issue in self.issues]


def load_config(config_path: str | Path = "goal.toml") -> GoalConfig:
    path = Path(config_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")
    with path.open("rb") as config_file:
        raw = tomllib.load(config_file)
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a TOML table")

    root = _path(raw.get("project", {}).get("root") if isinstance(raw.get("project"), dict) else None, path.parent, path.parent)
    root = root.resolve()
    name = _required_str(raw, "name")
    state_dir = _path(raw.get("state_dir", ".goal"), root, root)
    runs_dir = _path(raw.get("runs_dir", ".goal/runs"), root, root)

    artifact_raw = _required_table(raw, "artifact")
    artifact = ArtifactConfig(
        path=_path(_required_str(artifact_raw, "path"), root, root),
        copy_as=_optional_filename(artifact_raw, "copy_as"),
    )

    producer_raw = _required_table(raw, "producer")
    producer = ProducerConfig(command=_required_str(producer_raw, "command"))

    tik_raw = _required_table(raw, "tik")
    tik_prompt = _prompt_from(tik_raw, required_key="prompt")
    verdict_raw = tik_raw.get("verdict", {})
    if verdict_raw is None:
        verdict_raw = {}
    if not isinstance(verdict_raw, dict):
        raise ConfigError("[tik.verdict] must be a table")
    verdict = VerdictConfig(
        ready_field=str(verdict_raw.get("ready_field", "artifact_ready")),
        blockers_field=str(verdict_raw.get("blockers_field", "blocking_objections")),
        required_fields=tuple(_string_list(verdict_raw.get("required_fields", ["artifact_ready", "blocking_objections"]), "tik.verdict.required_fields")),
        fingerprint_fields=tuple(_string_list(verdict_raw.get("fingerprint_fields", ["blocking_objections", "central_bottleneck"]), "tik.verdict.fingerprint_fields")),
    )
    tik_provider = _required_str(tik_raw, "provider")
    tik_model = _optional_str(tik_raw, "model")
    if tik_provider == "api" and tik_model is None:
        tik_model = DEFAULT_API_TIK_MODEL
    tik = TikConfig(
        provider=tik_provider,
        prompt=tik_prompt,
        model=tik_model,
        command=_optional_str(tik_raw, "command"),
        skill=_optional_str(tik_raw, "skill"),
        base_url=_optional_str(tik_raw, "base_url"),
        binary=str(tik_raw.get("binary", "oracle")),
        engine=str(tik_raw.get("engine", "browser")),
        timeout=str(tik_raw.get("timeout", "auto")),
        timeout_seconds=float(tik_raw.get("timeout_seconds", 1800)),
        max_file_size_bytes=int(tik_raw.get("max_file_size_bytes", 25_000_000)),
        max_output_tokens=int(tik_raw.get("max_output_tokens", 4096)),
        store=bool(tik_raw.get("store", False)),
        verdict=verdict,
    )

    tok_raw = _required_table(raw, "tok")
    if "command" in tok_raw:
        raise ConfigError("unsupported tok field: command; tok provider must be 'codex_goal' or 'claude_code_goal'")
    tok_prompt = _prompt_from(tok_raw, required_key="prompt_template")
    write_dirs = tuple(_path(item, root, root) for item in _string_list(tok_raw.get("write_dirs"), "tok.write_dirs"))
    run_cwd = _path(tok_raw["run_cwd"], root, root) if "run_cwd" in tok_raw else (write_dirs[0] if write_dirs else root)
    runtime_write_dirs = tuple(
        _path(item, root, root)
        for item in _string_list(tok_raw.get("runtime_write_dirs", []), "tok.runtime_write_dirs")
    )
    tok = TokConfig(
        provider=_required_str(tok_raw, "provider"),
        prompt_template=tok_prompt,
        write_dirs=write_dirs,
        sandbox=str(tok_raw.get("sandbox", "workspace-write")),
        run_cwd=run_cwd,
        runtime_write_dirs=runtime_write_dirs,
        model=_optional_str(tok_raw, "model"),
        codex_features=tuple(_string_list(tok_raw.get("codex_features", []), "tok.codex_features")),
    )

    safety_raw = raw.get("safety", {})
    if safety_raw is None:
        safety_raw = {}
    if not isinstance(safety_raw, dict):
        raise ConfigError("[safety] must be a table")
    generated_dirs = tuple(
        _path(item, root, root)
        for item in _string_list(safety_raw.get("generated_dirs", ["output", "build"]), "safety.generated_dirs")
    )
    safety = SafetyConfig(
        generated_dirs=generated_dirs,
        max_blocker_repeats=int(safety_raw.get("max_blocker_repeats", 3)),
        lock_stale_seconds=int(safety_raw.get("lock_stale_seconds", 6 * 60 * 60)),
        max_history_items=int(safety_raw.get("max_history_items", 50)),
    )

    no_mistakes_raw = raw.get("no_mistakes", {})
    if no_mistakes_raw is None:
        no_mistakes_raw = {}
    if not isinstance(no_mistakes_raw, dict):
        raise ConfigError("[no_mistakes] must be a table")
    unsupported_no_mistakes_fields = sorted(set(no_mistakes_raw) - NO_MISTAKES_FIELDS)
    if unsupported_no_mistakes_fields:
        fields = ", ".join(unsupported_no_mistakes_fields)
        raise ConfigError(f"unsupported [no_mistakes] field(s): {fields}; no-mistakes is fully automatic when enabled")
    no_mistakes = NoMistakesConfig(
        enabled=_bool(no_mistakes_raw.get("enabled"), True, "no_mistakes.enabled"),
        binary=str(no_mistakes_raw.get("binary", "no-mistakes")).strip(),
        mode=str(no_mistakes_raw.get("mode", "lightspeed")).strip(),
        branch_prefix=str(no_mistakes_raw.get("branch_prefix", "goal-cli")).strip(),
        intent=_optional_str(no_mistakes_raw, "intent"),
        skip_steps=tuple(_string_list(no_mistakes_raw.get("skip_steps", []), "no_mistakes.skip_steps")),
        timeout_seconds=float(no_mistakes_raw.get("timeout_seconds", 0)),
        checkpoint_message=str(
            no_mistakes_raw.get(
                "checkpoint_message",
                "goal-cli checkpoint: {goal_name} heartbeat {iteration} {phase}",
            )
        ).strip(),
    )

    observability_raw = raw.get("observability", {})
    if observability_raw is None:
        observability_raw = {}
    if not isinstance(observability_raw, dict):
        raise ConfigError("[observability] must be a table")
    unsupported_observability_fields = sorted(set(observability_raw) - OBSERVABILITY_FIELDS)
    if unsupported_observability_fields:
        fields = ", ".join(unsupported_observability_fields)
        raise ConfigError(f"unsupported [observability] field(s): {fields}; observability uses standard OpenTelemetry/OTLP")
    observability = ObservabilityConfig(
        enabled=_bool(observability_raw.get("enabled"), True, "observability.enabled"),
        service_name=str(observability_raw.get("service_name", "goal-cli")).strip(),
        endpoint=str(observability_raw.get("endpoint", "http://localhost:4318/v1/traces")).strip(),
        timeout_seconds=float(observability_raw.get("timeout_seconds", 5.0)),
    )

    return GoalConfig(
        path=path,
        root=root,
        name=name,
        state_dir=state_dir,
        runs_dir=runs_dir,
        artifact=artifact,
        producer=producer,
        tik=tik,
        tok=tok,
        safety=safety,
        no_mistakes=no_mistakes,
        observability=observability,
    )


def analyze_config_policy(config: GoalConfig) -> ConfigPolicyReport:
    issues: list[ConfigIssue] = []
    if not _inside(config.root, config.path):
        issues.append(ConfigIssue("config.outside_root", f"config file must be inside project root: {config.path}"))
    if config.tik.provider not in {"oracle", "api", "codex_file", "claude_code_file"}:
        issues.append(ConfigIssue("tik.provider.unsupported", f"unsupported tik provider: {config.tik.provider}"))
    if config.tok.provider not in {"codex_goal", "claude_code_goal"}:
        issues.append(ConfigIssue("tok.provider.unsupported", f"unsupported tok provider: {config.tok.provider}"))
    if config.tik.provider == "oracle" and not config.tik.command:
        issues.append(ConfigIssue("tik.command.required", "tik provider 'oracle' requires tik.command"))
    if config.tik.provider == "api" and tik_prompt_starts_with_slash_command(config.tik.prompt):
        issues.append(
            ConfigIssue(
                "tik.prompt.slash_unsupported",
                "tik provider 'api' cannot execute slash skill commands; set tik.skill and remove the leading slash command",
            )
        )
    if config.tik.skill:
        if config.tik.provider != "api":
            issues.append(ConfigIssue("tik.skill.unsupported", "tik.skill is only supported for tik provider 'api'"))
        elif resolve_tik_skill_path(config.tik.skill, config.root) is None:
            issues.append(ConfigIssue("tik.skill.missing", f"tik.skill could not be resolved to a SKILL.md file: {config.tik.skill}"))
    if config.tok.provider in {"codex_goal", "claude_code_goal"} and config.tok.sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
        issues.append(ConfigIssue("tok.sandbox.unsupported", f"unsupported tok sandbox: {config.tok.sandbox}"))
    if config.no_mistakes.enabled:
        if not config.no_mistakes.binary:
            issues.append(ConfigIssue("no_mistakes.binary.empty", "no_mistakes.binary must be non-empty when no_mistakes is enabled"))
        if config.no_mistakes.mode not in NO_MISTAKES_MODES:
            issues.append(ConfigIssue("no_mistakes.mode.unsupported", f"unsupported no_mistakes mode: {config.no_mistakes.mode}"))
        if not config.no_mistakes.checkpoint_message:
            issues.append(ConfigIssue("no_mistakes.checkpoint_message.empty", "no_mistakes.checkpoint_message must be non-empty when no_mistakes is enabled"))
        for step in config.no_mistakes.skip_steps:
            if step not in NO_MISTAKES_SKIP_STEPS:
                issues.append(ConfigIssue("no_mistakes.skip_steps.unsupported", f"unsupported no_mistakes skip step: {step}"))
        if config.no_mistakes.timeout_seconds < 0:
            issues.append(ConfigIssue("no_mistakes.timeout_seconds.negative", "no_mistakes.timeout_seconds must be non-negative"))
    if config.observability.enabled:
        if not config.observability.service_name:
            issues.append(ConfigIssue("observability.service_name.empty", "observability.service_name must be non-empty when observability is enabled"))
        if not config.observability.endpoint:
            issues.append(ConfigIssue("observability.endpoint.empty", "observability.endpoint must be non-empty when observability is enabled"))
        if config.observability.timeout_seconds <= 0:
            issues.append(ConfigIssue("observability.timeout_seconds.non_positive", "observability.timeout_seconds must be positive when observability is enabled"))
    issues.extend(ConfigIssue("prompt.placeholder", issue) for issue in validate_prompt_templates(config))
    issues.extend(ConfigIssue("prompt.language", issue) for issue in validate_runtime_prompt_language(config))

    protected_paths = config_protected_paths(config)
    writable_scopes, writable_issues = analyze_writable_scope_policy(config, protected_paths)
    issues.extend(writable_issues)
    runtime_writable_scopes, runtime_writable_issues = analyze_runtime_writable_scope_policy(config)
    issues.extend(runtime_writable_issues)
    issues.extend(analyze_run_cwd_policy(config))
    return ConfigPolicyReport(
        root=_resolve(config.root),
        protected_paths=protected_paths,
        writable_scopes=writable_scopes,
        runtime_writable_scopes=runtime_writable_scopes,
        issues=tuple(issues),
    )


def validate_config(config: GoalConfig) -> list[str]:
    return analyze_config_policy(config).messages()


def config_protected_paths(config: GoalConfig) -> tuple[Path, ...]:
    root = _resolve(config.root)
    protected = [
        _resolve(Path(".git"), root),
        _resolve(config.path),
        _resolve(config.state_dir),
        _resolve(config.runs_dir),
        _resolve(config.artifact.path),
    ]
    protected.extend(_resolve(path) for path in config.safety.generated_dirs)
    return tuple(protected)


def config_runtime_protected_paths(config: GoalConfig) -> tuple[Path, ...]:
    root = _resolve(config.root)
    return (
        _resolve(Path(".git"), root),
        _resolve(config.path),
        _resolve(config.state_dir),
        _resolve(config.runs_dir),
    )


def analyze_writable_scope_policy(
    config: GoalConfig,
    protected_paths: tuple[Path, ...] | None = None,
) -> tuple[tuple[WritableScopeFact, ...], tuple[ConfigIssue, ...]]:
    issues: list[ConfigIssue] = []
    facts: list[WritableScopeFact] = []
    root = _resolve(config.root)
    protected_paths = protected_paths or config_protected_paths(config)

    if not config.tok.write_dirs:
        issues.append(ConfigIssue("tok.write_dirs.empty", "tok.write_dirs must contain at least one writable source directory"))

    for write_dir in config.tok.write_dirs:
        resolved = _resolve(write_dir)
        protected_overlap = next((protected_path for protected_path in protected_paths if _paths_overlap(resolved, protected_path)), None)
        fact = WritableScopeFact(
            path=write_dir,
            resolved=resolved,
            inside_root=_inside(root, resolved),
            is_project_root=resolved == root,
            exists=resolved.exists(),
            is_dir=resolved.is_dir(),
            protected_overlap=protected_overlap,
        )
        facts.append(fact)
        if fact.is_project_root:
            issues.append(ConfigIssue("tok.write_dir.project_root", f"tok.write_dirs must not include the project root: {write_dir}"))
        if not fact.inside_root:
            issues.append(ConfigIssue("tok.write_dir.outside_root", f"tok.write_dirs must stay inside project root: {write_dir}"))
        if not fact.exists:
            issues.append(ConfigIssue("tok.write_dir.missing", f"tok.write_dirs entry does not exist: {write_dir}"))
        elif not fact.is_dir:
            issues.append(ConfigIssue("tok.write_dir.not_dir", f"tok.write_dirs entry is not a directory: {write_dir}"))
        if fact.protected_overlap is not None:
            issues.append(ConfigIssue("tok.write_dir.protected_overlap", f"tok.write_dirs entry overlaps protected path {fact.protected_overlap}: {write_dir}"))
    return tuple(facts), tuple(issues)


def validate_writable_scopes(config: GoalConfig) -> list[str]:
    _, issues = analyze_writable_scope_policy(config)
    return [issue.message for issue in issues]


def analyze_runtime_writable_scope_policy(config: GoalConfig) -> tuple[tuple[WritableScopeFact, ...], tuple[ConfigIssue, ...]]:
    issues: list[ConfigIssue] = []
    facts: list[WritableScopeFact] = []
    root = _resolve(config.root)
    protected_paths = config_runtime_protected_paths(config)

    for write_dir in config.tok.runtime_write_dirs:
        resolved = _resolve(write_dir)
        protected_overlap = next((protected_path for protected_path in protected_paths if _paths_overlap(resolved, protected_path)), None)
        fact = WritableScopeFact(
            path=write_dir,
            resolved=resolved,
            inside_root=_inside(root, resolved),
            is_project_root=resolved == root,
            exists=resolved.exists(),
            is_dir=resolved.is_dir(),
            protected_overlap=protected_overlap,
        )
        facts.append(fact)
        if fact.is_project_root:
            issues.append(ConfigIssue("tok.runtime_write_dir.project_root", f"tok.runtime_write_dirs must not include the project root: {write_dir}"))
        if not fact.inside_root:
            issues.append(ConfigIssue("tok.runtime_write_dir.outside_root", f"tok.runtime_write_dirs must stay inside project root: {write_dir}"))
        if not fact.exists:
            issues.append(ConfigIssue("tok.runtime_write_dir.missing", f"tok.runtime_write_dirs entry does not exist: {write_dir}"))
        elif not fact.is_dir:
            issues.append(ConfigIssue("tok.runtime_write_dir.not_dir", f"tok.runtime_write_dirs entry is not a directory: {write_dir}"))
        if fact.protected_overlap is not None:
            issues.append(
                ConfigIssue("tok.runtime_write_dir.protected_overlap", f"tok.runtime_write_dirs entry overlaps protected control path {fact.protected_overlap}: {write_dir}")
            )
    return tuple(facts), tuple(issues)


def analyze_run_cwd_policy(config: GoalConfig) -> tuple[ConfigIssue, ...]:
    run_cwd = config.tok.run_cwd or (config.tok.write_dirs[0] if config.tok.write_dirs else config.root)
    root = _resolve(config.root)
    resolved = _resolve(run_cwd)
    issues: list[ConfigIssue] = []
    if not _inside(root, resolved):
        issues.append(ConfigIssue("tok.run_cwd.outside_root", f"tok.run_cwd must stay inside project root: {run_cwd}"))
    if not resolved.exists():
        issues.append(ConfigIssue("tok.run_cwd.missing", f"tok.run_cwd does not exist: {run_cwd}"))
    elif not resolved.is_dir():
        issues.append(ConfigIssue("tok.run_cwd.not_dir", f"tok.run_cwd is not a directory: {run_cwd}"))
    return tuple(issues)


def validate_prompt_templates(config: GoalConfig) -> list[str]:
    issues: list[str] = []
    tik_unknown = template_placeholders(config.tik.prompt) - TIK_PROMPT_PLACEHOLDERS
    for placeholder in sorted(tik_unknown):
        issues.append(f"unknown tik prompt placeholder: {{{placeholder}}}")
    tok_unknown = template_placeholders(config.tok.prompt_template) - TOK_PROMPT_PLACEHOLDERS
    for placeholder in sorted(tok_unknown):
        issues.append(f"unknown tok prompt placeholder: {{{placeholder}}}")
    return issues


def tik_prompt_starts_with_slash_command(prompt: str) -> bool:
    for line in prompt.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith("/") and " " not in stripped
    return False


def resolve_tik_skill_path(reference: str, root: Path) -> Path | None:
    candidates = tik_skill_candidate_paths(reference, root)
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def tik_skill_candidate_paths(reference: str, root: Path) -> tuple[Path, ...]:
    path = Path(reference)
    if path.is_absolute() or "/" in reference or "\\" in reference or reference.endswith(".md"):
        candidate = path if path.is_absolute() else root / path
        if candidate.name == "SKILL.md":
            return (candidate.resolve(strict=False),)
        return ((candidate / "SKILL.md") if candidate.suffix == "" else candidate).resolve(strict=False),

    home = Path.home()
    return tuple(
        candidate.resolve(strict=False)
        for candidate in (
            root / "skills" / reference / "SKILL.md",
            home / ".codex" / "skills" / reference / "SKILL.md",
            home / ".agents" / "skills" / reference / "SKILL.md",
            home / ".claude" / "skills" / reference / "SKILL.md",
        )
    )


def validate_runtime_prompt_language(config: GoalConfig) -> list[str]:
    issues: list[str] = []
    prompt_sources = {
        "tik.prompt": config.tik.prompt,
        "tok.prompt": config.tok.prompt_template,
    }
    for label, prompt in prompt_sources.items():
        for term, pattern in FORBIDDEN_RUNTIME_PROMPT_PATTERNS.items():
            if pattern.search(prompt):
                issues.append(f"forbidden runtime prompt term in {label}: {term}")
    return issues


def dump_config_summary(config: GoalConfig) -> str:
    summary = {
        "name": config.name,
        "root": str(config.root),
        "state_path": str(config.state_path),
        "runs_dir": str(config.runs_dir),
        "artifact": str(config.artifact.path),
        "producer": config.producer.command,
        "tik_provider": config.tik.provider,
        "tik_model": config.tik.model,
        "tik_skill": config.tik.skill,
        "tik_base_url": config.tik.base_url,
        "tok_provider": config.tok.provider,
        "tok_run_cwd": str(config.tok.run_cwd or (config.tok.write_dirs[0] if config.tok.write_dirs else config.root)),
        "write_dirs": [str(path) for path in config.tok.write_dirs],
        "runtime_write_dirs": [str(path) for path in config.tok.runtime_write_dirs],
        "no_mistakes_enabled": config.no_mistakes.enabled,
        "no_mistakes_mode": config.no_mistakes.mode,
        "no_mistakes_skip_steps": list(config.no_mistakes.skip_steps),
        "observability_enabled": config.observability.enabled,
        "observability_endpoint": config.observability.endpoint,
    }
    return json.dumps(summary, ensure_ascii=False, indent=2) + "\n"


def api_tik_value_source(names: tuple[str, ...]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return name, value
    for env_file in api_tik_env_file_paths():
        source, value = _env_file_value(env_file, names)
        if value:
            return source, value
    return None, None


def api_tik_env_file_paths() -> tuple[Path, ...]:
    explicit_path = os.environ.get(API_TIK_ENV_FILE_ENV_VAR)
    if explicit_path:
        return (Path(explicit_path).expanduser(),)
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser()
    return (config_home / "goal-cli" / "api.env",)


def _env_file_value(path: Path, names: tuple[str, ...]) -> tuple[str | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if key not in names:
            continue
        value = _parse_env_file_value(raw_value)
        if value:
            return f"{path}:{key}", value
    return None, None


def _parse_env_file_value(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _required_table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"[{key}] must be defined")
    return value


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_str(raw: dict[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string when provided")
    return value.strip()


def _optional_filename(raw: dict[str, Any], key: str) -> str | None:
    value = _optional_str(raw, key)
    if value is None:
        return None
    path = Path(value)
    if path.name != value or value in {".", ".."}:
        raise ConfigError(f"{key} must be a filename, not a path: {value}")
    return value


def _bool(value: Any, default: bool, label: str) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ConfigError(f"{label} must be a boolean")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        raise ConfigError(f"{label} must be a string list")
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"{label} must be a string list")
    return [item.strip() for item in value]


def _prompt_from(raw: dict[str, Any], required_key: str) -> str:
    prompt_table = raw.get("prompt")
    if isinstance(prompt_table, dict):
        value = prompt_table.get("text")
        if isinstance(value, str) and value.strip():
            return value.strip() + "\n"
        value = prompt_table.get("template")
        if isinstance(value, str) and value.strip():
            return value.strip() + "\n"
    value = raw.get(required_key)
    if isinstance(value, str) and value.strip():
        return value.strip() + "\n"
    raise ConfigError(f"{required_key} must be defined as a non-empty string")


def _path(value: Any, root: Path, default: Path) -> Path:
    if value is None:
        return default
    if not isinstance(value, str | Path):
        raise ConfigError(f"path value must be a string: {value!r}")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=False)


def _resolve(path: Path, root: Path | None = None) -> Path:
    candidate = path if path.is_absolute() else (root or Path.cwd()) / path
    return candidate.resolve(strict=False)


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _paths_overlap(left: Path, right: Path) -> bool:
    left = left.resolve(strict=False)
    right = right.resolve(strict=False)
    return left == right or _inside(left, right) or _inside(right, left)
