# Worked Example: Results Section Scaffold

This example demonstrates AI-assisted manuscript working text with disclosure
and direct-submission gates visible.

## Inputs

- `output/tables/table1_baseline.csv`
- `output/figures/event_study.svg`
- `output/audit/.aiss row-loss checks`
- `docs/research_design.md`

## Evidence Inventory

| artifact | evidence type | use |
|---|---|---|
| `table1_baseline.csv` | estimate | main DID result |
| `event_study.svg` | diagnostic | pre-trend and dynamic pattern |
| `.aiss row-loss checks` | design fact | final sample and restrictions |
| `research_design.md` | design fact | unit, treatment, FE, clustering |

## Claim Ledger

| claim_id | claim_text_or_slot | claim_type | evidence_path | support_level | risk | author_action | author_boundary | artifact_kind |
|---|---|---|---|---|---|---|---|---|
| C1 | preferred specification estimates post-treatment difference | estimate | table column 4 | strong | scale ambiguity | cite | scaffold_only | scaffold_only |
| C2 | design compares treated and untreated city-years | design_fact | research_design.md | strong | causal language | soften | scaffold_only | scaffold_only |
| C3 | pre-trends are visually flat | diagnostic | event_study.svg | partial | missing citation | add_evidence | needs_author_decision | decision_prompt |
| C4 | policy improves innovation capacity | interpretation | table + figure | weak | overclaim | revise_target | scaffold_only | scaffold_only |
| C5 | missing controls do not affect results | diagnostic | robustness needed | missing | unsupported mechanism | delete | scaffold_only | scaffold_only |

## AI-Assisted Working Text Plan

| paragraph | purpose | evidence to use | gate status |
|---|---|---|---|
| 1 | orient reader to table | table title, model column, sample | AI-assisted working text; not direct-submission ready |
| 2 | state preferred estimate | coefficient, SE/CI, N, FE, clustering | AI-assisted working text; not direct-submission ready |
| 3 | connect event-study diagnostic | baseline period, pre-treatment coefficients, bands | AI-assisted working text; not direct-submission ready |
| 4 | state boundary | `.aiss` row-loss checks, missingness, design assumption | AI-assisted working text; not direct-submission ready |

## Disallowed Presentation

Do not present this AI-assisted working text as no-AI or direct-submission
ready:

```text
The policy significantly promotes innovation and confirms the effectiveness of urban pilot programs.
```

Why:

- "promotes" is causal and too broad without stating design.
- "innovation" may exceed `ln_patent`.
- "confirms effectiveness" is policy language beyond the estimate.

## Disclosure Gate

- `ai_contribution_disclosure`: required
- `human_accountability_status`: needs_author_review
- `submission_policy_check_status`: not_checked
- `direct_submission_status`: not_ready

## Safe Working-Text Notes

- Use the exact outcome name.
- Mention city and year fixed effects if in the table.
- Report N and clustering.
- State the event-study baseline period.
- Avoid mechanism claims unless mechanism table exists.
