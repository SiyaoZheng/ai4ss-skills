#!/usr/bin/env python3
"""Generate a factory-level, condition-blinded AI4SS workflow evaluation.

This evaluation is intentionally broader than the earlier skill-use packet
tests. It asks whether a rough research topic is turned into a traceable
research factory chain:

rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/checks ->
literature/data evidence gates -> .aiss analysis readiness -> .aiss analysis artifacts ->
bounded claim/review artifacts.

The outputs generated here are deterministic structural packets. They are not
live LLM generations and they are not a true double-blind field experiment.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from dataclasses import dataclass, replace
from pathlib import Path


DEFAULT_OUTDIR = Path("docs/factory_level_eval")
DEFAULT_SEED = 20260701

WEIGHTS = {
    "research_object": 15,
    "mida_design": 15,
    "ai4ss_model_check": 15,
    "evidence_data_chain": 15,
    "analysis_loop": 15,
    "boundary_author_decision": 15,
    "end_to_end_continuity": 10,
}

DIMENSION_TERMS = {
    "research_object": [
        "research_model.aiss",
        "route declarations",
        "route_id",
        "route_decl_id",
        "minimum viable study",
        "failure_signal",
    ],
    "mida_design": [
        "selected route",
        "seven mida declarations",
        "Model",
        "Inquiry",
        "Data strategy",
        "Answer strategy",
        "mida_id",
        "decision_decl_id",
    ],
    "ai4ss_model_check": [
        "research_model.aiss",
        "ai4ss_check_report.txt",
        "aiss.py compile",
        "aiss.py lint",
        "aiss.py run",
        "model_id",
        "bridge_id",
    ],
    "evidence_data_chain": [
        "paper declarations",
        "source declarations",
        "span declarations",
        "claim declarations",
        "relation declarations",
        "concept declarations",
        "causal declarations",
        "bridge declarations",
        "source-status checks",
        "data source declarations",
        "artifact declarations",
        "empirical declarations",
        "observation declarations",
        "coupling declarations",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
    ],
    "analysis_loop": [
        "readiness check declarations",
        "readiness_status",
        "analysis artifact declarations",
        "adapter declarations",
        "derive declarations",
        "first-pass table",
        "interpretation_boundary",
    ],
    "boundary_author_decision": [
        "bounded claim declarations",
        "AI-use ledger",
        "TOP disclosure matrix",
        "replication_package_status",
        "deviation_log_status",
        "AI-disclosed manuscript package",
        "transparency package",
        "author decision",
        "Author should decide",
        "Claim boundary",
        "ai_contribution_disclosure",
        "human_accountability_status",
        "submission_policy_check_status",
        "direct_submission_status",
        "bounded claim",
    ],
    "end_to_end_continuity": [
        "route_id=R1",
        "route_decl_id=demo.route_r1",
        "mida_id=demo.mida_r1_inquiry",
        "model_id=demo.platform_innovation",
        "bridge_id=demo.causal_bridge_exposure",
        "design_source=docs/research_model.aiss",
        "registration_status",
        "analysis_plan_path",
        "materials_transparency_status",
        "analysis_code_transparency_status",
        "reporting_transparency_status",
        "ai_contribution_disclosure",
        "human_accountability_status",
        "submission_policy_check_status",
        "direct_submission_status",
        "next_skill_route",
    ],
}

RISK_PENALTIES = {
    "hidden AI or direct-submission-ready prose": 8,
    "causal claim before readiness": 5,
    "treats checker pass as proof": 6,
    "prose-only handoff": 4,
    "no author decision": 5,
    "unverified source synthesis": 4,
}


@dataclass(frozen=True)
class FactoryCase:
    case_id: str
    rough_topic: str
    available_materials: str
    task: str


@dataclass(frozen=True)
class FactoryOutput:
    condition: str
    summary: str
    artifacts: list[str]
    gate_statuses: list[str]
    trace_markers: list[str]
    validator_refs: list[str]
    author_decisions: list[str]
    risky_moves: list[str]


CASES = [
    FactoryCase(
        case_id="city_platform_green_patents",
        rough_topic=(
            "Can city digital-government platform rollout help firms produce more "
            "green patents?"
        ),
        available_materials=(
            "city rollout notes, firm-year patent panel, preliminary policy-source "
            "links, and an uncertain firm-city linkage key"
        ),
        task=(
            "Turn the rough topic into a first-pass autonomous research-factory "
            "chain. The chain should make the research object, design declaration, "
            ".aiss model, evidence/data gates, .aiss analysis readiness, .aiss "
            "analysis artifacts, transparency package, bounded claim handoff, and "
            "AI-disclosed manuscript package with direct-submission status inspectable."
        ),
    ),
    FactoryCase(
        case_id="platform_theory_mapping",
        rough_topic=(
            "What theoretical mechanism could connect digital-government platform "
            "exposure to firm green innovation, and what rival explanations should "
            "remain visible?"
        ),
        available_materials=(
            "verified literature evidence declarations, seed route/MIDA declarations, and notes "
            "about administrative-friction and baseline city-capacity explanations"
        ),
        task=(
            "Turn verified literature evidence into a theory-mapping handoff. The "
            "chain should preserve source paper ids, proposed .aiss objects, rival "
            "or boundary conditions, observable implications, AI-use disclosure, "
            "and author decisions."
        ),
    )
]


def generic_output() -> FactoryOutput:
    return FactoryOutput(
        condition="generic_agent",
        summary=(
            "The agent proposes a plausible research plan: define treated cities, "
            "merge firms to cities, run a DID/event-study, collect literature, and "
            "prepare a cautious interpretation memo after tables are produced. The plan "
            "is coherent but mostly prose. Handoffs depend on the conversation, not "
            "stable model objects or validators."
        ),
        artifacts=[
            "loose research plan with hypothesis, variables, and suggested estimator",
            "loose data todo list naming city rollout list, patent data, and controls",
            "loose literature notes with seed-paper themes",
            "loose analysis outline with DID and event-study table ideas",
        ],
        gate_statuses=[
            "Research route described in prose, but no .aiss route_id or failure_signal declaration",
            "Design is partly stated, but no selected .aiss route plus seven MIDA declarations",
            "No research_model.aiss or ai4ss_check_report.txt",
            "Literature and data tasks are suggested but not linked to .aiss evidence or data declarations",
            "No .aiss readiness check before model execution",
            "Claim boundary is stated informally",
            "No transparency package or replication-package status",
        ],
        trace_markers=[
            "variable names: rollout, treated_city, green_patent_count",
            "mentions firm-year unit and city-year rollout timing",
            "uses prose-only handoff between planning, data, literature, and analysis",
        ],
        validator_refs=[
            "suggests checking missingness and parallel trends, but names no local validator",
        ],
        author_decisions=[
            "Author should decide whether the causal interpretation is credible",
        ],
        risky_moves=[
            "prose-only handoff",
            "causal claim before readiness",
            "unverified source synthesis",
        ],
    )


def factory_output() -> FactoryOutput:
    return FactoryOutput(
        condition="ai4ss_factory",
        summary=(
            "The agent produces a linked research-state chain rather than a final "
            "answer. It starts with .aiss route declarations and a minimum viable "
            "study, declares MIDA in .aiss, saves a checked .aiss model, "
            "records literature, theory, data, and analysis evidence as .aiss declarations when "
            "it affects the model, routes survey/data cleaning through upstream "
            "ai4ss-skills where relevant, runs .aiss readiness checks, records "
            "first-pass outputs as .aiss analysis artifacts, declares transparency and "
            "replication-package status, and hands bounded claims to an AI-disclosed manuscript package."
        ),
        artifacts=[
            "research_model.aiss route declarations with route_id=R1, route_decl_id=demo.route_r1, minimum viable study, materials_gap, first_action, failure_signal, stop_reason, next_skill_route",
            "research_model.aiss selected route and seven mida declarations covering Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, and Report boundary",
            "registration_status=registration_relevant, protocol_path=docs/protocol_scaffold.md, analysis_plan_path=docs/analysis_plan.md, deviation_log_status=none_declared",
            "research_model.aiss decision declarations with decision_decl_id values",
            "research_model.aiss",
            "ai4ss_check_report.txt",
            ".aiss paper/source/span/claim/relation declarations for verified literature evidence",
            ".aiss concept/causal/bridge/check/decision declarations for theory mapping, rivals, scope, and source status",
            ".aiss source/artifact/empirical/observation/coupling/bridge/check declarations for data construction and row-loss evidence",
            "materials_transparency_status=partial, data_transparency_status=restricted, fair_metadata_status=needs_review, replication_package_status=partial",
            "DDI metadata and cleaning audit paths when codebook-parse, cleaning-contract, and cleaning-execute apply",
            ".aiss readiness check declarations",
            ".aiss analysis artifact declarations with first-pass table, diagnostic output, readiness_status, and interpretation_boundary",
            "analysis_code_transparency_status=runnable, computational_reproducibility_status=partial, runtime and seed notes referenced from .aiss",
            ".aiss diagnostic check declarations for rival, scope, mechanism weakness, and overclaim risks",
            ".aiss bounded claim declarations",
            "top_disclosure_matrix with reporting_transparency_status=needs_author_review",
            "AI-disclosed manuscript package checklist with ai_contribution_disclosure=required, human_accountability_status=needs_author_review, submission_policy_check_status=not_checked, direct_submission_status=not_ready",
            "AI-use ledger entry",
        ],
        gate_statuses=[
            "G1 pass: route_id=R1 and route_decl_id=demo.route_r1 create a .aiss research object with a failure signal",
            "G2 pass: design_source=docs/research_model.aiss contains .aiss MIDA declarations through mida_id values",
            "G3 pass: research_model.aiss checked through aiss.py compile/lint/run",
            "G4 pass: bridge_id=demo.causal_bridge_exposure records empirical bridge and weak commensurability",
            "G5 pass: literature evidence is recorded as .aiss paper/source/span/claim declarations",
            "G6 pass: data contract includes .aiss source, artifact, empirical, observation, coupling, bridge, and check declarations plus upstream cleaning-route placeholders",
            "G7 pass: .aiss readiness checks report readiness_status before execution",
            "G8 pass: .aiss analysis artifacts link outputs back to model_id=demo.platform_innovation and bridge_id=demo.causal_bridge_exposure",
            "G9 pass: bounded claim with AI-use disclosure and direct-submission gate visible",
            "G10 pass: transparency package declares registration, protocol, analysis_plan_path, materials, data, code, reporting, FAIR metadata, and deviation_log_status",
            "G11 pass: replication_package_status records scripts, runtime, data locators, seeds, logs, and restricted-access notes",
            "G12 pass: AI-disclosed manuscript package uses top_disclosure_matrix, ai_contribution_disclosure, human_accountability_status, submission_policy_check_status, and direct_submission_status",
        ],
        trace_markers=[
            "route_id=R1",
            "route_decl_id=demo.route_r1",
            "mida_id=demo.mida_r1_inquiry",
            "decision_decl_id=demo.decision_r1_identification",
            "design_source=docs/research_model.aiss",
            "registration_status=registration_relevant",
            "analysis_plan_path=docs/analysis_plan.md",
            "materials_transparency_status=partial",
            "analysis_code_transparency_status=runnable",
            "reporting_transparency_status=needs_author_review",
            "ai_contribution_disclosure=required",
            "human_accountability_status=needs_author_review",
            "submission_policy_check_status=not_checked",
            "direct_submission_status=not_ready",
            "replication_package_status=partial",
            "ai4ss_model_path=docs/examples/research_model.aiss",
            "model_id=demo.platform_innovation",
            "concept_id=demo.exposed_unit; demo.high_innovation",
            "causal_id=demo.exposure_to_innovation",
            "bridge_id=demo.causal_bridge_exposure",
            "check_id=demo.check_source_status gates source-supported theory updates",
            "decision_id=demo.decision_rival_capacity routes baseline city capacity to methods-reviewer",
            "decision_id=demo.decision_scope_rollout routes audited rollout scope to ask_author",
            ".aiss literature declarations -> concept:demo.exposed_unit; causal:demo.exposure_to_innovation; bridge:demo.causal_bridge_exposure",
            "next_skill_route moves from study-design-builder to research-data-builder, research-analysis-runner, and methods-reviewer",
        ],
        validator_refs=[
            "python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss",
            "validate_ai4ss_model.py uses unified aiss.py compile/lint/run semantics",
            "python3 scripts/validate_skillpack_workflow.py",
            "python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv",
            "python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv",
        ],
        author_decisions=[
            "author decision: whether the target comparison is substantively credible",
            "author decision: acceptable missing-link threshold before firm-year analysis",
            "author decision: whether to abandon causal language if bridge/readiness stays weak",
            "author decision: whether mechanism strength and theoretical contribution are only framing hypotheses or author-approved claims",
            "AI-assisted working prose remains disclosure-gated; bounded claim declarations and author decision slots are visible for review",
            "author decision: disclosure wording and replication-package access limits before final paper submission",
        ],
        risky_moves=[],
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmt_score(value: float) -> str:
    return f"{value:.1f}"


def output_text(output: FactoryOutput) -> str:
    blocks = [
        output.summary,
        "\n".join(output.artifacts),
        "\n".join(output.gate_statuses),
        "\n".join(output.trace_markers),
        "\n".join(output.validator_refs),
        "\n".join(output.author_decisions),
        "\n".join(output.risky_moves),
    ]
    return "\n".join(blocks)


def score_output(output: FactoryOutput) -> dict[str, float]:
    text = output_text(output)
    scores: dict[str, float] = {}
    for dimension, terms in DIMENSION_TERMS.items():
        found = sum(1 for term in terms if term.lower() in text.lower())
        scores[dimension] = WEIGHTS[dimension] * found / len(terms)

    penalty = 0
    risk_text = "\n".join(output.risky_moves).lower()
    for risk, points in RISK_PENALTIES.items():
        if risk.lower() in risk_text:
            penalty += points

    raw_total = sum(scores.values())
    scores["risk_penalty"] = float(penalty)
    scores["total"] = max(0.0, raw_total - penalty)
    return scores


def packet_body(packet_id: str, case: FactoryCase, output: FactoryOutput) -> str:
    artifacts = "\n".join(f"- {item}" for item in output.artifacts)
    gates = "\n".join(f"- {item}" for item in output.gate_statuses)
    traces = "\n".join(f"- {item}" for item in output.trace_markers)
    validators = "\n".join(f"- {item}" for item in output.validator_refs)
    decisions = "\n".join(f"- {item}" for item in output.author_decisions)
    risks = "\n".join(f"- {item}" for item in output.risky_moves) or "- none visible"
    return f"""# Factory-Level Blinded Packet {packet_id}

