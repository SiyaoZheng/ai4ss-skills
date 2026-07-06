#!/usr/bin/env python3
"""Validate AI4SS research workspace path discipline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from research_workspace_contract import (
    CANONICAL_STATE_PATH,
    CONTRACT_DOC,
    CONTRACT_TERMS,
    FORBIDDEN_LEGACY_TERMS,
    RESEARCH_FACTORY_SKILLS,
    SCAFFOLD_DIRS,
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_contract_doc(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / CONTRACT_DOC
    if not path.exists():
        return [f"{path}: missing research workspace contract"]
    body = text(path)
    for term in CONTRACT_TERMS:
        if term not in body:
            errors.append(f"{path}: missing `{term}`")
    return errors


def validate_skill_files(root: Path) -> list[str]:
    errors: list[str] = []
    for skill in RESEARCH_FACTORY_SKILLS:
        skill_dir = root / "skills" / skill
        paths = [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]
        for path in paths:
            if not path.exists():
                continue
            body = text(path)
            for forbidden in FORBIDDEN_LEGACY_TERMS:
                if forbidden in body:
                    errors.append(f"{path}: forbidden legacy workspace path `{forbidden}`")
        skill_md = skill_dir / "SKILL.md"
        body = text(skill_md)
        if CONTRACT_DOC not in body:
            errors.append(f"{skill_md}: must reference `{CONTRACT_DOC}` instead of repeating the workspace tree")
        if CANONICAL_STATE_PATH not in body:
            errors.append(f"{skill_md}: missing canonical state path `{CANONICAL_STATE_PATH}`")
    return errors


def validate_scaffold(root: Path) -> list[str]:
    errors: list[str] = []
    scaffold = root / "evals" / "factory_e2e_apsr_pdf" / "scaffold"
    if not scaffold.exists():
        return errors
    for rel in SCAFFOLD_DIRS:
        if not (scaffold / rel).exists():
            errors.append(f"{scaffold}: missing `{rel}`")
    makefile = scaffold / "Makefile"
    if makefile.exists():
        body = text(makefile)
        for term in (".ai4ss", "data/intermediate", "data/processed", "output/logs", "paper/full_draft.pdf"):
            if term not in body:
                errors.append(f"{makefile}: missing `{term}`")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()

    errors = [
        *validate_contract_doc(root),
        *validate_skill_files(root),
        *validate_scaffold(root),
    ]
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS research workspace contract validation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
