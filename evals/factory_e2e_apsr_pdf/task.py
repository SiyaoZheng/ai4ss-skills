"""Inspect eval for one-idea-to-data-backed-APSR-draft-PDF skillpack performance.

The evaluated agent receives exactly one research idea as the sample input.
The scorer reads only `paper/full_draft.pdf`, extracts text from that PDF, and
uses an Inspect model-graded judge to score the draft. No `.aiss`, logs, TeX,
tables, scripts, data files, or other intermediate artifacts are used for
scoring. The PDF itself must make public-source discovery, real observed data
acquisition, analysis-sample construction, and analysis evidence visible to
receive high marks.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState
from inspect_ai.tool import Skill
from inspect_ai.util import sandbox
from inspect_swe import codex_cli


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from ai4ss_factory_contracts.latex_plugin import bundled_latex_plugin_skills  # noqa: E402

IDEA = "Idea: Does neighborhood service-center exposure change resident civic trust?"
PDF_PATH = "paper/full_draft.pdf"
AGENTS_PATH = ROOT / "evals" / "factory_e2e_apsr_pdf" / "scaffold" / "AGENTS.md"
EXPORTED_PDF_DIR = ROOT / "docs" / "evals" / "factory-e2e-apsr-pdf" / "generated-pdfs"
MAX_PDF_TEXT_CHARS = 60000
FORBIDDEN_SYNTHETIC_DATA_PATTERNS = (
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
WEBSEARCH_MCP_URL = "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp"
WEBPARSER_MCP_SSE_URL = "https://dashscope.aliyuncs.com/api/v1/mcps/WebParser/sse"
DEEPSEEK_OPENAI_BASE_URL = "https://api.deepseek.com/v1"
DASHSCOPE_OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_WEBPARSER_MODEL = "qwen3.6-plus"
DASHSCOPE_WEBSEARCH_MODEL = "qwen3.6-plus"
BAILIAN_MCP_BRIDGE_COMMAND = "python3"
BAILIAN_MCP_BRIDGE_ARGS = ["/workspace/scripts/bailian_mcp_bridge.py"]
BROWSER_USE_MCP_COMMAND = "sh"
BROWSER_USE_MCP_BOOTSTRAP = (
    'if [ -n "$DASHSCOPE_API_KEY" ]; then '
    'export OPENAI_API_KEY="$DASHSCOPE_API_KEY"; '
    f'export OPENAI_BASE_URL="{DASHSCOPE_OPENAI_BASE_URL}"; '
    'export BROWSER_USE_LLM_MODEL="qwen-plus"; '
    'elif [ -n "$DEEPSEEK_API_KEY" ]; then '
    'export OPENAI_API_KEY="$DEEPSEEK_API_KEY"; '
    f'export OPENAI_BASE_URL="${{DEEPSEEK_BASE_URL:-{DEEPSEEK_OPENAI_BASE_URL}}}"; '
    'export BROWSER_USE_LLM_MODEL="deepseek-chat"; '
    'fi; '
    'export BROWSER_USE_HEADLESS="${BROWSER_USE_HEADLESS:-true}"; '
    'exec uvx --from "browser-use[cli]" browser-use --mcp'
)
BROWSER_USE_MCP_ARGS = ["-lc", BROWSER_USE_MCP_BOOTSTRAP]
IQS_MCP_SERVERS = {
    "IQSWebSearch": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-search",
    "IQSLiteSearch": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-litesearch",
    "IQSReadPage": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-readpage",
}


def env_file_value(name: str) -> str | None:
    """Read simple KEY=value env files used by official IQS docs."""
    for path in (Path.home() / ".alibabacloud" / "iqs" / "env",):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == name:
                return value.strip().strip('"').strip("'") or None
    return None


def runtime_env_value(name: str) -> str | None:
    return os.environ.get(name) or env_file_value(name)


def websearch_mcp_preflight_available(api_key: str | None) -> bool:
    if not api_key:
        return False
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ai4ss-harness-preflight", "version": "0.1.0"},
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        WEBSEARCH_MCP_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 400
    except (OSError, urllib.error.HTTPError, urllib.error.URLError):
        return False


def codex_runtime_env() -> dict[str, str]:
    deepseek_key = runtime_env_value("DEEPSEEK_API_KEY")
    dashscope_key = runtime_env_value("DASHSCOPE_API_KEY")
    openai_key = deepseek_key or runtime_env_value("OPENAI_API_KEY")
    openai_base_url = (
        runtime_env_value("DEEPSEEK_BASE_URL")
        or runtime_env_value("OPENAI_BASE_URL")
        or DEEPSEEK_OPENAI_BASE_URL
    )
    env = {
        "BROWSER_USE_HEADLESS": "true",
        "OPENAI_BASE_URL": openai_base_url,
        "BROWSER_USE_LLM_MODEL": runtime_env_value("BROWSER_USE_LLM_MODEL")
        or ("qwen-plus" if dashscope_key else "deepseek-chat"),
    }
    if openai_key:
        env["OPENAI_API_KEY"] = openai_key
    if deepseek_key:
        env["DEEPSEEK_API_KEY"] = deepseek_key
    if deepseek_base_url := runtime_env_value("DEEPSEEK_BASE_URL"):
        env["DEEPSEEK_BASE_URL"] = deepseek_base_url
    for key in (
        "DASHSCOPE_API_KEY",
        "ALIYUN_IQS_API_KEY",
        "BROWSER_USE_API_KEY",
        "ANTHROPIC_API_KEY",
        "BROWSER_USE_DISABLE_SECURITY",
    ):
        value = runtime_env_value(key)
        if value:
            env[key] = value
    if env.get("DASHSCOPE_API_KEY"):
        env["DASHSCOPE_RESPONSES_BASE_URL"] = DASHSCOPE_OPENAI_BASE_URL
        env["DASHSCOPE_WEBPARSER_MCP_URL"] = WEBPARSER_MCP_SSE_URL
        env["DASHSCOPE_WEBPARSER_MODEL"] = DASHSCOPE_WEBPARSER_MODEL
        env["DASHSCOPE_WEBSEARCH_MODEL"] = DASHSCOPE_WEBSEARCH_MODEL
    return env


def codex_runtime_config_overrides() -> dict[str, str]:
    overrides = {
        "approval_policy": '"never"',
        "mcp_servers.browser-use.command": f'"{BROWSER_USE_MCP_COMMAND}"',
        "mcp_servers.browser-use.args": json.dumps(BROWSER_USE_MCP_ARGS),
    }
    if runtime_env_value("DASHSCOPE_API_KEY"):
        overrides["mcp_servers.WebSearch.command"] = f'"{BAILIAN_MCP_BRIDGE_COMMAND}"'
        overrides["mcp_servers.WebSearch.args"] = json.dumps(BAILIAN_MCP_BRIDGE_ARGS)
    if runtime_env_value("ALIYUN_IQS_API_KEY"):
        for name, url in IQS_MCP_SERVERS.items():
            overrides[f"mcp_servers.{name}.url"] = f'"{url}"'
            overrides[f"mcp_servers.{name}.env_http_headers"] = '{"X-API-Key" = "ALIYUN_IQS_API_KEY"}'
    return overrides

FULL_RESEARCH_FACTORY_SKILLS = (
    "research-starter",
    "study-design-builder",
    "literature-matrix",
    "public-data-sources",
    "research-data-builder",
    "research-analysis-runner",
    "top-journal-figures",
    "methods-reviewer",
    "analysis-explainer",
    "latex-tables",
    "did-expert",
    "academic-writing-scaffold",
    "reviewer-response",
)

AGENT_SYSTEM_PROMPT = f"""You are being evaluated on whether you can turn a single research idea into a data-backed APSR-level draft PDF.

