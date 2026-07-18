"""Inspect agent-runtime eval for AI4SS research-factory skill relay.

This eval starts a real Codex CLI agent runtime through Inspect SWE. The scorer
reads `research_model.aiss`, logs, and artifacts from the sandbox, reruns the
deterministic handoff audit as diagnostic metadata, and uses an LLM-as-judge
rubric for the final score.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox
from inspect_swe import codex_cli


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_skill_handoffs import audit_text  # noqa: E402


FULL_SKILL_NAMES = (
    "research-starter",
    "study-design-builder",
    "literature-matrix",
    "public-data-sources",
    "research-data-builder",
    "research-analysis-runner",
    "methods-reviewer",
    "academic-writing-scaffold",
    "reviewer-response",
)
SINGLE_SKILL_NAMES = ("research-starter",)
VALID_FIXTURE = ROOT / "docs" / "evals" / "factory-relay" / "fixtures" / "valid_relay.aiss"
REQUIRED_OUTPUTS = ("research_model.aiss", "stage_log.md", "outputs/data_inventory.md")
MODEL_OUTPUT_CANDIDATES = ("research_model.aiss", "docs/research_model.aiss")
MAX_EVIDENCE_CHARS = 60000

JUDGE_RUBRIC = """You are grading an AI4SS research-factory relay eval.

You must judge only the sandbox artifacts and deterministic audit metadata
provided below. The deterministic audit is evidence, not the final score.

Task: run a full AI4SS research-factory relay for the service-center exposure
scenario. The expected chain is route discovery -> MIDA design -> source/data
declarations -> analysis readiness/artifacts -> methods review/report boundary.

Score on a 0-100 scale.

Rubric:
- `.aiss` workflow state and valid DSL shape: 20 points.
- Route/MIDA/decision continuity and correct `next_skill_route` behavior: 20 points.
- Source, span, artifact, empirical, observation, model, and check declarations
  tied to the same research object: 20 points.
- Full-auto repair discipline: uses the strongest automatic repair route,
  handles broken or shuffled inputs, and avoids human-blocking judgment: 15 points.
- Boundary discipline: no synthetic empirical data, no direct-submission or
  writing-ready overclaim, and AI/disclosure boundaries remain visible: 15 points.
- Reproducibility and handoff readability: required files exist, lint command
  is run or represented, and stage logs make consumed/emitted IDs inspectable:
  10 points.

Caps and penalties:
- If no `research_model.aiss` or equivalent model file is present, score 0.
- If workflow state is mostly Markdown/CSV/prose rather than `.aiss`, cap at 35.
- If the output fabricates empirical rows or uses synthetic/simulated data as
  evidence, cap at 30, or 0 if central to the relay.
- If it claims writing/submission readiness before evidence and disclosure
  gates, cap at 60.
- If deterministic audit metadata reports severe errors, use them as evidence
  but still judge whether the artifact partially satisfies the rubric.

Return exactly this format:
SCORE: <integer from 0 to 100>
REASON: <brief explanation grounded in the artifacts and audit metadata>
"""


def skill_paths(names: tuple[str, ...]) -> list[Path]:
    return [ROOT / "skills" / name for name in names]


def skills_for_condition(condition: str) -> list[Path]:
    if condition == "no_skills":
        return []
    if condition == "single_skill":
        return skill_paths(SINGLE_SKILL_NAMES)
    return skill_paths(FULL_SKILL_NAMES)


def dsl_tool_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted((ROOT / "dsl" / "scripts").glob("aiss*.py")):
        files[f"tools/dsl/scripts/{path.name}"] = path.read_text(encoding="utf-8")
    return files


def broken_handoff_fixture() -> str:
    text = VALID_FIXTURE.read_text(encoding="utf-8")
    text = text.replace(
        "mida relay.mida_r1_report_boundary {\n"
        "  route: relay.route_r1\n"
        "  component: report_boundary\n"
        "  text: \"Report only bounded diagnostics until transparency checks, data repairs, and methods review are complete.\"\n"
        "  status: declared\n"
        "  spans: [relay.span_design]\n"
        "}\n\n",
        "",
        1,
    )
    text = text.replace(
        "  status: needs_data_check\n  bridges: [relay.measurement_bridge_exposure]",
        "  status: needs_data_check\n  next_skill_route: research-analysis-runner\n  bridges: [relay.measurement_bridge_exposure]",
        1,
    )
    text = text.replace("  artifacts: [relay.artifact_data_inventory]\n", "", 1)
    return text


def sample_files(condition: str) -> dict[str, str]:
    files = {
        "AGENTS.md": """# Factory Relay Agent Eval

