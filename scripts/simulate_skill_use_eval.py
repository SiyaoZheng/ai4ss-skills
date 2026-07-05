#!/usr/bin/env python3
"""Diagnostic simulation for inspecting skill-guided output structure.

The simulation compares two agent conditions on the same scholar-facing tasks:

- no_skill: generic assistant behavior without the local project skills.
- skill_guided: behavior constrained by the local scholar workbench skills.

It does not call an LLM and must not be reported as an eval score. The goal is
to inspect whether the skill universe changes the shape of deliverables in ways
scholars can inspect.
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
    assumption_register: tuple[str, ...]
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
    "assumption_register": 15,
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
            assumption_register=("auto-select controls using declared design and data availability",),
            risky_moves=("omits a merge review declaration", "variable construction is described only in prose"),
            summary="Returns a usable cleaned dataset and some row-count evidence, but merge ambiguity and variable provenance remain weak.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss row-loss checks", ".aiss merge checks", ".aiss variable-provenance observations", "output/logs/build_panel.log"),
            trace_markers=("row counts", "merge unmatched rows", "variable construction rule", "raw data untouched"),
            validator_refs=("validate_ai4ss_model.py",),
            assumption_register=("auto-route left_only city-years to scope and linkage checks",),
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
            assumption_register=("auto-prioritize full-text checking by source relevance and claim centrality",),
            risky_moves=("mixes secondary summaries into synthesis",),
            summary="Returns rough source notes, but source locators and synthesis eligibility are not enforced.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss literature evidence declarations", ".aiss screening decisions", ".aiss source locators"),
            trace_markers=("DOI or source URL", "claim_source_locator", "verification_level"),
            validator_refs=("validate_ai4ss_model.py",),
            assumption_register=("auto-bound abstract-only rows to background context unless source checks support more",),
            risky_moves=(),
            summary="Returns checked source-evidence declarations that mostly separate verified primary sources from unverified or secondary-only evidence; synthesis eligibility still needs spot checking.",
        ),
    ),
    EvalCase(
        case_id="claim_discipline",
        scholar_question="结果解释有没有说过头？",
        task="Prepare result-section support from table1, event-study figure, and research design notes.",
        expected_artifacts=(".aiss diagnostic checks", ".aiss bounded claim declarations", ".aiss assumption-register declarations"),
        expected_trace_markers=("estimand", "sample and N", "FE and clustering", "support_level"),
        expected_validators=("validate_ai4ss_model.py", "validate_ai4ss_model.py"),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=("result prose draft", "loose claim notes"),
            trace_markers=("estimand", "sample and N"),
            validator_refs=(),
            assumption_register=("auto-narrow wording when support level is below claim strength",),
            risky_moves=("hidden AI or direct-submission-ready prose", "mechanism evidence is not separated from interpretation"),
            summary="Returns a plausible paragraph plus notes, but it lacks disclosure/direct-submission status and under-specifies claim strength.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss diagnostic checks", ".aiss bounded claim declarations", ".aiss assumption-register declarations"),
            trace_markers=("estimand", "sample and N", "support_level"),
            validator_refs=("validate_ai4ss_model.py", "validate_ai4ss_model.py"),
            assumption_register=("auto-bound causal language to the declared estimand", "auto-route mechanism gaps to new analysis when evidence is thin"),
            risky_moves=(),
            summary="Returns claim slots, risks, and visible AI-use/submission gate status; FE/cluster still need model-object confirmation.",
        ),
    ),
    EvalCase(
        case_id="revision_trace",
        scholar_question="返修有没有证据链？",
        task="Process reviewer comments about identification, mechanism evidence, and literature coverage.",
        expected_artifacts=(".aiss reviewer-request decisions", "revision_trace/", ".aiss open automation decisions"),
        expected_trace_markers=("comment_id", "planned_action", "done_evidence", "confidentiality_status"),
        expected_validators=("validate_ai4ss_model.py",),
        no_skill=SimulatedOutput(
            condition="no_skill",
            artifacts=("response letter draft", "loose revision plan"),
            trace_markers=("comment_id", "planned_action"),
            validator_refs=(),
            assumption_register=("auto-set response tone from reviewer request severity and evidence strength",),
            risky_moves=("hidden AI or direct-submission-ready prose", "done evidence is missing for several promised changes"),
            summary="Returns a plausible response package, but it lacks a visible disclosure/direct-submission gate and done evidence for several promised changes.",
        ),
        skill_guided=SimulatedOutput(
            condition="skill_guided",
            artifacts=(".aiss reviewer-request decisions", "revision_trace/", ".aiss open automation decisions"),
            trace_markers=("comment_id", "planned_action", "confidentiality_status"),
            validator_refs=("validate_ai4ss_model.py",),
            assumption_register=("auto-select rebut versus partial accept from evidence status", "auto-apply confidentiality handling rules"),
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
    assumption_register = 1.0 if output.assumption_register else 0.0
    total = (
        artifact * WEIGHTS["artifacts"]
        + trace * WEIGHTS["traceability"]
        + boundary * WEIGHTS["boundary"]
        + validation * WEIGHTS["validation"]
        + assumption_register * WEIGHTS["assumption_register"]
    )
    return {
        "artifacts": artifact * WEIGHTS["artifacts"],
        "traceability": trace * WEIGHTS["traceability"],
        "boundary": boundary * WEIGHTS["boundary"],
        "validation": validation * WEIGHTS["validation"],
        "assumption_register": assumption_register * WEIGHTS["assumption_register"],
        "total": total,
    }


def fmt_score(value: float) -> str:
    return f"{value:.1f}"


def render_report() -> str:
    lines: list[str] = []
    lines.append("# Simulated Skill-Use Diagnostic")
    lines.append("")
    lines.append("Status: non-blinded diagnostic demonstration. Use `scripts/run_blind_skill_use_eval.py` for the condition-blinded LLM-as-judge packet protocol.")
    lines.append("")
    lines.append("This deterministic simulation compares a careful generic agent with a skill-guided agent on four scholar-facing workbench tasks. It checks output structure, not model intelligence, and it does not produce eval scores.")
    lines.append("")
    lines.append("## Structure Cues")
    lines.append("")
    lines.append("| dimension | weight | what it asks |")
    lines.append("|---|---:|---|")
    lines.append("| artifacts | 30 | Did the agent produce the canonical audit objects? |")
    lines.append("| traceability | 20 | Can claims or rows be traced to sources, logs, or model objects? |")
    lines.append("| boundary | 20 | Did the agent keep AI-use disclosure and direct-submission gates visible while avoiding unsafe scholarly moves? |")
    lines.append("| validation | 15 | Did the agent name the relevant validator or gate? |")
    lines.append("| assumption_register | 15 | Did the agent surface auto-selected assumptions and repair routes? |")
    lines.append("")
    lines.append("## Structural Comparison")
    lines.append("")
    lines.append("| case | scholar question | no_skill structure | skill_guided structure |")
    lines.append("|---|---|---|---|")

    details: list[str] = []
    for case in CASES:
        lines.append(
            f"| `{case.case_id}` | {case.scholar_question} | {case.no_skill.summary} | {case.skill_guided.summary} |"
        )

        details.append(f"### `{case.case_id}`")
        details.append("")
        details.append(f"Task: {case.task}")
        details.append("")
        details.append("| condition | artifacts | trace markers | risky moves | summary |")
        details.append("|---|---|---|---|---|")
        for output in (case.no_skill, case.skill_guided):
            artifacts = ", ".join(output.artifacts) or "none"
            traces = ", ".join(output.trace_markers) or "none"
            risks = ", ".join(output.risky_moves) or "none"
            details.append(
                f"| `{output.condition}` | {artifacts} | {traces} | {risks} | {output.summary} |"
            )
        details.append("")

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The diagnostic contrast is about structure: canonical artifacts appear, hidden-AI or direct-submission risks become visible, and validation gates become explicit. It is not a score and should not be reported as an effect estimate.")
    lines.append("")
    lines.append("For teaching, this is the right claim: skills are useful only if they change the agent from answer production to inspectable, AI-disclosed research objects and working text.")
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
