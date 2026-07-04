#!/usr/bin/env python3
"""Generate a factory-level, condition-blinded AI4SS workflow evaluation.

This evaluation is intentionally broader than the earlier skill-use packet
tests. It asks whether a rough research topic is turned into a traceable
research factory chain:

rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/checks ->
literature/data evidence gates -> analysis readiness -> analysis manifest ->
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
        "research_starter_packet.md",
        "research_route_cards.csv",
        "route_id",
        "route_decl_id",
        "minimum viable study",
        "failure_signal",
    ],
    "mida_design": [
        "study_design_declaration.csv",
        "Model",
        "Inquiry",
        "Data strategy",
        "Answer strategy",
        "mida_id",
        "design_decision_register.csv",
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
        "literature_matrix.csv",
        "compiled_ai4ss_path",
        "sample_flow.csv",
        "merge_audit.csv",
        "variable_provenance.csv",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
    ],
    "analysis_loop": [
        "analysis_readiness_check.csv",
        "readiness_status",
        "analysis_run_manifest.csv",
        "first-pass table",
        "interpretation_boundary",
    ],
    "boundary_author_decision": [
        "claim_ledger.csv",
        "AI-use ledger",
        "author decision",
        "Author should decide",
        "Claim boundary",
        "no manuscript prose",
        "bounded claim",
    ],
    "end_to_end_continuity": [
        "route_id=R1",
        "route_decl_id=demo.route_r1",
        "mida_id=demo.mida_r1_inquiry",
        "model_id=demo.platform_innovation",
        "bridge_id=demo.causal_bridge_exposure",
        "design_source=docs/study_design_declaration.csv",
        "next_skill_route",
    ],
}

RISK_PENALTIES = {
    "writes manuscript prose": 8,
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
            ".aiss model, evidence/data gates, analysis readiness, analysis "
            "manifest, and bounded claim handoff inspectable before any manuscript "
            "prose is written."
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
            "research_plan.md with hypothesis, variables, and suggested estimator",
            "data_todo.md listing city rollout list, patent data, and controls",
            "literature_notes.md with seed-paper themes",
            "analysis_outline.md with DID and event-study table ideas",
        ],
        gate_statuses=[
            "Research route described in prose, but no route_id or failure_signal sidecar",
            "Design is partly stated, but no study_design_declaration.csv",
            "No research_model.aiss or ai4ss_check_report.txt",
            "Literature and data tasks are suggested but not linked to compiled evidence or audit sidecars",
            "No analysis_readiness_check.csv before model execution",
            "Claim boundary is stated informally",
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
            "study, declares MIDA as .aiss rows, saves a checked .aiss model, compiles literature evidence when "
            "it affects the model, routes survey/data cleaning through upstream "
            "ai4ss-skills where relevant, runs an analysis-readiness gate, records "
            "first-pass outputs in a manifest, and hands bounded claims to review."
        ),
        artifacts=[
            "research_starter_packet.md",
            "research_route_cards.csv with route_id=R1, route_decl_id=demo.route_r1, minimum viable study, materials_gap, first_action, failure_signal, stop_reason, next_skill_route",
            "study_design_declaration.csv with mida_id values covering Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, and Report boundary",
            "design_decision_register.csv with decision_decl_id values",
            "research_model.aiss",
            "ai4ss_check_report.txt",
            "literature_candidate_discovery.csv",
            "literature_matrix.csv with evidence_table_path, compiled_ai4ss_path, evidence_compile_status, model_id, concept_id, causal_id, bridge_id",
            "sample_flow.csv",
            "merge_audit.csv",
            "variable_provenance.csv",
            "DDI metadata and cleaning audit paths when codebook-parse, cleaning-contract, and cleaning-execute apply",
            "analysis_readiness_check.csv",
            "analysis_run_manifest.csv with first-pass table, diagnostic output, readiness_status, interpretation_boundary",
            "methods issue_table.csv",
            "claim_ledger.csv",
            "AI-use ledger entry",
        ],
        gate_statuses=[
            "G1 pass: route_id=R1 and route_decl_id=demo.route_r1 create a .aiss research object with a failure signal",
            "G2 pass: design_source=docs/study_design_declaration.csv mirrors .aiss MIDA declarations through mida_id values",
            "G3 pass: research_model.aiss checked through aiss.py compile/lint/run",
            "G4 pass: bridge_id=demo.causal_bridge_exposure records empirical bridge and weak commensurability",
            "G5 pass: literature evidence uses compiled_ai4ss_path and validate_literature_evidence_compile.py",
            "G6 pass: data contract includes sample_flow.csv, merge_audit.csv, variable_provenance.csv, and upstream cleaning-route placeholders",
            "G7 pass: analysis_readiness_check.csv reports readiness_status before execution",
            "G8 pass: analysis_run_manifest.csv links outputs back to model_id=demo.platform_innovation and bridge_id=demo.causal_bridge_exposure",
            "G9 pass: bounded claim and no manuscript prose until methods review",
        ],
        trace_markers=[
            "route_id=R1",
            "route_decl_id=demo.route_r1",
            "mida_id=demo.mida_r1_inquiry",
            "decision_decl_id=demo.decision_r1_identification",
            "design_source=docs/study_design_declaration.csv",
            "ai4ss_model_path=docs/examples/research_model.aiss",
            "model_id=demo.platform_innovation",
            "concept_id=demo.exposed_unit; demo.high_innovation",
            "causal_id=demo.exposure_to_innovation",
            "bridge_id=demo.causal_bridge_exposure",
            "next_skill_route moves from study-design-builder to research-data-builder, research-analysis-runner, and methods-reviewer",
        ],
        validator_refs=[
            "python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss",
            "validate_ai4ss_model.py uses unified aiss.py compile/lint/run semantics",
            "python3 scripts/validate_literature_evidence_compile.py skills/literature-matrix/examples/valid_literature_matrix.csv",
            "python3 scripts/validate_analysis_readiness.py skills/research-analysis-runner/examples/valid_analysis_readiness_check.csv",
            "python3 skills/research-analysis-runner/scripts/validate_analysis_manifest.py skills/research-analysis-runner/examples/valid_analysis_run_manifest.csv",
            "python3 skills/literature-matrix/scripts/validate_literature_matrix.py skills/literature-matrix/examples/valid_literature_matrix.csv",
            "python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv",
        ],
        author_decisions=[
            "author decision: whether the target comparison is substantively credible",
            "author decision: acceptable missing-link threshold before firm-year analysis",
            "author decision: whether to abandon causal language if bridge/readiness stays weak",
            "no manuscript prose; only bounded claim entries for author review",
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

## Author-Owned Decisions

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
  sidecars, validators, and author-decision boundaries.

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
- Award evidence/data points when literature, source, sample-flow, merge, and
  variable-provenance artifacts are tied to the same route and model.
- Award analysis-loop points only when readiness is checked before execution and
  first-pass outputs link back to the declared design.
- Award boundary points when the packet avoids manuscript prose and leaves
  scholarly judgment to the researcher.
- Award continuity points when the same route, model, bridge, and design-source
  identifiers travel across the chain.

Penalize direct manuscript writing, causal claims before readiness, unverified
source synthesis, and treating a checker pass as proof of identification.
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
            "The structural comparison exposes the specific gap that the local `.aiss` factory is meant to close: a careful generic agent can outline a credible study, but the handoff remains prose-heavy and weakly replayable. The factory packet scores higher because it carries the same route, design source, model IDs, bridge IDs, evidence gates, data contracts, readiness check, analysis manifest, and bounded claim handoff through the whole chain.",
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
