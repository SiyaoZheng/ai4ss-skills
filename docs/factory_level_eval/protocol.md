# Factory-Level AI4SS Workflow Evaluation Protocol

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

The two condition outputs are randomly assigned to packet IDs with seed `20260701`.

## Preregistered Rubric

- `research_object`: 15 points
- `mida_design`: 15 points
- `ai4ss_model_check`: 15 points
- `evidence_data_chain`: 15 points
- `analysis_loop`: 15 points
- `boundary_author_decision`: 15 points
- `end_to_end_continuity`: 10 points

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