## Rough Research Task

Topic: {case.rough_topic}

Available materials: {case.available_materials}

Task: {case.task}

## Agent Deliverable Summary

{output.summary}

## Artifacts Reported

{artifacts}

## Gate Statuses Reported

{gates}

## Traceability Markers

{traces}

## Validation Commands Or Gates

{validators}

## Human-Accountability Decisions

{decisions}

## Concern Signals Visible To Grader

{risks}
"""


def protocol(seed: int) -> str:
    weights = "\n".join(f"- `{name}`: {weight} points" for name, weight in WEIGHTS.items())
    return f"""# Factory-Level AI4SS Workflow Evaluation Protocol

## Status

This is a condition-blinded structural evaluation of the local AI4SS autonomous
research factory workflow. It is stronger than a single-skill packet demo
because it scores the whole chain from rough topic to checked research-state
objects. It is still not a live double-blind field experiment.

## Research Question

Does the `.aiss`-centered factory workflow make a rough social-science topic
more inspectable, replayable, and bounded than a careful generic research-agent
plan?

## Experimental Unit

One packet is one full-chain deliverable for the same rough topic. The matched
conditions are:

- `generic_agent`: careful research-assistant planning without the local
  `.aiss` factory gates.
- `ai4ss_factory`: workflow constrained by MIDA, `.aiss` model objects, local
  validators, and author-decision boundaries.

