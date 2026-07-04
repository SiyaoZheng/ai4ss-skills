---
name: research-slides-builder
description: >
  Research presentation skill for converting verified social-science evidence into bounded
  presentation plans or deck artifacts. Use for presentation structure, evidence-to-presentation mapping,
  visual claim checks, privacy checks, and source-linked figures without inventing claims.
  Triggers: "research slides", "conference deck", "presentation from results", "slide claims",
  "研究汇报", "学术汇报", "做slides", "结果展示".
---

# Research Slides Builder

Turn verified research evidence into presentation artifacts without overstating what the evidence can support.

## Scholar Workbench

This skill answers: "已验证证据怎样讲给听众？" Its value is not making a prettier deck; it is making each slide claim source-linked, scoped, and bounded.

## Core Rule

Only present claims that can be traced to checked evidence. Do not invent results, simplify away uncertainty, or turn slide rhetoric into manuscript claims.

## AI4SS Runtime Gate

Do not build research slides from disconnected tables, figures, or memory when the project is inside the research factory. Locate `research_model.aiss`, selected route, MIDA declarations, evidence artifacts, methods diagnostics, and report-boundary declarations before planning slides.

Slide claims and deck artifacts must be represented or referenced by `.aiss` presentation `artifact`, bounded `claim`, source-link, privacy `check`, or author `decision` declarations. A deck file can be an output artifact, but it is not the workflow state.

## Methodology Foundation

This skill sits in the `Report` layer of the MIDA spine. It preserves target inquiry, source artifact, sample or scope, uncertainty, privacy status, interpretation boundary, and author decision points.

When a slide references a concept, causal implication, bridge, estimate, figure, or literature fact, it must preserve relevant `.aiss` ids and `ai4ss_check_status`.

## Workflow Contract

- Upstream inputs: `research_model.aiss`, checked `.aiss` claims, tables, figures, data artifacts, literature evidence, methods-review findings, author draft notes, venue/audience constraints, or existing deck files.
- Produces: slide structure, source-linked claim slots, visual object instructions, privacy checks, reporting-transparency reminders, deck artifacts when requested, and `.aiss` presentation `artifact`, bounded `claim`, source-link, `check`, or `decision` declarations.
- Handoff fields: `route_id`, `target_inquiry`, `claim_id`, `source_artifact`, `sample_or_scope`, `uncertainty_or_caveat`, `privacy_status`, `reporting_transparency_status`, `visual_object`, `interpretation_boundary`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `academic-writing-scaffold`, `reviewer-response`, `ask_author`, or `none`.

## Routing Boundaries

Use this skill for source-linked presentation planning and deck artifact creation. Use `methods-reviewer` when evidence validity is uncertain. Use `academic-writing-scaffold` for paper-oriented writing support and reporting disclosures. Do not use this skill to create no-AI/direct-submission scholarly claims, hide data/code limits, or fabricate visual evidence.

## Workflow

```text
Step -1: Confirm scope
-> Identify audience, venue, time limit, deck format, confidentiality limits, and source files.
-> Locate research_model.aiss and checked evidence when this is a research-factory project.

Step 0: Evidence map
-> Map each proposed slide claim to a checked source artifact, sample/scope note, uncertainty, and interpretation boundary.
-> Block or route back when a claim lacks evidence.

Step 1: Plan deck
-> Build a slide sequence with one claim slot per slide.
-> Pair each claim slot with visual material, source link, and caveat.
-> Keep author decisions visible for sensitive or speculative claims.

Step 2: Produce artifact if requested
-> Create or edit the deck file.
-> Verify that figures, captions, labels, and source notes match the underlying evidence.

Step 3: Hand off
-> Return deck path or slide plan, touched `.aiss` ids, privacy status, and next route.
```

## Default Outputs

- Updated `research_model.aiss` or deterministic `.aiss` fragment with presentation artifacts, bounded slide claims, privacy checks, and author decisions.
- Slide sequence or deck artifact when requested.
- Source-linked claim list, visual object list, and caveat list in the chat response.
- Blocked handoff with `next_skill_route` when evidence or privacy status is insufficient.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when presentation declarations are added or changed.
- Use project-specific render or export commands to verify deck artifacts when a deck file is produced.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [visual-rules.md](references/visual-rules.md) | Evidence-to-slide rules, uncertainty display, privacy checks, and source-link standards | Planning or auditing slides |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for slide planning and claim checks | Turning evidence into a presentation task |
| [worked-example.md](references/worked-example.md) | Example bounded slide sequence | Teaching or demonstrating the skill |
