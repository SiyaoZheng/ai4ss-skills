# Blind Skill-Use Evaluation Protocol

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

Within each case, the two condition outputs are randomly assigned to packet IDs using seed `20260625`. The seed is fixed for reproducibility.

## Rubric

The grading dimensions and weights are preregistered before unblinding:

- artifacts: 30 points
- traceability: 20 points
- boundary: 20 points
- validation: 15 points
- assumption_register: 15 points

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
