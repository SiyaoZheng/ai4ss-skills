#!/usr/bin/env python3
"""Generate a condition-blinded skill-use evaluation packet set.

This is a stricter companion to `simulate_skill_use_eval.py`.
It creates:

- anonymized output packets for graders;
- a private condition mapping;
- a blank human grading sheet;
- LLM-as-judge prompt files;
- a blank LLM judge score sheet;
- an unblinded report template after scoring.

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

from simulate_skill_use_eval import CASES, WEIGHTS, EvalCase, SimulatedOutput


DEFAULT_OUTDIR = Path("docs/blind_skill_use_eval")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def packet_body(packet_id: str, case: EvalCase, output: SimulatedOutput) -> str:
    artifacts = "\n".join(f"- {item}" for item in output.artifacts) or "- none"
    traces = "\n".join(f"- {item}" for item in output.trace_markers) or "- none"
    validators = "\n".join(f"- {item}" for item in output.validator_refs) or "- none"
    decisions = "\n".join(f"- {item}" for item in output.assumption_register) or "- none"
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

## Automation Assumptions Surfaced

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

## LLM-As-Judge Scoring

`judge_prompts/` contains one bounded prompt per blinded packet.
`llm_judge_scores.csv` is the only score sheet for this package.
`unblinded_report.md` joins those scores to `private_mapping.csv` after scoring.

## Limits

- Outputs are simulated templates, not live LLM generations.
- The script author knows the hypothesis and generated both conditions.
- Deterministic packet construction is not an eval score.
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
- Award assumption-register points when the packet states auto-selected assumptions, limits, and repair routes.

Freeze scores before seeing any condition mapping.
"""


def judge_prompt(packet_id: str, packet_text: str) -> str:
    weights = "\n".join(f"- `{name}`: {weight} points" for name, weight in WEIGHTS.items())
    return f"""You are the LLM-as-judge for a condition-blinded AI4SS skill-use packet.

Judge only the blinded packet below. Do not use the hidden condition mapping,
repository state, or any transcript outside the packet.

Score the packet on a 0-100 scale using this rubric:

{weights}

Return exactly:
SCORE: <integer from 0 to 100>
REASON: <brief explanation grounded in the packet>

Blinded packet `{packet_id}`:

```markdown
{packet_text}
```
"""


def condition_outputs(case: EvalCase) -> list[SimulatedOutput]:
    return [
        replace(case.no_skill, condition="no_skill"),
        replace(case.skill_guided, condition="skill_guided"),
    ]


def make_packets(outdir: Path, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rng = random.Random(seed)
    mapping_rows: list[dict[str, str]] = []
    judge_rows: list[dict[str, str]] = []
    packet_counter = 1

    for case in CASES:
        outputs = condition_outputs(case)
        rng.shuffle(outputs)
        for output in outputs:
            packet_id = f"P{packet_counter:03d}"
            packet_counter += 1

            blinded_output = replace(output, condition="blinded")
            packet_text = packet_body(packet_id, case, blinded_output)
            write_text(outdir / "packets" / f"{packet_id}.md", packet_text)
            prompt_path = outdir / "judge_prompts" / f"{packet_id}.md"
            write_text(prompt_path, judge_prompt(packet_id, packet_text))

            mapping_rows.append(
                {
                    "packet_id": packet_id,
                    "case_id": case.case_id,
                    "condition": output.condition,
                    "scholar_question": case.scholar_question,
                }
            )

            judge_rows.append(
                {
                    "packet_id": packet_id,
                    "case_id": case.case_id,
                    "judge_prompt": str(prompt_path.relative_to(outdir)),
                    "llm_score_0_100": "",
                    "judge_reason": "",
                    "judge_model": "",
                }
            )

    return mapping_rows, judge_rows


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
            "assumption_register_0_15": "",
            "total_0_100": "",
            "notes": "",
        }
        for row in mapping_rows
    ]


def unblinded_report(mapping_rows: list[dict[str, str]], judge_rows: list[dict[str, str]]) -> str:
    mapping_by_packet = {row["packet_id"]: row for row in mapping_rows}
    rows = []
    for score in judge_rows:
        mapped = mapping_by_packet[score["packet_id"]]
        rows.append({**score, **{"condition": mapped["condition"], "scholar_question": mapped["scholar_question"]}})

    by_condition = {"no_skill": [], "skill_guided": []}
    for row in rows:
        if row.get("llm_score_0_100"):
            by_condition[row["condition"]].append(float(row["llm_score_0_100"]))

    lines = [
        "# Unblinded Skill-Use Evaluation Report",
        "",
        "This report joins `llm_judge_scores.csv` to `private_mapping.csv` after scoring.",
        "",
        "| packet | case | condition | LLM score | judge prompt |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        score = row.get("llm_score_0_100") or "-"
        lines.append(f"| {row['packet_id']} | `{row['case_id']}` | `{row['condition']}` | {score} | `{row['judge_prompt']}` |")

    lines.append("")
    if by_condition["no_skill"] and by_condition["skill_guided"]:
        avg_no = sum(by_condition["no_skill"]) / len(by_condition["no_skill"])
        avg_skill = sum(by_condition["skill_guided"]) / len(by_condition["skill_guided"])
        lines.extend(
            [
                f"Average `no_skill`: **{avg_no:.1f} / 100**",
                f"Average `skill_guided`: **{avg_skill:.1f} / 100**",
                f"Average gain: **+{avg_skill - avg_no:.1f} points**",
            ]
        )
    else:
        lines.append("This package is ready for LLM-as-judge scoring. Do not report a skill-use gain until `llm_judge_scores.csv` has model judge scores.")
    lines.extend(
        [
            "",
            "Interpretation must remain narrow. This structural packet package can test whether outputs expose audit artifacts, validation gates, AI-use disclosure, and explicit assumption registers. It is not evidence that any particular live LLM will behave this way.",
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

    mapping_rows, judge_rows = make_packets(args.outdir, args.seed)
    write_csv(
        args.outdir / "private_mapping.csv",
        mapping_rows,
        ["packet_id", "case_id", "condition", "scholar_question"],
    )
    write_csv(
        args.outdir / "llm_judge_scores.csv",
        judge_rows,
        ["packet_id", "case_id", "judge_prompt", "llm_score_0_100", "judge_reason", "judge_model"],
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
            "assumption_register_0_15",
            "total_0_100",
            "notes",
        ],
    )
    write_text(args.outdir / "unblinded_report.md", unblinded_report(mapping_rows, judge_rows))
    print(f"wrote blinded evaluation package to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