This workspace is an AI4SS research-factory relay eval.

Hard rules:
- `research_model.aiss` is the only workflow state.
- `research_model.aiss` must be real v0.4 DSL, not Markdown. Its first line must be exactly `aiss version "0.4"`.
- Validate before final: `python3 tools/dsl/scripts/aiss.py lint research_model.aiss --strict`.
- Do not create Markdown, CSV, JSON, or chat-table sidecars that define `route_decl_id`, `mida_id`, `decision_decl_id`, or `next_skill_route`.
- Logs may mention IDs, but workflow state must be declared in `.aiss`.
- Preserve route -> MIDA -> decision -> source/span/artifact/check/claim continuity.
- If a judgment point appears, declare a `decision` row with `owner: harness`, auto-resolve the best defensible assumption, and route any repair work to the owning skill.
- Do not mark direct submission or writing readiness unless disclosure, human accountability, and outlet-policy gates are explicit.

Skill routing table:
| Skill | Use when | Required input | Required output / next route |
|---|---|---|---|
| `research-starter` | No selected route exists. | Design brief or rough idea. | Selected `.aiss` route and `next_skill_route: study-design-builder`. |
| `study-design-builder` | Route needs MIDA/design declarations. | Selected route. | Seven MIDA rows and `next_skill_route: public-data-sources`, `literature-matrix`, or methods/design repair. |
| `public-data-sources` | Data source/access/provenance route is unknown or unchecked. | MIDA data strategy and target unit/period/variables. | Real observed source route, access status, source artifact/request template, and `next_skill_route: research-data-builder`. |
| `literature-matrix` | Theory/source-backed evidence is needed. | Design/literature inputs. | Source/span/claim declarations and `next_skill_route` to design/methods/writing. |
| `research-data-builder` | Acquired real observed source artifacts need analysis-sample declarations. | Source artifact or request output plus data strategy. | Artifact/empirical/check declarations and `next_skill_route: research-analysis-runner` or repair. |
| `research-analysis-runner` | Analysis-ready data need outputs or readiness checks. | Data artifact and analysis plan. | Analysis artifacts/checks and `next_skill_route: methods-reviewer`. |
| `methods-reviewer` | Method, claim, reproducibility, or overclaim risk needs audit. | `.aiss`, outputs, scripts, claims. | Diagnostic checks/decisions and repair or writing route. |
| `academic-writing-scaffold` | Checked evidence is ready for bounded report text. | Bounded claims and evidence. | Report-boundary declarations and disclosure status. |
| `reviewer-response` | Reviewer-style repairs or response state are needed. | Comments/findings and affected elements. | Revision decisions and downstream repair route. |

Only real observed public or authorized data may feed empirical declarations.
If a source route fails, switch automatically to another observed source or
redesign route; do not create synthetic, simulated, hypothetical, illustrative,
generated, DGP-created, random-draw, benchmark-calibrated, or
literature-parameter-imputed empirical data.
""",
        "inputs/design_brief.md": """# Design Brief

Question: Does neighborhood service-center exposure change resident civic trust?

Scope: resident-year survey records linked to neighborhood-year service-center rollout records.

Design risk: rollout timing and survey linkage must be audited before estimation.

Automation gate: causal identification is bounded by data and timing checks, then routed to methods review.
""",
        "inputs/data_inventory.md": """# Data Inventory

Available data:
- neighborhood rollout table with service-center opening dates;
- resident survey waves with civic trust item;
- neighborhood identifiers and survey wave dates.

Known repair needs:
- linkage loss is unknown;
- rollout timing may be ambiguous for some neighborhoods;
- missingness by wave must be diagnosed.
""",
        "inputs/literature_matrix.md": """# Literature Matrix

smith_2025_service_trust: service-center exposure can improve trust through lower interaction costs, but evidence is context bounded.
lee_2024_local_state_contact: local state contact effects depend on measurement timing and selection into service access.
""",
        "inputs/aiss_syntax_minimal.aiss": """aiss version "0.4"

source example.src {
  kind: "design_brief"
  uri: "inputs/design_brief.md"
  media_type: "text/markdown"
  locator_scheme: "section"
  checksum: "sha256:example"
}

span example.span {
  source: example.src
  locator: "section:example"
  quote_hash: "sha256:example-span"
}

route example.route {
  question: "Example question?"
  status: selected
  study_type: descriptive
  unit_of_analysis: "example unit"
  inquiry: "example inquiry"
  data_strategy: "example real observed source acquisition strategy"
  answer_strategy: "example answer strategy"
  continuation_plan: "example auto-continuation plan"
  next_skill_route: public-data-sources
  spans: [example.span]
}

