#!/usr/bin/env python3
"""One-click AI4SS manuscript review with AutoChecklist and DeepSeek.

This is intentionally a CLI workflow, not a Codex skill. Each run is a fresh
snapshot: it extracts the current PDF, builds checklists from the supplied
Markdown file, sends only that snapshot to AutoChecklist, and writes immutable
run artifacts under the output directory.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "run_autochecklist_deepseek_reasoned_score.py"

DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_VISUAL_SUITES = {"FMT", "TAB", "APP"}
DEFAULT_DROPPED_IMAGE_ITEM_IDS = {
    "FIG-001",
    "FIG-002",
    "FIG-003",
    "FIG-004",
    "FIG-005",
    "FIG-006",
    "FIG-007",
    "FIG-008",
    "FIG-009",
}
DEFAULT_VISUAL_KEYWORDS = [
    "图",
    "表",
    "figure",
    "fig.",
    "table",
    "appendix",
    "附录",
    "notes",
    "dependent variable",
    "standard error",
    "coefficient",
    "legend",
    "axis",
    "plot",
    "heatmap",
    "randomization",
    "event study",
]

SUITE_RE = re.compile(
    r"^## Suite\s+(?P<number>\d+)\s+[-—]\s+(?P<code>[^：:]+)[：:](?P<name>.+?)\s*$"
)
SUBHEADING_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
ITEM_RE = re.compile(
    r"^- \[[ xX]?\]\s+\*\*(?P<item_id>[A-Za-z0-9_-]+)\*\*\s+"
    r"(?P<assertion>.*?)\s*\((?P<verification>[MHR])\)\s*$"
)
GUIDE_RE = re.compile(r"（(?P<guide>指南[^）]+)）\s*$")

TEXT_LIMITED_RE = re.compile(
    r"(not visible|cannot verify|not provided|provided text|text-only|"
    r"visual|figure itself|actual figure|actual table|PDF|image|axis|legend)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ToolPaths:
    pdftotext: str
    pdfinfo: str | None
    pdftocairo: str | None
    pdftohtml: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def run_command(
    command: list[str],
    *,
    timeout: int = 180,
    cwd: Path | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        cwd=str(cwd) if cwd else None,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


def require_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"ERROR: required executable not found on PATH: {name}")
    return found


def optional_tool(name: str) -> str | None:
    return shutil.which(name)


def discover_tools(skip_visual: bool) -> ToolPaths:
    pdftotext = require_tool("pdftotext")
    pdfinfo = optional_tool("pdfinfo")
    pdftocairo = None if skip_visual else optional_tool("pdftocairo")
    pdftohtml = None if skip_visual else optional_tool("pdftohtml")
    return ToolPaths(
        pdftotext=pdftotext,
        pdfinfo=pdfinfo,
        pdftocairo=pdftocairo,
        pdftohtml=pdftohtml,
    )


def normalize_assertion(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().rstrip()


def suite_name_and_guide(raw_name: str) -> tuple[str, str | None]:
    raw_name = raw_name.strip()
    match = GUIDE_RE.search(raw_name)
    if not match:
        return raw_name, None
    return GUIDE_RE.sub("", raw_name).strip(), match.group("guide")


def parse_checklist_markdown(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    suites: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    current_suite: dict[str, Any] | None = None
    current_section: str | None = None
    errors: list[str] = []

    for line_number, line in enumerate(text.splitlines(), 1):
        suite_match = SUITE_RE.match(line)
        if suite_match:
            suite_name, guide_ref = suite_name_and_guide(suite_match.group("name"))
            current_suite = {
                "suite_number": int(suite_match.group("number")),
                "suite_code": suite_match.group("code").strip().upper(),
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
                errors.append(f"line {line_number}: could not parse checklist item: {line}")
                continue
            if current_suite is None:
                errors.append(f"line {line_number}: checklist item appears before any suite")
                continue
            assertion = normalize_assertion(item_match.group("assertion"))
            verification = item_match.group("verification")
            question = (
                "Does the manuscript itself visibly satisfy this checklist criterion? "
                f"Criterion ({verification}): {assertion}"
            )
            item = {
                "id": item_match.group("item_id").strip(),
                "suite_number": current_suite["suite_number"],
                "suite_code": current_suite["suite_code"],
                "suite_name": current_suite["suite_name"],
                "guide_ref": current_suite["guide_ref"],
                "section": current_section,
                "assertion": assertion,
                "question": question,
                "verification": verification,
                "source_line": line_number,
            }
            items.append(item)
            current_suite["item_count"] += 1

    if errors:
        raise SystemExit("ERROR parsing checklist:\n" + "\n".join(errors))

    counts = Counter(item["verification"] for item in items)
    return {
        "schema": "ai4ss.dp16276_autochecklist_review.v1",
        "source": str(path.resolve()),
        "source_sha256": sha256_bytes(data),
        "counts": {
            "suites": len(suites),
            "items": len(items),
            "by_verification": dict(sorted(counts.items())),
        },
        "suites": suites,
        "items": items,
    }


def extract_pdf_text(pdf: Path, tools: ToolPaths, out_dir: Path) -> tuple[str, str]:
    text_path = out_dir / "manuscript.txt"
    proc = run_command([tools.pdftotext, str(pdf), "-"], timeout=180)
    text = proc.stdout
    text_path.write_text(text, encoding="utf-8")
    return text, str(text_path)


def extract_pdf_layout_text(pdf: Path, tools: ToolPaths, out_dir: Path) -> list[str]:
    layout_path = out_dir / "manuscript-layout.txt"
    proc = run_command([tools.pdftotext, "-layout", str(pdf), "-"], timeout=180)
    layout = proc.stdout
    layout_path.write_text(layout, encoding="utf-8")
    pages = layout.split("\f")
    return [page.rstrip() for page in pages if page.strip()]


def pdf_page_count(pdf: Path, tools: ToolPaths, layout_pages: list[str]) -> int:
    if tools.pdfinfo:
        try:
            proc = run_command([tools.pdfinfo, str(pdf)], timeout=60)
            match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, re.MULTILINE)
            if match:
                return int(match.group(1))
        except Exception:
            pass
    return len(layout_pages)


def select_visual_pages(layout_pages: list[str], page_count: int, limit: int) -> list[int]:
    selected: list[int] = []
    lowered_keywords = [keyword.lower() for keyword in DEFAULT_VISUAL_KEYWORDS]
    for index in range(1, page_count + 1):
        page_text = layout_pages[index - 1] if index - 1 < len(layout_pages) else ""
        lowered = page_text.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            selected.append(index)

    if not selected:
        selected = list(range(1, min(page_count, limit) + 1))
    elif len(selected) < min(page_count, limit):
        for index in range(1, page_count + 1):
            if index not in selected:
                selected.append(index)
            if len(selected) >= min(page_count, limit):
                break
    return sorted(selected[:limit])


def convert_svg_pages(pdf: Path, tools: ToolPaths, pages: list[int], out_dir: Path) -> list[Path]:
    if not tools.pdftocairo:
        return []
    svg_dir = out_dir / "svg_pages"
    svg_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for page in pages:
        output = svg_dir / f"page-{page:03d}.svg"
        run_command(
            [tools.pdftocairo, "-svg", "-f", str(page), "-l", str(page), str(pdf), str(output)],
            timeout=120,
        )
        if output.exists():
            paths.append(output)
    return paths


def svg_stats(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    viewbox_match = re.search(r'viewBox="([^"]+)"', text)
    image_tags: list[dict[str, str]] = []
    for match in re.finditer(r"<image\b(?P<attrs>[^>]*)>", text):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group("attrs")))
        attrs.pop("href", None)
        attrs.pop("xlink:href", None)
        image_tags.append(attrs)
        if len(image_tags) >= 5:
            break
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "viewBox": viewbox_match.group(1) if viewbox_match else None,
        "path_elements": text.count("<path"),
        "image_elements": text.count("<image"),
        "image_tags": image_tags,
        "text_elements": text.count("<text"),
        "use_elements": text.count("<use"),
    }


def extract_positioned_xml(pdf: Path, tools: ToolPaths, pages: list[int], out_dir: Path) -> Path | None:
    if not tools.pdftohtml or not pages:
        return None
    xml_dir = out_dir / "positioned_text"
    xml_dir.mkdir(parents=True, exist_ok=True)
    prefix = xml_dir / "pages"
    first = min(pages)
    last = max(pages)
    run_command(
        [tools.pdftohtml, "-xml", "-hidden", "-f", str(first), "-l", str(last), str(pdf), str(prefix)],
        timeout=180,
    )
    xml_path = prefix.with_suffix(".xml")
    return xml_path if xml_path.exists() else None


def parse_positioned_text(xml_path: Path | None, pages: set[int], max_chars_per_page: int) -> dict[int, str]:
    if xml_path is None or not xml_path.exists():
        return {}
    try:
        root = ElementTree.parse(xml_path).getroot()
    except ElementTree.ParseError:
        return {}

    positioned: dict[int, str] = {}
    for page in root.findall("page"):
        number_raw = page.get("number")
        if not number_raw:
            continue
        number = int(number_raw)
        if number not in pages:
            continue
        header = f"Page {number} positioned text, canvas {page.get('width')} x {page.get('height')}:"
        rows: list[tuple[int, int, str]] = []
        for node in page.findall("text"):
            text = "".join(node.itertext()).strip()
            if not text:
                continue
            try:
                top = int(float(node.get("top") or 0))
                left = int(float(node.get("left") or 0))
            except ValueError:
                top, left = 0, 0
            rows.append((top, left, text))
        rows.sort(key=lambda item: (item[0], item[1]))
        lines = [header]
        for top, left, text in rows:
            lines.append(f"[top={top:04d}, left={left:04d}] {text}")
            if sum(len(line) + 1 for line in lines) >= max_chars_per_page:
                lines.append("[truncated]")
                break
        positioned[number] = "\n".join(lines)
    return positioned


def compact_layout_page(page_number: int, text: str, max_chars: int) -> str:
    stripped = text.strip()
    if len(stripped) > max_chars:
        stripped = stripped[:max_chars].rstrip() + "\n[truncated]"
    return f"Page {page_number} layout text:\n{stripped}"


def build_visual_supplement(
    pdf: Path,
    tools: ToolPaths,
    out_dir: Path,
    layout_pages: list[str],
    page_count: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if args.skip_visual:
        return {
            "enabled": False,
            "reason": "disabled by --skip-visual",
            "text": "",
            "pages": [],
            "svg_pages": [],
        }

    pages = select_visual_pages(layout_pages, page_count, args.max_visual_pages)
    svg_paths = convert_svg_pages(pdf, tools, pages, out_dir)
    svg_by_page: dict[int, dict[str, Any]] = {}
    for path in svg_paths:
        match = re.search(r"page-(\d+)\.svg$", path.name)
        if match:
            svg_by_page[int(match.group(1))] = svg_stats(path)

    xml_path = extract_positioned_xml(pdf, tools, pages, out_dir)
    positioned = parse_positioned_text(xml_path, set(pages), args.max_positioned_chars_per_page)

    supplement_lines = [
        "VISUAL SUPPLEMENT",
        "This supplement is derived from the same PDF snapshot. Use it for table, figure, appendix, and formatting checks.",
        "SVG pages were generated with pdftocairo. Full SVG artifacts are saved on disk; compact page stats and positioned text are inlined below.",
        f"PDF: {pdf}",
        f"Visual pages included: {', '.join(str(page) for page in pages)}",
        "",
        "SVG page inventory:",
    ]
    for page in pages:
        stats = svg_by_page.get(page)
        if stats:
            image_tag_text = ""
            if stats.get("image_tags"):
                image_tag_text = f"; image_tags={json.dumps(stats['image_tags'], ensure_ascii=False)}"
            supplement_lines.append(
                "- Page {page}: {path}; bytes={bytes}; viewBox={viewBox}; "
                "paths={path_elements}; images={image_elements}; text={text_elements}; uses={use_elements}{image_tag_text}".format(
                    page=page,
                    image_tag_text=image_tag_text,
                    **stats,
                )
            )
        else:
            supplement_lines.append(f"- Page {page}: SVG unavailable")

    supplement_lines.append("")
    supplement_lines.append("Positioned page text and layout excerpts:")
    for page in pages:
        if page in positioned:
            supplement_lines.append(positioned[page])
        elif page - 1 < len(layout_pages):
            supplement_lines.append(compact_layout_page(page, layout_pages[page - 1], args.max_layout_chars_per_page))

    text = "\n\n".join(supplement_lines)
    visual_path = out_dir / "visual_supplement.txt"
    visual_path.write_text(text, encoding="utf-8")
    return {
        "enabled": True,
        "pages": pages,
        "visual_supplement_path": str(visual_path),
        "positioned_xml": str(xml_path) if xml_path else None,
        "svg_pages": [str(path) for path in svg_paths],
        "svg_stats": [svg_by_page[page] for page in pages if page in svg_by_page],
        "text": text,
    }


def make_autochecklist(items: list[dict[str, Any]], checklist_id: str, input_context: str) -> dict[str, Any]:
    return {
        "id": checklist_id,
        "items": [
            {
                "id": item["id"],
                "question": item["question"],
                "weight": 100.0,
                "category": item["suite_code"],
                "metadata": {
                    "id": item["id"],
                    "assertion": item["assertion"],
                    "verification": item["verification"],
                    "suite_number": item["suite_number"],
                    "suite_code": item["suite_code"],
                    "suite_name": item["suite_name"],
                    "section": item.get("section"),
                    "source_line": item.get("source_line"),
                    "question": item["question"],
                },
            }
            for item in items
        ],
        "source_method": "dp16276-tdd-manual-checklist",
        "generation_level": "corpus",
        "input": input_context,
        "metadata": {
            "scoring_scope": "M/H items only; R items held out for reader tests",
            "stateless": True,
        },
    }


def grouped_by_suite(items: list[dict[str, Any]]) -> OrderedDict[str, list[dict[str, Any]]]:
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for item in items:
        groups.setdefault(item["suite_code"], []).append(item)
    return groups


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_input_context(pdf: Path, checklist: Path, visual_enabled: bool) -> str:
    return "\n".join(
        [
            "AI4SS stateless manuscript review.",
            "Use only the supplied PDF-derived target text and visual supplement.",
            "Ignore conversation history, memory, previous reviews, and outside project knowledge.",
            "Answer YES only when the manuscript visibly satisfies the criterion in this snapshot.",
            "Answer NO when evidence is absent, unclear, contradicted, or requires reader-test evidence.",
            "Reader-test (R) criteria are held out and must not be inferred.",
            "For visual suites, use the SVG-derived visual supplement and positioned text when provided.",
            f"PDF path: {pdf}",
            f"Checklist path: {checklist}",
            f"Visual supplement enabled: {visual_enabled}",
        ]
    )


def prepare_run(args: argparse.Namespace) -> dict[str, Any]:
    pdf = args.pdf.expanduser().resolve()
    checklist_path = args.checklist.expanduser().resolve()
    if not pdf.exists():
        raise SystemExit(f"ERROR: PDF not found: {pdf}")
    if not checklist_path.exists():
        raise SystemExit(f"ERROR: checklist not found: {checklist_path}")
    if not RUNNER.exists():
        raise SystemExit(f"ERROR: scoring runner not found: {RUNNER}")

    tools = discover_tools(args.skip_visual)
    out_dir = args.out_dir
    if out_dir is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = Path("/tmp") / f"ai4ss-autochecklist-review-{stamp}"
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_checklist_markdown(checklist_path)
    suite_filter = {suite.upper() for suite in args.suite} if args.suite else None
    selected = [
        item
        for item in parsed["items"]
        if suite_filter is None or item["suite_code"] in suite_filter or str(item["suite_number"]) in suite_filter
    ]
    dropped_image_items: list[dict[str, Any]] = []
    if not args.keep_image_items:
        kept: list[dict[str, Any]] = []
        for item in selected:
            if item["id"] in DEFAULT_DROPPED_IMAGE_ITEM_IDS:
                dropped_image_items.append(item)
            else:
                kept.append(item)
        selected = kept
    scored_items = [item for item in selected if item["verification"] in {"M", "H"}]
    reader_items = [item for item in selected if item["verification"] == "R"]

    text, text_path = extract_pdf_text(pdf, tools, out_dir)
    layout_pages = extract_pdf_layout_text(pdf, tools, out_dir)
    pages = pdf_page_count(pdf, tools, layout_pages)
    visual = build_visual_supplement(pdf, tools, out_dir, layout_pages, pages, args)
    input_context = build_input_context(pdf, checklist_path, bool(visual["enabled"]))

    write_json(out_dir / "parsed_checklist.json", parsed)
    write_json(out_dir / "reader_queue.json", {"count": len(reader_items), "items": reader_items})
    write_json(
        out_dir / "dropped_image_items.json",
        {
            "count": len(dropped_image_items),
            "policy": "default: drop FIG-001 through FIG-009 because they require judging figure/image bodies rather than manuscript text",
            "items": dropped_image_items,
        },
    )

    visual_suites = {suite.upper() for suite in args.visual_suite}
    text_target = text
    visual_target = (
        "MANUSCRIPT TEXT\n"
        "===============\n"
        f"{text}\n\n"
        "PDF VISUAL EVIDENCE\n"
        "===================\n"
        f"{visual['text']}"
    )
    write_jsonl(out_dir / "data_text.jsonl", [{"input": input_context, "target": text_target}])
    write_jsonl(out_dir / "data_visual.jsonl", [{"input": input_context, "target": visual_target}])

    suite_dir = out_dir / "suite_checklists"
    suite_dir.mkdir(parents=True, exist_ok=True)
    suite_jobs: list[dict[str, Any]] = []
    for suite, suite_items in grouped_by_suite(scored_items).items():
        checklist_json = make_autochecklist(
            suite_items,
            checklist_id=f"dp16276_{suite}_{len(suite_items)}",
            input_context=input_context,
        )
        checklist_path_out = suite_dir / f"{suite}.json"
        write_json(checklist_path_out, checklist_json)
        use_visual = bool(visual["enabled"]) and suite in visual_suites
        suite_jobs.append(
            {
                "suite": suite,
                "item_count": len(suite_items),
                "checklist": str(checklist_path_out),
                "data": str(out_dir / ("data_visual.jsonl" if use_visual else "data_text.jsonl")),
                "visual_target": use_visual,
            }
        )

    manifest = {
        "created_at": utc_now(),
        "run_dir": str(out_dir),
        "source_pdf": str(pdf),
        "source_pdf_sha256": sha256_file(pdf),
        "source_checklist_md": str(checklist_path),
        "source_checklist_sha256": parsed["source_sha256"],
        "text_extraction": {
            "tool": tools.pdftotext,
            "text_path": text_path,
            "text_sha256": sha256_text(text),
            "layout_pages": len(layout_pages),
            "pdf_pages": pages,
        },
        "visual": {k: v for k, v in visual.items() if k != "text"},
        "scoring": {
            "engine": "AutoChecklist ChecklistScorer",
            "mode": "batch with item-mode retry",
            "capture_reasoning": True,
            "model": args.model,
            "reasoning_effort": DEFAULT_REASONING_EFFORT,
            "structured_output": "DeepSeek strict tool call via local OpenAI-compatible shim; JSON Output fallback",
            "jobs": args.jobs,
            "client_timeout_seconds": args.client_timeout,
            "shim_timeout_seconds": args.shim_timeout,
        },
        "items": {
            "selected_total": len(selected),
            "scored_mh": len(scored_items),
            "reader_queue_r": len(reader_items),
            "dropped_image_items": len(dropped_image_items),
            "source_total": parsed["counts"]["items"],
            "source_by_verification": parsed["counts"]["by_verification"],
        },
        "suite_jobs": suite_jobs,
    }
    write_json(out_dir / "manifest.json", manifest)
    return {
        "out_dir": out_dir,
        "pdf": pdf,
        "checklist": checklist_path,
        "parsed": parsed,
        "manifest": manifest,
        "scored_items": scored_items,
        "reader_items": reader_items,
        "dropped_image_items": dropped_image_items,
        "suite_jobs": suite_jobs,
    }


def validate_score_file(path: Path, expected_count: int) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size == 0:
        return False, "score file is missing or empty"
    try:
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception as exc:  # noqa: BLE001
        return False, f"score file is not valid JSONL: {exc}"
    count = sum(len(line.get("item_scores", [])) for line in lines)
    if count != expected_count:
        return False, f"expected {expected_count} item scores, found {count}"
    missing_reasoning = [
        score.get("item_id")
        for line in lines
        for score in line.get("item_scores", [])
        if not str(score.get("reasoning") or "").strip()
    ]
    if missing_reasoning:
        return False, f"missing reasoning for {len(missing_reasoning)} items"
    return True, "ok"


def run_suite_job(job: dict[str, Any], args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    suite = job["suite"]
    output_dir = out_dir / "suite_scores"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{suite}.scores.jsonl"
    log_path = output_dir / f"{suite}.log"

    base_command = [
        sys.executable,
        str(RUNNER),
        "--data",
        job["data"],
        "--checklist",
        job["checklist"],
        "-o",
        str(output_path),
        "--mode",
        "batch",
        "--model",
        args.model,
        "--max-tokens",
        str(args.max_tokens),
        "--timeout",
        str(args.shim_timeout),
        "--client-timeout",
        str(args.client_timeout),
    ]
    env = os.environ.copy()
    env["DEEPSEEK_REASONING_EFFORT"] = DEFAULT_REASONING_EFFORT
    env.setdefault("DEEPSEEK_STRUCTURED_MODE", "strict_tool")

    started = utc_now()
    proc = subprocess.run(
        base_command,
        cwd=str(SCRIPT_DIR.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=args.process_timeout,
    )
    log_path.write_text(
        "COMMAND: " + " ".join(base_command) + "\n\nSTDOUT:\n" + proc.stdout + "\n\nSTDERR:\n" + proc.stderr,
        encoding="utf-8",
    )
    ok, reason = validate_score_file(output_path, job["item_count"])
    mode = "batch"

    if proc.returncode != 0 or not ok:
        retry_output = output_dir / f"{suite}.item-retry.scores.jsonl"
        retry_log = output_dir / f"{suite}.item-retry.log"
        retry_command = list(base_command)
        retry_command[retry_command.index("batch")] = "item"
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        retry_command[retry_command.index(str(output_path))] = str(retry_output)
        proc_retry = subprocess.run(
            retry_command,
            cwd=str(SCRIPT_DIR.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=args.process_timeout,
        )
        retry_log.write_text(
            "BATCH_RETURN_CODE: "
            + str(proc.returncode)
            + "\nBATCH_VALIDATION: "
            + reason
            + "\n\nCOMMAND: "
            + " ".join(retry_command)
            + "\n\nSTDOUT:\n"
            + proc_retry.stdout
            + "\n\nSTDERR:\n"
            + proc_retry.stderr,
            encoding="utf-8",
        )
        ok, reason = validate_score_file(retry_output, job["item_count"])
        if ok:
            output_path = retry_output
            log_path = retry_log
            mode = "item-retry"
            proc = proc_retry
        else:
            return {
                "suite": suite,
                "ok": False,
                "mode": mode,
                "returncode": proc_retry.returncode,
                "reason": reason,
                "log": str(retry_log),
                "output": str(retry_output),
                "started_at": started,
                "finished_at": utc_now(),
            }

    return {
        "suite": suite,
        "ok": True,
        "mode": mode,
        "returncode": proc.returncode,
        "reason": reason,
        "log": str(log_path),
        "output": str(output_path),
        "started_at": started,
        "finished_at": utc_now(),
        "visual_target": job["visual_target"],
    }


def run_all_suites(prepared: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    out_dir = prepared["out_dir"]
    jobs = prepared["suite_jobs"]
    if not jobs:
        return []
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        future_by_suite = {
            pool.submit(run_suite_job, job, args, out_dir): job["suite"]
            for job in jobs
        }
        for future in concurrent.futures.as_completed(future_by_suite):
            suite = future_by_suite[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "suite": suite,
                        "ok": False,
                        "mode": "batch",
                        "returncode": None,
                        "reason": str(exc),
                        "log": None,
                        "output": None,
                        "started_at": None,
                        "finished_at": utc_now(),
                    }
                )
    results.sort(key=lambda item: [job["suite"] for job in jobs].index(item["suite"]))
    write_json(out_dir / "suite_results.json", results)
    failures = [result for result in results if not result.get("ok")]
    if failures:
        failed = ", ".join(f"{item['suite']} ({item['reason']})" for item in failures)
        raise SystemExit(f"ERROR: scoring failed for suite(s): {failed}")
    return results


def load_score_records(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for result in results:
        path = Path(result["output"])
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                record["_suite"] = result["suite"]
                record["_score_output"] = str(path)
                record["_score_mode"] = result["mode"]
                records.append(record)
    return records


def answer_is_pass(answer: Any) -> bool:
    value = getattr(answer, "value", answer)
    return str(value).lower() == "yes"


def classify_failure(suite: str, reasoning: str, visual_target: bool) -> str:
    if visual_target and TEXT_LIMITED_RE.search(reasoning):
        return "VISUAL-CHECK"
    return "REVISION-CANDIDATE"


def aggregate_results(prepared: dict[str, Any], suite_results: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir: Path = prepared["out_dir"]
    item_lookup = {item["id"]: item for item in prepared["scored_items"]}
    visual_suite_lookup = {result["suite"]: bool(result.get("visual_target")) for result in suite_results}
    score_records = load_score_records(suite_results)

    combined: list[dict[str, Any]] = []
    suite_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for record in score_records:
        for score in record.get("item_scores", []):
            item_id = score.get("item_id")
            item = item_lookup.get(item_id, {})
            suite = item.get("suite_code") or record.get("_suite") or "UNKNOWN"
            status = "pass" if answer_is_pass(score.get("answer")) else "fail"
            suite_counts[suite][status] += 1
            reasoning = str(score.get("reasoning") or "").strip()
            combined.append(
                {
                    "item_id": item_id,
                    "suite": suite,
                    "suite_name": item.get("suite_name"),
                    "verification": item.get("verification"),
                    "assertion": item.get("assertion"),
                    "answer": score.get("answer"),
                    "status": status,
                    "reasoning": reasoning,
                    "failure_class": None
                    if status == "pass"
                    else classify_failure(suite, reasoning, visual_suite_lookup.get(suite, False)),
                    "source_line": item.get("source_line"),
                }
            )

    combined.sort(key=lambda row: (str(row["suite"]), str(row["item_id"])))
    pass_count = sum(1 for row in combined if row["status"] == "pass")
    fail_count = sum(1 for row in combined if row["status"] == "fail")
    reasoning_count = sum(1 for row in combined if row["reasoning"])

    suite_summaries: list[dict[str, Any]] = []
    for suite in grouped_by_suite(prepared["scored_items"]):
        counts = suite_counts[suite]
        total = counts["pass"] + counts["fail"]
        suite_summaries.append(
            {
                "suite": suite,
                "pass": counts["pass"],
                "fail": counts["fail"],
                "total": total,
                "pass_rate": counts["pass"] / total if total else 0.0,
                "visual_target": visual_suite_lookup.get(suite, False),
            }
        )

    summary = {
        "created_at": utc_now(),
        "run_dir": str(out_dir),
        "source_pdf": str(prepared["pdf"]),
        "source_checklist_md": str(prepared["checklist"]),
        "scoring": prepared["manifest"]["scoring"],
        "items": {
            "scored_mh": len(prepared["scored_items"]),
            "reader_queue_r": len(prepared["reader_items"]),
            "dropped_image_items": len(prepared["dropped_image_items"]),
            "total_source_checklist_items": prepared["parsed"]["counts"]["items"],
            "pass": pass_count,
            "fail": fail_count,
            "pass_rate": pass_count / len(combined) if combined else 0.0,
            "all_scored_items_have_reasoning": reasoning_count == len(combined),
        },
        "suite_summaries": suite_summaries,
        "failure_classes": dict(Counter(row["failure_class"] for row in combined if row["failure_class"])),
    }
    write_json(out_dir / "reasoned_combined_scores.json", combined)
    write_json(out_dir / "reasoned_summary.json", summary)
    return {"combined": combined, "summary": summary}


def render_report(prepared: dict[str, Any], aggregated: dict[str, Any]) -> Path:
    out_dir: Path = prepared["out_dir"]
    summary = aggregated["summary"]
    combined = aggregated["combined"]
    manifest = prepared["manifest"]
    fail_rows = [row for row in combined if row["status"] == "fail"]
    fail_by_suite: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for row in fail_rows:
        fail_by_suite.setdefault(row["suite"], []).append(row)

    lines = [
        "# AI4SS AutoChecklist Review Report",
        "",
        f"- PDF: `{prepared['pdf']}`",
        f"- Checklist: `{prepared['checklist']}`",
        "- Engine: AutoChecklist `ChecklistScorer(mode=\"batch\", capture_reasoning=True)`",
        "- Backend: DeepSeek V4 Pro, reasoning effort max, strict structured-output shim",
        f"- Run dir: `{out_dir}`",
        f"- Scored M/H items: {summary['items']['scored_mh']}; pass: {summary['items']['pass']}; fail: {summary['items']['fail']}; pass rate: {summary['items']['pass_rate']:.3f}",
        f"- Reader-test `(R)` items held out: {summary['items']['reader_queue_r']}",
        f"- Image-body FIG items dropped: {summary['items']['dropped_image_items']}",
        "",
        "## Stateless Snapshot",
        "",
        f"- PDF SHA-256: `{manifest['source_pdf_sha256']}`",
        f"- Checklist SHA-256: `{manifest['source_checklist_sha256']}`",
        f"- Extracted text SHA-256: `{manifest['text_extraction']['text_sha256']}`",
        f"- PDF pages: {manifest['text_extraction']['pdf_pages']}",
        "- Prompt boundary: score only the extracted manuscript snapshot; ignore agent context, memory, and previous reviews.",
        "",
        "## Visual Evidence",
        "",
    ]
    visual = manifest.get("visual", {})
    if visual.get("enabled"):
        lines.extend(
            [
                f"- SVG pages: {len(visual.get('svg_pages', []))}",
                f"- Visual pages included: {', '.join(str(page) for page in visual.get('pages', []))}",
                f"- Visual supplement: `{visual.get('visual_supplement_path')}`",
                f"- Positioned text XML: `{visual.get('positioned_xml')}`",
            ]
        )
    else:
        lines.append(f"- Disabled: {visual.get('reason')}")

    lines.extend(
        [
            "",
            "## Suite Summary",
            "",
            "| Suite | Visual | Pass | Fail | Total | Pass rate |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary["suite_summaries"]:
        lines.append(
            f"| {row['suite']} | {'yes' if row.get('visual_target') else 'no'} | "
            f"{row['pass']} | {row['fail']} | {row['total']} | {row['pass_rate']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Fail-First Read",
            "",
            "Treat REVISION-CANDIDATE items as direct manuscript fixes. Treat VISUAL-CHECK items as figure/table/layout defects only if the saved SVG/positioned-text evidence confirms the model's concern.",
            "",
        ]
    )

    for suite, rows in fail_by_suite.items():
        lines.append(f"### {suite} ({len(rows)} fail)")
        lines.append("")
        for row in rows:
            lines.append(
                f"- `{row['item_id']}` [{row.get('verification')}; {row.get('failure_class')}] {row.get('assertion')}"
            )
            if row.get("reasoning"):
                lines.append(f"  - Reasoning: {row['reasoning']}")
        lines.append("")

    if prepared["reader_items"]:
        lines.extend(
            [
                "## Reader-Test Queue",
                "",
                "These `(R)` criteria were not scored by the LLM because they require real reader evidence.",
                "",
            ]
        )
        for item in prepared["reader_items"]:
            lines.append(f"- `{item['id']}` [{item['suite_code']}] {item['assertion']}")
        lines.append("")

    if prepared["dropped_image_items"]:
        lines.extend(
            [
                "## Dropped Image Items",
                "",
                "These criteria require judging the rendered figure/image body and are excluded from the default one-click review.",
                "",
            ]
        )
        for item in prepared["dropped_image_items"]:
            lines.append(f"- `{item['id']}` [{item['suite_code']}] {item['assertion']}")
        lines.append("")

    report = out_dir / "reasoned_fail_first_report.md"
    report.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a stateless one-click AutoChecklist review on a manuscript PDF."
    )
    parser.add_argument("pdf", nargs="?", type=Path, help="Manuscript PDF to review.")
    parser.add_argument("--pdf", dest="pdf_option", type=Path, help="Manuscript PDF to review.")
    parser.add_argument("--checklist", required=True, type=Path, help="DP16276 checklist Markdown file.")
    parser.add_argument("--out-dir", type=Path, help="Output directory. Default: /tmp/ai4ss-autochecklist-review-<timestamp>.")
    parser.add_argument("--suite", action="append", default=[], help="Restrict to a suite code or number. Repeatable.")
    parser.add_argument("--visual-suite", action="append", default=sorted(DEFAULT_VISUAL_SUITES), help="Suite code that should receive visual supplement. Repeatable.")
    parser.add_argument("--keep-image-items", action="store_true", help="Do not drop FIG image-body criteria.")
    parser.add_argument("--skip-visual", action="store_true", help="Disable SVG/positioned-text visual supplement.")
    parser.add_argument("--max-visual-pages", type=int, default=40, help="Maximum pages to include in visual supplement.")
    parser.add_argument("--max-positioned-chars-per-page", type=int, default=5000)
    parser.add_argument("--max-layout-chars-per-page", type=int, default=2500)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--jobs", type=int, default=3, help="Concurrent suite scoring jobs.")
    parser.add_argument("--shim-timeout", type=int, default=360)
    parser.add_argument("--client-timeout", type=int, default=420)
    parser.add_argument("--process-timeout", type=int, default=1200)
    parser.add_argument("--dry-run", action="store_true", help="Prepare artifacts only; do not call the model.")
    args = parser.parse_args(argv)
    if args.pdf_option is not None:
        args.pdf = args.pdf_option
    if args.pdf is None:
        parser.error("PDF is required, either positional or via --pdf")
    if args.jobs < 1:
        parser.error("--jobs must be >= 1")
    if args.max_visual_pages < 1:
        parser.error("--max-visual-pages must be >= 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.dry_run and not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("ERROR: DEEPSEEK_API_KEY is not set")

    prepared = prepare_run(args)
    if args.dry_run:
        print(f"Prepared review artifacts: {prepared['out_dir']}")
        print(f"Manifest: {prepared['out_dir'] / 'manifest.json'}")
        print(f"Suites: {len(prepared['suite_jobs'])}; scored items: {len(prepared['scored_items'])}; reader queue: {len(prepared['reader_items'])}; dropped image items: {len(prepared['dropped_image_items'])}")
        return 0

    suite_results = run_all_suites(prepared, args)
    aggregated = aggregate_results(prepared, suite_results)
    report = render_report(prepared, aggregated)
    summary = aggregated["summary"]
    print(f"Review complete: {prepared['out_dir']}")
    print(f"Report: {report}")
    print(
        "Pass rate: {rate:.3f} ({passed}/{total}); failed: {failed}; reader queue: {reader}".format(
            rate=summary["items"]["pass_rate"],
            passed=summary["items"]["pass"],
            total=summary["items"]["scored_mh"],
            failed=summary["items"]["fail"],
            reader=summary["items"]["reader_queue_r"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
