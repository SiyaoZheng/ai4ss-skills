#!/usr/bin/env python3
"""Validate a local `.aiss` research model with the unified AISS v0.4 CLI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_TERMS = (
    "aiss version \"0.4\"",
    "paper",
    "source",
    "span",
    "route",
    "mida",
    "decision",
    "attribute",
    "concept",
    "model",
)


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def candidate_tool_roots() -> list[Path]:
    roots: list[Path] = []
    env_root = os.environ.get("AI4SS_SKILLS_DIR")
    if env_root:
        roots.append(Path(env_root))
    roots.extend(
        [
            Path.cwd(),
            Path.cwd() / "ai4ss-skills",
            Path.cwd().parent / "ai4ss-skills",
            Path.cwd() / ".external" / "ai4ss-skills",
            Path("/tmp/ai4ss-skills-inspect"),
        ]
    )
    seen: set[Path] = set()
    ordered: list[Path] = []
    for root in roots:
        resolved = root.expanduser()
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(resolved)
    return ordered


def find_toolchain() -> Path | None:
    for root in candidate_tool_roots():
        scripts = root / "dsl" / "scripts"
        if (scripts / "aiss.py").exists():
            return scripts
    return None


def run_aiss(toolchain: Path, command: str, model_path: Path, *, strict: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(toolchain / "aiss.py"), command, str(model_path)]
    if strict and command in {"compile", "lint"}:
        cmd.append("--strict")
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit wrapper JSON instead of text.")
    parser.add_argument("--no-strict", action="store_true", help="Do not promote missing span provenance during lint.")
    args = parser.parse_args()

    model_path = args.model_path
    if model_path.suffix != ".aiss":
        return fail(f"{model_path}: local research models must use the .aiss extension")
    if not model_path.exists():
        return fail(f"{model_path}: file does not exist")

    text = model_path.read_text(encoding="utf-8")
    missing_terms = [term for term in REQUIRED_TERMS if term not in text]
    if missing_terms:
        return fail(f"{model_path}: missing core DSL terms: {', '.join(missing_terms)}")

    toolchain = find_toolchain()
    if toolchain is None:
        searched = ", ".join(str(path) for path in candidate_tool_roots())
        return fail(
            "could not find ai4ss-skills DSL tools; set AI4SS_SKILLS_DIR "
            f"or clone SiyaoZheng/ai4ss-skills. searched: {searched}"
        )

    strict = not args.no_strict
    compile_result = run_aiss(toolchain, "compile", model_path, strict=strict)
    lint_result = run_aiss(toolchain, "lint", model_path, strict=strict)
    run_result = run_aiss(toolchain, "run", model_path)

    lint_payload = _parse_json_or_text(lint_result.stdout)
    lint_ok = isinstance(lint_payload, dict) and bool(lint_payload.get("ok"))
    ok = compile_result.returncode == 0 and lint_result.returncode == 0 and run_result.returncode == 0 and lint_ok
    if args.json:
        payload = {
            "ok": ok,
            "model_path": str(model_path),
            "toolchain": str(toolchain),
            "compile": {
                "returncode": compile_result.returncode,
                "stdout": _parse_json_or_text(compile_result.stdout),
                "stderr": compile_result.stderr.strip(),
            },
            "lint": {
                "returncode": lint_result.returncode,
                "stdout": lint_payload,
                "stderr": lint_result.stderr.strip(),
            },
            "run": {
                "returncode": run_result.returncode,
                "stdout": _parse_json_or_text(run_result.stdout),
                "stderr": run_result.stderr.strip(),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"AI4SS model: {model_path}")
        print(f"Toolchain: {toolchain}")
        for label, result in (("compile", compile_result), ("lint", lint_result), ("run", run_result)):
            print(f"## aiss.py {label}")
            print(result.stdout.rstrip())
            if result.stderr.strip():
                print(result.stderr.rstrip(), file=sys.stderr)
        print("PASS .aiss model validation" if ok else "FAIL .aiss model validation")

    return 0 if ok else 1


def _parse_json_or_text(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text.strip()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