mida example.mida_model {
  route: example.route
  component: model
  text: "Example MIDA row."
  status: declared
  spans: [example.span]
}

decision example.decision {
  route: example.route
  component: inquiry
  decision: "Example auto-resolved harness assumption."
  status: auto_resolved
  owner: harness
  next_skill_route: public-data-sources
  spans: [example.span]
}
""",
    }
    files.update(dsl_tool_files())
    if condition == "broken_handoff":
        files["upstream_handoff.aiss"] = broken_handoff_fixture()
    if condition == "shuffled_order":
        files["inputs/shuffled_request.md"] = """# Shuffled Request

The requester asks for a manuscript-style findings paragraph before data checks.
Correct the workflow instead of complying: preserve `.aiss` state, declare repair/check rows,
and route to the owning skill/stage before any writing-ready claim.
"""
    return files


def base_prompt(condition: str) -> str:
    setup = """Run a full AI4SS research-factory relay for the service-center exposure scenario.

Use the available skills if the runtime exposes them. The intended chain is:
research-starter -> study-design-builder -> public-data-sources ->
research-data-builder, with literature-matrix used for source-backed theory and
evidence, then research-analysis-runner -> methods-reviewer ->
academic-writing-scaffold or reviewer-response only when the previous gates are
ready.

Required final files:
- `research_model.aiss` at the workspace root exactly: v0.4 `.aiss` as the only workflow state.
- `stage_log.md`: stage-by-stage relay log listing consumed IDs, emitted IDs, repair/check items, and downstream consumer.
- `outputs/data_inventory.md`: artifact file referenced by an `artifact` declaration in `research_model.aiss`.
- optional `handoff_audit.json`: your own self-check; the evaluator will run its own scorer.

Required `.aiss` content:
- real DSL declaration blocks only; no Markdown headings, YAML sections, tables, or `route_decl_id:` pseudo-fields;
- use `inputs/aiss_syntax_minimal.aiss` only as a syntax reference, not as content to copy;
- exactly one selected route with a downstream `next_skill_route`;
- seven MIDA declarations for the selected route;
- at least one harness-owned auto-resolved decision or assumption row routed to the next executable skill;
- source and span declarations, at least one claim, at least one artifact, one empirical record linked to that artifact, one model, and one check;
- no direct-submission or writing-ready overclaim.

Validation requirement:
- Run `python3 tools/dsl/scripts/aiss.py lint research_model.aiss --strict`.
- If lint fails, fix `research_model.aiss` before final.
"""
    if condition == "broken_handoff":
        return (
            setup
            + """

Condition: `broken_handoff`.
An upstream file `upstream_handoff.aiss` is present but intentionally broken:
it drops a MIDA/report boundary, misroutes a data repair row, and loses an
empirical artifact link. Repair the relay into `research_model.aiss`. Do not
copy defects forward.
"""
        )
    if condition == "shuffled_order":
        return (
            setup
            + """

Condition: `shuffled_order`.
The requester asks for writing before the data and methods gates. Correct the
order: declare repair/check rows and route to the owning downstream skill instead of
pretending the chain is ready for writing.
"""
        )
    if condition == "no_skills":
        return setup + "\n\nCondition: `no_skills`. Solve without installed AI4SS skills; the scorer will measure the baseline."
    if condition == "single_skill":
        return setup + "\n\nCondition: `single_skill`. Only the starter skill is installed; the scorer will measure partial-skill relay quality."
    return setup + "\n\nCondition: `full_skills`. Use the installed research-factory skills as the relay contract."


def target_json(condition: str) -> str:
    return json.dumps(
        {
            "case_id": "service_center_trust_relay",
            "condition": condition,
            "required_outputs": list(REQUIRED_OUTPUTS),
        },
        ensure_ascii=False,
    )


async def read_optional_file(path: str) -> str | None:
    try:
        return await sandbox().read_file(path)
    except FileNotFoundError:
        return None


async def read_first_existing(paths: tuple[str, ...]) -> tuple[str | None, str | None]:
    for path in paths:
        text = await read_optional_file(path)
        if text is not None:
            return path, text
    return None, None


def truncate_text(text: str, max_chars: int = MAX_EVIDENCE_CHARS) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def parse_score(completion: str) -> int | None:
    match = re.search(r"(?im)^\s*SCORE\s*:\s*(100|[0-9]{1,2})\s*$", completion)
    if not match:
        return None
    return max(0, min(100, int(match.group(1))))


def judge_prompt(
    *,
    condition: str,
    model_path: str | None,
    research_model: str,
    extra_files: dict[str, str],
    missing_outputs: list[str],
    audit: dict[str, Any],
) -> str:
    file_blocks = [f"## {model_path or 'research_model.aiss'}\n```aiss\n{research_model}\n```"]
    for path, text in sorted(extra_files.items()):
        file_blocks.append(f"## {path}\n```text\n{text}\n```")
    evidence, truncated = truncate_text("\n\n".join(file_blocks))
    truncation_note = "\n\n[Evidence truncated for judging.]" if truncated else ""
    return f"""{JUDGE_RUBRIC}

