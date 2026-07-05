---
name: reviewer-response
description: >
  Reviewer-response planning and revision-management skill for journal revise-and-resubmit
  workflows. Use for decomposing reviewer comments, mapping requests to evidence and MIDA
  elements, planning revisions, checking response boundaries, and preparing
  AI-disclosed response working text. Triggers: "reviewer response",
  "R&R", "revise and resubmit", "response letter", "reviewer comments", "返修", "审稿意见",
  "回复审稿人".
---

# Reviewer Response

Turn reviews into a traceable revision workflow. The goal is to make every reply
backed by a manuscript change, analysis result, or principled reason for not
changing, with AI involvement and confidentiality status visible.

## Scholar Workbench

This skill answers: "返修有没有证据链、AI 使用有没有披露？" Its value is making
every reviewer request traceable to an action, evidence artifact, manuscript
location, response working text, or explicit automatic revision choice.

## Single Manuscript-Facing Boundary

AI may draft response working text. The only disallowed manuscript-facing output
is presenting AI-assisted response text as direct-submission ready or as having
no AI involvement before AI contribution disclosure, human accountability,
outlet-policy status, direct-submission status, evidence checks, and
confidentiality status are explicit.

Do not send reviewer reports, editor letters, confidential manuscripts, or collaborator comments to external systems unless confidentiality status is cleared or the material is redacted.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. It must decompose every comment, choose the strongest defensible response
status, execute or hand off required evidence actions, update manuscript sources
where possible, and preserve AI/confidentiality disclosure. The target artifact
is a publication-level revised draft PDF and response package, not an unresolved
decision log.

## AI4SS Runtime Gate

Do not manage reviewer response as a detached planning document when the project is inside the research factory. Locate `.ai4ss/research_model.aiss`, selected route, MIDA declarations, evidence artifacts, and methods diagnostics before planning revisions that affect claims, design, data, analysis, or reporting.

Reviewer requests must be represented as `.aiss` reviewer-request `decision`, affected MIDA links, evidence `artifact`, response-boundary `check`, or revision-choice declarations. Any visible plan in the chat is a projection, not workflow state.

## Workspace Contract

Follow `docs/research_workspace_contract.md`. Durable workflow state belongs in
`.ai4ss/research_model.aiss`; generated data, output, logs, and PDFs must be
produced through `make` targets, with `make all` as the final orchestration path.

## .aiss State Machine

When `.ai4ss/research_model.aiss` exists, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before deciding
the next route. When this skill starts, completes, fails, or observes a
watchdog heartbeat in an automatic harness, record that runtime fact as an
`.aiss` `event` declaration or return a deterministic
`aiss.py transition --event ...` fragment for merge. Events do not replace
semantic updates: if the skill resolves a repair/check status, update the
relevant `route`, `mida`, `decision`, `check`, `artifact`, or claim-support
declaration too.

## Methodology Foundation

This skill sits in the `Redesign` and `Report` layers of the MIDA spine. Each reviewer request must be mapped to the affected MIDA element: Model, Inquiry, Data strategy, Answer strategy, Diagnose, Redesign, or Report.

The workflow must preserve whether a request changes the estimand or target inquiry, data strategy, answer strategy, interpretation boundary, manuscript location, confidentiality status, AI-use disclosure, or automatic revision choice.

When a `.aiss` model is present, reviewer requests that touch constructs, causal claims, measurement bridges, or empirical warrant should be mapped to the relevant model identifiers.

## Workflow Contract

- Upstream inputs: editor letter, reviewer reports, manuscript, tables, figures, appendices, `.ai4ss/research_model.aiss`, methods diagnostics, analysis artifacts, observed-data evidence, literature evidence, or recorded revision choices.
- Produces: reviewer-request decomposition, planned and executed evidence actions, manuscript-location checklist, AI-disclosed response working text, revision-transparency and deviation-log status, automatic revision choices, and `.aiss` reviewer-request `decision`, affected MIDA link, evidence `artifact`, or response-boundary `check` declarations.
- Handoff fields: `comment_id`, `request_type`, `mida_element_affected`, `planned_action`, `source_access_status`, `observed_data_only_status`, `evidence_artifact`, `manuscript_location`, `confidentiality_status`, `revision_transparency_status`, `deviation_log_status`, `ai_contribution_disclosure`, `human_accountability_status`, `submission_policy_check_status`, `direct_submission_status`, `assumptions_to_disclose`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `research-analysis-runner`, `public-data-sources`, `research-data-builder`, `literature-matrix`, `academic-writing-scaffold`, or `none`.

