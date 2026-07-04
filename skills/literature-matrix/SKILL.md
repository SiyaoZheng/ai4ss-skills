---
name: literature-matrix
description: >
  Source-grounded literature discovery and evidence-matrix skill for social-science research.
  Use when searching, screening, extracting, or updating literature tables from Google Scholar,
  Crossref, Semantic Scholar, journal pages, working-paper sites, Zotero libraries, PDFs, or user
  supplied bibliographies. Triggers: "literature matrix", "文献矩阵", "literature review search",
  "Zotero", "DOI", "screen papers", "extract identification strategy", "do not write prose yet",
  "source-grounded literature", "找文献", "文献综述前的检索", "文献检索", "引用核查", "建立文献矩阵".
---

# Literature Matrix

Build a verifiable literature base before the researcher writes review prose. The skill's default deliverable is not only a matrix; it is a discovery-to-evidence package with candidate sources, source-status decisions, extraction rows, evidence clusters, and open judgment calls.

## Scholar Workbench

This skill answers: "文献证据是不是一手来源？" Its value is not summarizing papers faster; it is tying each literature fact to a verified source, locator, version, and synthesis eligibility decision.

## Core Rule

Do not invent citations, DOI, publication status, consensus claims, or findings. If a source cannot be verified, mark it as unverified and keep it out of the main evidence table.

## Runtime and Validation Guardrails

- Use safe file discovery (`Path.glob`, `rg --files`, or quoted patterns) when inventorying matrices, theory sidecars, PDFs, and reports; unquoted brace globs in zsh are a known failure mode.
- Run the relevant matrix, discovery, theory-synthesis, or evidence-compile validator before finalizing a handoff or webpage.
- If a validator fails, do not summarize the matrix as complete. Fix the source IDs, required fields, verification labels, or import path and rerun.
- When running an installed validator outside this repo, set `AI4SS_SKILLS_ROOT` to the `ai4ss-skills` source checkout if factory-contract imports are unavailable.

## Search Quality Rule

Do not stop at schema design when the user needs a literature base. Unless the user already supplies a closed PDF/Zotero set, produce a candidate discovery ledger first: search strata, exact queries, seed sources, backward/forward chasing targets, source-status labels, and next verification actions. A literature matrix without a candidate ledger is incomplete for open-ended search tasks.

## Methodology Foundation

This skill treats literature work as an evidence-focused `Data strategy` within the MIDA spine, with a `Diagnose` gate for source status and synthesis eligibility.

Before synthesis, it must declare source scope, search strata, screening rule, extraction fields, source-status labels, and unresolved verification actions. It does not replace discipline-expert reading or author-owned interpretation.

When a `.aiss` model is present, verified source rows should preserve the relevant `model_id`, `concept_id`, `causal_id`, or `bridge_id`. Literature evidence can support or challenge model elements, but it must not silently rewrite them.

When literature evidence is used to create or revise model elements, compile the structured evidence table through the upstream `ai4ss-skills` `compile_evidence.py` semantics and save the deterministic `.aiss` output. Matrix rows should record `evidence_table_path`, `compiled_ai4ss_path`, and `evidence_compile_status` so the source-to-model step can be rerun.

When verified literature rows are used for theory mapping, create `literature_theory_synthesis.csv` as a handoff sidecar before any `.aiss` model update. The synthesis sidecar may propose concepts, mechanisms, boundary conditions, rival explanations, observable implications, measurement links, or scope conditions, but it must preserve source rows and author decisions. For a full theory workbench, use that sidecar as the entrypoint and add `theory_rival_map.csv`, `theory_scope_map.csv`, and structured `theory_evidence.md` for the existing `compile_evidence.py` path.

## Workflow Contract

- Upstream inputs: starter packet, study design brief, `study_design_declaration.csv`, `research_model.aiss`, route cards, seed papers, Zotero/PDF sets, bibliographies, search questions, or source-verification requests.
- Produces: `literature_candidate_discovery.csv`, `literature_matrix.csv`, optional `literature_theory_synthesis.csv`, optional `theory_rival_map.csv`, optional `theory_scope_map.csv`, screening logs, evidence clusters, optional structured evidence markdown, compiled `.aiss` fragments or models, and open source questions.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `source_scope`, `verified_sources`, `excluded_sources`, `evidence_clusters`, `literature_gaps`, `claim_boundaries`, `synthesis_id`, `synthesis_type`, `proposed_aiss_object`, `rival_id`, `scope_id`, `author_decision_needed`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `evidence_table_path`, `compiled_ai4ss_path`, `evidence_compile_status`, `next_skill_route`.
- Downstream routes: `study-design-builder`, `methods-reviewer`, `academic-writing-scaffold`, `reviewer-response`, `research-slides-builder`, or `ask_author`.

## Routing Boundaries

Use this skill for search, screening, source verification, extraction, and evidence clustering. If source findings change the route or design, hand the decision back to `study-design-builder`. Do not use it to write final literature-review prose; hand verified matrices to `academic-writing-scaffold` for scaffold-only writing support. Do not use it to judge empirical validity beyond what the source visibly reports; hand design doubts to `methods-reviewer`.

## Workflow

