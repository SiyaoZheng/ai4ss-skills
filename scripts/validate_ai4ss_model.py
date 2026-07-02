#!/usr/bin/env python3
"""Validate a local `.aiss` research model with the ai4ss-skills DSL tools.

The upstream repository still names the parser/checker modules `aiss_*`.
This wrapper makes the local contract explicit: project artifacts use the
`.aiss` extension, while the current upstream implementation supplies the
parser, checker, and bridge diagnosands.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_TERMS = ("attribute", "concept", "model")


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
        if (scripts / "aiss_checker.py").exists() and (scripts / "aiss_bridge.py").exists():
            return scripts
    return None


def run_tool(script: Path, model_path: Path, json_output: bool) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(script), str(model_path)]
    if json_output:
        cmd.append("--json")
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit wrapper JSON instead of text.")
    parser.add_argument("--skip-bridge", action="store_true", help="Skip bridge diagnosands.")
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

    checker = run_tool(toolchain / "aiss_checker.py", model_path, True)
    bridge = None if args.skip_bridge else run_tool(toolchain / "aiss_bridge.py", model_path, True)

    ok = checker.returncode == 0 and (bridge is None or bridge.returncode == 0)
    if args.json:
        payload = {
            "ok": ok,
            "model_path": str(model_path),
            "toolchain": str(toolchain),
            "checker": {
                "returncode": checker.returncode,
                "stdout": _parse_json_or_text(checker.stdout),
                "stderr": checker.stderr.strip(),
            },
            "bridge": None
            if bridge is None
            else {
                "returncode": bridge.returncode,
                "stdout": _parse_json_or_text(bridge.stdout),
                "stderr": bridge.stderr.strip(),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"AI4SS model: {model_path}")
        print(f"Toolchain: {toolchain}")
        print(checker.stdout.rstrip())
        if checker.stderr.strip():
            print(checker.stderr.rstrip(), file=sys.stderr)
        if bridge is not None:
            print(bridge.stdout.rstrip())
            if bridge.stderr.strip():
                print(bridge.stderr.rstrip(), file=sys.stderr)
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
