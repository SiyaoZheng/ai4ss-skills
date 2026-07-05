#!/usr/bin/env python3
"""Fail if the draft PDF reports forbidden synthetic empirical data."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PATTERNS = (
    re.compile(r"\bsynthetic\s+(?:data|dataset|sample|observations?|records?|panel|microdata)\b", re.I),
    re.compile(r"\bsimulated\s+(?:data|dataset|sample|observations?|records?|panel|microdata)\b", re.I),
    re.compile(r"\bhypothetical\s+(?:data|dataset|sample|observations?|records?|panel|microdata)\b", re.I),
    re.compile(r"\billustrative\s+(?:data|dataset|sample|observations?|records?|panel|microdata)\b", re.I),
    re.compile(r"\bdata[- ]generating process\b", re.I),
    re.compile(r"\bDGP\b"),
    re.compile(r"\bconstructed from published parameter(?: estimates| benchmarks)?\b", re.I),
    re.compile(r"\bpublished parameter (?:estimates|benchmarks)\b", re.I),
    re.compile(r"\bparameters? (?:chosen|calibrated) to reproduce published\b", re.I),
    re.compile(r"\brandom(?:ly)? generated (?:data|dataset|observations?|records?|sample)\b", re.I),
)


def pdf_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdftotext failed for {path}")
    return result.stdout


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "paper/full_draft.pdf")
    text = pdf_text(path)
    for pattern in PATTERNS:
        match = pattern.search(text)
        if match:
            print(f"Forbidden synthetic-data evidence in {path}: {match.group(0)}", file=sys.stderr)
            return 1
    print(f"Real observed data contract check passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