The user input will contain only one idea. Do not assume that hidden data,
literature packets, or background files exist. You are expected to autonomously
search for public data and public source documentation, acquire real observed
public or authorized data, construct the observed analysis sample where
feasible, run transparent statistical or descriptive analysis, and then write
the PDF.

The sandbox contains `/workspace/AGENTS.md`. Read and follow its full-auto skill
routing table before acting.

You may create any intermediate files you need, including scripts, downloaded
data, tables, figures, and research-model artifacts, but the only required final
artifact is `{PDF_PATH}`. The final PDF must stand alone: include visible data
source names or URLs, access dates, sample construction, measurement choices,
analysis commands or reproducibility notes, tables or figures with actual
computed values, and limitations.

Use available official search MCP tools autonomously. Prefer the Alibaba Cloud
Bailian `WebSearch` MCP for live source discovery when present. In this harness
`WebSearch` may be a local stdio bridge exposing `bailian_web_search` and
`bailian_web_parse`; use those tools directly rather than waiting for the user
or for a remote endpoint to recover. If Alibaba Cloud IQS MCP tools are also
present, use `IQSWebSearch.common_search`,
`IQSLiteSearch.web_search`, and `IQSReadPage.readpage_basic` or
`IQSReadPage.readpage_scrape` as supplementary search and extraction tools. Do
not ask the user to choose routes, keys, sources, or data paths during the run.

