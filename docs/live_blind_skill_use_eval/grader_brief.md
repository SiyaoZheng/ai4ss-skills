# Live Blinded Packet Grader Brief

Score each packet as a research-assistance deliverable for a computational social
scientist. Do not infer or guess how the packet was produced. No condition labels
are provided.

## Materials

- `packets/*.md`
- `human_grading_sheet.csv`
- this `grader_brief.md`

Do not use `_private/private_mapping.csv`, `raw_generations/`, generation prompts,
or `unblinded_report.md` during grading.

## Rubric

- `artifacts`: 30 points
- `traceability`: 20 points
- `boundary`: 20 points
- `validation`: 15 points
- `author_decision`: 15 points

## Scoring Guidance

- Award artifact points for concrete research objects: `.aiss` route, MIDA,
  source-evidence, row-loss, merge, diagnostic, claim, presentation, and
  reviewer-request declarations.
- Award traceability points when rows, claims, comments, or findings can be traced
  to files, logs, locators, model objects, or explicit source checks.
- Award boundary points when the packet avoids hidden-AI or direct-submission-ready
  manuscript/response text, unsafe confidentiality handling, and unsupported claims.
- Award validation points when the packet names a concrete validator, gate, or
  check that could fail.
- Award author-decision points when scholarly judgment remains visibly assigned
  to the researcher.

Freeze scores before viewing any condition mapping.
