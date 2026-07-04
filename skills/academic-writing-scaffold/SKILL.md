---
name: academic-writing-scaffold
description: >
  Academic writing support skill that does not directly write manuscript prose.
  Use for evidence maps, argument outlines, bounded claim checks, citation-gap checks,
  causal-language risk checks, section planning, and author-facing revision notes for
  social-science papers. Triggers: "writing scaffold", "argument outline", "claim audit",
  "evidence map", "citation gaps", "table to claim", "do not write the paper",
  "academic writing boundary", "论文写作边界", "写作支架", "不要代写", "作者自己写".
---

# Academic Writing Scaffold

Support academic writing without directly writing the manuscript. The skill produces structures, checks, and author decision points that help the researcher write their own prose.

## Scholar Workbench

This skill answers: "作者怎样自己写得更稳？" Its value is not writing scholarly prose; it is turning evidence into bounded claim slots, risk labels, and author decision questions before the researcher writes.

## Hard Boundary

Do not draft final manuscript paragraphs, introductions, literature review prose, result prose, abstracts, conclusions, polished response text, or replacement wording for insertion into a paper. Direct AI writing is outside this skill.

Allowed outputs are evidence inventories, bounded claim slots, section-level scaffolds, table-to-claim audits, citation-gap checks, causal-language risk labels, issue labels, revision targets, and author decision questions.

## AI4SS Runtime Gate

Do not build writing scaffolds from disconnected tables or memory when the project is inside the research factory. Locate `research_model.aiss`, selected route, MIDA declarations, checked evidence artifacts, and methods-review diagnostics before creating report-boundary work.

Writing support must preserve `.aiss` bounded `claim`, report-boundary `mida`, citation-gap `decision`, and author `decision` declarations. Any visible outline or table in the chat is a projection from those declarations, not workflow state.

## Methodology Foundation

This skill sits in the `Report` layer of the MIDA spine. It preserves the declared `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, evidence source, support level, uncertainty, diagnosed limits, and author decision point while refusing to write final manuscript prose.

The core check is whether a proposed claim still matches the declared research object, or whether it silently turns an output into a stronger scholarly claim. `commensurability_status` and `ai4ss_check_status` must remain visible when they are available.

## Workflow Contract

- Upstream inputs: `research_model.aiss`, checked `.aiss` evidence declarations, methods-review diagnostics, data artifacts, analysis artifacts, literature source declarations, author draft, table/figure captions, or reviewer-response evidence.
- Produces: evidence inventory, bounded claim slots, section scaffold, unsupported-claim and citation-gap checks, causal-language risk notes, author decision points, and `.aiss` bounded `claim`, report-boundary `mida`, or `decision` declarations.
- Handoff fields: `route_id`, `target_inquiry`, `evidence_sources`, `claim_id`, `interpretation_boundary`, `diagnosed_limit`, `unsupported_claims`, `citation_gaps`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `ai_writing_boundary`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `literature-matrix`, `research-slides-builder`, `reviewer-response`, `ask_author`, or `none`.

## Routing Boundaries

Do not use this skill for source search or bibliographic verification; use `literature-matrix`. Do not use it to decide empirical validity; use `methods-reviewer`. Do not use it for final reviewer letters; use `reviewer-response` for scaffolds only.

## Workflow

```text
Step -1: Clarify the writing task
-> Identify the target section, evidence files, language, audience, and what the user wants to decide.
-> State that final prose must be authored by the researcher.
-> Locate research_model.aiss and checked evidence when this is a research-factory project.

Step 0: Inventory evidence
-> Read tables, figures, captions, `.aiss` declarations, model notes, literature evidence, and design notes.
-> Separate design facts, estimates, diagnostics, literature facts, interpretations, and speculative mechanisms.

Step 1: Build scaffold
-> Use references/section-scaffolds.md for section-specific structure.
-> Use references/claim-audit.md to map claims to evidence and flag unsupported language.
-> Attach each claim slot to relevant `.aiss` concept, causal implication, bridge, claim, or check ids.

Step 2: Return author-facing materials
-> Provide evidence inventory, bounded claim slots, section structure, citation gaps, and author decisions.
-> For each paragraph slot, provide purpose, evidence to use, required citation, and risk note.
-> Do not fill in final sentences.

Step 3: Audit author draft if provided
-> Check whether the user's prose overclaims, lacks citations, changes the estimand, or hides limitations.
-> Suggest issue labels, revision targets, and author decision questions only; do not provide replacement wording for manuscript prose.

Step 4: Record AI-use boundary when relevant
-> If the scaffold will support a manuscript, response package, or shared teaching artifact, update the project AI-use ledger according to local policy.
```

## Output Shape

For most tasks, return evidence inventory, bounded claim slots, section or paragraph scaffold, unsupported-claim and citation-gap checklist, author decision points, and any `.aiss` ids touched.

For research-factory work, durable report-boundary state belongs in `research_model.aiss`; chat-visible tables or outlines are temporary projections.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when claim slots or report-boundary declarations are added or changed.
- Use `scripts/validate_ai_use_ledger.py` when local policy requires updating the AI-use ledger.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [claim-audit.md](references/claim-audit.md) | Claim strength, evidence fit, causal language, and authorship boundary checks | Mapping outputs to claim slots |
| [section-scaffolds.md](references/section-scaffolds.md) | Section-specific scaffold patterns without final prose | Structuring an author-written section |
| [author-workbench.md](references/author-workbench.md) | Author decision surface for theory, evidence slots, and claim boundaries | Preparing author review |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for claim audits, section scaffolds, and citation-gap checks | Turning a writing need into an agent task |
| [worked-example.md](references/worked-example.md) | Example scaffold with evidence boundaries | Teaching or demonstrating the skill |
