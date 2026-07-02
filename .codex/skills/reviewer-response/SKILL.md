---
name: reviewer-response
description: >
  Reviewer-response planning and revision-management skill for journal resubmissions, R&R letters,
  editor letters, referee reports, point-by-point reply scaffolds, manuscript change tracking, and
  revision memos. Use when handling reviewer comments, translating reviews into action plans,
  mapping changes to manuscript locations, building response scaffolds, or assigning accept, partial,
  clarify, rebut, cannot_do, and needs_author statuses. It does not directly write final submission-ready
  response prose. Triggers: "reviewer response", "R&R", "revise and resubmit", "response scaffold",
  "审稿意见", "审稿意见处理", "返修", "返修回复", "point-by-point", "revision matrix".
---

# Reviewer Response

Turn reviews into a traceable revision plan and response scaffold. The goal is to make every author-written reply backed by a manuscript change, analysis result, or principled reason for not changing.

## Scholar Workbench

This skill answers: "返修有没有证据链？" Its value is not producing polished replies; it is making every reviewer request traceable to an action, evidence artifact, manuscript location, or explicit author decision.

## Core Rule

Do not draft final submission-ready response prose. First classify every reviewer request and check whether the manuscript, tables, figures, appendices, or new analyses support the planned reply.

Do not send reviewer reports, editor letters, confidential manuscripts, or collaborator comments to external systems unless the revision matrix `confidentiality_status` is `cleared` or `redacted`.

## Methodology Foundation

This skill sits in the `Redesign` and `Report` layers of the MIDA spine. Each reviewer request must be mapped to the affected MIDA element: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, or Report.

The matrix must preserve whether a request changes the estimand or target inquiry, data strategy, answer strategy, interpretation boundary, manuscript location, confidentiality status, or author decision. It does not write the final response letter.

When a `.aiss` model is present, reviewer requests that touch constructs, causal claims, measurement bridges, or empirical warrant should be mapped to the relevant model identifiers.

## Workflow Contract

- Upstream inputs: editor letter, reviewer reports, manuscript, tables, figures, appendices, `research_model.aiss`, methods issue table, analysis run manifest, data/literature audit outputs, or author decisions.
- Produces: `revision_matrix.csv`, revision plan, response scaffold with author-fillable slots, manuscript-location checklist, and open decisions.
- Handoff fields: `comment_id`, `request_type`, `mida_element_affected`, `planned_action`, `evidence_artifact`, `manuscript_location`, `confidentiality_status`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `research-analysis-runner`, `research-data-builder`, `literature-matrix`, `academic-writing-scaffold`, `ask_author`, or `none`.

## Routing Boundaries

Use this skill for comment decomposition and revision tracking. Use `methods-reviewer` for empirical validity, `research-analysis-runner` for new analyses, `research-data-builder` for confirmed data or pipeline work, and `academic-writing-scaffold` only for author-facing paper scaffolds after evidence is checked.

## Workflow

```
Step -1: Prepare materials
-> Read editor letter, reviewer reports, manuscript, appendices, tables, figures, and prior response if any.
-> Preserve reviewer numbering and exact comment boundaries.
-> Record confidentiality status before using external tools.

Step 0: Build revision matrix
-> Split comments into atomic requests.
-> Classify: conceptual, identification, data, methods, robustness, literature, writing, formatting, scope.
-> Assign canonical status: accept, partial, clarify, rebut, cannot_do, needs_author.

Step 1: Plan revisions
-> Read references/response-workflow.md.
-> Use references/revision-matrix.md for required columns.
-> Identify analyses or text changes before writing response prose.

Step 2: Build response scaffold
-> Provide reply logic, evidence, manuscript locations, and risk notes.
-> Use slot-based author prompts instead of polished final prose.
-> For declined requests, identify the research-design or data boundary the author must explain.

Step 3: Audit
-> Check every response points to a manuscript location or action.
-> Flag claims that need updated tables, figures, or appendices.
-> Update the AI-use ledger with `tool_model`, `task`, `inputs`, `outputs`, `human_review`, `disclosure_location`, and `confidentiality_approval_status` when the response package will be shared.
```

## Output Shape

For a full R&R task, produce:

1. `docs/revision_matrix.csv` or a Markdown table.
2. `docs/revision_plan.md`.
3. Response scaffold with author-fillable slots.
4. List of manuscript sections/tables/figures that must be updated.
5. Open decisions for the author.

If a Markdown table or XLSX workbook is easier for the author, keep a CSV sidecar with the canonical revision-matrix schema and validate that CSV.

## Script Utilities

- Run `scripts/validate_revision_matrix.py <path>` to check revision-matrix columns and status labels.

## Response Standards

- Preserve the reviewer's numbering and quote only short snippets when needed.
- Avoid boilerplate gratitude in every item.
- Do not claim that an analysis was added unless the output exists.
- Do not concede a point that would change the estimand or paper scope without user approval.
- Separate "we revised the text" from "we ran new analysis".
- Keep disagreement narrow and evidence-based.
- Final response prose must be authored and approved by the researcher.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [response-workflow.md](references/response-workflow.md) | Full R&R workflow, response scaffold patterns, and refusal-boundary logic | Planning response scaffolds |
| [revision-matrix.md](references/revision-matrix.md) | Revision matrix schema and status definitions | Creating the traceable action table |
| [comment-taxonomy.md](references/comment-taxonomy.md) | Reviewer comment types, hidden requests, and status decisions | Decomposing referee reports |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for intake, revision planning, evidence checks, and response scaffolds | Turning reviews into bounded agent tasks |
| [worked-example.md](references/worked-example.md) | Example R&R decomposition, revision matrix rows, and author-fillable response scaffold | Teaching or demonstrating the skill |
