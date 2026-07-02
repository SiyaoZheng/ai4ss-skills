---
name: academic-writing-scaffold
description: >
  Academic writing support skill that does not directly write manuscript prose.
  Use for evidence maps, argument outlines, claim ledgers, section plans, table-to-claim audits,
  citation-gap checks, causal-language risk checks, paragraph skeletons, and author-facing revision
  notes for social-science papers. Triggers: "writing scaffold", "argument outline", "claim audit",
  "evidence map", "citation gaps", "table to claim", "do not write the paper", "academic writing boundary",
  "论文写作边界", "写作支架", "不要代写", "作者自己写".
---

# Academic Writing Scaffold

Support academic writing without directly writing the manuscript. The skill produces structures, checks, and evidence maps that help the researcher write their own prose.

## Scholar Workbench

This skill answers: "结果解释有没有说过头？" Its value is not writing scholarly prose; it is turning evidence into claim slots, risk labels, and author decision questions before the researcher writes.

## Methodology Foundation

This skill sits in the `Report` layer of the MIDA spine. It preserves the declared inquiry or estimand, evidence source, support level, uncertainty, diagnosed limits, and author decision point while refusing to write final manuscript prose.

The core check is whether a proposed claim still matches the declared `Model`, `Inquiry`, `Data strategy`, and `Answer strategy`, or whether it silently turns an output into a stronger scholarly claim.

When a `.aiss` model is present, claim rows must preserve the relevant model, concept, causal, or bridge ids and the model check status. A checked model element can support a claim slot; it still cannot become AI-written manuscript prose.

## Hard Boundary

Do not draft final manuscript paragraphs, introductions, literature review prose, result prose, abstracts, conclusions, polished response text, or replacement wording for insertion into a paper. Direct AI writing is outside this skill.

Allowed outputs:

- Evidence maps.
- Claim ledgers.
- Section outlines.
- Paragraph skeletons with claim slots, not finished prose.
- Table-to-claim audits.
- Citation-gap lists.
- Causal-language risk checks.
- Issue labels, revision targets, and author decision questions.

## Workflow Contract

- Upstream inputs: study design brief, `study_design_declaration.csv`, `research_model.aiss`, literature matrix, analysis run manifest, methods issue table, data audit outputs, author draft, table/figure captions, or reviewer-response evidence.
- Produces: evidence inventory, claim ledger, section outline, paragraph skeletons with slots, citation gaps, causal-language risk notes, and author decision points.
- Handoff fields: `route_id`, `target_inquiry`, `evidence_sources`, `claim_ledger`, `interpretation_boundary`, `diagnosed_limit`, `unsupported_claims`, `citation_gaps`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `ai_writing_boundary`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `literature-matrix`, `research-slides-builder`, `reviewer-response`, `ask_author`, or `none`.

## Routing Boundaries

Do not use this skill for source search or bibliographic verification; use `literature-matrix`.
Do not use it to decide empirical validity; use `methods-reviewer`.
Do not use it for final reviewer letters; use `reviewer-response` for scaffolds only.

## Workflow

```
Step -1: Clarify the writing task
-> Identify the target section, evidence files, language, audience, and what the user wants to decide.
-> State that final prose must be authored by the researcher.

Step 0: Inventory evidence
-> Read tables, figures, captions, model notes, literature matrices, and research design notes.
-> Separate design facts, estimates, diagnostics, literature facts, interpretations, and speculative mechanisms.

Step 1: Build scaffold
-> Use references/section-scaffolds.md for section-specific outlines.
-> Use references/claim-audit.md to map claims to evidence and flag unsupported language.
-> If `.aiss` model ids are available, attach each claim slot to the relevant concept, causal implication, or bridge.

Step 2: Return author-facing materials
-> Provide a claim ledger and outline.
-> For each paragraph, provide purpose, evidence to use, required citation, and risk note.
-> Do not fill in the final sentences.

Step 3: Audit author draft if provided
-> Check whether the user's prose overclaims, lacks citations, changes the estimand, or hides limitations.
-> Suggest issue labels, revision targets, and author decision questions only; do not provide replacement wording for manuscript prose.

Step 4: Record AI-use boundary when relevant
-> If the scaffold will support a manuscript, response package, or shared teaching artifact, update an AI-use ledger with `tool_model`, `task`, `inputs`, `outputs`, `human_review`, `disclosure_location`, and `confidentiality_approval_status`.
```

## Output Shape

For most tasks, return:

1. Evidence inventory.
2. Claim ledger.
3. Section or paragraph scaffold.
4. Unsupported-claim and citation-gap checklist.
5. Author decision points.

If any table is returned in Markdown, also write or request a CSV sidecar with the canonical snake_case schema before validation.

## Script Utilities

- Run `scripts/validate_claim_ledger.py <path>` to check claim-ledger columns and authorship-boundary markers.
- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` before using model-linked claims as evidence-ready slots.

## Standards

- Do not upgrade "association" to "effect" unless the design supports causal language.
- Do not smooth conflicting evidence into a single story.
- Do not invent transitions that conceal missing evidence.
- Keep mechanism claims separate from tested mechanism evidence.
- Use exact table, figure, and source paths where possible.
- Do not treat AI-generated scaffold text as author-approved prose.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [section-scaffolds.md](references/section-scaffolds.md) | Author-facing outlines for paper sections without final prose | Planning a section |
| [claim-audit.md](references/claim-audit.md) | Claim types, evidence mapping, and wording-risk checks | Auditing evidence or a user draft |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for evidence maps, claim ledgers, paragraph skeletons, and draft audits | Turning writing support into bounded agent tasks |
| [author-workbench.md](references/author-workbench.md) | Author-only workflow that separates AI-produced scaffold from human-authored prose | Keeping the academic writing boundary operational |
| [worked-example.md](references/worked-example.md) | Example result-section scaffold and claim audit without final prose | Teaching or demonstrating the skill |
