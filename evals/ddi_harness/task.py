"""Inspect agent-runtime eval for the AI4SS DDI cleaning harness.

This is intentionally an Inspect task, not a local subprocess smoke test:
- each Sample receives only fixture files;
- inspect_swe starts a real Codex CLI agent runtime;
- the AI4SS DDI skills are supplied through the official solver `skills=...`;
- Docker provides a fresh sandbox per sample;
- the scorer reruns the submitted R script, records deterministic checks as
  metadata, and uses an LLM-as-judge rubric for the final score.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any

import yaml
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import Model, get_model
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox
from inspect_swe import codex_cli


ROOT = Path(__file__).resolve().parents[2]
SKILL_NAMES = ("codebook-parse", "cleaning-contract", "cleaning-execute")
AI4SS_DDI_SKILLS = [ROOT / "skills" / name for name in SKILL_NAMES]
OUTPUT_CSV = "fixture-clean.csv"
SCRIPT = "fixture-cleaning.R"
METADATA = "ddi-metadata.yaml"
MAX_JUDGE_CHARS = 60000

JUDGE_RUBRIC = """You are grading an AI4SS DDI survey-cleaning harness eval.

Judge only the sandbox artifacts, expected oracle, and deterministic check
metadata provided below. The deterministic checks are evidence and objective
diagnostics, not the final score.

Task: a live Codex agent must use the AI4SS DDI skills to parse survey metadata,
declare a cleaning contract, implement a reproducible R cleaning script, rerun
the script, create the clean CSV, and preserve metadata provenance.

Score on a 0-100 scale.

Rubric:
- Cleaning-contract fidelity to the harness decisions and DDI metadata: 25 points.
- Correct executable transformation in the R script, including missing-value
  semantics before recode/reversal, filtering, renaming, derived variables, and
  weight normalization: 30 points.
- Clean CSV correctness relative to the expected oracle, including columns,
  row order, missing values, and numeric tolerances: 25 points.
- Metadata/provenance quality: non-empty cleaning contract, CleaningOperation
  event, file references, and reproducible audit trail: 15 points.
- Harness discipline and reproducibility: no hand-written output without script,
  no human-blocking decisions, and no unrelated workspace edits: 5 points.

Caps and penalties:
- If the R script is missing, score 0.
- If the script does not rerun, cap at 40.
- If the clean CSV is missing after rerun, cap at 35.
- If the clean CSV materially disagrees with the oracle, cap at 65 even if the
  explanation is plausible.
- If metadata lacks a cleaning contract or CleaningOperation event, cap at 80.
- If the output is hand-written or not reproducible from `raw.csv`, cap at 30.

Return exactly this format:
SCORE: <integer from 0 to 100>
REASON: <brief explanation grounded in the artifacts and check metadata>
"""


class CaseSpec:
    def __init__(
        self,
        *,
        case_id: str,
        title: str,
        raw_csv: str,
        variables: list[dict[str, Any]],
        decisions: list[str],
        expected_columns: list[str],
        expected_rows: list[dict[str, Any]],
        script_required_patterns: list[str],
    ) -> None:
        self.case_id = case_id
        self.title = title
        self.raw_csv = raw_csv
        self.variables = variables
        self.decisions = decisions
        self.expected_columns = expected_columns
        self.expected_rows = expected_rows
        self.script_required_patterns = script_required_patterns


def variable(
    name: str,
    label: str,
    representation: dict[str, Any],
    *,
    missing: dict[str, Any] | None = None,
    is_weight: bool = False,
    is_geographic: bool = False,
    concept: str | None = None,
) -> dict[str, Any]:
    return {
        "id": f"var_{name}",
        "name": name,
        "label": label,
        "is_temporal": False,
        "is_geographic": is_geographic,
        "is_weight": is_weight,
        "concept": concept,
        "unit_type": "Person",
        "universe": None,
        "representation": representation,
        "missing": missing
        or {"schema_ref": None, "codes": {}, "ranges": [], "blank_is_missing": True},
        "source_variables": [],
        "derivation_rule": None,
        "_parse_flags": [],
        "_needs_review": False,
    }


def code_repr(codes: dict[int, str], classification_level: str = "nominal") -> dict[str, Any]:
    return {
        "type": "code",
        "storage_type": "integer",
        "codes": codes,
        "category_scheme_ref": None,
        "classification_level": classification_level,
    }


def scale_repr(codes: dict[int, str]) -> dict[str, Any]:
    return {
        "type": "scale",
        "storage_type": "integer",
        "codes": codes,
        "category_scheme_ref": None,
    }


def number_repr(storage_type: str = "numeric") -> dict[str, Any]:
    return {"type": "numeric", "storage_type": storage_type}


def case_specs() -> list[CaseSpec]:
    return [
        CaseSpec(
            case_id="positive_missing_and_execution_order",
            title="Positive missing treatment before reversal; valid 9 in another variable",
            raw_csv="""country,trust,edu,drop_me,w