```
Step -1: Define scope
-> Research question, population, intervention/exposure, outcomes, methods, years, disciplines, languages.
-> Decide whether the task is search, screening, extraction, update, or synthesis.

Step 0: Discover candidate sources
-> For open-ended topics, follow references/candidate-discovery.md before extraction.
-> Build search strata and candidate sources across primary source pages, working-paper repositories, DOI records, citation indexes, local PDFs, and snowballing targets.
-> Keep a candidate ledger with source status and next verification action.

Step 1: Gather and verify sources
-> Use user-supplied PDFs, Zotero exports, local ref/ notes, and live search when current coverage matters.
-> Keep exact URLs, DOI, working-paper pages, or PDF paths.

Step 2: Screen
-> Apply inclusion/exclusion rules.
-> Keep rejected-but-relevant items in a separate sheet with reasons.

Step 3: Extract
-> Fill the matrix schema before any narrative synthesis.
-> Extract methods as research design facts, not vague topic labels.
-> If a `.aiss` model exists, bind each source row to the relevant concept, causal implication, bridge, or `not_applicable:<reason>`.
-> If the source row creates or revises model elements, create structured evidence markdown and compile it into `.aiss` with the local wrapper around unified v0.4 `compile_evidence.py`.

Step 4: Verify
-> Spot-check bibliographic metadata, identification strategy, data source, and result direction against the source.
-> Mark uncertain cells explicitly.
-> Validate deterministic evidence compilation before handing compiled model fragments downstream.

Step 5: Hand off
-> Output a matrix plus remaining human judgment questions.
-> If verified rows support theory mapping, output literature_theory_synthesis.csv with source_paper_ids, rival_or_boundary, observable_implication, proposed_aiss_object, evidence_strength, and author_decision_needed.
-> Only verified_primary or verified_local source rows may support proposed_aiss_object. Unverified theory candidates remain open questions.
-> For theory workbench use, split mechanisms into actor/action/mediating_condition/outcome_link, add rival and scope sidecars, and keep novelty or mechanism-strength choices as author decisions.
-> If synthesis is requested, provide a synthesis outline and evidence clusters, not final manuscript prose.
-> Update an AI-use ledger when literature extraction or synthesis scaffolding supports a manuscript or shared artifact.
```

## Default Outputs

- `docs/literature_matrix.csv` as the validator-ready sidecar, with optional `.xlsx` mirror.
- `docs/literature_candidate_discovery.csv` for open-ended search tasks.
- `docs/literature_screening_log.md`.
- `docs/literature_open_questions.md`.
- Optional `docs/literature_theory_synthesis.csv` when verified literature rows are grouped for theory mapping.
- Optional `docs/theory_rival_map.csv`, `docs/theory_scope_map.csv`, and `docs/theory_evidence.md` for reusable theory workbench handoff.
- Optional `docs/literature_evidence.md` and compiled `.aiss` output when source rows are turned into model fragments.
- Optional `docs/search_queries.md` when live search is used.

## Script Utilities

- Run `scripts/validate_literature_matrix.py <path>` to check required matrix columns, verification levels, synthesis eligibility, and row shape.
- Run `scripts/validate_literature_discovery.py <path>` to check candidate-discovery columns, source-status labels, search strata, and next-action fields.
- Run `scripts/validate_literature_theory_synthesis.py <path>` to check theory-synthesis columns, source-row grounding, evidence strength, model handoff eligibility, and author decisions.
- Run `scripts/validate_theory_workbench.py <workbench-dir>` when theory synthesis, rival map, scope map, and structured evidence markdown are handed off together.
- Run `scripts/validate_literature_evidence_compile.py <literature_matrix.csv>` to recompile evidence markdown and compare it with saved `.aiss` outputs.
- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when literature rows claim to support model elements.

## Screening Standards

- Prefer primary sources: journal pages, working-paper repositories, official author pages, DOI records, arXiv/SSRN/NBER/IZA/CEPR pages when appropriate.
- Distinguish peer-reviewed articles, working papers, preprints, book chapters, datasets, blog posts, and secondary summaries.
- Preserve publication year and access date for web sources.
- Never merge two similarly titled papers unless author, title, venue, and year match.
- For social-science empirical papers, extract sample, unit, period, outcome, treatment/exposure, identification strategy, fixed effects, standard errors, and validation checks when available.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [search-and-screen.md](references/search-and-screen.md) | Query design, source hierarchy, screening log, and verification rules | Starting a search or refreshing coverage |
| [candidate-discovery.md](references/candidate-discovery.md) | Candidate-source discovery, seed audit, snowballing, and source-status ledger rules | Starting an open-ended literature base or when source coverage matters |
| [matrix-schema.md](references/matrix-schema.md) | Recommended literature matrix columns and extraction rules | Creating or reviewing the matrix |
| [theory-synthesis.md](references/theory-synthesis.md) | Literature-to-theory synthesis sidecar and handoff rules | Turning verified rows into theory-mapping candidates |
| [evidence-compile.md](references/evidence-compile.md) | Deterministic literature evidence markdown to `.aiss` compilation contract | Turning verified source rows into model fragments |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for search, screening, extraction, deduplication, and synthesis outlines | Turning a literature need into an agent task |
| [source-verification.md](references/source-verification.md) | DOI, PDF, Zotero, publication-status, and claim-verification procedures | Checking whether sources and extracted claims are real |
| [worked-example.md](references/worked-example.md) | Place-based policy and innovation matrix example with evidence clusters and open questions | Teaching or demonstrating the skill |
