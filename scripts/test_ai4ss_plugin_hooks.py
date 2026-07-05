#!/usr/bin/env python3
"""Regression tests for AI4SS Codex plugin hooks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "guard_generated_outputs.py"


def run_hook(payload: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"hook exited {proc.returncode}: {proc.stderr}")
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def bash_payload(command: str) -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def patch_payload(command: str) -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": command},
    }


def denied(result: dict[str, Any]) -> bool:
    output = result.get("hookSpecificOutput")
    return isinstance(output, dict) and output.get("permissionDecision") == "deny"


def assert_denied(payload: dict[str, Any]) -> None:
    result = run_hook(payload)
    if not denied(result):
        raise AssertionError(f"expected denial, got {result!r}")


def assert_allowed(payload: dict[str, Any]) -> None:
    result = run_hook(payload)
    if result:
        raise AssertionError(f"expected allow, got {result!r}")


def main() -> int:
    assert_allowed(bash_payload("make all"))
    assert_allowed(bash_payload("pdftotext paper/full_draft.pdf - | head"))
    assert_allowed(
        patch_payload(
            "*** Begin Patch\n"
            "*** Update File: paper/full_draft.tex\n"
            "@@\n"
            "-old\n"
            "+new\n"
            "*** End Patch\n"
        )
    )
    assert_allowed(
        patch_payload(
            "*** Begin Patch\n"
            "*** Add File: .ai4ss/research_model.aiss\n"
            "+route project.r1 {\n"
            "+}\n"
            "*** End Patch\n"
        )
    )

    assert_denied(bash_payload("python3 scripts/build_tables.py > output/tables/main.tex"))
    assert_denied(bash_payload("mkdir -p data/intermediate && touch data/intermediate/panel.csv"))
    assert_denied(bash_payload("mkdir -p output/audit && touch output/audit/sample_flow.csv"))
    assert_denied(bash_payload("mkdir -p outputs && touch outputs/data_inventory.md"))
    assert_denied(bash_payload("mkdir -p data/interim && touch data/interim/source_inventory.csv"))
    assert_denied(bash_payload("mkdir -p data/analysis && touch data/analysis/panel.csv"))
    assert_denied(bash_payload("Rscript scripts/run_analysis.R"))
    assert_denied(bash_payload("latexmk paper/full_draft.tex"))
    assert_denied(
        patch_payload(
            "*** Begin Patch\n"
            "*** Add File: output/tables/main.tex\n"
            "+table\n"
            "*** End Patch\n"
        )
    )
    assert_denied(
        patch_payload(
            "*** Begin Patch\n"
            "*** Update File: paper/full_draft.pdf\n"
            "@@\n"
            "-old\n"
            "+new\n"
            "*** End Patch\n"
        )
    )

    print("PASS AI4SS plugin hook tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
