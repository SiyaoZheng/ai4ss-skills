#!/usr/bin/env python3
"""Run the Inspect/inspect_swe DDI agent-runtime harness eval."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "openai-api/deepseek/deepseek-v4-pro"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_LOG_DIR = Path(os.environ.get("AI4SS_INSPECT_LOG_DIR", "/tmp/ai4ss-inspect-logs"))
TASK = ROOT / "evals" / "ddi_harness" / "task.py"


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


def latest_eval_log(log_dir: Path) -> Path | None:
    logs = sorted(log_dir.glob("*.eval"), key=lambda path: path.stat().st_mtime)
    return logs[-1] if logs else None


def inspect_log_header(inspect_cli: str, log_file: Path) -> dict | None:
    result = subprocess.run(
        [inspect_cli, "log", "dump", str(log_file), "--header-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"WARN could not read Inspect log summary: {result.stderr.strip()}", file=sys.stderr)
        return None
    return json.loads(result.stdout)


def print_result_summary(header: dict, log_file: Path, summary_json: Path | None, *, judge_model: str | None) -> None:
    scores = header.get("results", {}).get("scores", [])
    reductions = header.get("reductions", [])
    results = header.get("results", {})
    stats = header.get("stats", {})
    eval_info = header.get("eval", {})
    model = header.get("eval", {}).get("model")
    score = None
    metric_name = None
    scored_samples = None
    unscored_samples = None
    samples: list[dict] = []
    if scores:
        first_score = scores[0]
        metrics = first_score.get("metrics", {}) or {}
        for candidate in ("mean", "accuracy"):
            metric = metrics.get(candidate)
            if isinstance(metric, dict) and metric.get("value") is not None:
                score = metric.get("value")
                metric_name = candidate
                break
        scored_samples = first_score.get("scored_samples")
        unscored_samples = first_score.get("unscored_samples")
    for reduction in reductions:
        for sample in reduction.get("samples", []):
            samples.append(
                {
                    "id": sample.get("sample_id") or sample.get("id"),
                    "score": sample.get("value") if "value" in sample else sample.get("score"),
                    "explanation": sample.get("explanation"),
                    "metadata": sample.get("metadata") or {},
                }
            )

    summary = {
        "status": header.get("status"),
        "model": model,
        "judge_model": judge_model or model,
        "task": eval_info.get("task"),
        "dataset": eval_info.get("dataset"),
        "total_samples": results.get("total_samples"),
        "completed_samples": results.get("completed_samples"),
        "samples_scored": scored_samples,
        "samples_unscored": unscored_samples,
        "samples_total": None
        if scored_samples is None and unscored_samples is None
        else (scored_samples or 0) + (unscored_samples or 0),
        "score": score,
        "metric": metric_name,
        "samples": samples,
        "model_usage": stats.get("model_usage", {}),
        "log": str(log_file),
    }
    print(
        "RESULT "
        f"status={summary['status']} "
        f"model={summary['model']} "
        f"judge_model={summary['judge_model']} "
        f"scored={summary['samples_scored']}/{summary['samples_total']} "
        f"{summary['metric'] or 'score'}={summary['score']} "
        f"log={summary['log']}"
    )
    for sample in samples:
        print(
            "SAMPLE "
            f"id={sample['id']} "
            f"score={sample['score']} "
            f"explanation={sample['explanation']!r}"
        )
    if summary_json:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["codex"], default="codex", help="Agent runtime. Currently only Codex CLI via inspect_swe is supported.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Inspect model. Defaults to {DEFAULT_MODEL}.")
    parser.add_argument("--judge-model", help="Optional grader model. Defaults to the same Inspect model as the agent.")
    parser.add_argument("--limit", help="Optional Inspect sample limit, e.g. 1 or 1-3. Defaults to the full dataset.")
    parser.add_argument("--retry-log", type=Path, help="Retry a previous Inspect .eval log with `inspect eval-retry` instead of starting a new run.")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR, help="Inspect log directory.")
    parser.add_argument("--summary-json", type=Path, help="Optional path for a machine-readable result summary.")
    parser.add_argument("--skip-docker-check", action="store_true", help="Skip the preflight Docker daemon check.")
    parser.add_argument("--dry-run", action="store_true", help="Print the Inspect command without running it.")
    parser.add_argument("inspect_args", nargs=argparse.REMAINDER, help="Extra args passed after `inspect eval`.")
    args = parser.parse_args()
    inspect_args = [arg for arg in args.inspect_args if arg != "--"]

    inspect_cli = shutil.which("inspect")
    if not inspect_cli and not args.dry_run:
        return fail(
            "Inspect CLI is not installed. Install the existing harness stack with: "
            "python3 -m pip install -r evals/ddi_harness/requirements.txt"
        )
    if args.retry_log:
        if not args.retry_log.exists():
            return fail(f"missing Inspect retry log: {args.retry_log}")
    elif not TASK.exists():
        return fail(f"missing Inspect task: {TASK}")
    if not args.skip_docker_check and not args.dry_run and not docker_is_ready():
        return fail("Docker is not ready. Start Docker or Colima, for example: colima start")

    env = os.environ.copy()
    if args.model.startswith("openai-api/deepseek/") and not os.environ.get("DEEPSEEK_API_KEY") and not args.dry_run:
        return fail("DEEPSEEK_API_KEY is required for the default DeepSeek Inspect provider.")
    if args.model.startswith("openai-api/deepseek/"):
        env.setdefault("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)

    args.log_dir.mkdir(parents=True, exist_ok=True)
    if args.retry_log:
        if args.limit:
            return fail("--limit cannot be used with --retry-log; retry scope is defined by the Inspect log.")
        command = [
            inspect_cli or "inspect",
            "eval-retry",
            str(args.retry_log),
            "--log-dir",
            str(args.log_dir),
            *([] if not args.judge_model else ["-T", f"judge_model={args.judge_model}"]),
            *inspect_args,
        ]
    else:
        command = [
            inspect_cli or "inspect",
            "eval",
            str(TASK.relative_to(ROOT)),
            "--model",
            args.model,
            "--log-dir",
            str(args.log_dir),
            *([] if not args.judge_model else ["-T", f"judge_model={args.judge_model}"]),
            *inspect_args,
        ]
        if args.limit:
            command.extend(["--limit", args.limit])
    print(" ".join(command))
    if args.dry_run:
        return 0
    returncode = subprocess.run(command, cwd=ROOT, env=env, check=False).returncode
    log_file = latest_eval_log(args.log_dir)
    if log_file:
        header = inspect_log_header(inspect_cli, log_file)
        if header:
            print_result_summary(header, log_file, args.summary_json, judge_model=args.judge_model)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