156,9,1,x,1
156,4,9,x,2
392,1,1,x,5
156,2,2,x,3
""",
            variables=[
                variable(
                    "country",
                    "Country code",
                    code_repr({156: "China", 392: "Japan"}),
                    is_geographic=True,
                    concept="country",
                ),
                variable(
                    "trust",
                    "Institutional trust, 1 low to 4 high, 9 no answer",
                    scale_repr({1: "low", 2: "some", 3: "high", 4: "very high"}),
                    missing={
                        "schema_ref": None,
                        "codes": {9: {"label": "No answer", "type": "refused"}},
                        "ranges": [],
                        "blank_is_missing": True,
                    },
                    concept="institutional trust",
                ),
                variable(
                    "edu",
                    "Education, where 9 is postgraduate and valid data",
                    code_repr({1: "primary", 2: "secondary", 9: "postgraduate"}, "ordinal"),
                    concept="education",
                ),
                variable("drop_me", "Administrative field to drop", {"type": "text", "storage_type": "string"}),
                variable("w", "Sampling weight", number_repr(), is_weight=True, concept="survey weight"),
            ],
            decisions=[
                "Universe: keep only China rows, `country == 156`.",
                "`trust`: code 9 is refused/no-answer missing; apply missing treatment before recode or reversal; reverse the 1-4 scale as `5 - trust`; rename to `trust_rev`.",
                "`edu`: code 9 is valid substantive postgraduate data; recode `{1: 0, 2: 1, 9: 2}` and rename to `edu_level`.",
                "Drop `drop_me` from the final analysis dataset.",
                "Normalize weight `w` so the retained-sample mean is 1, output as `weight`.",
                "Build `trust_edu_index = trust_rev + edu_level` after rename.",
                "Final columns, in order: `trust_rev`, `edu_level`, `trust_edu_index`, `weight`.",
            ],
            expected_columns=["trust_rev", "edu_level", "trust_edu_index", "weight"],
            expected_rows=[
                {"trust_rev": None, "edu_level": 0, "trust_edu_index": None, "weight": 0.5},
                {"trust_rev": 1, "edu_level": 2, "trust_edu_index": 3, "weight": 1.0},
                {"trust_rev": 3, "edu_level": 1, "trust_edu_index": 4, "weight": 1.5},
            ],
            script_required_patterns=[r"country", r"156", r"trust", r"edu", r"weight"],
        ),
        CaseSpec(
            case_id="range_missing_and_valid_sentinel",
            title="Range-style missing value and a superficially suspicious valid code",
            raw_csv="""country,region,life_sat,party,wt,audit
