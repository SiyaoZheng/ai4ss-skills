---
name: literature-matrix
description: >
  Source-grounded literature discovery and evidence-mapping skill for social-science research.
  Use when searching, screening, extracting, verifying, or organizing literature evidence,
  including source coverage, primary-source checks, theory mapping, citation-gap analysis,
  and `.aiss` evidence declarations. Triggers: "literature matrix", "source verification",
  "evidence map", "search papers", "screen literature", "theory synthesis", "citation gaps",
  "文献矩阵", "文献检索", "证据整理", "理论映射".
---

# Literature Matrix

Build literature evidence as source-grounded declarations, not as memory or narrative synthesis. The default result is a verified evidence chain that can update or constrain the governing `.aiss` research object.

## Scholar Workbench

This skill answers: "文献证据是不是一手来源？" Its value is not producing a literature review; it is making source status, screening rules, extraction uncertainty, rival explanations, and theory handoffs inspectable before claims are written.

## Core Rule

Use primary or locally verified sources where possible. Never turn unverified search results or model memory into `.aiss` concepts, causal links, bridges, or reportable claims.

## AI4SS Runtime Gate

Do not run this skill as a generic bibliography helper inside the research factory. Before producing evidence declarations or downstream handoffs, locate the governing `research_model.aiss` with a selected route and MIDA declarations, or create provisional route declarations through `research-starter` first.

Literature evidence that affects the model must enter `.aiss` directly or through deterministic `.aiss` fragments. Candidate notes, source exports, PDFs, and search logs can exist as evidence artifacts, but they are not workflow state and cannot substitute for `.aiss` declarations.

## Runtime Failure Guardrails

- Use live web search, DOI pages, journal pages, working-paper repositories, author pages, Zotero exports, local PDFs, or user-supplied source files when current coverage or source truth matters.
- Preserve exact source locators: URL, DOI, repository page, PDF path, page, table, figure, or quote locator.
- Keep source status explicit: verified primary, verified local, secondary, unverified, duplicate, excluded, or needs review.
- If a source updates the research model, bind the update to `.aiss` `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, or `decision` declarations.

## Methodology Foundation

This skill realizes the literature side of the `Data strategy` and `Diagnose` parts of the MIDA spine. Literature is evidence data: it needs source scope, screening rules, extraction fields, verification status, and claim-support limits.

The skill can propose model edits as source-grounded `.aiss` declarations, author `decision` declarations, or AI-disclosed literature-review working text. It does not mark theoretical novelty or direct-submission status ready without source support, disclosure, and human-accountability gates.

When verified literature changes a concept, causal implication, bridge, mechanism, rival explanation, or scope condition, the model change must preserve `ai4ss_model_path`, source spans, and author decision status.

## Workflow Contract

- Upstream inputs: `research_model.aiss`, route declarations, MIDA declarations, seed papers, Zotero/PDF sets, bibliographies, search questions, source-verification requests, or author-supplied scope rules.
- Produces: verified source locators, search-strategy and source-status transparency evidence, screening and extraction evidence, evidence clusters, open source questions, and `.aiss` `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, or `decision` declarations.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `source_scope`, `search_strategy_status`, `source_status`, `paper_id`, `span_id`, `claim_id`, `concept_id`, `causal_id`, `bridge_id`, `evidence_strength`, `materials_transparency_status`, `author_decisions`, `ai4ss_model_path`, `ai4ss_check_status`, `validation_commands`, `next_skill_route`.
- Downstream routes: `study-design-builder`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response`, or `ask_author`.

## Routing Boundaries

Use this skill for literature search, screening, extraction, verification, source-status diagnosis, and `.aiss` evidence declarations. Do not use it to write literature-review prose, decide final theoretical contribution, certify empirical identification, or create a design without routing through `study-design-builder`.

## Workflow

```text
Step -1: Scope
-> Read AGENTS.md, research_model.aiss, route/MIDA declarations, and user-supplied source rules.
-> Identify what evidence question the literature must answer.
-> If no route exists, create or route to `.aiss` route declarations before production extraction.