## Blinding

Packet files in `packets/` hide the condition label. The private mapping lives
in `_private/private_mapping.csv` and should remain hidden until scores are
frozen. The packet contents may still reveal differences because the factory
condition exposes `.aiss` artifacts by design.

## Randomization

The two condition outputs are randomly assigned to packet IDs with seed `{seed}`.

## Preregistered Rubric

{weights}

The rubric is intentionally artifact- and gate-oriented. It does not score
publication quality, empirical truth, or prose elegance.

## Human Grading

Give graders only:

- `grader_brief.md`
- `packets/`
- `human_grading_sheet.csv`
- optionally `gate_matrix_blinded.csv`

Do not give graders `_private/private_mapping.csv` or `unblinded_report.md`
before grades are frozen.

## Limits

- Outputs are deterministic structural packets, not live LLM generations.
- Generation is not blind; the script author knows the hypothesis.
- Rule-based scoring rewards the declared factory contract by design.
- A stronger follow-up would use independently generated live outputs, concealed
  condition assignment during scoring, independent human expert graders, and
  inter-rater reliability.
"""


def grader_brief() -> str:
    weights = "\n".join(f"- `{name}`: {weight} points" for name, weight in WEIGHTS.items())
    return f"""# Factory-Level Blinded Packet Grader Brief