156,1,99,7,1,x
156,2,10,9,3,x
156,1,2,1,2,x
392,1,8,7,9,x
""",
            variables=[
                variable(
                    "country",
                    "Country code",
                    code_repr({156: "China", 392: "Japan"}),
                    is_geographic=True,
                    concept="country",
                ),
                variable("region", "Fixture region", code_repr({1: "North", 2: "South"}), concept="region"),
                variable(
                    "life_sat",
                    "Life satisfaction, 0 low to 10 high, 99 refused",
                    number_repr("integer"),
                    missing={
                        "schema_ref": None,
                        "codes": {99: {"label": "Refused", "type": "refused"}},
                        "ranges": [],
                        "blank_is_missing": True,
                    },
                    concept="life satisfaction",
                ),
                variable(
                    "party",
                    "Party proximity, 9 is a valid other-party response",
                    code_repr({1: "incumbent", 7: "nonpartisan", 9: "other valid"}),
                    concept="party proximity",
                ),
                variable("wt", "Sampling weight", number_repr(), is_weight=True, concept="survey weight"),
                variable("audit", "Administrative field to drop", {"type": "text", "storage_type": "string"}),
            ],
            decisions=[
                "Universe: keep rows where `country == 156` and `region` is 1 or 2.",
                "`life_sat`: 99 is missing/refused; reverse the 0-10 scale as `10 - life_sat`; rename to `life_sat_rev`.",
                "`party`: code 9 is valid, not missing; recode `{1: 1, 7: 0, 9: 2}` and rename to `party_group`.",
                "Drop `audit` from the final analysis dataset.",
                "Normalize weight `wt` so the retained-sample mean is 1, output as `weight`.",
                "Build `attitude_index = life_sat_rev + party_group` after missing treatment and recode.",
                "Final columns, in order: `life_sat_rev`, `party_group`, `attitude_index`, `weight`.",
            ],
            expected_columns=["life_sat_rev", "party_group", "attitude_index", "weight"],
            expected_rows=[
                {"life_sat_rev": None, "party_group": 0, "attitude_index": None, "weight": 0.5},
                {"life_sat_rev": 0, "party_group": 2, "attitude_index": 2, "weight": 1.5},
                {"life_sat_rev": 8, "party_group": 1, "attitude_index": 9, "weight": 1.0},
            ],
            script_required_patterns=[r"country", r"156", r"region", r"life_sat", r"party", r"wt"],
        ),
        CaseSpec(
            case_id="derive_after_rename_and_drop",
            title="Derived variable must happen after filtering, renaming, and reverse coding",
            raw_csv="""country,age,income,trust,audit,wt
156,18,999,1,x,2
156,30,5,4,x,2
156,45,8,2,x,4
840,22,6,3,x,3
""",
            variables=[
                variable(
                    "country",
                    "Country code",
                    code_repr({156: "China", 840: "United States"}),
                    is_geographic=True,
                    concept="country",
                ),
                variable("age", "Age in years", number_repr("integer"), concept="age"),
                variable(
                    "income",
                    "Income score, 999 refused",
                    number_repr("integer"),
                    missing={
                        "schema_ref": None,
                        "codes": {999: {"label": "Refused", "type": "refused"}},
                        "ranges": [],
                        "blank_is_missing": True,
                    },
                    concept="income",
                ),
                variable(
                    "trust",
                    "Trust, 1 low to 4 high",
                    scale_repr({1: "low", 2: "some", 3: "high", 4: "very high"}),
                    concept="trust",
                ),
                variable("audit", "Administrative field to drop", {"type": "text", "storage_type": "string"}),
                variable("wt", "Sampling weight", number_repr(), is_weight=True, concept="survey weight"),
            ],
            decisions=[
                "Universe: keep rows where `country == 156` and `age >= 21`.",
                "`income`: 999 is missing/refused; rename to `income_score`.",
                "`trust`: reverse the 1-4 scale as `5 - trust`; rename to `trust_rev`.",
                "Drop `audit` from the final analysis dataset.",
                "Normalize weight `wt` so the retained-sample mean is 1, output as `weight`.",
                "Build `resources_trust = income_score * trust_rev` after filtering, missing treatment, rename, and reverse coding.",
                "Final columns, in order: `income_score`, `trust_rev`, `resources_trust`, `weight`.",
            ],
            expected_columns=["income_score", "trust_rev", "resources_trust", "weight"],
            expected_rows=[
                {"income_score": 5, "trust_rev": 1, "resources_trust": 5, "weight": 2 / 3},
                {"income_score": 8, "trust_rev": 3, "resources_trust": 24, "weight": 4 / 3},
            ],
            script_required_patterns=[r"country", r"156", r"age", r"21", r"income", r"trust", r"wt"],
        ),
    ]


def fixture_metadata(case: CaseSpec) -> str:
    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "ddi_version": "3.3",
        "study": {
            "name": f"Agent runtime harness fixture: {case.case_id}",
            "id": case.case_id,
            "agency": "AI4SS eval harness",
            "universe": "Adults in the fixture survey",
            "analysis_unit": "Person",
            "data_source": "raw.csv",
            "wave": None,
        },
        "shared_category_schemes": {},
        "shared_missing_schemas": {},
        "variables": case.variables,
        "processing_events": [
            {
                "event_id": "evt001",
                "type": "ParseDDI",
                "timestamp": "2026-07-04T00:00:00Z",
                "description": "Fixture DDI metadata prepared for Inspect agent-runtime eval.",
                "inputs": ["raw.csv"],
                "outputs": [METADATA],
                "operator": "eval_fixture",
            }
        ],
    }
    return yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)


def sample_files(case: CaseSpec) -> dict[str, str]:
    return {
        "AGENTS.md": """# Agent Runtime Harness Eval

