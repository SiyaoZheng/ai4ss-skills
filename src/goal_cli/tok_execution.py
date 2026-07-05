from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters import run_command_logged
from .config import TokConfig


TOK_REPORT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "goal-cli tok report",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "source_change_possible",
        "revision_strategy",
        "sources_changed",
        "expected_artifact_visible_improvement",
        "remaining_artifact_bottleneck",
    ],
    "properties": {
        "source_change_possible": {"type": "boolean"},
        "revision_strategy": {"type": "string", "minLength": 1},
        "sources_changed": {"type": "array", "items": {"type": "string"}},
        "expected_artifact_visible_improvement": {"type": "array", "items": {"type": "string"}},
        "remaining_artifact_bottleneck": {"type": "string"},
    },
}


@dataclass(frozen=True)
class TokExecutionPlan:
    command: tuple[str, ...]
    cwd: Path
    prompt: str
    report_path: Path
    schema_path: Path
    prompt_path: Path
    provider_prompt_path: Path
    log_path: Path
    validation_log_path: Path


@dataclass(frozen=True)
class TokExecutionResult:
    ok: bool
    report_path: Path | None
    report: dict[str, Any] | None
    errors: tuple[str, ...]
    plan: TokExecutionPlan | None = None

    @property
    def detail(self) -> str:
        return "; ".join(self.errors) if self.errors else "tok report ok"


def execute_tok(config: TokConfig, prompt: str, run_dir: Path, timeout_seconds: float | None = None) -> TokExecutionResult:
    if config.provider != "codex_goal":
        raise ValueError(f"unsupported tok provider: {config.provider}")

    run_dir.mkdir(parents=True, exist_ok=True)
    if not config.write_dirs:
        failed_path = run_dir / "tok_FAILED.txt"
        failed_path.write_text("tok.write_dirs is empty\n", encoding="utf-8")
        return TokExecutionResult(False, None, None, ("tok.write_dirs is empty",))

    plan = build_codex_goal_tok_plan(config, prompt, run_dir)
    plan.prompt_path.write_text(prompt, encoding="utf-8")
    plan.schema_path.write_text(json.dumps(TOK_REPORT_SCHEMA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plan.provider_prompt_path.write_text(plan.prompt, encoding="utf-8")

    ok = run_command_logged(list(plan.command), plan.cwd, plan.log_path, plan.prompt, timeout_seconds=timeout_seconds)
    if not ok:
        return TokExecutionResult(False, None, None, ("tok provider failed",), plan)
    if not plan.report_path.exists():
        return TokExecutionResult(False, None, None, ("tok report was not written",), plan)

    report = read_tok_report(plan.report_path)
    errors = tuple(tok_report_errors(report))
    if errors:
        plan.validation_log_path.write_text("\n".join(errors) + "\n", encoding="utf-8")
        return TokExecutionResult(False, None, report, errors, plan)

    plan.validation_log_path.write_text("tok report ok\n", encoding="utf-8")
    return TokExecutionResult(True, plan.report_path, report, (), plan)


def build_codex_goal_tok_plan(config: TokConfig, prompt: str, run_dir: Path) -> TokExecutionPlan:
    final_prompt = _codex_goal_prompt(prompt)
    schema_path = run_dir / "tok_report.schema.json"
    output_path = run_dir / "tok_report.json"
    command = [
        "codex",
        "exec",
        "-C",
        str(config.write_dirs[0]),
        "--skip-git-repo-check",
        "--sandbox",
        config.sandbox,
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
    ]
    enabled_features = list(config.codex_features)
    if "goals" not in enabled_features:
        enabled_features.append("goals")
    for feature in enabled_features:
        command.extend(["--enable", feature])
    if config.model:
        command.extend(["-m", config.model])
    for write_dir in config.write_dirs[1:]:
        command.extend(["--add-dir", str(write_dir)])
    command.append("-")
    return TokExecutionPlan(
        command=tuple(command),
        cwd=config.write_dirs[0],
        prompt=final_prompt,
        report_path=output_path,
        schema_path=schema_path,
        prompt_path=run_dir / "tok_prompt.md",
        provider_prompt_path=run_dir / "tok_codex_goal_prompt.md",
        log_path=run_dir / "tok_codex.log",
        validation_log_path=run_dir / "tok_report_validation.log",
    )


def read_tok_report(report_path: Path) -> dict[str, Any] | None:
    return _parse_json_object(report_path.read_text(encoding="utf-8"))


def tok_report_errors(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return ["tok report is not parseable JSON object"]
    errors: list[str] = []
    allowed = set(TOK_REPORT_SCHEMA["properties"])
    missing = [field for field in TOK_REPORT_SCHEMA["required"] if field not in report]
    for field in missing:
        errors.append(f"tok report missing required field: {field}")
    extra = sorted(set(report) - allowed)
    for field in extra:
        errors.append(f"tok report contains unsupported field: {field}")
    if "source_change_possible" in report and not isinstance(report["source_change_possible"], bool):
        errors.append("source_change_possible must be boolean")
    for field in ("revision_strategy", "remaining_artifact_bottleneck"):
        if field in report and (not isinstance(report[field], str) or not report[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    for field in ("sources_changed", "expected_artifact_visible_improvement"):
        if field in report and not _is_string_list(report[field]):
            errors.append(f"{field} must be a list of strings")
    if report.get("source_change_possible") is True and report.get("sources_changed") == []:
        errors.append("sources_changed must be non-empty when source_change_possible is true")
    return errors


def _codex_goal_prompt(prompt: str) -> str:
    return (
        "/goal\n"
        "Run this as an internal Codex goal. The goal is complete only when the next "
        "canonical artifact produced by the configured producer can pass tik. "
        "Within this session, make one bounded source revision inside the writable scopes, "
        "record what changed as JSON matching the provided schema, and stop. Do not treat the tok report as completion; "
        "completion is reserved for a later tik pass.\n\n"
        f"{prompt}"
    )


def _parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)
