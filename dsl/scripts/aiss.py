#!/usr/bin/env python3
"""Unified AISS CLI.

The current implementation routes unified v0.4 commands to `aiss_unified.py`.
This is the only DSL entrypoint used by the research-factory skillpack.
"""

from __future__ import annotations

from aiss_unified import main


if __name__ == "__main__":
    raise SystemExit(main())
