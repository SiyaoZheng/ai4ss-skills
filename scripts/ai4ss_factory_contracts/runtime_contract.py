"""Runtime contract checks for research data and analysis runs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import importlib.util
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

GLOB_CHARS = set("*?[")


def split_fields(values: list[str]) -> list[str]:
    fields: list[str] = []
    for value in values:
        for part in value.replace(",", ";").split(";"):
            stripped = part.strip()
            if stripped:
                fields.append(stripped)
    return fields


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        pass
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


def display_path(path: Path, cwd: Path) -> str:
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)


def resolve_input(value: str, cwd: Path) -> tuple[list[Path], list[str]]:
    problems: list[str] = []
    raw = Path(value).expanduser()
    pattern = raw if raw.is_absolute() else cwd / raw
    if any(char in value for char in GLOB_CHARS):
        matches = sorted(Path(match) for match in glob.glob(str(pattern)))
        if not matches:
            problems.append(f"glob matched no files: {value}")
        return matches, problems
    path = pattern
    if not path.exists():
        problems.append(f"path does not exist: {value}")
    return [path], problems


def check_python_imports(imports: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    problems: list[str] = []
    for module in imports:
        ok = importlib.util.find_spec(module) is not None
        checks.append({"type": "python_import", "name": module, "ok": ok})
        if not ok:
            problems.append(f"missing Python module: {module}")
    return checks, problems


def check_r_packages(packages: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    if not packages:
        return [], []
    expression = ";".join(
        f"if (!requireNamespace('{pkg}', quietly=TRUE)) stop('missing R package: {pkg}', call.=FALSE)"
        for pkg in packages
    )
    try:
        result = subprocess.run(
            ["Rscript", "--vanilla", "-e", expression],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return [
            {
                "type": "r_packages",
                "packages": packages,
                "ok": False,
                "stderr": "Rscript not found",
            }
        ], ["Rscript not found; cannot check R packages"]
    checks = [
        {
            "type": "r_packages",
            "packages": packages,
            "ok": result.returncode == 0,
            "stderr": result.stderr.strip()[-500:],
        }
    ]
    problems = [] if result.returncode == 0 else [result.stderr.strip() or "R package check failed"]
    return checks, problems


def csv_schema(path: Path) -> tuple[list[str], int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = sum(1 for _ in reader)
    return fields, rows


def parquet_schema(path: Path) -> tuple[list[str], int]:
    try:
        import polars as pl  # type: ignore

        frame = pl.read_parquet(path)
        return list(frame.columns), frame.height
    except ModuleNotFoundError:
        pass
    try:
        import pandas as pd  # type: ignore

        frame = pd.read_parquet(path)
        return list(frame.columns), int(frame.shape[0])
    except ModuleNotFoundError as exc:
        raise RuntimeError("parquet schema check requires polars or pandas with a parquet engine") from exc
    except Exception as exc:
        raise RuntimeError(f"parquet schema check failed: {exc}") from exc


def excel_schema(path: Path) -> tuple[list[str], int]:
    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("Excel schema check requires pandas and an Excel reader such as openpyxl") from exc
    try:
        frame = pd.read_excel(path, nrows=1000)
    except Exception as exc:
        raise RuntimeError(f"Excel schema check failed; verify pandas has an Excel reader installed: {exc}") from exc
    return [str(column) for column in frame.columns], int(frame.shape[0])


def data_schema(path: Path) -> tuple[list[str], int]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return csv_schema(path)
    if suffix == ".parquet":
        return parquet_schema(path)
    if suffix in {".xlsx", ".xls"}:
        return excel_schema(path)
    raise RuntimeError(f"unsupported schema check format: {path.suffix}")


def duplicate_key_count_csv(path: Path, keys: list[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = tuple(row.get(column, "") for column in keys)
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
    return duplicates


def check_schema(path: Path, required: list[str], key_columns: list[str]) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    fields, row_count = data_schema(path)
    missing = sorted(set(required) - set(fields))
    if missing:
        problems.append(f"{path}: missing required columns: {';'.join(missing)}")
    duplicate_keys: int | str | None = None
    missing_keys = sorted(set(key_columns) - set(fields))
    if missing_keys:
        problems.append(f"{path}: missing key columns: {';'.join(missing_keys)}")
    elif key_columns and path.suffix.lower() == ".csv":
        duplicate_keys = duplicate_key_count_csv(path, key_columns)
        if duplicate_keys:
            problems.append(f"{path}: duplicate key rows for {','.join(key_columns)}: {duplicate_keys}")
    elif key_columns:
        duplicate_keys = "not_checked_for_non_csv"
    return {
        "type": "schema",
        "path": str(path),
        "columns": fields,
        "row_count": row_count,
        "required_columns": required,
        "missing_columns": missing,
        "key_columns": key_columns,
        "duplicate_key_rows": duplicate_keys,
        "ok": not problems,
    }, problems


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="Project root for relative path checks.")
    parser.add_argument("--path", action="append", default=[], help="Required path or quoted glob. Repeatable.")
    parser.add_argument("--data", action="append", default=[], help="Data file whose schema should be checked.")
    parser.add_argument("--required-columns", action="append", default=[], help="Semicolon or comma separated columns.")
    parser.add_argument("--key-columns", action="append", default=[], help="Semicolon or comma separated key columns.")
    parser.add_argument("--python-import", action="append", default=[], help="Python module import to check.")
    parser.add_argument("--r-package", action="append", default=[], help="R package to check with requireNamespace.")
    parser.add_argument("--expect-output", action="append", default=[], help="Expected output file. Repeatable.")
    parser.add_argument("--fresh-after", help="Unix timestamp or ISO timestamp; expected outputs must be newer.")
    parser.add_argument("--json-output", type=Path, help="Optional path to write the JSON report.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cwd = args.cwd.expanduser().resolve()
    problems: list[str] = []
    checks: list[dict[str, Any]] = []

    try:
        fresh_after = parse_time(args.fresh_after)
    except ValueError as exc:
        fresh_after = None
        problems.append(f"invalid --fresh-after value: {args.fresh_after}: {exc}")

    requested_checks = any(
        [
            args.path,
            args.data,
            args.python_import,
            args.r_package,
            args.expect_output,
        ]
    )
    if not requested_checks:
        problems.append("no runtime contract checks requested")

    if not cwd.exists():
        problems.append(f"cwd does not exist: {cwd}")
    for value in args.path:
        matches, path_problems = resolve_input(value, cwd)
        problems.extend(path_problems)
        checks.append(
            {
                "type": "path",
                "input": value,
                "matches": [display_path(path, cwd) for path in matches if path.exists()],
                "ok": not path_problems,
            }
        )

    py_checks, py_problems = check_python_imports(args.python_import)
    checks.extend(py_checks)
    problems.extend(py_problems)

    r_checks, r_problems = check_r_packages(args.r_package)
    checks.extend(r_checks)
    problems.extend(r_problems)

    required_columns = split_fields(args.required_columns)
    key_columns = split_fields(args.key_columns)
    for value in args.data:
        paths, path_problems = resolve_input(value, cwd)
        problems.extend(path_problems)
        for path in paths:
            if not path.exists():
                continue
            try:
                check, schema_problems = check_schema(path, required_columns, key_columns)
            except Exception as exc:  # noqa: BLE001 - report exact runtime contract failure.
                check = {"type": "schema", "path": str(path), "ok": False, "error": str(exc)}
                schema_problems = [f"{path}: {exc}"]
            checks.append(check)
            problems.extend(schema_problems)

    for value in args.expect_output:
        paths, path_problems = resolve_input(value, cwd)
        problems.extend(path_problems)
        for path in paths:
            ok = path.exists()
            mtime = path.stat().st_mtime if ok else None
            fresh = ok and (fresh_after is None or mtime >= fresh_after)
            if ok and not fresh:
                problems.append(f"output is stale: {value}")
            checks.append(
                {
                    "type": "expected_output",
                    "path": display_path(path, cwd),
                    "exists": ok,
                    "mtime": mtime,
                    "fresh_after": fresh_after,
                    "ok": bool(fresh),
                }
            )

    report = {
        "status": "pass" if not problems else "fail",
        "cwd": str(cwd),
        "problems": problems,
        "checks": checks,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_output:
        json_output = args.json_output.expanduser()
        if not json_output.is_absolute():
            json_output = cwd / json_output
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not problems else 1