Step 0: Search plan
-> Declare source scope, search strata, exact queries or seed sources, source types, and next verification actions.
-> Treat query strings, databases, inclusion/exclusion rules, access dates, and source-status labels as transparency materials that may need to be reported or replicated.
-> Use live search when coverage or publication status may have changed.

Step 1: Gather and verify
-> Open primary pages or local source files.
-> Deduplicate similar titles by author, title, venue, and year.
-> Mark uncertain or secondary sources explicitly.

Step 2: Extract
-> Extract design facts, sample, unit, period, outcome, exposure, identification strategy, result direction, limitations, and source locators.
-> Separate verified facts from author judgment and model proposals.

Step 3: Update `.aiss`
-> Add or revise source-grounded declarations only when the source is verified enough for the claimed use.
-> Encode rivals, scope limits, weak mechanisms, and unresolved novelty as `.aiss` `check` or `decision` declarations.

Step 4: Hand off
-> Return evidence clusters, open source questions, touched `.aiss` ids, and validation commands.
-> If literature-review working prose is requested, mark it as AI-assisted,
source-linked, and not direct-submission ready unless the disclosure gate passes.
```

## Default Outputs

- Updated `research_model.aiss` or deterministic `.aiss` fragment with source-grounded literature declarations.
- Source locator inventory and extraction notes referenced from `.aiss` when useful.
- Evidence clusters and open author/source questions in the chat response.
- Validation command output for `scripts/validate_ai4ss_model.py`.
- Blocked handoff with `next_skill_route` when source status, route declarations, or MIDA declarations are insufficient.

## Script Utilities

- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` after adding or changing literature declarations.
- Use `dsl/scripts/compile_evidence.py` only when converting deterministic source evidence into `.aiss`; do not use it to create a parallel handoff format.
- Use source-specific tooling such as DOI pages, Zotero exports, PDF extraction, or live web search to verify source truth before model updates.

## Screening Standards

- Prefer primary sources: journal pages, working-paper repositories, official author pages, DOI records, arXiv/SSRN/NBER/IZA/CEPR pages when appropriate.
- Distinguish peer-reviewed articles, working papers, preprints, book chapters, datasets, blog posts, and secondary summaries.
- Preserve publication year and access date for web sources.
- Never merge two similarly titled papers unless author, title, venue, and year match.
- For social-science empirical papers, extract sample, unit, period, outcome, treatment/exposure, identification strategy, fixed effects, standard errors, and validation checks when available.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [search-and-screen.md](references/search-and-screen.md) | Query design, source hierarchy, screening, and verification rules | Starting a search or refreshing coverage |
| [candidate-discovery.md](references/candidate-discovery.md) | Candidate-source discovery, seed audit, snowballing, and source-status vocabulary | Starting an open-ended literature base or when source coverage matters |
| [matrix-schema.md](references/matrix-schema.md) | Legacy extraction vocabulary; translate useful fields into `.aiss` declarations | Maintaining older projects that already have extraction tables |
| [theory-synthesis.md](references/theory-synthesis.md) | Theory-mapping vocabulary for concepts, mechanisms, rivals, scope, and author decisions | Turning verified sources into model candidates |
| [evidence-compile.md](references/evidence-compile.md) | Deterministic evidence-to-`.aiss` compilation contract | Turning verified source rows into model fragments |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for search, screening, extraction, deduplication, and synthesis outlines | Turning a literature need into an agent task |
| [source-verification.md](references/source-verification.md) | DOI, PDF, Zotero, publication-status, and claim-verification procedures | Checking whether sources and extracted claims are real |
| [worked-example.md](references/worked-example.md) | Place-based policy and innovation evidence example | Teaching or demonstrating the skill |