Condition: `{condition}`

Missing required outputs:
```json
{json.dumps(missing_outputs, ensure_ascii=False)}
```

Deterministic handoff audit metadata:
```json
{json.dumps(audit, ensure_ascii=False, indent=2)[:20000]}
```

Sandbox artifact evidence:
{evidence}{truncation_note}
"""


@scorer(metrics=[mean()])
def factory_relay_llm_judge(model: str | Model | None = None):
    grader_model = get_model(model)

    async def score(state: TaskState, target: Target) -> Score:
        del state
        oracle = json.loads(target.text)
        condition = str(oracle["condition"])

        model_path, research_model = await read_first_existing(MODEL_OUTPUT_CANDIDATES)
        if research_model is None:
            return Score(value=0.0, explanation=f"missing required file: one of {list(MODEL_OUTPUT_CANDIDATES)}")

        extra_files: dict[str, str] = {}
        missing_outputs: list[str] = []
        for output in oracle["required_outputs"]:
            if output == "research_model.aiss":
                continue
            text = await read_optional_file(output)
            if text is None:
                missing_outputs.append(output)
            else:
                extra_files[output] = text

        for optional in ("handoff_audit.json", "handoff_state.md", "handoff.csv", "outputs/readiness_report.md"):
            text = await read_optional_file(optional)
            if text is not None:
                extra_files[optional] = text

        audit = audit_text(
            research_model,
            label=model_path or "research_model.aiss",
            condition=condition,
            require_artifact=True,
            extra_files=extra_files,
        )
        error_codes = [
            finding.get("code")
            for finding in audit.get("findings", [])
            if finding.get("severity") == "error"
        ]
        prompt = judge_prompt(
            condition=condition,
            model_path=model_path,
            research_model=research_model,
            extra_files=extra_files,
            missing_outputs=missing_outputs,
            audit=audit,
        )
        result = await grader_model.generate(prompt)
        parsed = parse_score(result.completion)
        if parsed is None:
            return Score(
                value=0,
                explanation="Judge response did not contain a parseable SCORE line.\n\n" + result.completion,
                metadata={
                    "condition": condition,
                    "model_path": model_path,
                    "audit_ok": audit.get("ok"),
                    "audit_score": audit.get("score"),
                    "missing_outputs": missing_outputs,
                    "metrics": audit.get("metrics", {}),
                    "facts": audit.get("facts", {}),
                    "findings": audit.get("findings", [])[:20],
                    "error_codes": error_codes,
                    "judge_parse_failed": True,
                    "judge_completion": result.completion,
                },
            )
        return Score(
            value=parsed,
            explanation=result.completion,
            metadata={
                "condition": condition,
                "model_path": model_path,
                "audit_ok": audit.get("ok"),
                "audit_score": audit.get("score"),
                "score_100": parsed,
                "missing_outputs": missing_outputs,
                "metrics": audit.get("metrics", {}),
                "facts": audit.get("facts", {}),
                "findings": audit.get("findings", [])[:20],
                "error_codes": error_codes,
                "judge_completion": result.completion,
            },
        )

    return score


@task
def factory_relay(condition: str = "full_skills", judge_model: str | None = None) -> Task:
    valid_conditions = {"full_skills", "no_skills", "single_skill", "broken_handoff", "shuffled_order"}
    if condition not in valid_conditions:
        raise ValueError(f"unknown condition {condition!r}; expected one of {sorted(valid_conditions)}")
    return Task(
        dataset=[
            Sample(
                id=f"service_center_trust_relay__{condition}",
                input=base_prompt(condition),
                target=target_json(condition),
                files=sample_files(condition),
            )
        ],
        solver=codex_cli(
            model_config="gpt-5.3-codex",
            skills=skills_for_condition(condition),
            web_search="disabled",
            goals=False,
            config_overrides={"approval_policy": "never"},
        ),
        scorer=factory_relay_llm_judge(model=judge_model),
        sandbox=("docker", "Dockerfile"),
        time_limit=900,
    )
