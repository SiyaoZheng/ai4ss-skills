# Factory-Level AI4SS Workflow Evaluation Protocol

## Status

This is a condition-blinded structural evaluation of the local AI4SS autonomous
research factory workflow. It is stronger than a single-skill packet demo
because it scores the whole chain from rough topic to checked research-state
objects. Scores must come from LLM-as-judge; this package does not contain
rule-based scores.

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
  validators, and explicit automation assumption boundaries.

## Blinding

Packet files in `packets/` hide the condition label. The private mapping lives
in `_private/private_mapping.csv` and should remain hidden until scores are
frozen. The packet contents may still reveal differences because the factory
condition exposes `.aiss` artifacts by design.

## Randomization

The two condition outputs are randomly assigned to packet IDs with seed `20260701`.

## Preregistered LLM-As-Judge Rubric

- `research_object`: 13 points
- `mida_design`: 13 points
- `ai4ss_model_check`: 13 points
- `evidence_data_chain`: 14 points
- `analysis_loop`: 13 points
- `figure_package`: 10 points
- `claim_boundary_automation`: 14 points
- `end_to_end_continuity`: 10 points

The rubric is intentionally artifact- and gate-oriented. It does not score
publication quality, empirical truth, or prose elegance.

## Human Audit Sheet

For non-scoring expert review, give auditors only:

- `grader_brief.md`
- `packets/`
- `human_grading_sheet.csv`
- optionally `gate_matrix_blinded.csv`

Do not report the human sheet as the eval score. The score interface is
`judge_prompts/` plus `llm_judge_scores.csv`.

## Limits

- Outputs are deterministic structural packets, not live LLM generations.
- Generation is not blind; the script author knows the hypothesis.
- Rule-based scoring is not used as the eval result. The prompt files under
  `judge_prompts/` are the scoring interface.
- A stronger follow-up would use independently generated live outputs, concealed
  condition assignment during scoring, independent LLM judges, expert audit of
  the judge rubric, and inter-rater reliability.
