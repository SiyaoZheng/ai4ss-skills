#!/usr/bin/env python3
"""Run the Inspect/inspect_swe factory relay agent-runtime eval."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "evals" / "factory_relay" / "task.py"
DEFAULT_MODEL = "openai-api/deepseek/deepseek-v4-pro"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_LOG_DIR = Path(os.environ.get("AI4SS_FACTORY_RELAY_LOG_DIR", "/tmp/ai4ss-factory-relay-logs"))
DEFAULT_SUMMARY_JSON = ROOT / "docs" / "evals" / "factory-relay" / "inspect-relay-summary.json"
DEFAULT_SUMMARY_MD = ROOT / "docs" / "evals" / "factory-relay" / "inspect-relay-summary.md"
DEFAULT_CONDITIONS = ("no_skills", "single_skill", "full_skills", "broken_handoff", "shuffled_order")


def fail(message: str) -> int:
    print(f"FAIL {message}", file=sys.stderr)
    return 1


def docker_is_ready() -> bool:
    if not shutil.which("docker"):
        return False
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def latest_eval_log(log_dir: Path, *, after: set[Path] | None = None) -> Path | None:
    logs = sorted(log_dir.glob("*.eval"), key=lambda path: path.stat().st_mtime)
    if after is not None:
        new_logs = [path for path in logs if path not in after]
        if new_logs:
            return new_logs[-1]
    return logs[-1] if logs else None


def inspect_log_header(inspect_cli: str, log_file: Path) -> dict[str, Any] | None:
    result = subprocess.run(
        [inspect_cli, "log", "dump", str(log_file), "--header-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"WARN could not read Inspect log header for {log_file}: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"WARN could not parse Inspect log header for {log_file}: {exc}", file=sys.stderr)
        return None


def sample_rows_from_header(header: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for reduction in header.get("reductions", []) or []:
        for sample in reduction.get("samples", []) or []:
            samples.append(
                {
                    "id": sample.get("sample_id") or sample.get("id"),
                    "score": sample.get("value") if "value" in sample else sample.get("score"),
                    "explanation": sample.get("explanation"),
                    "metadata": sample.get("metadata") or {},
                }
            )
    return samples


def condition_from_header(header: dict[str, Any]) -> str | None:
    eval_info = header.get("eval", {}) or {}
    if eval_info.get("task") != "factory_relay":
        return None
    task_args = eval_info.get("task_args", {}) or {}
    condition = task_args.get("condition")
    return str(condition) if condition else None


def latest_header_for_condition(
    inspect_cli: str,
    log_dir: Path,
    condition: str,
    *,
    exclude_logs: set[str],
) -> tuple[Path, dict[str, Any]] | tuple[None, None]:
    logs = sorted(log_dir.glob("*.eval"), key=lambda path: path.stat().st_mtime, reverse=True)
    for log_file in logs:
        if str(log_file) in exclude_logs:
            continue
        header = inspect_log_header(inspect_cli, log_file)
        if not header:
            continue
        if condition_from_header(header) == condition:
            return log_file, header
    return None, None


def mean_score_from_header(header: dict[str, Any]) -> float | None:
    scores = header.get("results", {}).get("scores", []) or []
    if scores:
        metrics = scores[0].get("metrics", {}) or {}
        for key in ("mean", "accuracy"):
            value = metrics.get(key, {}).get("value") if isinstance(metrics.get(key), dict) else None
            if value is not None:
                return float(value)
    samples = sample_rows_from_header(header)
    numeric_scores = [float(sample["score"]) for sample in samples if isinstance(sample.get("score"), (int, float))]
    if numeric_scores:
        return sum(numeric_scores) / len(numeric_scores)
    return None


def summarize_header(condition: str, header: dict[str, Any] | None, log_file: Path | None, returncode: int) -> dict[str, Any]:
    if not header:
        return {
            "condition": condition,
            "returncode": returncode,
            "status": "missing_header",
            "score": None,
            "log": str(log_file) if log_file else None,
            "samples": [],
        }
    eval_info = header.get("eval", {}) or {}
    results = header.get("results", {}) or {}
    stats = header.get("stats", {}) or {}
    samples = sample_rows_from_header(header)
    return {
        "condition": condition,
        "returncode": returncode,
        "status": header.get("status"),
        "model": eval_info.get("model") or header.get("eval", {}).get("model"),
        "task": eval_info.get("task"),
        "dataset": eval_info.get("dataset"),
        "total_samples": results.get("total_samples"),
        "completed_samples": results.get("completed_samples"),
        "score": mean_score_from_header(header),
        "samples": samples,
        "model_usage": stats.get("model_usage", {}),
        "log": str(log_file) if log_file else None,
    }


def marginal_gain(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition = {item["condition"]: item for item in results}

    def score(condition: str) -> float | None:
        value = by_condition.get(condition, {}).get("score")
        return float(value) if isinstance(value, (int, float)) else None

    def delta(lhs: str, rhs: str) -> float | None:
        left = score(lhs)
        right = score(rhs)
        if left is None or right is None:
            return None
        return round(left - right, 4)

    return {
        "full_vs_no_skills": delta("full_skills", "no_skills"),
        "full_vs_single_skill": delta("full_skills", "single_skill"),
        "broken_handoff_vs_no_skills": delta("broken_handoff", "no_skills"),
        "shuffled_order_vs_no_skills": delta("shuffled_order", "no_skills"),
        "full_skills_score": score("full_skills"),
        "no_skills_score": score("no_skills"),
        "single_skill_score": score("single_skill"),
        "broken_handoff_score": score("broken_handoff"),
        "shuffled_order_score": score("shuffled_order"),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Factory Relay Inspect Agent-Runtime Eval",
        "",
        f"Model: `{payload['model']}`",
        "",
        "| condition | status | score | log |",
        "| --- | --- | ---: | --- |",
    ]
    for result in payload["results"]:
        score = "-" if result.get("score") is None else f"{float(result['score']):.4f}"
        log = result.get("log") or "-"
        lines.append(f"| `{result['condition']}` | {result.get('status')} | {score} | `{log}` |")
    lines.extend(["", "## Audit Findings", "", "| condition | audit_ok | error codes |", "| --- | --- | --- |"])
    for result in payload["results"]:
        sample = (result.get("samples") or [{}])[0]
        metadata = sample.get("metadata") or {}
        audit_ok = metadata.get("audit_ok")
        errors = ", ".join(metadata.get("error_codes") or []) or "-"
        lines.append(f"| `{result['condition']}` | {audit_ok} | {errors} |")
    lines.extend(["", "## Marginal Gain", ""])
    for key, value in payload["marginal_gain"].items():
        display = "-" if value is None else f"{float(value):.4f}"
        lines.append(f"- `{key}`: {display}")
    lines.append("")
    return "\n".join(lines)


def parse_conditions(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_CONDITIONS)
    conditions = [item.strip() for item in raw.replace(",", " ").split() if item.strip()]
    invalid = [item for item in conditions if item not in DEFAULT_CONDITIONS]
    if invalid:
        raise ValueError(f"unknown condition(s): {', '.join(invalid)}")
    return conditions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["codex"], default="codex", help="Agent runtime. Currently Codex CLI via inspect_swe.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Inspect model. Defaults to {DEFAULT_MODEL}.")
    parser.add_argument("--judge-model", help="Optional grader model. Defaults to the same Inspect model as the agent.")
    parser.add_argument("--conditions", help=f"Comma/space separated subset. Defaults to: {', '.join(DEFAULT_CONDITIONS)}")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    parser.add_argument("--skip-docker-check", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print Inspect commands without running them.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop at the first non-zero Inspect run.")
    parser.add_argument("--merge-existing", action="store_true", help="Merge latest existing logs for conditions not run in this invocation.")
    parser.add_argument("--summarize-existing", action="store_true", help="Do not run Inspect; summarize latest existing logs for requested conditions.")
    parser.add_argument("inspect_args", nargs=argparse.REMAINDER, help="Extra args passed after `inspect eval`.")
    args = parser.parse_args()
    inspect_args = [arg for arg in args.inspect_args if arg != "--"]

    inspect_cli = shutil.which("inspect")
    if not inspect_cli and not args.dry_run:
        return fail(
            "Inspect CLI is not installed. Install with: "
            "python3 -m pip install -r evals/factory_relay/requirements.txt"
        )
    if not TASK.exists():
        return fail(f"missing Inspect task: {TASK}")
    if not args.skip_docker_check and not args.dry_run and not docker_is_ready():
        return fail("Docker is not ready. Start Docker or Colima, for example: colima start")
    if args.model.startswith("openai-api/deepseek/") and not os.environ.get("DEEPSEEK_API_KEY") and not args.dry_run:
        return fail("DEEPSEEK_API_KEY is required for the default DeepSeek Inspect provider.")

    try:
        conditions = parse_conditions(args.conditions)
    except ValueError as exc:
        return fail(str(exc))

    env = os.environ.copy()
    if args.model.startswith("openai-api/deepseek/"):
        env.setdefault("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    overall_returncode = 0

    if args.summarize_existing:
        for condition in conditions:
            log_file, header = latest_header_for_condition(inspect_cli or "inspect", args.log_dir, condition, exclude_logs=set())
            if log_file and header:
                results.append(summarize_header(condition, header, log_file, 0))
            else:
                results.append(
                    {
                        "condition": condition,
                        "returncode": 1,
                        "status": "missing_log",
                        "score": None,
                        "log": None,
                        "samples": [],
                    }
                )
    for condition in ([] if args.summarize_existing else conditions):
        command = [
            inspect_cli or "inspect",
            "eval",
            str(TASK.relative_to(ROOT)),
            "--model",
            args.model,
            "--log-dir",
            str(args.log_dir),
            "-T",
            f"condition={condition}",
            *([] if not args.judge_model else ["-T", f"judge_model={args.judge_model}"]),
            *inspect_args,
        ]
        print(" ".join(command))
        if args.dry_run:
            continue
        before = set(args.log_dir.glob("*.eval"))
        returncode = subprocess.run(command, cwd=ROOT, env=env, check=False).returncode
        if returncode != 0:
            overall_returncode = returncode if overall_returncode == 0 else overall_returncode
        log_file = latest_eval_log(args.log_dir, after=before)
        header = inspect_log_header(inspect_cli or "inspect", log_file) if log_file else None
        summary = summarize_header(condition, header, log_file, returncode)
        results.append(summary)
        print(
            "RESULT "
            f"condition={condition} status={summary.get('status')} "
            f"score={summary.get('score')} log={summary.get('log')}"
        )
        if args.fail_fast and returncode != 0:
            break

    if args.merge_existing and not args.dry_run:
        present = {result["condition"] for result in results}
        used_logs = {str(result.get("log")) for result in results if result.get("log")}
        for condition in DEFAULT_CONDITIONS:
            if condition in present:
                continue
            log_file, header = latest_header_for_condition(
                inspect_cli or "inspect",
                args.log_dir,
                condition,
                exclude_logs=used_logs,
            )
            if log_file and header:
                results.append(summarize_header(condition, header, log_file, 0))

    if args.dry_run:
        return 0

    payload = {
        "schema": "ai4ss.factory_relay_inspect_summary.v1",
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "conditions": conditions,
        "results": results,
        "marginal_gain": marginal_gain(results),
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"SUMMARY json={args.summary_json} markdown={args.summary_md}")
    return overall_returncode


if __name__ == "__main__":
    raise SystemExit(main())
