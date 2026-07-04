#!/usr/bin/env python3
"""CLI wrapper for the shared AI4SS runtime contract checker."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def add_factory_contracts_to_path() -> None:
    script_path = Path(__file__).resolve()
    candidates: list[Path] = []
    if env_root := os.environ.get("AI4SS_SKILLS_ROOT"):
        candidates.append(Path(env_root))
    candidates.extend([*script_path.parents, Path("/Users/siyaozheng/Documents/ai4ss-skills")])
    for root in candidates:
        scripts_dir = root / "scripts"
        if (scripts_dir / "ai4ss_factory_contracts").exists():
            sys.path.insert(0, str(scripts_dir))
            return


add_factory_contracts_to_path()

from ai4ss_factory_contracts.runtime_contract import main


if __name__ == "__main__":
    raise SystemExit(main())