For page parsing, when `DASHSCOPE_API_KEY` exists, you may call Alibaba Cloud's
official WebParser MCP through the DashScope OpenAI-compatible Responses API
instead of waiting for a Codex MCP tool. Use base URL `{DASHSCOPE_OPENAI_BASE_URL}`,
model `{DASHSCOPE_WEBPARSER_MODEL}`, and an MCP tool with
`server_protocol="sse"`, `server_label="WebParser"`,
`server_url="{WEBPARSER_MCP_SSE_URL}"`, and header
`Authorization: Bearer $DASHSCOPE_API_KEY`.

Do not invent data, citations, estimates, or submission readiness. Empirical
rows must come only from real observed public or authorized sources. Do not use
synthetic, simulated, hypothetical, illustrative, generated, benchmark-calibrated,
DGP-created, or random-draw data anywhere in the empirical chain. Published
coefficients, parameter benchmarks, and literature summary statistics may
support theory, measurement discussion, or power reasoning, but they cannot be
converted into analysis rows, tables, figures, estimates, or a substitute
dataset. If one public data path fails, document the acquisition attempt
briefly in the PDF, then switch automatically to another real observed public
or authorized source, measurement, unit, geography, or route that can support
a data-backed draft PDF. If research-factory skills are available, use the
data, analysis, literature, methods, and writing skills as needed rather than
stopping after a design scaffold.

If the OpenAI bundled LaTeX plugin skills are available, use `latex-doctor` to
diagnose PDF build failures and `latex-compile` to render
`paper/full_draft.tex` into `paper/full_draft.pdf`, preferably with TeX Live and
`xelatex` for broad font and Unicode support. The APSR PDF sandbox already has
TeX Live installed; do not run a managed TeX Live installer unless a harness
instruction explicitly authorizes that download.

For publication-facing figures, the only final plotting carrier is R/ggplot2.
Use Python, Stata, JavaScript, dashboards, screenshots, or interactive widgets
only for diagnosis or exploration; final paper figures must be generated by
reproducible ggplot2 code and exported from R. R helper packages may estimate,
tidy, compose, label, check, or export, but final manuscript figures must remain
named ggplot2 objects with explicit `ggsave()` calls. Figures in the same paper
must share one explicit ggplot2 style profile covering theme, typography,
dimensions, aspect ratios, margins, axes, point/line/interval geoms, color and
non-color encodings, legends, facets, annotations, caption/source-note
conventions, export device, and filename pattern. Prefer a shared
`scripts/figure_style.R` or an existing project house-style file.

Before finishing, ensure `{PDF_PATH}` exists and is readable as a PDF.
"""

JUDGE_RUBRIC = """You are grading a PDF manuscript draft for an AI4SS skillpack evaluation.

You must judge only the evidence provided below, which is text and metadata
extracted from `paper/full_draft.pdf`. Do not use the agent transcript, file
tree, logs, source TeX, `.aiss` files, tables outside the PDF, or any other
artifact. If something is not visible in the PDF evidence, treat it as absent.

Task given to the agent:
Idea: Does neighborhood service-center exposure change resident civic trust?

Grade the PDF on a 0-100 scale as a data-backed APSR-level draft, not as a
polished submission. The task tests whether the agent can move from one idea to
autonomous public-source discovery, real observed data acquisition,
analysis-sample construction, analysis, and bounded manuscript writing. Reward
honest boundedness, but do not reward a pure evidence plan as if it were
empirical work. Penalize fabricated empirical results, fabricated citations,
hidden AI use, or claims that are stronger than the PDF's visible evidence.