Score each packet as a full-chain research-assistance deliverable. Do not try to
guess the production condition. No condition labels are provided.

## Rubric

{weights}

## Scoring Guidance

- Award research-object points when a rough topic becomes `.aiss` route
  declarations, mirrored route cards, a minimum viable study, stop reason, and
  failure signal.
- Award MIDA points when `.aiss` `mida` declarations cover Model, Inquiry, Data
  strategy, Answer strategy, diagnosands, redesign, and reporting boundary.
- Award `.aiss` points when model paths, IDs, checker/bridge diagnostics, and
  stable concept or causal references are present.
- Award evidence/data points when literature, source, data provenance, row-loss,
  and bridge artifacts are tied to the same route and model through `.aiss`.
  For theory mapping, also look for validated `.aiss` literature, rival, scope,
  source-status, and model-update declarations.
- Award analysis-loop points only when readiness is checked before execution and
  first-pass outputs link back to the declared design.
- Award boundary points when manuscript or theory-section working text remains
  AI-disclosed and direct-submission gated, declares transparency and
  replication-package status, and leaves novelty, theoretical contribution,
  mechanism strength, disclosure wording, and scope framing to the researcher.
- Award continuity points when the same route, model, bridge, and design-source
  identifiers travel across the chain with registration, analysis-plan, data,
  code, reporting, and replication-package status.

