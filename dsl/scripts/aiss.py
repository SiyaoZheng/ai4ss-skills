#!/usr/bin/env python3
"""Unified AISS CLI.

The current implementation routes v0.3 commands to `aiss_v03.py`. Existing
v0.2 scripts remain available as legacy standalone tools.
"""

from __future__ import annotations

from aiss_v03 import main


if __name__ == "__main__":
    raise SystemExit(main())
