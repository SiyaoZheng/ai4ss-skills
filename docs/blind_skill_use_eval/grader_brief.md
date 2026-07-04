# Blinded Packet Grader Brief

## Task

Score each packet as a research-assistance deliverable for a social-science scholar. Do not try to infer how the packet was produced. No condition labels are provided.

## Materials You Should Receive

- `packets/*.md`
- `human_grading_sheet.csv`
- this `grader_brief.md`

Do not use `private_mapping.csv` or `unblinded_report.md` during grading.

## Scoring Rubric

Assign points using the preregistered dimensions:

- artifacts: 30 points
- traceability: 20 points
- boundary: 20 points
- validation: 15 points
- author_decision: 15 points

## Scoring Guidance

- Award artifact points when the packet reports concrete audit objects, not just narrative summaries.
- Award traceability points when rows, claims, comments, or findings can be traced to source files, logs, locators, or model objects.
- Award boundary points when the packet avoids hidden-AI or direct-submission-ready manuscript/response text, unsafe confidentiality handling, and unsupported scholarly claims.
- Award validation points when the packet identifies a concrete validator, gate, or check.
- Award author-decision points when the packet leaves scholarly judgment to the researcher and states what must be decided.

Freeze scores before seeing any condition mapping.