Use the AI4SS DDI survey-cleaning skills made available to this Codex runtime:
- `codebook-parse`
- `cleaning-contract`
- `cleaning-execute`

Skill routing table:
| Skill | Use when | Required input | Required output / next route |
|---|---|---|---|
| `codebook-parse` | DDI metadata or codebook content must become machine-readable variable metadata. | `raw.csv` and `ddi-metadata.yaml`. | Parsed/validated variable metadata, missing-value semantics, and `next_skill_route: cleaning-contract`. |
| `cleaning-contract` | Parsed metadata plus fixture decisions must become deterministic cleaning rules. | Parsed metadata, raw data preview, harness decisions. | Non-empty `cleaning_contract` in `ddi-metadata.yaml`, ordered operations, and `next_skill_route: cleaning-execute`. |
| `cleaning-execute` | A declared cleaning contract must be implemented and verified. | `raw.csv`, `ddi-metadata.yaml`, cleaning contract. | `fixture-cleaning.R`, `fixture-clean.csv`, `CleaningOperation` processing event, and no further route unless analysis is requested. |

Do not block for human judgment. Resolve every fixture decision automatically
from the harness prompt and metadata.

Do not edit files outside this workspace.
""",
        "raw.csv": case.raw_csv,
        METADATA: fixture_metadata(case),
    }


def prompt(case: CaseSpec) -> str:
    decisions = "\n".join(f"- {decision}" for decision in case.decisions)
    return f"""Run the AI4SS DDI survey-cleaning harness end to end for this fixture.

This is case `{case.case_id}`: {case.title}.

Use the existing `raw.csv` and `{METADATA}`. Apply the available AI4SS DDI
skills as the harness: declare the cleaning contract, execute it, and preserve
the metadata/provenance trail.

Harness decisions to auto-declare and execute:
{decisions}

Required files:
- update `{METADATA}` with a non-empty `cleaning_contract` and append a
  `processing_events` entry whose `type` is `CleaningOperation`;
- create `{SCRIPT}`, a reproducible R script implementing the declared
  contract from `raw.csv`;
- run `{SCRIPT}` and create `{OUTPUT_CSV}`.