Rubric:
- Research question and contribution: 15 points.
- Political-science theory and APSR relevance: 15 points.
- Autonomous public-source discovery and source provenance visible in the PDF: 15 points.
- Real observed data acquisition, analysis-sample construction, measurement
  validity, and reproducibility: 15 points.
- Empirical analysis, identification credibility, diagnostics, tables, or figures
  with actual computed values: 20 points.
- Bounded claims, limitations, transparency, and AI disclosure: 10 points.
- Manuscript organization and scholarly writing quality: 15 points.
- References and APSA/APSR-style presentation: 5 points.

Caps and penalties:
- Forbidden data-source gate: if the PDF reports synthetic, simulated,
  hypothetical, illustrative, generated, benchmark-calibrated, DGP-created, or
  random-draw data as empirical evidence, assign 0 regardless of transparency or
  writing quality. Treat analysis rows, model inputs, tables, figures, or
  estimates constructed from published parameter benchmarks as synthetic data
  even if the PDF calls them source-backed.
- If the PDF contains no actual acquired real observed data or constructed
  observed analysis sample, cap the score at 45.
- If the PDF contains data provenance but no actual analysis results, cap the
  score at 60.
- If the PDF claims completed empirical results without visible data provenance
  or reproducibility details, cap the score at 65 and penalize overclaiming.
- If fabricated citations, fabricated data, or fabricated estimates are evident,
  assign 0-30 depending on severity.

Calibration:
- 90-100: exceptional APSR-level draft package with strong theory, credible
  design, transparent public-data provenance, real analysis, bounded claims,
  and polished structure.
- 75-89: strong draft but with important gaps, missing evidence, or incomplete
  presentation.
- 55-74: plausible working paper scaffold with meaningful theory/design but not
  close to APSR level, or a thin empirical exercise with limited measurement.
- 35-54: generic or thin draft; little credible research design or evidence.
- 1-34: mostly boilerplate, unsupported, fabricated, or not a real manuscript.
- 0: missing/unreadable PDF or extracted content is effectively empty.

Return exactly this format:
SCORE: <integer from 0 to 100>
REASON: <brief explanation grounded only in the PDF evidence>
"""


def skill_paths(condition: str) -> list[Path | Skill]:
    if condition == "no_skills":
        return []
    if condition == "full_research_factory_skills":
        return [
            *(ROOT / "skills" / name for name in FULL_RESEARCH_FACTORY_SKILLS),
            *bundled_latex_plugin_skills(),
        ]
    raise ValueError(f"unknown condition: {condition}")


def extraction_prompt(pdf_info: str, pdf_text: str, truncated: bool) -> str:
    truncation_note = (
        f"\n\n[PDF text truncated to {MAX_PDF_TEXT_CHARS} characters for judging.]"
        if truncated
        else ""
    )
    return f"""{JUDGE_RUBRIC}

PDF metadata extracted from the PDF:
```text
{pdf_info.strip() or "[pdfinfo produced no metadata]"}
```

