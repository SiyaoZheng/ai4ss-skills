# Worked Example

## Intake

Rough topic: digital-government platforms and firm green innovation.

Available materials:

- A city-year policy list from public notices.
- Firm patent counts by year.
- Three seed papers on digital government and innovation.
- Notes from a policy report.

Hard boundaries:

- No final manuscript prose.
- Do not claim causality before identification review.
- Do not use confidential firm documents.

Desired next action: decide what can be tried first.

## Route Cards

| route | question | study type | first action | next skill |
|---|---|---|---|---|
| R1 | Did platform rollout coincide with changes in firm green patenting? | causal | Check city-year rollout timing, firm-city linkage, and pre/post coverage | `research-data-builder` |
| R2 | What mechanisms do policy documents claim for digital-government effects on firms? | text_analysis | Build a 20-document extraction schema for mechanism sentences | `literature-matrix` or `research-data-builder` |
| R3 | How does the literature measure digital government in firm outcomes research? | theory_mapping | Build a candidate source ledger from seed papers and snowballing targets | `literature-matrix` |

## Minimum Viable Study

Start with R1 only if the policy list has city identifiers, rollout year, and a linkable firm location field. The first viable output is not an estimate; it is a feasibility table:

- number of cities with rollout year;
- firm-year coverage before and after rollout;
- missing city linkage rate;
- earliest and latest rollout year;
- whether untreated or not-yet-treated comparison units exist.

## Stop Reason

Do not estimate the DID yet. The researcher must confirm whether platform rollout is plausibly exogenous enough to justify a causal route, or whether the project should become descriptive or text-based.

## Handoff Prompt

```text
Use $research-data-builder on route R1.

Inputs: policy rollout list, firm patent panel, firm-city linkage.
Goal: build a feasibility table only. Report city-year coverage, missing linkage, rollout-year distribution, and whether comparison units exist.
Do not estimate treatment effects. Stop if treatment timing or city linkage is ambiguous.
```
