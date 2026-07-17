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
    "blocked_invalid_review_evidence",
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
COMMAND_TIK_PROVIDERS = frozenset({"oracle", "checklist"})
SUPPORTED_TIK_PROVIDERS = COMMAND_TIK_PROVIDERS | frozenset({"api", "codex_file", "claude_code_file"})

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
    required_fields: tuple[str, ...] = ("artifact_ready",)


@dataclass(frozen=True)
class TikConfig:
    provider: str
    prompt: str
    label: str = "tik"
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
    providers: tuple["TikConfig", ...] = ()


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
class PerpetualConfig:
    enabled: bool = False
    healthy_interval_seconds: float = 6 * 60 * 60
    active_interval_seconds: float = 30 * 60
    provider_backoff_seconds: tuple[float, ...] = (5 * 60, 30 * 60, 2 * 60 * 60)


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
    perpetual: PerpetualConfig
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
        required_fields=tuple(_string_list(verdict_raw.get("required_fields", ["artifact_ready"]), "tik.verdict.required_fields")),
    )
    tik_providers_raw = _tik_providers_raw(tik_raw)
    tik_providers_config = _load_tik_providers(tik_raw, tik_providers_raw, tik_prompt, verdict)
    primary_tik = tik_providers_config[0]
    tik = TikConfig(
        provider=primary_tik.provider,
        prompt=primary_tik.prompt,
        label=primary_tik.label,
        model=primary_tik.model,
        command=primary_tik.command,
        skill=primary_tik.skill,
        base_url=primary_tik.base_url,
        binary=primary_tik.binary,
        engine=primary_tik.engine,
        timeout=primary_tik.timeout,
        timeout_seconds=primary_tik.timeout_seconds,
        max_file_size_bytes=primary_tik.max_file_size_bytes,
        max_output_tokens=primary_tik.max_output_tokens,
        store=primary_tik.store,
        verdict=verdict,
        providers=tik_providers_config,
    )

    tok_raw = _required_table(raw, "tok")
    if "command" in tok_raw:
        raise ConfigError("unsupported tok field: command; tok provider must be 'codex_goal', 'codex_app_server', or 'claude_code_goal'")
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

    perpetual_raw = raw.get("perpetual", {})
    if perpetual_raw is None:
        perpetual_raw = {}
    if not isinstance(perpetual_raw, dict):
        raise ConfigError("[perpetual] must be a table")
    perpetual = PerpetualConfig(
        enabled=_bool(perpetual_raw.get("enabled"), False, "perpetual.enabled"),
        healthy_interval_seconds=float(perpetual_raw.get("healthy_interval_seconds", 6 * 60 * 60)),
        active_interval_seconds=float(perpetual_raw.get("active_interval_seconds", 30 * 60)),
        provider_backoff_seconds=tuple(
            float(value)
            for value in _number_list(
                perpetual_raw.get("provider_backoff_seconds", [5 * 60, 30 * 60, 2 * 60 * 60]),
                "perpetual.provider_backoff_seconds",
            )
        ),
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
        perpetual=perpetual,
        no_mistakes=no_mistakes,
        observability=observability,
    )


def tik_providers(tik: TikConfig) -> tuple[TikConfig, ...]:
    return tik.providers or (tik,)


def tik_provider_types(tik: TikConfig) -> set[str]:
    return {provider.provider for provider in tik_providers(tik)}


