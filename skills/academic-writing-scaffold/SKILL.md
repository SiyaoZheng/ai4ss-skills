---
name: academic-writing-scaffold
description: >
  Academic writing support skill for AI-disclosed social-science manuscript work.
  Use for evidence maps, argument outlines, bounded claim checks, citation-gap checks,
  causal-language risk checks, section planning, AI-assisted working manuscript drafts,
  revision notes, and submission-gate checks. Triggers: "writing scaffold",
  "argument outline", "claim audit", "evidence map", "citation gaps", "table to claim",
  "draft manuscript section", "academic writing boundary", "论文写作边界", "写作支架",
  "AI披露", "投稿前检查".
---

# Academic Writing Scaffold

Support academic writing with explicit AI disclosure and submission gating. The
skill produces structures, checks, author decision points, and AI-assisted
working prose when requested.

## Scholar Workbench

This skill answers: "作者怎样写得更稳、披露得更清楚？" Its value is turning
evidence into bounded claim slots, risk labels, AI-assisted working text, and
submission-gate checks.

## Single Manuscript-Facing Boundary

AI may draft, revise, and assemble manuscript working text. The only disallowed
manuscript-facing output is presenting AI-assisted output as direct-submission
ready or as having no AI involvement. A manuscript package is
submission-ineligible until it records AI
contribution disclosure, human accountability status, outlet-policy-check
status, and direct-submission status.

Allowed outputs include evidence inventories, bounded claim slots, section-level
scaffolds, AI-assisted working paragraphs, table-to-claim audits, citation-gap
checks, causal-language risk labels, issue labels, revision targets, disclosure
language candidates, and author decision questions.

## AI4SS Runtime Gate

Do not build writing scaffolds from disconnected tables or memory when the project is inside the research factory. Locate `research_model.aiss`, selected route, MIDA declarations, checked evidence artifacts, and methods-review diagnostics before creating report-boundary work.

Writing support must preserve `.aiss` bounded `claim`, report-boundary `mida`, citation-gap `decision`, and author `decision` declarations. Any visible outline or table in the chat is a projection from those declarations, not workflow state.

## Methodology Foundation

This skill sits in the `Report` layer of the MIDA spine. It preserves the
declared `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, evidence
source, support level, uncertainty, diagnosed limits, AI-use disclosure, and
author decision point while drafting only AI-disclosed working text.

The core check is whether a proposed claim still matches the declared research object, or whether it silently turns an output into a stronger scholarly claim. `commensurability_status` and `ai4ss_check_status` must remain visible when they are available.

## Workflow Contract

- Upstream inputs: `research_model.aiss`, checked `.aiss` evidence declarations, methods-review diagnostics, data artifacts, analysis artifacts, literature source declarations, author draft, table/figure captions, or reviewer-response evidence.
- Produces: evidence inventory, bounded claim slots, section scaffold, AI-assisted working prose when requested, unsupported-claim and citation-gap checks, causal-language risk notes, TOP disclosure matrix, AI-disclosed manuscript assembly checklist, author decision points, and `.aiss` bounded `claim`, report-boundary `mida`, or `decision` declarations.
- Handoff fields: `route_id`, `target_inquiry`, `evidence_sources`, `claim_id`, `interpretation_boundary`, `diagnosed_limit`, `unsupported_claims`, `citation_gaps`, `reporting_transparency_status`, `top_disclosure_matrix`, `manuscript_assembly_status`, `replication_package_status`, `ai_contribution_disclosure`, `human_accountability_status`, `submission_policy_check_status`, `direct_submission_status`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `literature-matrix`, `research-slides-builder`, `reviewer-response`, `ask_author`, or `none`.

## Routing Boundaries

Do not use this skill for source search or bibliographic verification; use `literature-matrix`. Do not use it to decide empirical validity; use `methods-reviewer`. Use `reviewer-response` for reviewer-letter workflows, including AI-disclosed response working text.

## Workflow

```text
Step -1: Clarify the writing task
-> Identify the target section, evidence files, language, audience, and what the user wants to decide.
-> State that AI-assisted prose is working text until disclosure, accountability, policy, and direct-submission status are explicit.
-> Locate research_model.aiss and checked evidence when this is a research-factory project.

Step 0: Inventory evidence
-> Read tables, figures, captions, `.aiss` declarations, model notes, literature evidence, and design notes.
-> Separate design facts, estimates, diagnostics, literature facts, interpretations, and speculative mechanisms.

Step 1: Build scaffold
-> Use references/section-scaffolds.md for section-specific structure.
-> Use references/claim-audit.md to map claims to evidence and flag unsupported language.
-> Attach each claim slot to relevant `.aiss` concept, causal implication, bridge, claim, or check ids.

Step 2: Return author-facing materials
-> Provide evidence inventory, bounded claim slots, section structure, citation gaps, author decisions, and AI-assisted working text when requested.
-> For each paragraph slot or draft paragraph, provide purpose, evidence to use, required citation, risk note, and disclosure status.
-> Provide a reporting-transparency checklist that links registration, protocol, analysis plan, materials, data, code, and replication-package status to the sections where the researcher must disclose them.

Step 3: Audit author draft if provided
-> Check whether the user's prose overclaims, lacks citations, changes the estimand, or hides limitations.
-> Provide issue labels, revision targets, replacement working wording when useful, and author decision questions; mark replacements as AI-assisted working text.

Step 4: Record AI-use boundary when relevant
-> If the scaffold will support a manuscript, response package, or shared teaching artifact, update the project AI-use ledger according to local policy.
```

## Output Shape

For most tasks, return evidence inventory, bounded claim slots, section or paragraph scaffold, optional AI-assisted working text, unsupported-claim and citation-gap checklist, `top_disclosure_matrix`, manuscript assembly status, `ai_contribution_disclosure`, `human_accountability_status`, `submission_policy_check_status`, `direct_submission_status`, author decision points, and any `.aiss` ids touched.

For research-factory work, durable report-boundary state belongs in `research_model.aiss`; chat-visible tables or outlines are temporary projections.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when claim slots or report-boundary declarations are added or changed.
- Use `scripts/validate_ai_use_ledger.py` when local policy requires updating the AI-use ledger.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [claim-audit.md](references/claim-audit.md) | Claim strength, evidence fit, causal language, and disclosure/submission gate checks | Mapping outputs to claim slots |
| [section-scaffolds.md](references/section-scaffolds.md) | Section-specific scaffold patterns and AI-disclosed working text slots | Structuring a manuscript section |
| [author-workbench.md](references/author-workbench.md) | Author decision surface for theory, evidence slots, and claim boundaries | Preparing author review |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for claim audits, section scaffolds, and citation-gap checks | Turning a writing need into an agent task |
| [worked-example.md](references/worked-example.md) | Example scaffold with evidence boundaries | Teaching or demonstrating the skill |
