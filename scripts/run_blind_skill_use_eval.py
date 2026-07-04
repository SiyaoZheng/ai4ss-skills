#!/usr/bin/env python3
"""Generate a condition-blinded skill-use evaluation packet set.

This is a stricter companion to `simulate_skill_use_eval.py`.
It creates:

- anonymized output packets for graders;
- a private condition mapping;
- a blank human grading sheet;
- rule-based packet scores without condition labels;
- an unblinded report after scoring.

The generated evaluation is condition-blinded, not a true double-blind field
experiment. See the generated protocol for limits.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from dataclasses import replace
from pathlib import Path

from simulate_skill_use_eval import CASES, WEIGHTS, EvalCase, SimulatedOutput, fmt_score, score_output


DEFAULT_OUTDIR = Path("docs/blind_skill_use_eval")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def packet_body(packet_id: str, case: EvalCase, output: SimulatedOutput) -> str:
    artifacts = "\n".join(f"- {item}" for item in output.artifacts) or "- none"
    traces = "\n".join(f"- {item}" for item in output.trace_markers) or "- none"
    validators = "\n".join(f"- {item}" for item in output.validator_refs) or "- none"
    decisions = "\n".join(f"- {item}" for item in output.author_decisions) or "- none"
    concern_signals = "\n".join(f"- {item}" for item in output.risky_moves) or "- none"
    return f"""# Blinded Packet {packet_id}

## Task

Scholar question: {case.scholar_question}

Task: {case.task}

## Agent Deliverable Summary

{output.summary}

## Artifacts Reported

{artifacts}

## Traceability Markers Reported

{traces}

## Validation or Gate References Reported

{validators}

## Human-Accountability Decisions Surfaced

{decisions}

## Concern Signals Visible To Grader

{concern_signals}
"""


def protocol(seed: int) -> str:
    weights = "\n".join(f"- {name}: {weight} points" for name, weight in WEIGHTS.items())
    return f"""# Blind Skill-Use Evaluation Protocol

## Status

This is a condition-blinded structural simulation. It is more formal than the simple simulated report, but it is not a true double-blind experiment.

## Research Question

Does skill-guided agent behavior produce more scholar-inspectable outputs than careful generic agent behavior on four social-science research tasks?

## Conditions

- `no_skill`: careful generic agent behavior without the local project skills.
- `skill_guided`: behavior constrained by the local scholar workbench skills.

## Blinding

The packet files in `packets/` hide condition labels. A grader can see the task and output contents but not whether the output came from `no_skill` or `skill_guided`.

The private condition mapping is stored in `private_mapping.csv` and should not be given to graders before scoring.

## Randomization

Within each case, the two condition outputs are randomly assigned to packet IDs using seed `{seed}`. The seed is fixed for reproducibility.

## Rubric

The grading dimensions and weights are preregistered before unblinding:

{weights}

## Human Grading

Use `human_grading_sheet.csv` for independent grading. Recommended workflow:

1. Give graders only `grader_brief.md`, `packets/`, and `human_grading_sheet.csv`.
2. Ask each grader to score every packet before seeing `private_mapping.csv`.
3. Use at least two graders and compute inter-rater agreement before unblinding.
4. Unblind only after grades are frozen.

## Rule-Based Scoring

`rule_based_scores_blinded.csv` scores packets without condition labels. `unblinded_report.md` joins those scores to `private_mapping.csv` after scoring.

## Limits

- Outputs are simulated templates, not live LLM generations.
- The script author knows the hypothesis and generated both conditions.
- Rule-based scoring is deterministic and not a substitute for independent human grading.
- A true double-blind evaluation would require independently generated outputs, condition concealment during generation, blinded human graders, preregistration, and inter-rater reliability.
"""


def grader_brief() -> str:
    weights = "\n".join(f"- {name}: {weight} points" for name, weight in WEIGHTS.items())
    return f"""# Blinded Packet Grader Brief

## Task

Score each packet as a research-assistance deliverable for a social-science scholar. Do not try to infer how the packet was produced. No condition labels are provided.

## Materials You Should Receive

- `packets/*.md`
- `human_grading_sheet.csv`
- this `grader_brief.md`

Do not use `private_mapping.csv` or `unblinded_report.md` during grading.

## Scoring Rubric

Assign points using the preregistered dimensions:

{weights}

## Scoring Guidance

- Award artifact points when the packet reports concrete audit objects, not just narrative summaries.
- Award traceability points when rows, claims, comments, or findings can be traced to source files, logs, locators, or model objects.
- Award boundary points when the packet avoids hidden-AI or direct-submission-ready manuscript/response text, unsafe confidentiality handling, and unsupported scholarly claims.
- Award validation points when the packet identifies a concrete validator, gate, or check.
- Award author-decision points when the packet leaves scholarly judgment to the researcher and states what must be decided.

