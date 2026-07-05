#!/usr/bin/env python3
"""Run the PDF-only data-backed APSR draft Inspect agent-runtime eval."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "evals" / "factory_e2e_apsr_pdf" / "task.py"
DEFAULT_MODEL = "openai-api/deepseek/deepseek-v4-pro"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_LOG_DIR = Path(os.environ.get("AI4SS_APSR_PDF_LOG_DIR", "/tmp/ai4ss-apsr-pdf-logs"))
DEFAULT_SUMMARY_JSON = ROOT / "docs" / "evals" / "factory-e2e-apsr-pdf" / "inspect-summary.json"
DEFAULT_SUMMARY_MD = ROOT / "docs" / "evals" / "factory-e2e-apsr-pdf" / "inspect-summary.md"
DEFAULT_CONDITIONS = ("no_skills", "full_research_factory_skills")
SECRET_ENV_NAMES = (
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "DASHSCOPE_API_KEY",
    "ALIYUN_IQS_API_KEY",
    "BROWSER_USE_API_KEY",
    "ANTHROPIC_API_KEY",
)
SECRET_TOKEN_RE = re.compile(r"\b(?:sk|ak)-[A-Za-z0-9._=-]{12,}")


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


def secret_values(env: dict[str, str]) -> list[str]:
    values = []
    for name in SECRET_ENV_NAMES:
        value = env.get(name)
        if value and len(value) >= 8:
            values.append(value)
    return sorted(set(values), key=len, reverse=True)


def redact_text(text: str, secrets: list[str]) -> str:
    redacted = text
    for value in secrets:
        redacted = redacted.replace(value, "[REDACTED_SECRET]")
    return SECRET_TOKEN_RE.sub("[REDACTED_SECRET]", redacted)


def scrub_inspect_log(log_file: Path, env: dict[str, str]) -> None:
    """Rewrite an Inspect .eval zip with API keys redacted from JSON entries."""
    secrets = secret_values(env)
    if not secrets and not SECRET_TOKEN_RE.search(log_file.name):
        return
    tmp_path = log_file.with_suffix(log_file.suffix + ".redacted")
    compression = getattr(zipfile, "ZIP_ZSTANDARD", zipfile.ZIP_DEFLATED)
    changed = False
    try:
        with zipfile.ZipFile(log_file, "r") as source, zipfile.ZipFile(tmp_path, "w", compression=compression) as target:
            for info in source.infolist():
                data = source.read(info.filename)
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    target.writestr(info.filename, data)
                    continue
                redacted = redact_text(text, secrets)
                if redacted != text:
                    changed = True
                target.writestr(info.filename, redacted.encode("utf-8"))
        if changed:
            tmp_path.replace(log_file)
        else:
            tmp_path.unlink(missing_ok=True)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        print(f"WARN could not scrub Inspect log {log_file}: {exc}", file=sys.stderr)


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


def condition_from_header(header: dict[str, Any]) -> str | None:
    eval_info = header.get("eval", {}) or {}
    if eval_info.get("task") != "factory_e2e_apsr_pdf":
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
) -> tuple[Path | None, dict[str, Any] | None]:
    logs = sorted(log_dir.glob("*.eval"), key=lambda path: path.stat().st_mtime, reverse=True)
    for log_file in logs:
        if str(log_file) in exclude_logs:
            continue
        header = inspect_log_header(inspect_cli, log_file)
        if header and condition_from_header(header) == condition:
            return log_file, header
    return None, None


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


def mean_score_from_header(header: dict[str, Any]) -> float | None:
    scores = header.get("results", {}).get("scores", []) or []
    if scores:
        metrics = scores[0].get("metrics", {}) or {}
        value = metrics.get("mean", {}).get("value") if isinstance(metrics.get("mean"), dict) else None
        if value is not None:
            return float(value)
    sample_scores = [
        float(sample["score"])
        for sample in sample_rows_from_header(header)
        if isinstance(sample.get("score"), (int, float))
    ]
    if sample_scores:
        return sum(sample_scores) / len(sample_scores)
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
        "samples": sample_rows_from_header(header),
        "model_usage": stats.get("model_usage", {}),
        "log": str(log_file) if log_file else None,
    }


def marginal_gain(results: list[dict[str, Any]]) -> dict[str, float | None]:
    by_condition = {item["condition"]: item for item in results}

    def score(condition: str) -> float | None:
        value = by_condition.get(condition, {}).get("score")
        return float(value) if isinstance(value, (int, float)) else None

    full = score("full_research_factory_skills")
    base = score("no_skills")
    return {
        "full_vs_no_skills": None if full is None or base is None else round(full - base, 4),
        "full_research_factory_skills_score": full,
        "no_skills_score": base,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Factory E2E Data-Backed APSR PDF Inspect Eval",
        "",
        f"Model: `{payload['model']}`",
        "",
        "Input shown to the agent:",
        "",
        "```text",
        "Idea: Does neighborhood service-center exposure change resident civic trust?",
        "```",
        "",
        "Only scored file: `paper/full_draft.pdf`.",
        "",
        "The PDF must visibly document public data discovery, data construction, empirical analysis, and limitations; intermediate files are not scoring evidence.",
        "",
        "| condition | status | score_100 | log |",
        "| --- | --- | ---: | --- |",
    ]
    for result in payload["results"]:
        score = "-" if result.get("score") is None else f"{float(result['score']):.1f}"
        log = result.get("log") or "-"
        lines.append(f"| `{result['condition']}` | {result.get('status')} | {score} | `{log}` |")
    lines.extend(["", "## Sample Details", "", "| condition | pdf bytes | text chars | judge note |", "| --- | ---: | ---: | --- |"])
    for result in payload["results"]:
        sample = (result.get("samples") or [{}])[0]
        metadata = sample.get("metadata") or {}
        explanation = str(sample.get("explanation") or "")
        judge_note = " ".join(explanation.strip().split())[:240] or "-"
        pdf_bytes = metadata.get("pdf_bytes", "-")
        text_chars = metadata.get("pdf_text_chars", "-")
        lines.append(f"| `{result['condition']}` | {pdf_bytes} | {text_chars} | {judge_note} |")
    lines.extend(["", "## Marginal Gain", ""])
    for key, value in payload["marginal_gain"].items():
        display = "-" if value is None else f"{float(value):.1f}"
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
            "python3 -m pip install -r evals/factory_e2e_apsr_pdf/requirements.txt"
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
        if log_file:
            scrub_inspect_log(log_file, env)
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
        "schema": "ai4ss.factory_e2e_apsr_pdf_inspect_summary.v2",
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "scoring_evidence": "paper/full_draft.pdf only; data provenance and analysis must be visible in the PDF",
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
