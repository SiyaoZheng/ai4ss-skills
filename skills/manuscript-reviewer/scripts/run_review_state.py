#!/usr/bin/env python3
"""Create a stateless manuscript checklist review snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from parse_dp16276_checklist import parse_checklist_file


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKLIST_JSON = SCRIPT_DIR.parent / "assets" / "checklists" / "dp16276-tdd-checklist.json"
DEFAULT_MODEL = "claude-fable-5"
DEFAULT_PROVIDER = "openai"
DEFAULT_BASE_URL = "https://www.packyapi.com/v1"
DEFAULT_API_KEY_ENV = "PACKYCODE_CODEX_KEY"
DEFAULT_API_FORMAT = "chat"
DEFAULT_BACKEND = "cli"
DEFAULT_SCORER_MODE = "item"

ROUTE_BY_SUITE = {
    "RQ": "study-design-builder",
    "TITLE": "academic-writing-scaffold",
    "ABS": "academic-writing-scaffold",
    "INTRO": "academic-writing-scaffold",
    "LIT": "literature-matrix",
    "DATA": "research-data-builder",
    "ID": "methods-reviewer",
    "RES": "analysis-explainer",
    "TAB": "latex-tables",
    "FIG": "top-journal-figures",
    "CONC": "academic-writing-scaffold",
    "CITE": "literature-matrix",
    "APP": "academic-writing-scaffold",
    "STY": "academic-writing-scaffold",
    "FMT": "academic-writing-scaffold",
    "REV": "academic-writing-scaffold",
    "FINAL": "academic-writing-scaffold",
}
ROUTE_PRIORITY = [
    "DATA",
    "ID",
    "RES",
    "TAB",
    "FIG",
    "LIT",
    "CITE",
    "RQ",
    "ABS",
    "INTRO",
    "CONC",
    "TITLE",
    "APP",
    "STY",
    "FMT",
    "REV",
    "FINAL",
]

BATCH_PROMPT = """You are an evidence-constrained checklist scorer for a social-science manuscript.

Use only the explicit INPUT metadata and TARGET manuscript text below. Ignore
conversation history, memory, previous reviews, outside knowledge about the
project, and unstated assumptions.

Answer YES only when the manuscript itself visibly satisfies the criterion.
Answer NO when the criterion is absent, unclear, contradicted, merely implied,
or would require reader-test evidence that is not supplied.

INPUT:
{input}

TARGET:
{target}

CHECKLIST:
{checklist}
"""

ITEM_PROMPT = """You are an evidence-constrained checklist scorer for a social-science manuscript.

Use only the explicit INPUT metadata and TARGET manuscript text below. Ignore
conversation history, memory, previous reviews, outside knowledge about the
project, and unstated assumptions.

Answer YES only when the manuscript itself visibly satisfies the criterion.
Answer NO when the criterion is absent, unclear, contradicted, merely implied,
or would require reader-test evidence that is not supplied.

INPUT:
{input}

TARGET:
{target}

