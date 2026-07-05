#!/usr/bin/env python3
"""Parse the DP16276 paper-writing TDD checklist into structured JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SUITE_RE = re.compile(
    r"^## Suite\s+(?P<number>\d+)\s+[-—]\s+(?P<code>[^：:]+)[：:](?P<name>.+?)\s*$"
)
SUBHEADING_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
ITEM_RE = re.compile(
    r"^- \[[ xX]?\]\s+\*\*(?P<item_id>[A-Za-z0-9_-]+)\*\*\s+"
    r"(?P<assertion>.*?)\s*\((?P<verification>[MHR])\)\s*$"
)
GUIDE_RE = re.compile(r"（(?P<guide>指南[^）]+)）\s*$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_assertion(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip()


def suite_name_and_guide(raw_name: str) -> tuple[str, str | None]:
    raw_name = raw_name.strip()
    match = GUIDE_RE.search(raw_name)
    if not match:
        return raw_name, None
    guide_ref = match.group("guide")
    return GUIDE_RE.sub("", raw_name).strip(), guide_ref


def parse_checklist_text(text: str, source: str | None = None, source_sha256: str | None = None) -> dict[str, Any]:
    suites: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    current_suite: dict[str, Any] | None = None
    current_section: str | None = None
    parse_errors: list[str] = []

    for line_number, line in enumerate(text.splitlines(), 1):
        suite_match = SUITE_RE.match(line)
        if suite_match:
            suite_name, guide_ref = suite_name_and_guide(suite_match.group("name"))
            current_suite = {
                "suite_number": int(suite_match.group("number")),
                "suite_code": suite_match.group("code").strip(),
                "suite_name": suite_name,
                "guide_ref": guide_ref,
                "item_count": 0,
            }
            suites.append(current_suite)
            current_section = None
            continue

        subheading_match = SUBHEADING_RE.match(line)
        if subheading_match:
            current_section = subheading_match.group("title").strip()
            continue

        if line.startswith("- [ ] **") or line.startswith("- [x] **") or line.startswith("- [X] **"):
            item_match = ITEM_RE.match(line)
            if not item_match:
                parse_errors.append(f"line {line_number}: could not parse checklist item: {line}")
                continue
            if current_suite is None:
                parse_errors.append(f"line {line_number}: checklist item appears before any suite")
                continue

            assertion = normalize_assertion(item_match.group("assertion"))
            item = {
                "id": item_match.group("item_id").strip(),
                "suite_number": current_suite["suite_number"],
                "suite_code": current_suite["suite_code"],
                "suite_name": current_suite["suite_name"],
                "guide_ref": current_suite["guide_ref"],
                "section": current_section,
                "assertion": assertion,
                "question": f"稿件是否满足：{assertion}",
                "verification": item_match.group("verification"),
                "source_line": line_number,
            }
            items.append(item)
            current_suite["item_count"] += 1

    if parse_errors:
        raise ValueError("\n".join(parse_errors))

    verification_counts = Counter(item["verification"] for item in items)
    return {
        "schema": "ai4ss.dp16276_checklist.v0.1",
        "source": source,
        "source_sha256": source_sha256,
        "counts": {
            "suites": len(suites),
            "items": len(items),
            "by_verification": dict(sorted(verification_counts.items())),
        },
        "suites": suites,
        "items": items,
    }


def parse_checklist_file(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    return parse_checklist_text(text, source=str(path.resolve()), source_sha256=sha256_bytes(data))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklist", type=Path, help="Path to the DP16276 TDD checklist Markdown file.")
    parser.add_argument("-o", "--output", type=Path, help="Write structured JSON to this path.")
    parser.add_argument("--expect-items", type=int, help="Fail if the parsed item count differs.")
    args = parser.parse_args(argv)

    try:
        parsed = parse_checklist_file(args.checklist)
    except Exception as exc:  # noqa: BLE001 - CLI should emit a readable parser failure.
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    if args.expect_items is not None and parsed["counts"]["items"] != args.expect_items:
        print(
            f"ERROR expected {args.expect_items} items, parsed {parsed['counts']['items']}",
            file=sys.stderr,
        )
        return 3

    rendered = json.dumps(parsed, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    counts = parsed["counts"]
    print(
        f"PASS parsed {counts['items']} items across {counts['suites']} suites: "
        f"{counts['by_verification']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
