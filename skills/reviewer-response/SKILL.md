---
name: reviewer-response
description: >
  Reviewer-response planning and revision-management skill for journal revise-and-resubmit
  workflows. Use for decomposing reviewer comments, mapping requests to evidence and MIDA
  elements, planning revisions, checking response boundaries, and preparing author-fillable
  response slots without writing final response prose. Triggers: "reviewer response",
  "R&R", "revise and resubmit", "response letter", "reviewer comments", "返修", "审稿意见",
  "回复审稿人".
---

# Reviewer Response

Turn reviews into a traceable revision workflow. The goal is to make every author-written reply backed by a manuscript change, analysis result, or principled reason for not changing.

## Scholar Workbench

This skill answers: "返修有没有证据链？" Its value is not producing polished replies; it is making every reviewer request traceable to an action, evidence artifact, manuscript location, or explicit author decision.

## Core Rule

Do not draft final submission-ready response prose. First classify every reviewer request and check whether the manuscript, tables, figures, appendices, or new analyses support the planned reply.

Do not send reviewer reports, editor letters, confidential manuscripts, or collaborator comments to external systems unless confidentiality status is cleared or the material is redacted.

## AI4SS Runtime Gate

Do not manage reviewer response as a detached planning document when the project is inside the research factory. Locate `research_model.aiss`, selected route, MIDA declarations, evidence artifacts, and methods diagnostics before planning revisions that affect claims, design, data, analysis, or reporting.

Reviewer requests must be represented as `.aiss` reviewer-request `decision`, affected MIDA links, evidence `artifact`, response-boundary `check`, or author `decision` declarations. Any visible plan in the chat is a projection for the author, not workflow state.

## Methodology Foundation

This skill sits in the `Redesign` and `Report` layers of the MIDA spine. Each reviewer request must be mapped to the affected MIDA element: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, or Report.

The workflow must preserve whether a request changes the estimand or target inquiry, data strategy, answer strategy, interpretation boundary, manuscript location, confidentiality status, or author decision. It does not write the final response letter.

When a `.aiss` model is present, reviewer requests that touch constructs, causal claims, measurement bridges, or empirical warrant should be mapped to the relevant model identifiers.

## Workflow Contract

- Upstream inputs: editor letter, reviewer reports, manuscript, tables, figures, appendices, `research_model.aiss`, methods diagnostics, analysis artifacts, data/literature evidence, or author decisions.
- Produces: reviewer-request decomposition, planned evidence actions, manuscript-location checklist, author-fillable response slots, open decisions, and `.aiss` reviewer-request `decision`, affected MIDA link, evidence `artifact`, response-boundary `check`, or author `decision` declarations.
- Handoff fields: `comment_id`, `request_type`, `mida_element_affected`, `planned_action`, `evidence_artifact`, `manuscript_location`, `confidentiality_status`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `research-analysis-runner`, `research-data-builder`, `literature-matrix`, `academic-writing-scaffold`, `ask_author`, or `none`.

## Routing Boundaries

Use this skill for comment decomposition and revision tracking. Use `methods-reviewer` for empirical validity, `research-analysis-runner` for new analyses, `research-data-builder` for confirmed data or pipeline work, and `academic-writing-scaffold` only for author-facing paper scaffolds after evidence is checked.

## Workflow

```text
Step -1: Prepare materials
-> Read editor letter, reviewer reports, manuscript, appendices, tables, figures, and prior response if any.
-> Preserve reviewer numbering and exact comment boundaries.
-> Record confidentiality status before using external tools.
-> Locate research_model.aiss when the revision affects research-factory claims or evidence.

Step 0: Decompose requests
-> Split comments into atomic requests.
-> Classify: conceptual, identification, data, methods, robustness, literature, writing, formatting, scope.
-> Assign canonical status: accept, partial, clarify, rebut, cannot_do, needs_author.
-> Map each request to MIDA and `.aiss` ids where applicable.

Step 1: Plan revisions
-> Identify analyses, data repairs, source checks, methods review, or author decisions before drafting any response slot.
-> Record durable revision state as `.aiss` decisions, checks, or evidence artifacts.

Step 2: Build author-fillable response slots
-> Provide reply logic, evidence, manuscript locations, and risk notes.
-> Use slot-based author prompts instead of polished final prose.
-> For declined requests, identify the research-design or data boundary the author must explain.

Step 3: Audit
-> Check every planned reply points to a manuscript location, action, or explicit author decision.
-> Flag claims that need updated tables, figures, appendices, or `.aiss` declarations.
-> Update the local AI-use ledger when the response package will be shared and policy requires it.
```

## Output Shape

For a full R&R task, return reviewer-request decomposition, planned evidence actions, author-fillable response slots, manuscript sections/tables/figures to update, open author decisions, and touched `.aiss` ids.

For research-factory work, durable revision state belongs in `research_model.aiss`; no generated plan file is required by default.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when reviewer-response declarations are added or changed.
- Use project-specific build, analysis, or render commands to verify claimed manuscript or appendix changes before saying a response is supported.

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
| [response-workflow.md](references/response-workflow.md) | Full R&R workflow, response slot patterns, and refusal-boundary logic | Planning response scaffolds |
| [revision-matrix.md](references/revision-matrix.md) | Legacy request-decomposition vocabulary; translate useful fields into `.aiss` decisions | Maintaining older projects with existing revision tables |
| [comment-taxonomy.md](references/comment-taxonomy.md) | Reviewer comment types, hidden requests, and status decisions | Decomposing referee reports |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for intake, revision planning, evidence checks, and response scaffolds | Turning reviews into bounded agent tasks |
| [worked-example.md](references/worked-example.md) | Example R&R decomposition and author-fillable response slots | Teaching or demonstrating the skill |
