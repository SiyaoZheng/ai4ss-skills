#!/usr/bin/env python3
"""Compile structured literature evidence markdown into a .aiss file."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


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
        if (candidate / "compile_evidence.py").exists():
            return candidate
    raise FileNotFoundError("cannot find ai4ss-skills dsl/scripts with compile_evidence.py")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_md", type=Path)
    parser.add_argument("output_aiss", type=Path)
    parser.add_argument("--toolchain-dir", type=Path)
    args = parser.parse_args()

    if args.output_aiss.suffix != ".aiss":
        return fail(f"{args.output_aiss}: output must use .aiss extension")
    if not args.evidence_md.exists():
        return fail(f"{args.evidence_md}: evidence markdown not found")

    try:
        toolchain = find_toolchain(args.toolchain_dir)
    except FileNotFoundError as exc:
        return fail(str(exc))

    result = subprocess.run(
        [sys.executable, str(toolchain / "compile_evidence.py"), str(args.evidence_md)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return fail(result.stderr.strip() or result.stdout.strip() or "compile_evidence.py failed")

    args.output_aiss.parent.mkdir(parents=True, exist_ok=True)
    args.output_aiss.write_text(result.stdout, encoding="utf-8")
    print(f"PASS compiled {args.evidence_md} -> {args.output_aiss}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
