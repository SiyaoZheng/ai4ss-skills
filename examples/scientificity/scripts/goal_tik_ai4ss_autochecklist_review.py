#!/usr/bin/env python3
"""Goal-cli oracle tik wrapper for the AI4SS AutoChecklist reviewer."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNNER = ROOT / "scripts" / "ai4ss_autochecklist_review.py"
DEFAULT_CHECKLIST = ROOT / "docs" / "dp16276-tdd-checklist.md"


def env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default.resolve()


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    return int(value)


def build_command(artifact: Path, out_dir: Path, checklist: Path, runner: Path) -> list[str]:
    command = [
        sys.executable,
        str(runner),
        "--pdf",
        str(artifact),
        "--checklist",
        str(checklist),
        "--out-dir",
        str(out_dir),
        "--jobs",
        str(env_int("AI4SS_AUTOCHECKLIST_JOBS", 3)),
        "--max-tokens",
        str(env_int("AI4SS_AUTOCHECKLIST_MAX_TOKENS", 32768)),
        "--shim-timeout",
        str(env_int("AI4SS_AUTOCHECKLIST_SHIM_TIMEOUT", 360)),
        "--client-timeout",
        str(env_int("AI4SS_AUTOCHECKLIST_CLIENT_TIMEOUT", 420)),
        "--process-timeout",
        str(env_int("AI4SS_AUTOCHECKLIST_PROCESS_TIMEOUT", 1200)),
    ]
    model = os.environ.get("AI4SS_AUTOCHECKLIST_MODEL")
    if model:
        command.extend(["--model", model])
    if os.environ.get("AI4SS_AUTOCHECKLIST_SKIP_VISUAL") == "1":
        command.append("--skip-visual")
    if os.environ.get("AI4SS_AUTOCHECKLIST_DRY_RUN") == "1":
        command.append("--dry-run")
    for suite in os.environ.get("AI4SS_AUTOCHECKLIST_SUITES", "").split(","):
        suite = suite.strip()
        if suite:
            command.extend(["--suite", suite])
    return command


def fail_fast(message: str, code: int = 1) -> int:
    print(f"AI4SS AutoChecklist tik failed: {message}", file=sys.stderr)
    return code


def main() -> int:
    dry_run = os.environ.get("AI4SS_AUTOCHECKLIST_DRY_RUN") == "1"
    artifact = env_path("GOAL_ARTIFACT", ROOT / "output" / "scientificity-paper.pdf")
    run_dir = env_path("GOAL_RUN_DIR", ROOT / ".goal" / "manual-ai4ss-autochecklist")
    checklist = env_path("AI4SS_AUTOCHECKLIST_CHECKLIST", DEFAULT_CHECKLIST)
    runner = env_path("AI4SS_AUTOCHECKLIST_RUNNER", DEFAULT_RUNNER)
    out_dir = env_path("AI4SS_AUTOCHECKLIST_OUT_DIR", run_dir / "ai4ss-autochecklist-review")

    if not artifact.exists():
        return fail_fast(f"artifact not found: {artifact}")
    if not checklist.exists():
        return fail_fast(f"checklist not found: {checklist}")
    if not runner.exists():
        return fail_fast(f"review runner not found: {runner}")

    out_dir.mkdir(parents=True, exist_ok=True)
    command = build_command(artifact, out_dir, checklist, runner)
    process = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        print("# AI4SS AutoChecklist Review")
        print("")
        print("AutoChecklist runner failed before producing a valid goal-cli verdict.")
        print("")
        print(f"Command: `{shlex.join(command)}`")
        print("")
        if process.stdout.strip():
            print("## Runner Stdout")
            print("")
            print(process.stdout.strip())
            print("")
        if process.stderr.strip():
            print("## Runner Stderr")
            print("")
            print(process.stderr.strip())
            print("")
        return process.returncode

    manifest_path = out_dir / "manifest.json"
    if dry_run:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print("# AI4SS AutoChecklist Review Dry Run")
        print("")
        print(f"- Run dir: `{out_dir}`")
        print(f"- Checklist: `{checklist}`")
        print(f"- Suites: {len(manifest.get('suite_jobs', []))}")
        print(f"- Scored M/H items: {manifest.get('items', {}).get('scored_mh')}")
        print(f"- Reader-test items held out: {manifest.get('items', {}).get('reader_queue_r')}")
        print(f"- Dropped image-body items: {manifest.get('items', {}).get('dropped_image_items')}")
        print("")
        print("## Goal-Cli Verdict")
        print("")
        print("```json")
        print(
            json.dumps(
                {
                    "artifact_ready": False,
                    "blocking_objections": ["AI4SS AutoChecklist dry-run only"],
                    "reviewed_artifact_sha256": manifest.get("source_pdf_sha256"),
                    "current_artifact_sha256": manifest.get("source_pdf_sha256"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print("```")
        return 0

    summary_path = out_dir / "reasoned_summary.json"
    report_path = out_dir / "reasoned_fail_first_report.md"
    if not summary_path.exists():
        return fail_fast(f"summary not found after review: {summary_path}")
    if not report_path.exists():
        return fail_fast(f"report not found after review: {report_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = summary.get("items", {})
    scored = int(items.get("scored_mh") or 0)
    failed = int(items.get("fail") or 0)
    ready = scored > 0 and failed == 0
    blockers = []
    if scored <= 0:
        blockers.append("AutoChecklist produced no scored M/H items")
    for row in summary.get("suite_summaries", []):
        suite_failures = int(row.get("fail") or 0)
        if suite_failures:
            blockers.append(f"{row.get('suite', 'UNKNOWN')}: {suite_failures} failed checklist item(s)")

    print(report_path.read_text(encoding="utf-8").rstrip())
    print("")
    print("## Goal-Cli Verdict")
    print("")
    print("```json")
    print(
        json.dumps(
            {
                "artifact_ready": ready,
                "blocking_objections": blockers,
                "reviewed_artifact_sha256": manifest.get("source_pdf_sha256"),
                "current_artifact_sha256": manifest.get("source_pdf_sha256"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
