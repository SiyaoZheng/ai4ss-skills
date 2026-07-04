---
name: research-slides-builder
description: >
  Research presentation skill for converting verified social-science results into slide maps,
  source maps, layout plans, reveal.js decks, PPT outlines, teaching demos, and visual result narratives. Use when
  making or auditing slides from existing tables, figures, logs, literature matrices, or author
  notes. It may organize and visualize verified evidence but must not invent findings, write
  manuscript prose, or produce final academic talk prose without author-supplied wording. Triggers: "research slides", "conference presentation", "reveal.js research deck", "PPT from results",
  "slides from results", "research result slides", "学术汇报", "研究结果汇报", "证据型幻灯片", "result narrative",
  "one claim per slide", "presentation audit".
---

# Research Slides Builder

Turn verified research artifacts into presentation materials. The deck should help an audience inspect the argument, evidence, and limits of the study.

## Scholar Workbench

This skill supports the same claim-discipline question in presentation form: "结果解释有没有说过头？" Its value is not slide polish; it is keeping every slide claim tied to a source artifact, visual object, and stated boundary.

## Core Rule

Slides may repackage verified evidence; they may not create new academic claims. If a conclusion is not in the tables, figures, literature matrix, or author notes, mark it as a gap.

For academic talks, conference decks, seminar slides, and manuscript-derived presentations, produce slide maps, evidence/source maps, layout plans, and author-fillable title/body slots. Do not write final academic presentation prose unless the source text is explicitly authored and supplied by the researcher. Non-academic teaching/demo decks may use explanatory slide text, but still must not invent research findings.

## Methodology Foundation

This skill sits in the `Report` layer of the MIDA spine. It turns declared evidence into public-facing slide claims while preserving inquiry or estimand, sample or scope, source artifact, uncertainty or caveat, privacy status, and interpretation boundary.

Its methodology status is partial: it supports transparent communication, but it does not itself diagnose empirical validity or supply a full visual-evidence methodology.

When a `.aiss` model is present, slide maps should preserve model identifiers for any claim slot that depends on a declared concept, causal implication, or empirical bridge.

## Workflow Contract

- Upstream inputs: verified tables, figures, `research_model.aiss`, analysis run manifest, methods issue table, literature matrix, data audit outputs, author notes, venue, audience, and time limit.
- Produces: slide map, source map, deck outline or edited deck, visual audit notes, privacy review, and evidence gaps.
- Handoff fields: `route_id`, `slide_id`, `claim_slot`, `source_artifact`, `sample_or_scope`, `uncertainty_or_caveat`, `evidence_status`, `visual_object`, `interpretation_boundary`, `privacy_status`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `academic-writing-scaffold`, `reviewer-response`, `ask_author`, or `none`.

## Routing Boundaries

Use this skill for deck structure, readability, slide-map validation, and privacy review. Do not use it for ordinary deck editing without research evidence. Do not use it to validate empirical claims; delegate result-claim and identification checks to `methods-reviewer`. Do not use it to write manuscript prose, final academic talk prose, or replacement wording for author-authored research slides.

## Workflow

```
Step -1: Inventory inputs
-> Tables, figures, model logs, data audit outputs, literature matrix, author notes, venue, audience, time limit.

Step 0: Build slide map
-> One slide = one claim or one task.
-> Map every claim to a source artifact.
-> Identify which slides are evidence, method, context, limitation, or discussion.

Step 1: Choose format
-> For reveal.js/HTML, inspect existing design system before editing.
-> For PPT outlines, specify author-fillable title slot, evidence object, visual layout, and speaker intent.
-> For teaching decks, show process and checkpoints, not only final results.

Step 2: Build or audit
-> Use references/deck-structure.md for narrative order.
-> Use references/visual-rules.md for figure/table treatment and layout checks.
-> Keep dense research content readable; avoid marketing-style claims.

Step 3: Verify
-> Open or inspect the final artifact when possible.
-> Check for unsupported claims, broken paths/assets, overflow, inconsistent terminology, and privacy leaks.
-> Update an AI-use ledger when the deck is shared outside the classroom or draws on confidential materials.
```

## Default Outputs

- Slide map with claim-source links.
- Deck outline, slide-map CSV, or edited teaching/demo slide file. For academic research decks, use author-fillable title/body slots unless author text is supplied.
- Evidence-gap list.
- Visual and privacy audit checklist.

For any slide map shown as Markdown, keep a CSV sidecar for `scripts/validate_slide_map.py`.

## Script Utilities

- Run `scripts/validate_slide_map.py <path>` to check slide-map columns and source-artifact coverage.

## Standards

- Use source labels or notes where the audience needs to verify a claim.
- Preserve estimand, sample, and uncertainty when reporting results.
- Keep methods slides specific: sample, variables, fixed effects, clustering, diagnostics.
- Use large visuals for tables and figures; do not paste unreadable regression tables.
- Do not include author personal info, contact details, or affiliations unless explicitly requested.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [deck-structure.md](references/deck-structure.md) | Research talk narrative patterns and slide map schema | Planning or reorganizing a deck |
| [visual-rules.md](references/visual-rules.md) | Rules for converting tables/figures into readable slides and auditing output | Building or reviewing slides |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for slide maps, result-deck conversion, reveal.js editing, and deck audits | Turning presentation needs into agent tasks |
| [revealjs-patterns.md](references/revealjs-patterns.md) | Single-file reveal.js structure, section discipline, CSS constraints, and local preview checks | Editing HTML slide artifacts |
| [worked-example.md](references/worked-example.md) | Example DID result deck map with slide claims, evidence paths, and audit notes | Teaching or demonstrating the skill |
