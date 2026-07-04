#!/usr/bin/env python3
"""Validate deterministic literature evidence compilation into .aiss."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


EXPECTED_COMPILE_STATUSES = {"compiled", "needs_review", "blocked", "not_applicable"}


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("empty file")
        required = {"paper_id", "evidence_table_path", "compiled_ai4ss_path", "evidence_compile_status"}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
        if not rows:
            raise ValueError("no data rows")
        return rows


def find_toolchain(explicit: Path | None) -> Path:
    candidates = []
    if explicit is not None:
        candidates.append(explicit)
    candidates.extend(
        [
            Path.cwd() / "dsl" / "scripts",
            Path.cwd() / "ai4ss-skills" / "dsl" / "scripts",
            Path.cwd().parent / "ai4ss-skills" / "dsl" / "scripts",
            Path.cwd() / ".external" / "ai4ss-skills" / "dsl" / "scripts",
            Path("/tmp/ai4ss-skills-inspect/dsl/scripts"),
        ]
    )
    for candidate in candidates:
        if (candidate / "compile_evidence.py").exists() and (candidate / "aiss.py").exists():
            return candidate
    raise FileNotFoundError("cannot find ai4ss-skills dsl/scripts with compile_evidence.py and aiss.py")


def resolve_path(path_text: str, csv_path: Path, repo_root: Path) -> Path | None:
    if path_text.startswith("not_applicable:"):
        return None
    raw = Path(path_text)
    candidates = [raw]
    if not raw.is_absolute():
        candidates = [repo_root / raw, Path.cwd() / raw, csv_path.parent / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def compile_evidence(toolchain: Path, evidence_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(toolchain / "compile_evidence.py"), str(evidence_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "compile_evidence.py failed")
    return result.stdout


def check_aiss(toolchain: Path, compiled_path: Path) -> str | None:
    compile_result = subprocess.run(
        [sys.executable, str(toolchain / "aiss.py"), "compile", str(compiled_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if compile_result.returncode != 0:
        return compile_result.stderr.strip() or compile_result.stdout.strip() or "aiss.py compile failed"
    lint_result = subprocess.run(
        [sys.executable, str(toolchain / "aiss.py"), "lint", str(compiled_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if lint_result.returncode != 0:
        return lint_result.stderr.strip() or lint_result.stdout.strip() or "aiss.py lint failed"
    try:
        lint_payload = json.loads(lint_result.stdout)
    except json.JSONDecodeError:
        return lint_result.stdout.strip() or "aiss.py lint returned invalid JSON"
    if not lint_payload.get("ok"):
        return lint_result.stdout.strip() or "aiss.py lint did not report ok=true"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("literature_matrix_csv", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--toolchain-dir", type=Path)
    args = parser.parse_args()

    try:
        rows = load_rows(args.literature_matrix_csv)
        toolchain = find_toolchain(args.toolchain_dir)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, FileNotFoundError) as exc:
        return fail(f"{args.literature_matrix_csv}: {exc}")

    errors: list[str] = []
    checked = 0
    for index, row in enumerate(rows, start=2):
        rid = row.get("paper_id") or f"row-{index}"
        status = row["evidence_compile_status"]
        if status not in EXPECTED_COMPILE_STATUSES:
            errors.append(f"{rid}: invalid evidence_compile_status={status}")
            continue
        evidence_path = resolve_path(row["evidence_table_path"], args.literature_matrix_csv, args.repo_root)
        compiled_path = resolve_path(row["compiled_ai4ss_path"], args.literature_matrix_csv, args.repo_root)
        if status == "compiled":
            if evidence_path is None:
                errors.append(f"{rid}: compiled row requires evidence_table_path")
                continue
            if compiled_path is None:
                errors.append(f"{rid}: compiled row requires compiled_ai4ss_path")
                continue
            if compiled_path.suffix != ".aiss":
                errors.append(f"{rid}: compiled_ai4ss_path must end with .aiss")
                continue
            try:
                generated = compile_evidence(toolchain, evidence_path)
                saved = compiled_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError, RuntimeError) as exc:
                errors.append(f"{rid}: {exc}")
                continue
            if generated != saved:
                errors.append(f"{rid}: compiled_ai4ss_path does not match deterministic compile_evidence.py output")
                continue
            check_error = check_aiss(toolchain, compiled_path)
            if check_error:
                errors.append(f"{rid}: compiled_ai4ss_path failed aiss.py validation: {check_error}")
                continue
            checked += 1
        elif status == "not_applicable":
            if not row["evidence_table_path"].startswith("not_applicable:"):
                errors.append(f"{rid}: not_applicable status requires evidence_table_path=not_applicable:<reason>")
            if not row["compiled_ai4ss_path"].startswith("not_applicable:"):
                errors.append(f"{rid}: not_applicable status requires compiled_ai4ss_path=not_applicable:<reason>")
        elif status in {"needs_review", "blocked"}:
            if row["compiled_ai4ss_path"].endswith(".aiss"):
                errors.append(f"{rid}: {status} rows must not point to a ready compiled .aiss artifact")

    if errors:
        return fail(f"{args.literature_matrix_csv}: {'; '.join(errors[:10])}")

    print(f"PASS {args.literature_matrix_csv}: {checked} compiled evidence rows match ai4ss-skills")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