PDF text extracted from the PDF:
```text
{pdf_text.strip() or "[pdftotext produced no text]"}
```{truncation_note}
"""


def parse_score(completion: str) -> int | None:
    match = re.search(r"(?im)^\s*SCORE\s*:\s*(100|[0-9]{1,2})\s*$", completion)
    if not match:
        return None
    return max(0, min(100, int(match.group(1))))


def synthetic_data_violation(pdf_text: str) -> str | None:
    for pattern in FORBIDDEN_SYNTHETIC_DATA_PATTERNS:
        match = pattern.search(pdf_text)
        if match:
            return " ".join(match.group(0).split())
    return None


def export_pdf_copy(pdf_bytes: bytes, sample_id: int | str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(sample_id)).strip("._") or "sample"
    output_path = EXPORTED_PDF_DIR / f"{safe_id}.pdf"
    EXPORTED_PDF_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return output_path


async def extract_pdf_evidence(sample_id: int | str) -> tuple[str, str, dict[str, Any]]:
    sbox = sandbox()
    pdf_bytes = await sbox.read_file(PDF_PATH, text=False)
    exported_pdf = export_pdf_copy(pdf_bytes, sample_id)
    metadata: dict[str, Any] = {
        "pdf_path": PDF_PATH,
        "pdf_bytes": len(pdf_bytes),
        "exported_pdf": str(exported_pdf),
    }

    info_result = await sbox.exec(["pdfinfo", PDF_PATH], timeout=30)
    metadata["pdfinfo_returncode"] = info_result.returncode
    pdf_info = info_result.stdout if info_result.returncode == 0 else info_result.stderr

    text_result = await sbox.exec(["pdftotext", "-layout", "-enc", "UTF-8", PDF_PATH, "-"], timeout=45)
    metadata["pdftotext_returncode"] = text_result.returncode
    if text_result.returncode != 0:
        metadata["pdftotext_error"] = text_result.stderr[:2000]
        return pdf_info, "", metadata

    pdf_text = text_result.stdout
    metadata["pdf_text_chars"] = len(pdf_text)
    return pdf_info, pdf_text, metadata


@scorer(metrics=[mean()])
def apsr_pdf_llm_judge(model: str | Model | None = None):
    grader_model = get_model(model)

    async def score(state: TaskState, target: Target) -> Score:
        del target
        try:
            pdf_info, pdf_text, metadata = await extract_pdf_evidence(state.sample_id)
        except FileNotFoundError:
            return Score(
                value=0,
                explanation=f"Missing required PDF: {PDF_PATH}",
                metadata={"pdf_path": PDF_PATH, "missing_pdf": True},
            )

        if not pdf_text.strip():
            return Score(
                value=0,
                explanation="PDF exists but yielded no extractable text for the PDF-only judge.",
                metadata={**metadata, "empty_pdf_text": True},
            )

        if violation := synthetic_data_violation(pdf_text):
            return Score(
                value=0,
                explanation=(
                    "Forbidden synthetic-data evidence in the PDF: "
                    f"{violation}. The APSR PDF harness requires only real observed "
                    "public or authorized empirical data; benchmark-calibrated, "
                    "simulated, hypothetical, illustrative, generated, DGP-created, "
                    "or random-draw data receive 0 before model judging."
                ),
                metadata={
                    **metadata,
                    "forbidden_synthetic_data": True,
                    "synthetic_data_match": violation,
                    "score_100": 0,
                },
            )

        truncated = len(pdf_text) > MAX_PDF_TEXT_CHARS
        prompt = extraction_prompt(pdf_info, pdf_text[:MAX_PDF_TEXT_CHARS], truncated)
        result = await grader_model.generate(prompt)
        parsed = parse_score(result.completion)
        if parsed is None:
            return Score(
                value=0,
                explanation="Judge response did not contain a parseable SCORE line.\n\n" + result.completion,
                metadata={**metadata, "judge_parse_failed": True, "judge_completion": result.completion},
            )
        return Score(
            value=parsed,
            explanation=result.completion,
            metadata={
                **metadata,
                "score_100": parsed,
                "judge_completion": result.completion,
                "pdf_text_truncated": truncated,
            },
        )

    return score


@task
def factory_e2e_apsr_pdf(
    condition: str = "full_research_factory_skills",
    judge_model: str | None = None,
) -> Task:
    valid_conditions = {"no_skills", "full_research_factory_skills"}
    if condition not in valid_conditions:
        raise ValueError(f"unknown condition {condition!r}; expected one of {sorted(valid_conditions)}")
    if not AGENTS_PATH.is_file():
        raise FileNotFoundError(f"missing harness AGENTS.md: {AGENTS_PATH}")
    return Task(
        dataset=[
            Sample(
                id=f"service_center_trust_apsr_pdf__{condition}",
                input=IDEA,
                target=PDF_PATH,
            )
        ],
        solver=codex_cli(
            system_prompt=AGENT_SYSTEM_PROMPT,
            skills=skill_paths(condition),
            web_search="live",
            goals=True,
            env=codex_runtime_env(),
            config_overrides=codex_runtime_config_overrides(),
        ),
        scorer=apsr_pdf_llm_judge(model=judge_model),
        sandbox=("docker", "Dockerfile"),
    )
