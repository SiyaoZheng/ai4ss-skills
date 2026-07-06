#!/usr/bin/env python3
"""Block direct edits to generated AI4SS research outputs.

The research workflow contract is: source code and manuscript sources are
editable, derived artifacts are regenerated through Make targets.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from research_workspace_contract import (  # noqa: E402
    PAPER_GENERATED_SUFFIXES,
    PROTECTED_PATH_PREFIXES,
    WORKFLOW_STAGE_SCRIPT_STEMS,
)

PATCH_FILE_HEADER_RE = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (?P<path>.+)$"
)
MAKE_RE = re.compile(r"(?:^|[;&|]\s*)(?:env\s+\S+=\S+\s+)*(?:g?make)(?:\s|$)")
WRITE_REDIRECT_RE = re.compile(r"(?<!<)>{1,2}(?!>)")
WRITE_COMMAND_RE = re.compile(
    r"\b(?:"
    r"cat\s*>|"
    r"cp|mv|rm|touch|mkdir|install|rsync|"
    r"tee(?:\s+-a)?|"
    r"sed\b[^;&|]*\s-i|"
    r"perl\b[^;&|]*\s-pi|"
    r"dd\b[^;&|]*\bof=|"
    r"curl\b[^;&|]*\s-o\b|"
    r"wget\b[^;&|]*\s-O\b|"
    r"python3?\s+-c|"
    r"Rscript\s+-e"
    r")\b",
    re.DOTALL,
)
STAGE_SCRIPT_RE = re.compile(
    r"\b(?:python3?|Rscript|bash|sh)\s+scripts/"
    + r"(?:"
    + "|".join(re.escape(stem) for stem in WORKFLOW_STAGE_SCRIPT_STEMS)
    + r")(?:\.[A-Za-z0-9]+)?(?:\s|$)"
)
LATEXMK_RE = re.compile(r"\blatexmk\b")


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def tool_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def normalized_path(path: str) -> str:
    path = path.strip().strip("\"'")
    while path.startswith("./"):
        path = path[2:]
    return path


def is_protected_path(path: str) -> bool:
    path = normalized_path(path)
    if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES):
        return True
    if path.startswith("paper/") and path.endswith(PAPER_GENERATED_SUFFIXES):
        return True
    return False


def protected_paths_in_text(text: str) -> list[str]:
    paths: list[str] = []
    candidates = re.findall(r"(?:\./)?(?:data|output|outputs|paper)(?:/[^\s'\";|&<>]+)+", text)
    for candidate in candidates:
        cleaned = normalized_path(candidate.rstrip("),]}."))
        if is_protected_path(cleaned):
            paths.append(cleaned)
    return sorted(set(paths))


def protected_paths_in_patch(command: str) -> list[str]:
    paths: list[str] = []
    for line in command.splitlines():
        match = PATCH_FILE_HEADER_RE.match(line)
        if match and is_protected_path(match.group("path")):
            paths.append(normalized_path(match.group("path")))
    return sorted(set(paths))


def has_write_intent(command: str) -> bool:
    if WRITE_REDIRECT_RE.search(command):
        return True
    return bool(WRITE_COMMAND_RE.search(command))


def invokes_make(command: str) -> bool:
    return bool(MAKE_RE.search(command))


def direct_stage_command(command: str) -> str | None:
    if STAGE_SCRIPT_RE.search(command):
        return "run pipeline stage scripts through make, not directly"
    if LATEXMK_RE.search(command):
        return "run latexmk through the Makefile paper target"
    return None


def deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def main() -> int:
    payload = load_payload()
    event = payload.get("hook_event_name")
    if event not in (None, "PreToolUse"):
        return 0

    tool_name = payload.get("tool_name")
    command = tool_command(payload)
    if not command:
        return 0

    if tool_name == "apply_patch":
        protected = protected_paths_in_patch(command)
        if protected:
            return deny(
                "Generated AI4SS outputs must not be edited directly: "
                + ", ".join(protected)
                + ". Regenerate them through make."
            )
        return 0

    if invokes_make(command):
        return 0

    stage_reason = direct_stage_command(command)
    if stage_reason:
        return deny(f"AI4SS workflow policy: {stage_reason}. Use an explicit make target.")

    protected = protected_paths_in_text(command)
    if protected and has_write_intent(command):
        return deny(
            "Generated AI4SS outputs must not be written directly: "
            + ", ".join(protected)
            + ". Regenerate them through make."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