def _tik_providers_raw(tik_raw: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw = tik_raw.get("providers")
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ConfigError("tik.providers must be an array of tables")
    if not raw:
        raise ConfigError("tik.providers must contain at least one provider table when defined")
    return tuple(raw)


def _load_tik_providers(
    tik_raw: dict[str, Any],
    providers_raw: tuple[dict[str, Any], ...],
    default_prompt: str,
    verdict: VerdictConfig,
) -> tuple[TikConfig, ...]:
    top_provider = _optional_str(tik_raw, "provider") if "provider" in tik_raw else None
    defaults = {
        "provider": top_provider,
        "prompt": default_prompt,
        "model": _optional_str(tik_raw, "model"),
        "command": _optional_str(tik_raw, "command"),
        "skill": _optional_str(tik_raw, "skill"),
        "base_url": _optional_str(tik_raw, "base_url"),
        "binary": str(tik_raw.get("binary", "oracle")),
        "engine": str(tik_raw.get("engine", "browser")),
        "timeout": str(tik_raw.get("timeout", "auto")),
        "timeout_seconds": float(tik_raw.get("timeout_seconds", 1800)),
        "max_file_size_bytes": int(tik_raw.get("max_file_size_bytes", 25_000_000)),
        "max_output_tokens": int(tik_raw.get("max_output_tokens", 4096)),
        "store": _bool(tik_raw.get("store"), False, "tik.store"),
    }
    if not providers_raw:
        if top_provider is None:
            raise ConfigError("tik.provider must be defined when tik.providers is not configured")
        return (
            _load_tik_provider(
                tik_raw,
                label="tik",
                provider=top_provider,
                defaults=defaults,
                verdict=verdict,
                label_context="tik",
            ),
        )

    providers: list[TikConfig] = []
    used_labels: set[str] = set()
    for index, provider_raw in enumerate(providers_raw, start=1):
        provider = _optional_str(provider_raw, "provider") if "provider" in provider_raw else top_provider
        if provider is None:
            raise ConfigError(f"tik.providers[{index}] must define provider")
        label = _tik_provider_label(provider_raw, provider, index, used_labels)
        providers.append(
            _load_tik_provider(
                provider_raw,
                label=label,
                provider=provider,
                defaults=defaults,
                verdict=verdict,
                label_context=f"tik.providers[{index}]",
            )
        )
    return tuple(providers)


def _load_tik_provider(
    raw: dict[str, Any],
    *,
    label: str,
    provider: str,
    defaults: dict[str, Any],
    verdict: VerdictConfig,
    label_context: str,
) -> TikConfig:
    prompt = _optional_prompt_from(raw, "prompt") or str(defaults["prompt"])
    model = _optional_str(raw, "model") if "model" in raw else defaults["model"]
    if provider == "api" and model is None:
        model = DEFAULT_API_TIK_MODEL
    return TikConfig(
        provider=provider,
        prompt=prompt,
        label=label,
        model=model,
        command=_optional_str(raw, "command") if "command" in raw else defaults["command"],
        skill=_optional_str(raw, "skill") if "skill" in raw else defaults["skill"],
        base_url=_optional_str(raw, "base_url") if "base_url" in raw else defaults["base_url"],
        binary=str(raw.get("binary", defaults["binary"])),
        engine=str(raw.get("engine", defaults["engine"])),
        timeout=str(raw.get("timeout", defaults["timeout"])),
        timeout_seconds=float(raw.get("timeout_seconds", defaults["timeout_seconds"])),
        max_file_size_bytes=int(raw.get("max_file_size_bytes", defaults["max_file_size_bytes"])),
        max_output_tokens=int(raw.get("max_output_tokens", defaults["max_output_tokens"])),
        store=_bool(raw.get("store"), bool(defaults["store"]), f"{label_context}.store"),
        verdict=verdict,
    )


def _optional_prompt_from(raw: dict[str, Any], required_key: str) -> str | None:
    if "prompt" not in raw and required_key not in raw:
        return None
    return _prompt_from(raw, required_key=required_key)


def _tik_provider_label(raw: dict[str, Any], provider: str, index: int, used_labels: set[str]) -> str:
    raw_label = _optional_str(raw, "label") if "label" in raw else None
    base = _safe_tik_label(raw_label or provider)
    if base == "tik":
        base = f"tik_{index}"
    label = base
    suffix = 2
    while label in used_labels:
        label = f"{base}_{suffix}"
        suffix += 1
    used_labels.add(label)
    return label


def _safe_tik_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return label or "provider"


def analyze_config_policy(config: GoalConfig) -> ConfigPolicyReport:
    issues: list[ConfigIssue] = []
    if not _inside(config.root, config.path):
        issues.append(ConfigIssue("config.outside_root", f"config file must be inside project root: {config.path}"))
    seen_tik_labels: set[str] = set()
    for tik_provider in tik_providers(config.tik):
        label = tik_provider.label
        if label in seen_tik_labels:
            issues.append(ConfigIssue("tik.label.duplicate", f"duplicate tik provider label: {label}"))
        seen_tik_labels.add(label)
        label_prefix = "tik" if len(tik_providers(config.tik)) == 1 else f"tik.providers.{label}"
        if tik_provider.provider not in SUPPORTED_TIK_PROVIDERS:
            issues.append(ConfigIssue("tik.provider.unsupported", f"unsupported tik provider for {label_prefix}: {tik_provider.provider}"))
        if tik_provider.provider in COMMAND_TIK_PROVIDERS and not tik_provider.command:
            issues.append(ConfigIssue("tik.command.required", f"tik provider '{tik_provider.provider}' requires {label_prefix}.command"))
        if tik_provider.provider == "api" and tik_prompt_starts_with_slash_command(tik_provider.prompt):
            issues.append(
                ConfigIssue(
                    "tik.prompt.slash_unsupported",
                    f"tik provider 'api' cannot execute slash skill commands in {label_prefix}.prompt; set skill and remove the leading slash command",
                )
            )
        if tik_provider.skill:
            if tik_provider.provider != "api":
                issues.append(ConfigIssue("tik.skill.unsupported", f"{label_prefix}.skill is only supported for tik provider 'api'"))
            elif resolve_tik_skill_path(tik_provider.skill, config.root) is None:
                issues.append(ConfigIssue("tik.skill.missing", f"{label_prefix}.skill could not be resolved to a SKILL.md file: {tik_provider.skill}"))
    if config.tok.provider not in {"codex_goal", "codex_app_server", "claude_code_goal"}:
        issues.append(ConfigIssue("tok.provider.unsupported", f"unsupported tok provider: {config.tok.provider}"))
    if config.tok.provider in {"codex_goal", "codex_app_server", "claude_code_goal"} and config.tok.sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
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
    if config.perpetual.enabled:
        if config.perpetual.healthy_interval_seconds <= 0:
            issues.append(ConfigIssue("perpetual.healthy_interval_seconds.non_positive", "perpetual.healthy_interval_seconds must be positive"))
        if config.perpetual.active_interval_seconds <= 0:
            issues.append(ConfigIssue("perpetual.active_interval_seconds.non_positive", "perpetual.active_interval_seconds must be positive"))
        if not config.perpetual.provider_backoff_seconds or any(value <= 0 for value in config.perpetual.provider_backoff_seconds):
            issues.append(ConfigIssue("perpetual.provider_backoff_seconds.invalid", "perpetual.provider_backoff_seconds must contain positive values"))
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
    for tik_provider in tik_providers(config.tik):
        label = "tik" if len(tik_providers(config.tik)) == 1 else f"tik.providers.{tik_provider.label}"
        tik_unknown = template_placeholders(tik_provider.prompt) - TIK_PROMPT_PLACEHOLDERS
        for placeholder in sorted(tik_unknown):
            issues.append(f"unknown {label} prompt placeholder: {{{placeholder}}}")
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
        "tok.prompt": config.tok.prompt_template,
    }
    for tik_provider in tik_providers(config.tik):
        label = "tik.prompt" if len(tik_providers(config.tik)) == 1 else f"tik.providers.{tik_provider.label}.prompt"
        prompt_sources[label] = tik_provider.prompt
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
        "tik_providers": [
            {
                "label": provider.label,
                "provider": provider.provider,
                "model": provider.model,
                "skill": provider.skill,
                "base_url": provider.base_url,
            }
            for provider in tik_providers(config.tik)
        ],
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


def _number_list(value: Any, label: str) -> list[float | int]:
    if not isinstance(value, list) or any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in value):
        raise ConfigError(f"{label} must be an array of numbers")
    return value


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