Penalize hidden-AI or direct-submission-ready manuscript writing, causal claims
before readiness, unverified source synthesis, and treating a checker pass as
proof of identification.
"""


def make_packets(outdir: Path, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rng = random.Random(seed)
    mapping_rows: list[dict[str, str]] = []
    score_rows: list[dict[str, str]] = []
    gate_rows: list[dict[str, str]] = []
    packet_counter = 1

    for case in CASES:
        outputs = [generic_output(), factory_output()]
        rng.shuffle(outputs)
        for output in outputs:
            packet_id = f"P{packet_counter:03d}"
            packet_counter += 1
            blinded_output = replace(output, condition="blinded")
            write_text(outdir / "packets" / f"{packet_id}.md", packet_body(packet_id, case, blinded_output))

            mapping_rows.append(
                {
                    "packet_id": packet_id,
                    "case_id": case.case_id,
                    "condition": output.condition,
                }
            )

            scores = score_output(blinded_output)
            score_row = {
                "packet_id": packet_id,
                "case_id": case.case_id,
                "research_object": fmt_score(scores["research_object"]),
                "mida_design": fmt_score(scores["mida_design"]),
                "ai4ss_model_check": fmt_score(scores["ai4ss_model_check"]),
                "evidence_data_chain": fmt_score(scores["evidence_data_chain"]),
                "analysis_loop": fmt_score(scores["analysis_loop"]),
                "boundary_author_decision": fmt_score(scores["boundary_author_decision"]),
                "end_to_end_continuity": fmt_score(scores["end_to_end_continuity"]),
                "risk_penalty": fmt_score(scores["risk_penalty"]),
                "total": fmt_score(scores["total"]),
            }
            score_rows.append(score_row)

            for index, gate in enumerate(output.gate_statuses, start=1):
                gate_rows.append(
                    {
                        "packet_id": packet_id,
                        "case_id": case.case_id,
                        "gate_index": str(index),
                        "gate_status": gate,
                    }
                )

    return mapping_rows, score_rows, gate_rows


def human_sheet(mapping_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in mapping_rows:
        rows.append(
            {
                "grader_id": "",
                "packet_id": row["packet_id"],
                "case_id": row["case_id"],
                "research_object_0_15": "",
                "mida_design_0_15": "",
                "ai4ss_model_check_0_15": "",
                "evidence_data_chain_0_15": "",
                "analysis_loop_0_15": "",
                "boundary_author_decision_0_15": "",
                "end_to_end_continuity_0_10": "",
                "risk_penalty_0_plus": "",
                "total_0_100": "",
                "notes": "",
            }
        )
    return rows


def unblinded_report(mapping_rows: list[dict[str, str]], score_rows: list[dict[str, str]], seed: int) -> str:
    mapping = {row["packet_id"]: row for row in mapping_rows}
    joined: list[dict[str, str]] = []
    for score in score_rows:
        joined.append({**score, "condition": mapping[score["packet_id"]]["condition"]})

    by_condition: dict[str, list[float]] = {"generic_agent": [], "ai4ss_factory": []}
    for row in joined:
        by_condition[row["condition"]].append(float(row["total"]))

    avg_generic = sum(by_condition["generic_agent"]) / len(by_condition["generic_agent"])
    avg_factory = sum(by_condition["ai4ss_factory"]) / len(by_condition["ai4ss_factory"])

    lines = [
        "# Unblinded Factory-Level AI4SS Workflow Evaluation Report",
        "",
        "This report joins `rule_based_scores_blinded.csv` to `_private/private_mapping.csv` after scoring.",
        "",
        f"Randomization seed: `{seed}`",
        "",
        "## Result Summary",
        "",
        f"- Average `generic_agent`: **{fmt_score(avg_generic)} / 100**",
        f"- Average `ai4ss_factory`: **{fmt_score(avg_factory)} / 100**",
        f"- Average gain: **{fmt_score(avg_factory - avg_generic)} points**",
        "",
        "## Packet Scores",
        "",
        "| packet | case | condition | research object | MIDA | .aiss | evidence/data | analysis | boundary | continuity | penalty | total |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in joined:
        lines.append(
            "| {packet_id} | `{case_id}` | `{condition}` | {research_object} | {mida_design} | "
            "{ai4ss_model_check} | {evidence_data_chain} | {analysis_loop} | "
            "{boundary_author_decision} | {end_to_end_continuity} | {risk_penalty} | {total} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The structural comparison exposes the specific gap that the local `.aiss` factory is meant to close: a careful generic agent can outline a credible study, but the handoff remains prose-heavy and weakly replayable. The factory packet scores higher because it carries the same route, design source, model IDs, bridge IDs, evidence gates, data contracts, readiness checks, analysis artifacts, transparency package, replication-package status, and bounded claim handoff through the whole chain.",
            "",
            "The appropriate claim is narrow. This package verifies that the local workflow now has an evaluable factory-level contract and a reproducible scoring harness. It does not prove that live agents will always use the factory correctly, that empirical claims are true, or that `.aiss` checker success establishes identification validity.",
            "",
            "## Remaining Evaluation Need",
            "",
            "The next stronger evaluation should replace these deterministic packets with independently generated live outputs, use independent human expert graders, and report inter-rater reliability before unblinding.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--clean", action="store_true", help="Remove generated output before rebuilding.")
    args = parser.parse_args()

    if args.clean and args.outdir.exists():
        shutil.rmtree(args.outdir)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_text(args.outdir / "protocol.md", protocol(args.seed))
    write_text(args.outdir / "grader_brief.md", grader_brief())

    mapping_rows, score_rows, gate_rows = make_packets(args.outdir, args.seed)
    write_csv(args.outdir / "_private" / "private_mapping.csv", mapping_rows, ["packet_id", "case_id", "condition"])
    write_csv(
        args.outdir / "rule_based_scores_blinded.csv",
        score_rows,
        [
            "packet_id",
            "case_id",
            "research_object",
            "mida_design",
            "ai4ss_model_check",
            "evidence_data_chain",
            "analysis_loop",
            "boundary_author_decision",
            "end_to_end_continuity",
            "risk_penalty",
            "total",
        ],
    )
    write_csv(args.outdir / "gate_matrix_blinded.csv", gate_rows, ["packet_id", "case_id", "gate_index", "gate_status"])
    write_csv(
        args.outdir / "human_grading_sheet.csv",
        human_sheet(mapping_rows),
        [
            "grader_id",
            "packet_id",
            "case_id",
            "research_object_0_15",
            "mida_design_0_15",
            "ai4ss_model_check_0_15",
            "evidence_data_chain_0_15",
            "analysis_loop_0_15",
            "boundary_author_decision_0_15",
            "end_to_end_continuity_0_10",
            "risk_penalty_0_plus",
            "total_0_100",
            "notes",
        ],
    )
    write_text(args.outdir / "unblinded_report.md", unblinded_report(mapping_rows, score_rows, args.seed))

    print(f"Generated factory-level evaluation package at {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
