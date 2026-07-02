# Live Condition-Blinded Skill-Use Evaluation Protocol

## Status

This package uses live agent-generated outputs and condition-blinded grading.
It is more probative than a structural simulation, but it is still not a true
double-blind field experiment.

## Research Question

Does skill-guided agent behavior produce more scholar-inspectable outputs than
careful generic agent behavior on four social-science research tasks?

## Experimental Unit

One packet is one agent deliverable for one scholar workbench case. Each case has
two matched outputs:

- `no_skill`: careful generic research-assistant behavior, instructed not to read
  project-local skill documents.
- `skill_guided`: behavior instructed to use the relevant project-local skill.

## Blinding And Randomization

Generation is not blinded because the prompt must assign a condition. Scoring is
condition-blinded: graders receive only `grader_brief.md`, `packets/`, and a
blank grading sheet. The condition mapping is kept in `_private/private_mapping.csv`
until grades are frozen.

Within each case, packet order is randomized. The seed is recorded privately and
disclosed in the unblinded report after grades are frozen. The paired case design
keeps the task constant while varying the generation condition.

## Preregistered Rubric

- `artifacts`: 30 points
- `traceability`: 20 points
- `boundary`: 20 points
- `validation`: 15 points
- `author_decision`: 15 points

## Grading Workflow

1. Generate raw outputs and save them under `raw_generations/`.
2. Run `python3 scripts/run_live_blind_skill_use_eval.py package --clean`.
3. Give graders only `grader_brief.md`, `packets/`, and `human_grading_sheet.csv`.
4. Save frozen grader files under `human_grades/`.
5. Run `python3 scripts/run_live_blind_skill_use_eval.py report`.
6. Read `unblinded_report.md` only after scoring is complete.

After grades are frozen, do not repackage with a fresh seed. To reproduce the
current mapping, run `package` with the seed disclosed in `_private/randomization_seed.txt`.

## Methodological Limits

- The generator agents know their assigned condition.
- The main evaluator creates the mapping and therefore cannot be blind.
- Agent graders are useful for a fast simulation of human scoring, not a
  replacement for independent human graders.
- Packet contents may still reveal style differences even after condition labels
  are removed.
- Scores estimate usefulness for traceable research assistance, not truth,
  publication quality, or final scholarly responsibility.

## Method References

- CONSORT 2025 is used only as a reporting analogy for distinguishing
  randomization, allocation concealment, blinding, and limitations; this package
  is not a randomized clinical trial.
- NLG and LLM-as-judge work motivates rubric-based form scoring and caution about
  evaluator bias; agent grader scores should be treated as provisional until
  checked by independent human experts.

References: BMJ CONSORT 2025 explanation and elaboration
<https://www.bmj.com/content/389/bmj-2024-081124>; CONSORT-SPIRIT blinding note
<https://www.consort-spirit.org/spiriteande24a/item-22-allocation-concealment-mechanism>;
G-Eval / EMNLP 2023 <https://aclanthology.org/2023.emnlp-main.153/>;
LLM-as-a-Judge survey <https://arxiv.org/html/2411.15594v6>.