QUESTION:
{question}
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_pdf(path: Path) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("PDF input requires `pdftotext`; convert the PDF to text or install poppler.")
    proc = subprocess.run(
        [executable, str(path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )
    return proc.stdout


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_data = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_data)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        parts = [node.text or "" for node in para.findall(".//w:t", ns)]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def read_manuscript(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(path), "pdftotext"
    if suffix == ".docx":
        return read_docx(path), "docx-xml"
    if suffix in {".md", ".markdown", ".txt", ".tex", ".rst"}:
        return read_text_file(path), "text"
    return read_text_file(path), "text-fallback"


def load_checklist(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if "items" not in data:
            raise ValueError(f"{path} is not a structured checklist JSON file")
        return data
    return parse_checklist_file(path)


def load_reader_evidence(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("reader evidence must be a JSON object keyed by checklist item id")
    normalized: dict[str, dict[str, Any]] = {}
    for item_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"reader evidence for {item_id} must be an object")
        status = str(value.get("status", "")).upper()
        if status not in {"PASS", "FAIL"}:
            raise ValueError(f"reader evidence for {item_id} must have status PASS or FAIL")
        normalized[str(item_id)] = {**value, "status": status}
    return normalized


def parse_suite_filter(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    values = {part.strip().upper() for part in raw.split(",") if part.strip()}
    return values or None


def selected_by_suite(item: dict[str, Any], suite_filter: set[str] | None) -> bool:
    if suite_filter is None:
        return True
    return str(item["suite_code"]).upper() in suite_filter or str(item["suite_number"]) in suite_filter


def item_route(item: dict[str, Any]) -> str:
    return ROUTE_BY_SUITE.get(str(item["suite_code"]).upper(), "academic-writing-scaffold")


def item_base(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "suite_number": item["suite_number"],
        "suite_code": item["suite_code"],
        "suite_name": item["suite_name"],
        "section": item.get("section"),
        "verification_tag": item["verification"],
        "assertion": item["assertion"],
        "question": item["question"],
        "source_line": item.get("source_line"),
        "next_skill_route": item_route(item),
    }


def score_answer_value(answer: Any) -> str:
    value = getattr(answer, "value", answer)
    return str(value).lower()


def run_autochecklist(
    items: list[dict[str, Any]],
    manuscript_text: str,
    input_metadata: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if args.backend == "cli":
        return run_autochecklist_cli(items, manuscript_text, input_metadata, args)
    return run_autochecklist_api(items, manuscript_text, input_metadata, args)


def packyapi_error_message(parsed: dict[str, Any] | None, body: str) -> str:
    if isinstance(parsed, dict):
        error = parsed.get("error", parsed)
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if parsed.get("message"):
            return str(parsed["message"])
    return body.strip()


def transform_autochecklist_request(body: dict[str, Any]) -> dict[str, Any]:
    messages = body.get("messages") or []
    system_parts: list[str] = []
    forwarded_messages: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        content = str(message.get("content") or "")
        if role == "system":
            system_parts.append(content)
        else:
            forwarded_messages.append({"role": role, "content": content})

    if not forwarded_messages:
        forwarded_messages.append({"role": "user", "content": ""})

    payload: dict[str, Any] = {
        "model": body.get("model") or DEFAULT_MODEL,
        "messages": forwarded_messages,
    }
    if system_parts:
        payload["system"] = "\n\n".join(part for part in system_parts if part)

    max_tokens = body.get("max_tokens") or body.get("max_completion_tokens")
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    # PackyAPI Fable rejects AutoChecklist's structured-output and temperature
    # parameters. The AutoChecklist prompt already contains the JSON schema
    # instruction, so the shim strips provider-incompatible transport fields.
    return payload


class PackyAPIFableShim:
    """Local OpenAI-compatible shim used only as AutoChecklist CLI base_url."""

    def __init__(self, target_base_url: str, api_key: str, timeout: int) -> None:
        self.target_base_url = target_base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.base_url: str | None = None

    def start(self) -> str:
        shim = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format: str, *args: Any) -> None:  # noqa: A002
                return

            def send_json(self, status: int, payload: dict[str, Any]) -> None:
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def proxy_get(self, path: str) -> None:
                request = urllib.request.Request(
                    f"{shim.target_base_url}{path}",
                    headers={"Authorization": f"Bearer {shim.api_key}"},
                )
                with urllib.request.urlopen(request, timeout=shim.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="replace"))
                self.send_json(response.status, payload)

            def do_GET(self) -> None:
                try:
                    if self.path.endswith("/models"):
                        self.proxy_get("/models")
                    else:
                        self.send_json(404, {"error": {"message": f"unsupported path: {self.path}"}})
                except Exception as exc:  # noqa: BLE001 - server should return JSON errors to the CLI.
                    self.send_json(502, {"error": {"message": str(exc)}})

            def do_POST(self) -> None:
                try:
                    if not self.path.endswith("/chat/completions"):
                        self.send_json(404, {"error": {"message": f"unsupported path: {self.path}"}})
                        return
                    content_length = int(self.headers.get("Content-Length", "0"))
                    raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
                    incoming = json.loads(raw_body)
                    payload = transform_autochecklist_request(incoming)
                    response_payload = self.forward_chat(payload)
                    self.send_json(200, response_payload)
                except urllib.error.HTTPError as exc:
                    body_text = exc.read().decode("utf-8", errors="replace")
                    try:
                        body = json.loads(body_text)
                    except json.JSONDecodeError:
                        body = {"error": {"message": body_text}}
                    self.send_json(exc.code, body)
                except Exception as exc:  # noqa: BLE001 - server should return JSON errors to the CLI.
                    self.send_json(502, {"error": {"message": str(exc)}})

            def forward_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                last_error: Exception | None = None
                for attempt in range(3):
                    request = urllib.request.Request(
                        f"{shim.target_base_url}/chat/completions",
                        data=data,
                        headers={
                            "Authorization": f"Bearer {shim.api_key}",
                            "Content-Type": "application/json",
                        },
                    )
                    try:
                        with urllib.request.urlopen(request, timeout=shim.timeout) as response:
                            return json.loads(response.read().decode("utf-8", errors="replace"))
                    except urllib.error.HTTPError:
                        raise
                    except Exception as exc:  # noqa: BLE001 - transient network failures are retried.
                        last_error = exc
                        if attempt < 2:
                            time.sleep(1.5 * (attempt + 1))
                raise RuntimeError(f"PackyAPI request failed after retries: {last_error}")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        return self.base_url

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)


def autochecklist_model_items(items: list[dict[str, Any]]) -> list[Any]:
    try:
        from autochecklist import ChecklistItem
    except ImportError as exc:
        raise RuntimeError(
            "AutoChecklist is not installed in this Python environment. "
            "Install it with `python3 -m pip install autochecklist`, or run with `--mode scaffold`."
        ) from exc

    return [
        ChecklistItem(
            id=item["id"],
            question=item["question"],
            category=item["suite_code"],
            metadata={
                "suite_number": item["suite_number"],
                "suite_name": item["suite_name"],
                "verification_tag": item["verification"],
                "source_line": item.get("source_line"),
            },
        )
        for item in items
    ]


def autochecklist_model(items: list[dict[str, Any]], input_metadata: str) -> Any:
    try:
        from autochecklist import Checklist
    except ImportError as exc:
        raise RuntimeError(
            "AutoChecklist is not installed in this Python environment. "
            "Install it with `python3 -m pip install autochecklist`, or run with `--mode scaffold`."
        ) from exc

    checklist_items = autochecklist_model_items(items)
    checklist = Checklist(
        id=f"dp16276_{sha256_text(json.dumps([item['id'] for item in items], sort_keys=True))[:12]}",
        items=checklist_items,
        source_method="dp16276_tdd_fixed",
        generation_level="corpus",
        input=input_metadata,
        metadata={"ai4ss_wrapper": "manuscript-reviewer"},
    )
    return checklist


def run_autochecklist_api(
    items: list[dict[str, Any]],
    manuscript_text: str,
    input_metadata: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    try:
        from autochecklist import ChecklistScorer
    except ImportError as exc:
        raise RuntimeError(
            "AutoChecklist is not installed in this Python environment. "
            "Install it with `python3 -m pip install autochecklist`, or run with `--mode scaffold`."
        ) from exc

    checklist = autochecklist_model(items, input_metadata)
    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            raise RuntimeError(f"requested API key environment variable is not set: {args.api_key_env}")
    custom_prompt = BATCH_PROMPT if args.scorer_mode == "batch" else ITEM_PROMPT
    scorer = ChecklistScorer(
        mode=args.scorer_mode,
        capture_reasoning=args.capture_reasoning,
        primary_metric=args.primary_metric,
        model=args.model,
        provider=args.provider,
        base_url=args.base_url,
        api_key=api_key,
        api_format=args.api_format,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        custom_prompt=custom_prompt,
    )
    score = scorer.score(checklist, target=manuscript_text, input=input_metadata)
    score_payload = score.model_dump(mode="json")
    score_payload["pass_rate"] = score.pass_rate
    score_payload["primary_score"] = score.primary_score
    score_payload["scaled_score_1_5"] = score.scaled_score_1_5
    return score_payload


def provider_env_key(provider: str | None) -> str:
    if provider == "openrouter":
        return "OPENROUTER_API_KEY"
    if provider == "openai":
        return "OPENAI_API_KEY"
    return "API_KEY"


def should_use_packyapi_cli_shim(args: argparse.Namespace) -> bool:
    return (
        bool(args.cli_packyapi_shim)
        and args.backend == "cli"
        and args.provider == "openai"
        and "packyapi.com" in str(args.base_url)
        and str(args.model).startswith("claude-fable")
    )


def run_autochecklist_cli(
    items: list[dict[str, Any]],
    manuscript_text: str,
    input_metadata: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    executable = shutil.which("autochecklist")
    if not executable:
        raise RuntimeError(
            "AutoChecklist CLI is not available. Install it with "
            "`python3 -m pip install autochecklist`, or run with `--backend api`."
        )

    checklist = autochecklist_model(items, input_metadata)
    scorer_prompt = BATCH_PROMPT if args.scorer_mode == "batch" else ITEM_PROMPT
    env = os.environ.copy()
    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            raise RuntimeError(f"requested API key environment variable is not set: {args.api_key_env}")
        env[provider_env_key(args.provider)] = api_key
        env[args.api_key_env] = api_key

    use_shim = should_use_packyapi_cli_shim(args)
    shim: PackyAPIFableShim | None = None
    command_base_url = args.base_url
    if use_shim:
        if not api_key:
            raise RuntimeError("PackyAPI Fable CLI shim requires --api-key-env")
        shim = PackyAPIFableShim(args.base_url, api_key, args.cli_timeout)
        command_base_url = shim.start()

    with tempfile.TemporaryDirectory(prefix="ai4ss-autochecklist-") as tmp:
        try:
            tmp_path = Path(tmp)
            checklist_path = tmp_path / "checklist.json"
            data_path = tmp_path / "data.jsonl"
            output_path = tmp_path / "scores.jsonl"
            prompt_path = tmp_path / "scorer_prompt.md"
            checklist.save(str(checklist_path))
            data_path.write_text(
                json.dumps({"input": input_metadata, "target": manuscript_text}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            prompt_path.write_text(scorer_prompt, encoding="utf-8")
            command = [
                executable,
                "score",
                "--checklist",
                str(checklist_path),
                "--data",
                str(data_path),
                "--output",
                str(output_path),
                "--overwrite",
                "--scorer",
                args.scorer_mode,
                "--scorer-model",
                args.model,
                "--provider",
                args.provider,
                "--scorer-prompt",
                str(prompt_path),
                "--input-key",
                "input",
                "--target-key",
                "target",
            ]
            if command_base_url:
                command.extend(["--base-url", command_base_url])
            if args.api_format:
                command.extend(["--api-format", args.api_format])

            proc = subprocess.run(
                command,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=args.cli_timeout,
            )
            if proc.returncode != 0:
                stderr = proc.stderr.strip() or proc.stdout.strip()
                raise RuntimeError(f"AutoChecklist CLI failed with exit {proc.returncode}: {stderr}")
            if not output_path.exists():
                raise RuntimeError("AutoChecklist CLI completed without writing an output JSONL file")
            records = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if len(records) != 1:
                raise RuntimeError(f"expected exactly one AutoChecklist CLI output record, got {len(records)}")
            record = records[0]
        finally:
            if shim is not None:
                shim.stop()

    pass_rate = record.get("pass_rate")
    return {
        "checklist_id": checklist.id,
        "judge_model": args.model,
        "scoring_method": f"cli:{args.scorer_mode}",
        "cli_adapter": "packyapi_fable_shim" if use_shim else None,
        "primary_score": pass_rate,
        "pass_rate": pass_rate,
        "weighted_score": record.get("weighted_score"),
        "normalized_score": record.get("normalized_score"),
        "item_scores": record.get("item_scores", []),
    }


def choose_next_route(items: list[dict[str, Any]]) -> str:
    failed = [item for item in items if item["status"] == "FAIL"]
    if not failed:
        return "none"
    priority = {suite: index for index, suite in enumerate(ROUTE_PRIORITY)}
    failed.sort(key=lambda item: (priority.get(str(item["suite_code"]).upper(), 999), item["id"]))
    return failed[0]["next_skill_route"]


def suite_counts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    suite_names: dict[str, str] = {}
    suite_numbers: dict[str, int] = {}
    for item in items:
        code = str(item["suite_code"])
        grouped[code][item["status"]] += 1
        suite_names[code] = item["suite_name"]
        suite_numbers[code] = item["suite_number"]

    rows = []
    for code in sorted(grouped, key=lambda value: suite_numbers[value]):
        row = {
            "suite_number": suite_numbers[code],
            "suite_code": code,
            "suite_name": suite_names[code],
            "counts": dict(sorted(grouped[code].items())),
        }
        rows.append(row)
    return rows


def write_markdown_report(state: dict[str, Any], path: Path) -> None:
    summary = state["summary"]
    manifest = state["manifest"]
    fail_items = [item for item in state["items"] if item["status"] == "FAIL"][:25]
    reader_items = [item for item in state["items"] if item["status"] == "REQUIRES_READER"][:25]

    lines = [
        "# Manuscript Review Snapshot",
        "",
        f"- Review id: `{state['review_id']}`",
        f"- Mode: `{manifest['config']['mode']}`",
        f"- Manuscript: `{manifest['manuscript']['path']}`",
        f"- Checklist: `{manifest['checklist']['path']}`",
        f"- Manuscript hash: `{manifest['manuscript']['sha256']}`",
        f"- Checklist hash: `{manifest['checklist']['sha256']}`",
        f"- Config hash: `{manifest['config_sha256']}`",
        f"- Next skill route: `{summary['next_skill_route']}`",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(summary["counts_by_status"].items()):
        lines.append(f"| {status} | {count} |")

    lines.extend(["", "## Fail First", ""])
    if fail_items:
        lines.extend(["| Item | Suite | Route | Assertion |", "|---|---|---|---|"])
        for item in fail_items:
            assertion = item["assertion"].replace("|", "\\|")
            lines.append(
                f"| `{item['id']}` | `{item['suite_code']}` | `{item['next_skill_route']}` | {assertion} |"
            )
    else:
        lines.append("No FAIL items in the selected automated scope.")

    lines.extend(["", "## Reader-Test Queue", ""])
    if reader_items:
        lines.extend(["| Item | Suite | Assertion |", "|---|---|---|"])
        for item in reader_items:
            assertion = item["assertion"].replace("|", "\\|")
            lines.append(f"| `{item['id']}` | `{item['suite_code']}` | {assertion} |")
    else:
        lines.append("No pending reader-test items in the selected scope.")

    lines.extend(["", "## Suite Summary", "", "| Suite | Counts |", "|---|---|"])
    for row in state["suite_summary"]:
        counts = ", ".join(f"{key}: {value}" for key, value in row["counts"].items())
        lines.append(f"| `{row['suite_code']}` {row['suite_name']} | {counts} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_state(args: argparse.Namespace) -> dict[str, Any]:
    manuscript_path = args.manuscript.resolve()
    checklist_path = args.checklist.resolve()
    reader_evidence_path = args.reader_evidence.resolve() if args.reader_evidence else None

    manuscript_bytes = manuscript_path.read_bytes()
    checklist_bytes = checklist_path.read_bytes()
    reader_evidence = load_reader_evidence(reader_evidence_path)

    manuscript_text, extractor = read_manuscript(manuscript_path)
    truncated = False
    if args.max_chars and len(manuscript_text) > args.max_chars:
        manuscript_text = manuscript_text[: args.max_chars]
        truncated = True

    checklist_data = load_checklist(checklist_path)
    suite_filter = parse_suite_filter(args.suites)
    selected_items = [item for item in checklist_data["items"] if selected_by_suite(item, suite_filter)]
    if args.max_items is not None:
        selected_items = selected_items[: args.max_items]

    config = {
        "mode": args.mode,
        "backend": args.backend,
        "suites": sorted(suite_filter) if suite_filter else None,
        "max_items": args.max_items,
        "max_chars": args.max_chars,
        "scorer_mode": args.scorer_mode,
        "capture_reasoning": args.capture_reasoning,
        "primary_metric": args.primary_metric,
        "model": args.model,
        "provider": args.provider,
        "base_url": args.base_url,
        "cli_packyapi_shim": args.cli_packyapi_shim,
        "api_key_env": args.api_key_env,
        "api_key_env_set": bool(os.environ.get(args.api_key_env)) if args.api_key_env else None,
        "api_format": args.api_format,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "reasoning_effort": args.reasoning_effort,
        "cli_timeout": args.cli_timeout,
        "reader_evidence_sha256": sha256_bytes(reader_evidence_path.read_bytes()) if reader_evidence_path else None,
        "ai4ss_model_path": str(args.ai4ss_model.resolve()) if args.ai4ss_model else None,
    }
    config_sha = sha256_text(json.dumps(config, sort_keys=True, ensure_ascii=False))
    manuscript_sha = sha256_bytes(manuscript_bytes)
    checklist_sha = sha256_bytes(checklist_bytes)
    review_id = sha256_text(f"{manuscript_sha}:{checklist_sha}:{config_sha}")[:16]

    input_metadata = json.dumps(
        {
            "review_id": review_id,
            "manuscript_path": str(manuscript_path),
            "checklist_path": str(checklist_path),
            "conversation_context_used": False,
            "reader_evidence_item_ids": sorted(reader_evidence),
            "ai4ss_model_path": str(args.ai4ss_model.resolve()) if args.ai4ss_model else None,
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    scored_candidates = [
        item for item in selected_items if item["verification"] != "R" and item["id"] not in reader_evidence
    ]
    autochecklist_scores: dict[str, dict[str, Any]] = {}
    scorer_metadata: dict[str, Any] = {}
    if args.mode == "autochecklist" and scored_candidates:
        raw_score = run_autochecklist(scored_candidates, manuscript_text, input_metadata, args)
        scorer_metadata = {
            "checklist_id": raw_score.get("checklist_id"),
            "judge_model": raw_score.get("judge_model"),
            "scoring_method": raw_score.get("scoring_method"),
            "cli_adapter": raw_score.get("cli_adapter"),
            "primary_score": raw_score.get("primary_score"),
            "pass_rate": raw_score.get("pass_rate"),
            "weighted_score": raw_score.get("weighted_score"),
            "normalized_score": raw_score.get("normalized_score"),
        }
        for item_score in raw_score.get("item_scores", []):
            autochecklist_scores[item_score["item_id"]] = item_score

    output_items: list[dict[str, Any]] = []
    for item in selected_items:
        row = item_base(item)
        item_id = item["id"]
        if item_id in reader_evidence:
            evidence = reader_evidence[item_id]
            row.update(
                {
                    "status": evidence["status"],
                    "evidence_status": "reader_evidence",
                    "reader_evidence": evidence,
                }
            )
        elif item["verification"] == "R":
            row.update(
                {
                    "status": "REQUIRES_READER",
                    "evidence_status": "reader_required",
                }
            )
        elif args.mode == "scaffold":
            row.update(
                {
                    "status": "NEEDS_EVIDENCE",
                    "evidence_status": "not_scored",
                }
            )
        else:
            item_score = autochecklist_scores.get(item_id)
            if not item_score:
                row.update(
                    {
                        "status": "ERROR",
                        "evidence_status": "missing_scorer_output",
                    }
                )
            else:
                answer = score_answer_value(item_score.get("answer"))
                row.update(
                    {
                        "status": "PASS" if answer == "yes" else "FAIL",
                        "answer": answer,
                        "reasoning": item_score.get("reasoning"),
                        "confidence": item_score.get("confidence"),
                        "confidence_level": item_score.get("confidence_level"),
                        "evidence_status": "llm_observation",
                    }
                )
        output_items.append(row)

    status_counts = Counter(item["status"] for item in output_items)
    next_route = choose_next_route(output_items)
    return {
        "schema": "ai4ss.manuscript_review_state.v0.1",
        "state_kind": "stateless_snapshot",
        "review_id": review_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "conversation_context_used": False,
        "manifest": {
            "manuscript": {
                "path": str(manuscript_path),
                "sha256": manuscript_sha,
                "bytes": len(manuscript_bytes),
                "extractor": extractor,
                "text_chars_used": len(manuscript_text),
                "truncated": truncated,
            },
            "checklist": {
                "path": str(checklist_path),
                "sha256": checklist_sha,
                "bytes": len(checklist_bytes),
                "schema": checklist_data.get("schema"),
                "counts": checklist_data.get("counts"),
            },
            "config": config,
            "config_sha256": config_sha,
        },
        "scorer_metadata": scorer_metadata,
        "summary": {
            "selected_items": len(output_items),
            "counts_by_status": dict(sorted(status_counts.items())),
            "next_skill_route": next_route,
        },
        "suite_summary": suite_counts(output_items),
        "items": output_items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""\
            Default checklist JSON:
              {DEFAULT_CHECKLIST_JSON}
            """
        ),
    )
    parser.add_argument("--manuscript", required=True, type=Path, help="Manuscript file (.md, .txt, .tex, .pdf, .docx).")
    parser.add_argument("--checklist", type=Path, default=DEFAULT_CHECKLIST_JSON, help="Checklist Markdown or structured JSON.")
    parser.add_argument("--outdir", required=True, type=Path, help="Directory for review_state.json and fail_first_report.md.")
    parser.add_argument("--mode", choices=("scaffold", "autochecklist"), default="scaffold")
    parser.add_argument("--backend", choices=("cli", "api"), default=DEFAULT_BACKEND, help="Scoring backend for --mode autochecklist.")
    parser.add_argument("--suites", help="Comma-separated suite codes or numbers, for example INTRO,ABS or 4,3.")
    parser.add_argument("--max-items", type=int, help="Limit selected items, mainly for smoke tests.")
    parser.add_argument("--max-chars", type=int, default=120_000, help="Max manuscript characters sent to scorer.")
    parser.add_argument("--reader-evidence", type=Path, help="Optional reader evidence JSON keyed by item id.")
    parser.add_argument("--ai4ss-model", type=Path, help="Optional .aiss path recorded for downstream handoff metadata.")
    parser.add_argument("--scorer-mode", choices=("batch", "item"), default=DEFAULT_SCORER_MODE)
    parser.add_argument("--capture-reasoning", action="store_true")
    parser.add_argument("--primary-metric", choices=("pass", "weighted", "normalized"), default="pass")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV, help="Environment variable name for the API key; the value is never written.")
    parser.add_argument("--api-format", default=DEFAULT_API_FORMAT)
    parser.add_argument(
        "--no-cli-packyapi-shim",
        dest="cli_packyapi_shim",
        action="store_false",
        help="Disable the local AutoChecklist-CLI-to-PackyAPI Fable compatibility shim.",
    )
    parser.set_defaults(cli_packyapi_shim=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--cli-timeout", type=int, default=300, help="Seconds before a scorer HTTP or AutoChecklist CLI run times out.")
    args = parser.parse_args(argv)

    try:
        state = build_state(args)
        args.outdir.mkdir(parents=True, exist_ok=True)
        state_path = args.outdir / "review_state.json"
        report_path = args.outdir / "fail_first_report.md"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_markdown_report(state, report_path)
    except Exception as exc:  # noqa: BLE001 - CLI should surface all operational failures.
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    summary = state["summary"]
    print(
        f"PASS review_id={state['review_id']} items={summary['selected_items']} "
        f"counts={summary['counts_by_status']} next_skill_route={summary['next_skill_route']}"
    )
    print(f"WROTE {state_path}")
    print(f"WROTE {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