Do not create a hand-written CSV without a reproducible script. The evaluator
will rerun `{SCRIPT}` in the sandbox before scoring.
"""


def target_json(case: CaseSpec) -> str:
    return json.dumps(
        {
            "case_id": case.case_id,
            "expected_columns": case.expected_columns,
            "expected_rows": case.expected_rows,
            "script_required_patterns": case.script_required_patterns,
        },
        ensure_ascii=False,
    )


def parse_scalar(value: str) -> Any:
    normalized = value.strip()
    if normalized in {"", "NA", "NaN", "nan", "NULL", "null", "None"}:
        return None
    try:
        return float(normalized)
    except ValueError:
        return normalized


def same_value(actual: Any, expected: Any, *, tolerance: float = 1e-6) -> bool:
    if expected is None:
        return actual is None
    if isinstance(expected, (int, float)):
        try:
            actual_float = float(actual)
        except (TypeError, ValueError):
            return False
        return math.isclose(actual_float, float(expected), rel_tol=tolerance, abs_tol=tolerance)
    return str(actual) == str(expected)


def compare_rows(
    rows: list[dict[str, str]],
    expected_columns: list[str],
    expected_rows: list[dict[str, Any]],
) -> tuple[bool, str, dict[str, Any]]:
    if not rows:
        return False, f"{OUTPUT_CSV} has no rows", {}
    columns = list(rows[0].keys())
    if columns != expected_columns:
        return False, f"unexpected columns: {columns}", {"columns": columns, "expected_columns": expected_columns}
    if len(rows) != len(expected_rows):
        return False, f"expected {len(expected_rows)} rows, got {len(rows)}", {"rows": len(rows)}

    actual_rows = [{key: parse_scalar(row[key]) for key in expected_columns} for row in rows]
    for row_index, (actual, expected) in enumerate(zip(actual_rows, expected_rows, strict=True), start=1):
        for key in expected_columns:
            if not same_value(actual[key], expected[key]):
                return (
                    False,
                    f"row {row_index} column {key} mismatch: got {actual[key]!r}, expected {expected[key]!r}",
                    {"actual": actual_rows, "expected": expected_rows},
                )
    return True, "clean CSV matched oracle", {"actual": actual_rows}


def metadata_passes(metadata_yaml: str) -> tuple[bool, str, dict[str, Any]]:
    metadata = yaml.safe_load(metadata_yaml)
    if not isinstance(metadata, dict):
        return False, f"{METADATA} is not a YAML mapping", {}
    contract = metadata.get("cleaning_contract")
    if not contract:
        return False, "metadata lacks a non-empty cleaning_contract", {}
    events = metadata.get("processing_events") or []
    if not isinstance(events, list) or not events:
        return False, "metadata lacks processing_events", {}
    cleaning_events = [event for event in events if isinstance(event, dict) and event.get("type") == "CleaningOperation"]
    if not cleaning_events:
        return False, "processing_events lacks a CleaningOperation event", {"events": events[-3:]}
    last_event = cleaning_events[-1]
    if OUTPUT_CSV not in json.dumps(last_event, ensure_ascii=False):
        return False, f"CleaningOperation event does not reference {OUTPUT_CSV}", {"event": last_event}
    return True, "metadata provenance matched oracle", {"processing_event": last_event.get("event_id")}


def script_passes(script_text: str, required_patterns: list[str]) -> tuple[bool, str]:
    for pattern in required_patterns:
        if not re.search(pattern, script_text, flags=re.IGNORECASE):
            return False, f"{SCRIPT} does not contain required pattern: {pattern}"
    return True, "script text matched oracle"


def truncate_text(text: str, max_chars: int = MAX_JUDGE_CHARS) -> tuple[str, bool]:
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
    oracle: dict[str, Any],
    raw_csv: str | None,
    script_text: str | None,
    clean_csv: str | None,
    metadata_yaml: str | None,
    checks: dict[str, Any],
) -> str:
    blocks = [
        "## Expected Oracle\n```json\n"
        + json.dumps(oracle, ensure_ascii=False, indent=2)
        + "\n```",
        "## Deterministic Check Metadata\n```json\n"
        + json.dumps(checks, ensure_ascii=False, indent=2)
        + "\n```",
    ]
    if raw_csv is not None:
        blocks.append(f"## raw.csv\n```csv\n{raw_csv}\n```")
    if script_text is not None:
        blocks.append(f"## {SCRIPT}\n```r\n{script_text}\n```")
    if clean_csv is not None:
        blocks.append(f"## {OUTPUT_CSV}\n```csv\n{clean_csv}\n```")
    if metadata_yaml is not None:
        blocks.append(f"## {METADATA}\n```yaml\n{metadata_yaml}\n```")
    evidence, truncated = truncate_text("\n\n".join(blocks))
    truncation_note = "\n\n[Evidence truncated for judging.]" if truncated else ""
    return f"""{JUDGE_RUBRIC}