Freeze scores before seeing any condition mapping.
"""


def condition_outputs(case: EvalCase) -> list[SimulatedOutput]:
    return [
        replace(case.no_skill, condition="no_skill"),
        replace(case.skill_guided, condition="skill_guided"),
    ]


def make_packets(outdir: Path, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rng = random.Random(seed)
    mapping_rows: list[dict[str, str]] = []
    score_rows: list[dict[str, str]] = []
    packet_counter = 1

    for case in CASES:
        outputs = condition_outputs(case)
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
                    "scholar_question": case.scholar_question,
                }
            )

            scores = score_output(case, blinded_output)
            score_rows.append(
                {
                    "packet_id": packet_id,
                    "case_id": case.case_id,
                    "artifacts": fmt_score(scores["artifacts"]),
                    "traceability": fmt_score(scores["traceability"]),
                    "boundary": fmt_score(scores["boundary"]),
                    "validation": fmt_score(scores["validation"]),
                    "author_decision": fmt_score(scores["author_decision"]),
                    "total": fmt_score(scores["total"]),
                }
            )

    return mapping_rows, score_rows


def make_human_sheet(mapping_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "grader_id": "",
            "packet_id": row["packet_id"],
            "case_id": row["case_id"],
            "artifacts_0_30": "",
            "traceability_0_20": "",
            "boundary_0_20": "",
            "validation_0_15": "",
            "author_decision_0_15": "",
            "total_0_100": "",
            "notes": "",
        }
        for row in mapping_rows
    ]


def unblinded_report(mapping_rows: list[dict[str, str]], score_rows: list[dict[str, str]]) -> str:
    mapping_by_packet = {row["packet_id"]: row for row in mapping_rows}
    rows = []
    for score in score_rows:
        mapped = mapping_by_packet[score["packet_id"]]
        rows.append({**score, **{"condition": mapped["condition"], "scholar_question": mapped["scholar_question"]}})

    by_condition = {"no_skill": [], "skill_guided": []}
    for row in rows:
        by_condition[row["condition"]].append(float(row["total"]))

    avg_no = sum(by_condition["no_skill"]) / len(by_condition["no_skill"])
    avg_skill = sum(by_condition["skill_guided"]) / len(by_condition["skill_guided"])

    lines = [
        "# Unblinded Skill-Use Evaluation Report",
        "",
        "This report joins `rule_based_scores_blinded.csv` to `private_mapping.csv` after scoring.",
        "",
        "| packet | case | condition | total |",
        "|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(f"| {row['packet_id']} | `{row['case_id']}` | `{row['condition']}` | {row['total']} |")

    lines.extend(
        [
            "",
            f"Average `no_skill`: **{fmt_score(avg_no)} / 100**",
            f"Average `skill_guided`: **{fmt_score(avg_skill)} / 100**",
            f"Average gain: **+{fmt_score(avg_skill - avg_no)} points**",
            "",
            "Interpretation: in this structural simulation, skill-guided packets score higher because they expose audit artifacts, validation gates, AI-use disclosure, and human-accountability decisions. This is not evidence that any particular LLM will behave this way in live use.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--seed", type=int, default=20260625)
    parser.add_argument("--clean", action="store_true", help="Remove the output directory before regenerating.")
    args = parser.parse_args()

    if args.clean and args.outdir.exists():
        shutil.rmtree(args.outdir)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_text(args.outdir / "protocol.md", protocol(args.seed))
    write_text(args.outdir / "grader_brief.md", grader_brief())

    mapping_rows, score_rows = make_packets(args.outdir, args.seed)
    write_csv(
        args.outdir / "private_mapping.csv",
        mapping_rows,
        ["packet_id", "case_id", "condition", "scholar_question"],
    )
    write_csv(
        args.outdir / "rule_based_scores_blinded.csv",
        score_rows,
        ["packet_id", "case_id", "artifacts", "traceability", "boundary", "validation", "author_decision", "total"],
    )
    write_csv(
        args.outdir / "human_grading_sheet.csv",
        make_human_sheet(mapping_rows),
        [
            "grader_id",
            "packet_id",
            "case_id",
            "artifacts_0_30",
            "traceability_0_20",
            "boundary_0_20",
            "validation_0_15",
            "author_decision_0_15",
            "total_0_100",
            "notes",
        ],
    )
    write_text(args.outdir / "unblinded_report.md", unblinded_report(mapping_rows, score_rows))
    print(f"wrote blinded evaluation package to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