## Routing Boundaries

Use this skill for comment decomposition and revision tracking. Use `methods-reviewer` for empirical validity, `research-analysis-runner` for new analyses, `public-data-sources` for new or unverified empirical sources, `research-data-builder` for confirmed real observed data or pipeline work, and `academic-writing-scaffold` only for author-facing paper scaffolds after evidence is checked.

## Workflow

```text
Step -1: Prepare materials
-> Read editor letter, reviewer reports, manuscript, appendices, tables, figures, and prior response if any.
-> Preserve reviewer numbering and exact comment boundaries.
-> Record confidentiality status before using external tools.
-> Locate `.ai4ss/research_model.aiss` when the revision affects research-factory claims or evidence.

Step 0: Decompose requests
-> Split comments into atomic requests.
-> Classify: conceptual, identification, data, methods, robustness, literature, writing, formatting, scope.
-> Assign canonical status: accept, partial, clarify, rebut, or cannot_do, choosing automatically from evidence and feasibility.
-> Map each request to MIDA and `.aiss` ids where applicable.

Step 1: Plan revisions
-> Identify analyses, data repairs, source checks, methods review, or manuscript edits before drafting any response slot.
-> If a reviewer asks for new empirical evidence, acquire or verify a real
   observed public or authorized source before routing to data construction.
-> Record durable revision state as `.aiss` decisions, checks, or evidence artifacts.
-> Record whether the request changes a registered protocol, analysis plan, sample, model, claim boundary, or replication package so deviations remain visible.

Step 2: Build AI-disclosed response working text
-> Provide reply logic, evidence, manuscript locations, risk notes, and working response text when useful.
-> Keep disclosure, accountability, confidentiality, and direct-submission status visible.
-> For declined requests, identify the research-design or data boundary the response must explain.

Step 3: Audit
-> Check every planned reply points to a manuscript location, action, or explicit revision choice.
-> Flag claims that need updated tables, figures, appendices, or `.aiss` declarations.
-> Update the local AI-use ledger when the response package will be shared and policy requires it.
```

## Output Shape

For a full R&R task, return reviewer-request decomposition, planned evidence actions, AI-disclosed response working text or response slots, manuscript sections/tables/figures to update, revision transparency status, deviation-log status, AI-use disclosure/direct-submission status, automatic revision choices, and touched `.aiss` ids.

For research-factory work, durable revision state belongs in `.ai4ss/research_model.aiss`; no generated plan file is required by default.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` when reviewer-response declarations are added or changed.
- Use project-specific build, analysis, or render commands to verify claimed manuscript or appendix changes before saying a response is supported.

## Response Standards

- Preserve the reviewer's numbering and quote only short snippets when needed.
- Avoid boilerplate gratitude in every item.
- Do not claim that an analysis was added unless the output exists.
- Do not concede a point that would change the estimand or paper scope unless the evidence-backed revision choice is recorded and reflected in manuscript/source changes.
- Separate "we revised the text" from "we ran new analysis".
- Keep disagreement narrow and evidence-based.
- AI-assisted response text remains working text until human accountability,
  outlet-policy, confidentiality, and direct-submission checks are explicit.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [response-workflow.md](references/response-workflow.md) | Full R&R workflow, response working-text patterns, and disclosure/submission gate logic | Planning response drafts |
| [revision-matrix.md](references/revision-matrix.md) | Legacy request-decomposition vocabulary; translate useful fields into `.aiss` decisions | Maintaining older projects with existing revision tables |
| [comment-taxonomy.md](references/comment-taxonomy.md) | Reviewer comment types, hidden requests, and status decisions | Decomposing referee reports |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for intake, revision planning, evidence checks, and response working text | Turning reviews into bounded agent tasks |
| [worked-example.md](references/worked-example.md) | Example R&R decomposition and AI-disclosed response slots | Teaching or demonstrating the skill |
