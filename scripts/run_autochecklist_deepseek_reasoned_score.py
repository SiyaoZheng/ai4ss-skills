#!/usr/bin/env python3
"""Run AutoChecklist scoring with per-item reasoning through the DeepSeek shim.

This is a thin runner for AutoChecklist's Python API. The upstream CLI exposes
the registered scorers but not the ``capture_reasoning`` constructor option, so
this script keeps AutoChecklist as the scoring engine and only supplies the
missing argument explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from autochecklist import Checklist
from autochecklist.providers.http_client import LLMHTTPClient
from autochecklist.scorers.base import ChecklistScorer

from autochecklist_deepseek_pro_max import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    DeepSeekProMaxShim,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a checklist with AutoChecklist capture_reasoning enabled."
    )
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--checklist", required=True, type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--input-key", default="input")
    parser.add_argument("--target-key", default="target")
    parser.add_argument("--mode", choices=["batch", "item"], default="batch")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("DEEPSEEK_SHIM_TIMEOUT", "300")))
    parser.add_argument(
        "--client-timeout",
        type=int,
        default=int(os.environ.get("AUTOCHECKLIST_CLIENT_TIMEOUT", "360")),
        help="Seconds for AutoChecklist's HTTP client to wait for the local shim.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: DEEPSEEK_API_KEY is not set")

    checklist = Checklist.load(str(args.checklist))
    records = read_jsonl(args.data)
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    reasoning_effort = os.environ.get("DEEPSEEK_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)
    structured_mode = os.environ.get("DEEPSEEK_STRUCTURED_MODE", "strict_tool")

    shim = DeepSeekProMaxShim(base_url, api_key, args.timeout, reasoning_effort, structured_mode)
    shim_url = shim.start()
    client = LLMHTTPClient(
        provider="openai",
        api_key=api_key,
        base_url=shim_url,
        timeout=args.client_timeout,
        api_format="chat",
    )
    try:
        scorer = ChecklistScorer(
            mode=args.mode,
            capture_reasoning=True,
            model=args.model,
            client=client,
            api_format="chat",
            max_tokens=args.max_tokens,
            reasoning_effort=reasoning_effort,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as fh:
            for record in records:
                score = scorer.score(
                    checklist,
                    target=record.get(args.target_key, ""),
                    input=record.get(args.input_key),
                )
                payload = {
                    args.input_key: record.get(args.input_key),
                    args.target_key: record.get(args.target_key),
                    **score.model_dump(mode="json"),
                    "pass_rate": score.pass_rate,
                    "primary_score": score.primary_score,
                }
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        print(f"Results written to: {args.output}")
        return 0
    finally:
        client.close()
        shim.stop()


if __name__ == "__main__":
    raise SystemExit(main())
