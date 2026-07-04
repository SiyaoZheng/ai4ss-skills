#!/usr/bin/env python3
"""Deterministic simulation for evaluating skill-guided agent behavior.

The simulation compares two agent conditions on the same scholar-facing tasks:

- no_skill: generic assistant behavior without the local project skills.
- skill_guided: behavior constrained by the local scholar workbench skills.

It does not call an LLM. The goal is to test whether the skill universe changes
the shape of deliverables in ways scholars can inspect.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SimulatedOutput:
    condition: str
    artifacts: tuple[str, ...]
    trace_markers: tuple[str, ...]
    validator_refs: tuple[str, ...]
    author_decisions: tuple[str, ...]
    risky_moves: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    scholar_question: str
    task: str
    expected_artifacts: tuple[str, ...]
    expected_trace_markers: tuple[str, ...]
    expected_validators: tuple[str, ...]
    no_skill: SimulatedOutput
    skill_guided: SimulatedOutput


WEIGHTS = {
    "artifacts": 30,
    "traceability": 20,
    "boundary": 20,
    "validation": 15,
    "author_decision": 15,
}


CASES = (
    EvalCase(
        case_id="data_provenance",
        scholar_question="数据怎么来的，样本怎么变的？",
        task="Build a city-year analysis sample from raw panel, controls, and policy list.",
        expected_artifacts=(".aiss row-loss checks", ".aiss merge checks", ".aiss variable-provenance observations", "output/logs/build_panel.log"),
        expected_trace_markers=("row counts", "merge unmatched rows", "variable construction rule", "raw data untouched"),
        expected_validators=("validate_ai4ss_model.py",),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=("analysis_panel.csv", "loose summary statistics", ".aiss row-loss checks", "output/logs/build_panel.log"),
            trace_markers=("row counts", "raw data untouched"),
            validator_refs=(),
            author_decisions=("ask whether to include controls",),
            risky_moves=("does not write a merge review declaration", "variable construction is described only in prose"),
            summary="Returns a usable cleaned dataset and some row-count evidence, but merge ambiguity and variable provenance remain weak.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss row-loss checks", ".aiss merge checks", ".aiss variable-provenance observations", "output/logs/build_panel.log"),
            trace_markers=("row counts", "merge unmatched rows", "variable construction rule", "raw data untouched"),
            validator_refs=("validate_ai4ss_model.py",),
            author_decisions=("decide whether left_only city-years remain in scope",),
            risky_moves=(),
            summary="Returns the derived data plus checked .aiss declarations that expose row loss and merge ambiguity.",
        ),
    ),
    EvalCase(
        case_id="literature_evidence",
        scholar_question="文献证据是不是一手来源？",
        task="Build a literature base for AI adoption and innovation outcomes before writing a review.",
        expected_artifacts=(".aiss literature evidence declarations", ".aiss screening decisions", ".aiss source locators"),
        expected_trace_markers=("DOI or source URL", "claim_source_locator", "verification_level", "included_in_synthesis"),
        expected_validators=("validate_ai4ss_model.py",),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=(".aiss literature evidence declarations", "loose literature notes"),
            trace_markers=("DOI or source URL", "verification_level"),
            validator_refs=(),
            author_decisions=("ask which papers are central enough for full-text checking",),
            risky_moves=("mixes secondary summaries into synthesis",),
            summary="Returns rough source notes, but source locators and synthesis eligibility are not enforced.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss literature evidence declarations", ".aiss screening decisions", ".aiss source locators"),
            trace_markers=("DOI or source URL", "claim_source_locator", "verification_level"),
            validator_refs=("validate_ai4ss_model.py",),
            author_decisions=("decide whether abstract-only rows can support a background claim",),
            risky_moves=(),
            summary="Returns checked source-evidence declarations that mostly separate verified primary sources from unverified or secondary-only evidence; synthesis eligibility still needs spot checking.",
        ),
    ),
    EvalCase(
        case_id="claim_discipline",
        scholar_question="结果解释有没有说过头？",
        task="Prepare result-section support from table1, event-study figure, and research design notes.",
        expected_artifacts=(".aiss diagnostic checks", ".aiss bounded claim declarations", ".aiss author decision declarations"),
        expected_trace_markers=("estimand", "sample and N", "FE and clustering", "support_level"),
        expected_validators=("validate_ai4ss_model.py", "validate_ai4ss_model.py"),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=("result prose draft", "loose claim notes"),
            trace_markers=("estimand", "sample and N"),
            validator_refs=(),
            author_decisions=("ask whether wording is too strong",),
            risky_moves=("writes final manuscript prose", "mechanism evidence is not separated from interpretation"),
            summary="Returns a plausible paragraph plus notes, but it crosses the direct-writing boundary and under-specifies claim strength.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss diagnostic checks", ".aiss bounded claim declarations", ".aiss author decision declarations"),
            trace_markers=("estimand", "sample and N", "support_level"),
            validator_refs=("validate_ai4ss_model.py", "validate_ai4ss_model.py"),
            author_decisions=("author decides causal language", "author decides whether mechanism claim needs new analysis"),
            risky_moves=(),
            summary="Returns claim slots and risks, leaving final prose and scholarly judgment to the author; FE/cluster still need model-object confirmation.",
        ),
    ),
    EvalCase(
        case_id="revision_trace",
        scholar_question="返修有没有证据链？",
        task="Process reviewer comments about identification, mechanism evidence, and literature coverage.",
        expected_artifacts=(".aiss reviewer-request decisions", "revision_trace/", ".aiss open author decisions"),
        expected_trace_markers=("comment_id", "planned_action", "done_evidence", "confidentiality_status"),
        expected_validators=("validate_ai4ss_model.py",),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=("response letter draft", "loose revision plan"),
            trace_markers=("comment_id", "planned_action"),
            validator_refs=(),
            author_decisions=("ask if tone is acceptable",),
            risky_moves=("writes final response prose", "done evidence is missing for several promised changes"),
            summary="Returns a plausible response package, but author cannot verify every promised change before prose appears.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss reviewer-request decisions", "revision_trace/", ".aiss open author decisions"),
            trace_markers=("comment_id", "planned_action", "confidentiality_status"),
            validator_refs=("validate_ai4ss_model.py",),
            author_decisions=("author decides rebut versus partial accept", "author approves confidential material handling"),
            risky_moves=(),
            summary="Returns a response scaffold with evidence links and open decisions; done_evidence still depends on actual analysis completion.",
        ),
    ),
)


def coverage_score(actual: tuple[str, ...], expected: tuple[str, ...]) -> float:
    if not expected:
        return 1.0
    actual_set = set(actual)
    return sum(1 for item in expected if item in actual_set) / len(expected)


def score_output(case: EvalCase, output: SimulatedOutput) -> dict[str, float]:
    artifact = coverage_score(output.artifacts, case.expected_artifacts)
    trace = coverage_score(output.trace_markers, case.expected_trace_markers)
    validation = coverage_score(output.validator_refs, case.expected_validators)
    boundary = max(0.0, 1.0 - 0.35 * len(output.risky_moves))
    author_decision = 1.0 if output.author_decisions else 0.0
    total = (
        artifact * WEIGHTS["artifacts"]
        + trace * WEIGHTS["traceability"]
        + boundary * WEIGHTS["boundary"]
        + validation * WEIGHTS["validation"]
        + author_decision * WEIGHTS["author_decision"]
    )
    return {
        "artifacts": artifact * WEIGHTS["artifacts"],
        "traceability": trace * WEIGHTS["traceability"],
        "boundary": boundary * WEIGHTS["boundary"],
        "validation": validation * WEIGHTS["validation"],
        "author_decision": author_decision * WEIGHTS["author_decision"],
        "total": total,
    }


def fmt_score(value: float) -> str:
    return f"{value:.1f}"


def render_report() -> str:
    lines: list[str] = []
    lines.append("# Simulated Skill-Use Evaluation")
    lines.append("")
    lines.append("Status: non-blinded demonstration. Use `scripts/run_blind_skill_use_eval.py` for the condition-blinded packet protocol.")
    lines.append("")
    lines.append("This deterministic simulation compares a careful generic agent with a skill-guided agent on four scholar-facing workbench tasks. It checks output structure, not model intelligence.")
    lines.append("")
    lines.append("## Rubric")
    lines.append("")
    lines.append("| dimension | weight | what it asks |")
    lines.append("|---|---:|---|")
    lines.append("| artifacts | 30 | Did the agent produce the canonical audit objects? |")
    lines.append("| traceability | 20 | Can claims or rows be traced to sources, logs, or model objects? |")
    lines.append("| boundary | 20 | Did the agent avoid direct final academic prose or unsafe scholarly moves? |")
    lines.append("| validation | 15 | Did the agent name the relevant validator or gate? |")
    lines.append("| author_decision | 15 | Did the agent surface decisions the researcher must own? |")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| case | scholar question | no_skill | skill_guided | delta |")
    lines.append("|---|---|---:|---:|---:|")

    totals = {"no_skill": 0.0, "skill_guided": 0.0}
    details: list[str] = []
    for case in CASES:
        no_score = score_output(case, case.no_skill)
        skill_score = score_output(case, case.skill_guided)
        totals["no_skill"] += no_score["total"]
        totals["skill_guided"] += skill_score["total"]
        delta = skill_score["total"] - no_score["total"]
        lines.append(
            f"| `{case.case_id}` | {case.scholar_question} | {fmt_score(no_score['total'])} | "
            f"{fmt_score(skill_score['total'])} | +{fmt_score(delta)} |"
        )

        details.append(f"### `{case.case_id}`")
        details.append("")
        details.append(f"Task: {case.task}")
        details.append("")
        details.append("| condition | artifacts | trace markers | risky moves | summary |")
        details.append("|---|---|---|---|---|")
        for output, score in ((case.no_skill, no_score), (case.skill_guided, skill_score)):
            artifacts = ", ".join(output.artifacts) or "none"
            traces = ", ".join(output.trace_markers) or "none"
            risks = ", ".join(output.risky_moves) or "none"
            details.append(
                f"| `{output.condition}` ({fmt_score(score['total'])}) | {artifacts} | {traces} | {risks} | {output.summary} |"
            )
        details.append("")

    avg_no = totals["no_skill"] / len(CASES)
    avg_skill = totals["skill_guided"] / len(CASES)
    lines.append("")
    lines.append(f"Average no_skill score: **{fmt_score(avg_no)} / 100**")
    lines.append(f"Average skill_guided score: **{fmt_score(avg_skill)} / 100**")
    lines.append(f"Average gain: **+{fmt_score(avg_skill - avg_no)} points**")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The simulated gain comes mostly from three changes: canonical artifacts appear, risky direct-writing moves are penalized, and validation gates become explicit. The skill-guided condition is not more creative; it is more inspectable.")
    lines.append("")
    lines.append("For teaching, this is the right claim: skills are useful only if they change the agent from answer production to audit-object production.")
    lines.append("")
    lines.append("## Case Details")
    lines.append("")
    lines.extend(details)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Optional Markdown report path.")
    args = parser.parse_args()

    report = render_report()
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