Sandbox artifact evidence:
{evidence}{truncation_note}
"""


@scorer(metrics=[mean()])
def ddi_harness_llm_judge(model: str | Model | None = None):
    grader_model = get_model(model)

    async def score(state: TaskState, target: Target) -> Score:
        del state
        oracle = json.loads(target.text)
        checks: dict[str, Any] = {"case_id": oracle["case_id"]}
        raw_csv: str | None = None
        script_text: str | None = None
        clean_csv: str | None = None
        metadata_yaml: str | None = None

        try:
            raw_csv = await sandbox().read_file("raw.csv")
        except FileNotFoundError:
            checks["raw_csv"] = {"ok": False, "explanation": "raw.csv missing"}

        try:
            script_text = await sandbox().read_file(SCRIPT)
        except FileNotFoundError as exc:
            return Score(value=0, explanation=f"missing required file: {exc}", metadata=checks)

        script_ok, script_explanation = script_passes(script_text, oracle["script_required_patterns"])
        checks["script_patterns"] = {"ok": script_ok, "explanation": script_explanation}

        result = await sandbox().exec(["Rscript", SCRIPT], timeout=120)
        checks["rerun"] = {
            "ok": result.success,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }
        if not result.success:
            prompt_text = judge_prompt(
                oracle=oracle,
                raw_csv=raw_csv,
                script_text=script_text,
                clean_csv=None,
                metadata_yaml=None,
                checks=checks,
            )
            judge = await grader_model.generate(prompt_text)
            parsed = parse_score(judge.completion)
            value = 0 if parsed is None else min(parsed, 40)
            return Score(
                value=value,
                explanation=(
                    "Judge response did not contain a parseable SCORE line.\n\n"
                    + judge.completion
                    if parsed is None
                    else judge.completion
                ),
                metadata={**checks, "judge_parse_failed": parsed is None, "judge_completion": judge.completion},
            )

        try:
            clean_csv = await sandbox().read_file(OUTPUT_CSV)
            metadata_yaml = await sandbox().read_file(METADATA)
        except FileNotFoundError as exc:
            checks["post_rerun_files"] = {"ok": False, "explanation": f"missing required file after rerun: {exc}"}
            prompt_text = judge_prompt(
                oracle=oracle,
                raw_csv=raw_csv,
                script_text=script_text,
                clean_csv=clean_csv,
                metadata_yaml=metadata_yaml,
                checks=checks,
            )
            judge = await grader_model.generate(prompt_text)
            parsed = parse_score(judge.completion)
            value = 0 if parsed is None else min(parsed, 35)
            return Score(
                value=value,
                explanation=(
                    "Judge response did not contain a parseable SCORE line.\n\n"
                    + judge.completion
                    if parsed is None
                    else judge.completion
                ),
                metadata={**checks, "judge_parse_failed": parsed is None, "judge_completion": judge.completion},
            )

        rows = list(csv.DictReader(io.StringIO(clean_csv)))
        rows_ok, rows_explanation, rows_metadata = compare_rows(
            rows,
            oracle["expected_columns"],
            oracle["expected_rows"],
        )
        checks["clean_csv"] = {
            "ok": rows_ok,
            "explanation": rows_explanation,
            "metadata": rows_metadata,
            "sha256": hashlib.sha256(clean_csv.encode("utf-8")).hexdigest(),
        }

        metadata_ok, metadata_explanation, event_metadata = metadata_passes(metadata_yaml)
        checks["metadata"] = {
            "ok": metadata_ok,
            "explanation": metadata_explanation,
            "metadata": event_metadata,
        }

        prompt_text = judge_prompt(
            oracle=oracle,
            raw_csv=raw_csv,
            script_text=script_text,
            clean_csv=clean_csv,
            metadata_yaml=metadata_yaml,
            checks=checks,
        )
        judge = await grader_model.generate(prompt_text)
        parsed = parse_score(judge.completion)
        if parsed is None:
            return Score(
                value=0,
                explanation="Judge response did not contain a parseable SCORE line.\n\n" + judge.completion,
                metadata={**checks, "judge_parse_failed": True, "judge_completion": judge.completion},
            )
        capped = parsed
        caps: list[str] = []
        if not rows_ok:
            capped = min(capped, 65)
            caps.append("clean_csv_mismatch_cap_65")
        if not metadata_ok:
            capped = min(capped, 80)
            caps.append("metadata_cap_80")
        if not script_ok:
            capped = min(capped, 85)
            caps.append("script_pattern_cap_85")

        return Score(
            value=capped,
            explanation=judge.completion,
            metadata={
                **checks,
                "score_100": capped,
                "raw_judge_score_100": parsed,
                "caps_applied": caps,
                "judge_completion": judge.completion,
            },
        )

    return score


@task
def ddi_harness(judge_model: str | None = None) -> Task:
    return Task(
        dataset=[
            Sample(
                id=case.case_id,
                input=prompt(case),
                target=target_json(case),
                files=sample_files(case),
            )
            for case in case_specs()
        ],
        solver=codex_cli(
            model_config="gpt-5.3-codex",
            skills=AI4SS_DDI_SKILLS,
            web_search="disabled",
            goals=False,
            config_overrides={"approval_policy": "never"},
        ),
        scorer=ddi_harness_llm_judge(model=judge_model),
        sandbox=("docker", "Dockerfile"),
        time_limit=900,
    )
