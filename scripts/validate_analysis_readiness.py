#!/usr/bin/env python3
"""Run the research-analysis-runner analysis-readiness validator."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


VALIDATOR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "research-analysis-runner"
    / "scripts"
    / "validate_analysis_readiness.py"
)


if __name__ == "__main__":
    if not VALIDATOR.exists():
        print(f"FAIL missing validator: {VALIDATOR}")
        raise SystemExit(1)
    sys.argv[0] = str(VALIDATOR)
    runpy.run_path(str(VALIDATOR), run_name="__main__")
