# AGENTS.md

This repository is the development home for AI4SS skills.

## Skill Layout

- All installable skills live as directory-format skills under
  `skills/<skill-name>/`.
- `skills/` is the only source tree. Do not add new top-level `*.skill`
  archives or sibling `*.skill/` directories.
- `.codex/skills` and `.agents/skills` should remain symlinks to `../skills`;
  edit the `skills/` source, not a duplicate copy.
- The research-factory skillpack uses `.aiss` as the local research-model
  extension. Upstream `aiss_*` names are script names only.

## Research Factory Spine

Maintain the research-factory skills as one workflow:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
observed public-source acquisition -> observed-data sample construction/check ->
literature evidence gates -> .aiss analysis readiness -> .aiss analysis artifacts ->
transparency package -> bounded claim handoff -> AI-disclosed manuscript package
```

The methodology spine is:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

`.aiss` is the research-factory state-machine engine. Use
`python3 dsl/scripts/aiss.py state <research_model.aiss>` to project the current
state and `python3 dsl/scripts/aiss.py transition <research_model.aiss> --event
<json>` to preview or append event-sourced runtime facts. `route`, `mida`, and
`decision` declarations remain the durable semantic research state; `event`
declarations record starts, completions, failures, heartbeat observations, and
watchdog recovery facts. `goal-cli` remains the external watchdog/timer/lock
owner and must not be modified from this repository.

## Skill Routing Table

This table is the normative skill router for full-auto harness work. Each row
must be callable without blocking for human judgment. Each skill emits or
preserves `next_skill_route`; if a route fails, the skill chooses the strongest
automatic repair or redesign route.

| Skill | Use when | Required input | Required output / next route |
|---|---|---|---|
| `research-starter` | A rough topic, one-sentence idea, source pile, or no selected route exists. | User idea or materials; optional `research_model.aiss`. | Candidate `.aiss` routes, one automatically selected route, assumptions, `next_skill_route` to `study-design-builder` or source/design repair. |
| `study-design-builder` | A selected route needs an executable design, MIDA declarations, estimand/quantity, variables, or analysis plan. | Selected route in `research_model.aiss` or starter output. | Seven MIDA declarations, design decisions, analysis/source needs, `next_skill_route` to `public-data-sources`, `literature-matrix`, `research-analysis-runner`, `methods-reviewer`, or `did-expert`. |
| `public-data-sources` | A design needs real observed public or authorized data, source verification, access classification, request template, or live data acquisition. | Selected route, MIDA data strategy, target unit/period/variables. | Ranked real observed source routes, chosen source, access status, source artifact/request template/provenance, `next_skill_route` to `research-data-builder` or automatic redesign. |
| `literature-matrix` | Theory, citations, source-backed claims, literature evidence, rival mechanisms, or source-status checks are needed. | Design or claim needs; seed papers/search terms; optional `.aiss`. | Verified source/span/claim/relation declarations and evidence synthesis, `next_skill_route` to design, methods, writing, or source/data repair. |
| `research-data-builder` | Acquired real observed source artifacts must become an auditable analysis sample, variables, linkage, row provenance, or data checks. | Source artifacts/request outputs, data strategy, `research_model.aiss`. | Processed data, row/source provenance, sample-flow and data checks, `.aiss` source/artifact/empirical declarations, `next_skill_route` to analysis or repair. |
| `research-analysis-runner` | Analysis-ready observed data and a design need scripts, tables, figures, model outputs, logs, or first-pass results. | Processed data, design, analysis plan, scripts or required variables. | Rerunnable scripts, outputs, logs, readiness/artifact/claim declarations, `next_skill_route` to `methods-reviewer`, writing, slides, or repair. |
| `did-expert` | DID, event study, staggered treatment, panel causal inference, synthetic-control-family estimator choice, or parallel-trends diagnostics are central. | Panel data, treatment timing, outcome/covariates, design or analysis outputs. | Estimator choice, diagnostics, corrected code or bounded identification language, `next_skill_route` to analysis, methods review, or design/source repair. |
| `methods-reviewer` | Identification, inference, robustness, reproducibility, result-claim fit, overclaiming, or method risk must be audited. | `.aiss`, scripts, logs, tables, figures, data artifacts, draft claims. | Findings, checks, automatic repair decisions, bounded claim support, `next_skill_route` to source, data, analysis, design, writing, slides, response, or DID specialist. |
| `analysis-explainer` | Statistical outputs need social-science interpretation, result narration, effect-size explanation, limitations, or reader-facing explanation. | Tables, model outputs, diagnostics, design context. | Detailed explanation tied to outputs and limits, `next_skill_route` to writing, methods review, tables, or analysis repair. |
| `latex-tables` | Regression/descriptive/model outputs need publication-ready LaTeX tables. | Model objects, CSVs, regression outputs, table specs. | LaTeX table files and notes, `next_skill_route` to writing, methods review, or analysis repair. |
| `top-journal-figures` | Verified empirical outputs need AER/QJE/JPE/APSR-grade paper figures, figure notes, ggplot2 code, vector exports, helper-tool triage, forced style consistency, or visual-integrity checks. | `.aiss`, R scripts, model outputs, figure data, source artifacts, target journal constraints; optional outputs from `fixest`, `did`, `marginaleffects`, `modelsummary`, `cregg`, `binsreg`, `rdrobust`, `sf`, or other R helpers. | R/ggplot2 plotting code, shared style profile, vector-first figures under `output/figures/`, captions/source notes, helper-tool transparency, style-consistency checks, visual-integrity checks, `next_skill_route` to methods review, writing, slides, or analysis/data repair. |
| `manuscript-reviewer` | A draft, PDF, title/abstract/introduction, or full manuscript needs stateless AutoChecklist TDD review, fail-first routing, or reader-test separation. | Explicit manuscript file, fixed checklist/version, optional `.aiss`, and optional reader evidence. | Context-sealed review snapshot with manifest hashes, PASS/FAIL/REQUIRES_READER items, fail-first repair route, and `next_skill_route` to design, source/data, analysis, methods, literature, tables, figures, writing, response, or none. |
| `academic-writing-scaffold` | Evidence-ready material needs manuscript outline, bounded claims, section drafting, citation-gap checks, disclosure, or `paper/full_draft.pdf` assembly. | Checked evidence, claims, methods findings, tables/figures, literature declarations. | AI-disclosed manuscript working text/source/PDF, claim boundaries, TOP/disclosure status, `next_skill_route` to methods, literature, slides, response, or none. |
| `research-slides-builder` | Verified research outputs need a presentation or teaching deck. | Bounded claims, figures/tables, source artifacts, privacy status. | Slides/deck source with source links and caveats, `next_skill_route` to writing, methods, or none. |
| `reviewer-response` | Peer-review comments require response planning, revision routing, evidence action, or AI-disclosed response text. | Reviewer comments, manuscript locations, `.aiss`, evidence/actions. | Reviewer-response decisions, revision state, response working text, `next_skill_route` to methods, analysis, source/data, literature, writing, or none. |
| `codebook-parse` | DDI/survey metadata, codebooks, variable labels, missing codes, or raw survey schema must become a machine-readable contract. | DDI/codebook/raw metadata files. | Parsed metadata and variable schema, `next_skill_route` to `cleaning-contract`. |
| `cleaning-contract` | Survey metadata and researcher decisions must become deterministic cleaning rules before execution. | Parsed metadata, raw data preview, cleaning decisions. | Explicit cleaning contract and provenance update, `next_skill_route` to `cleaning-execute`. |
| `cleaning-execute` | A declared survey-cleaning contract must be implemented and verified. | Raw data, metadata, cleaning contract. | R/Python cleaning script, cleaned data, execution audit, `next_skill_route` to analysis or methods review. |
| `codex` | Coding work should be delegated to a Codex CLI subagent/runtime. | Bounded coding task, repo path, constraints. | Subagent result, patch or report, `next_skill_route` to validation or summary. |
| `r-performance` | R code is slow, memory-heavy, vectorization-sensitive, or needs profiling/optimization without changing results. | R script/package/data-size context and expected unchanged outputs. | Profiling findings, optimized R code, equivalence checks, `next_skill_route` to analysis runner or methods review. |
| `sjtu-hpc` | Work needs SJTU HPC, Slurm, module, storage, job script, or remote execution guidance. | Job requirements, scripts, data path, cluster constraints. | Job script/commands/troubleshooting result, `next_skill_route` to analysis runner or none. |

Hard routing rules:
- Data are acquired, not produced. Empirical work must route through
  `public-data-sources` before `research-data-builder` unless a verified real
  observed source artifact with provenance already exists.
- For publication-facing social-science figures, the only final plotting
  carrier is R/ggplot2. Python, Stata, JavaScript, dashboards, screenshots, or
  interactive widgets may support diagnosis or exploration, but final paper
  figures must be generated by reproducible ggplot2 code and exported from R.
  R helper packages may estimate, tidy, compose, label, check, or export, but
  final manuscript figures must remain named ggplot2 objects with explicit
  `ggsave()` calls.
- Paper figures in the same manuscript must share one explicit ggplot2 style
  profile. The profile must cover theme, typography, dimensions, aspect ratios,
  margins, axes, point/line/interval geoms, color and non-color encodings,
  legends, facets, annotations, caption/source-note conventions, export device,
  and filename pattern. Prefer a shared `scripts/figure_style.R` or existing
  project house-style file; record any substantive exceptions.
- Synthetic, simulated, hypothetical, illustrative, generated, DGP-created,
  random-draw, benchmark-calibrated, or literature-parameter-imputed empirical
  data are invalid. Switch source, unit, geography, period, measure, or design
  route automatically instead.
- Harnesses must load an `AGENTS.md` in their sandbox. That file must include a
  skill route table for the skills available to the runtime.
- `inspect-agent-eval` is a meta-evaluation maintenance skill. It is not part
  of the automatic research-production harness route table.

The only manuscript-facing AI boundary in this skillpack is disclosure and
submission gating: skills may help draft, revise, audit, and assemble working
manuscript or reviewer-response text, but they must not present any output as
submission-ready or as having no AI involvement unless AI contribution
disclosure, human accountability, and outlet-policy checks are explicit.
Skills should create inspectable `.aiss` research objects, diagnostics,
evidence artifacts, transparency status, replication-package status, and
decision points. CSV files and derived Markdown notes are not workflow state.

## Validation

Run these checks after changing the research-factory skillpack:

```bash
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_research_workspace_contract.py
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss
python3 scripts/run_factory_level_eval.py --clean
python3 scripts/run_skill_handoff_audit_fixtures.py
```

Run these checks after changing plugin wrappers or plugin-bundled hooks:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/test_ai4ss_plugin_hooks.py
python3 scripts/validate_claude_plugin.py
```

For live agent-runtime harness evaluation, run these separately because they
start model-backed CLI agents. The default uses Inspect AI plus `inspect_swe`
with Codex CLI as the agent runtime and DeepSeek V4 Pro as the Inspect model
provider (`openai-api/deepseek/deepseek-v4-pro`).

All evaluation scores must be LLM-as-judge scores. Deterministic validators,
script reruns, `.aiss` audits, exact CSV comparisons, and structural packet
builders may be used as gates, diagnostics, or judge evidence, but they must not
be reported as the eval score.

For the DDI survey-cleaning harness:

```bash
python3 -m pip install -r evals/ddi_harness/requirements.txt
python3 scripts/run_agent_runtime_harness_eval.py --runtime codex --judge-model openai-api/deepseek/deepseek-v4-pro
```

For the research-factory relay handoff harness:

```bash
python3 -m pip install -r evals/factory_relay/requirements.txt
python3 scripts/run_factory_relay_eval.py --conditions no_skills,single_skill,full_skills,broken_handoff,shuffled_order --judge-model openai-api/deepseek/deepseek-v4-pro
```

For the one-idea-to-data-backed-APSR-draft PDF harness:

```bash
python3 -m pip install -r evals/factory_e2e_apsr_pdf/requirements.txt
python3 scripts/run_factory_e2e_apsr_pdf_eval.py --conditions no_skills,full_research_factory_skills
```

These evals require `DEEPSEEK_API_KEY` and a running Docker daemon, such as
Colima on macOS. The relay eval is an audit: do not interpret a high score as
empirical validity or as proof of positive skill marginal gain. The APSR PDF
eval is deliberately PDF-only: the agent input is the single idea sentence, and
the scorer reads only `paper/full_draft.pdf` with an Inspect LLM judge. The DDI
and relay evals also use LLM judges; their deterministic script/data checks and
handoff audits are judge evidence and metadata only. The agent is nevertheless
expected to autonomously discover public sources, acquire real observed public
or authorized data, construct the observed analysis sample, run analysis, and
make provenance/results visible in that PDF. Do not use `.aiss`, stage logs,
tables, figures, scripts, TeX, or other intermediate files as scoring evidence
for that eval.

The `.aiss` validators use the unified v0.4 DSL entrypoint in this repo:
`dsl/scripts/aiss.py compile`, `aiss.py lint`, and `aiss.py run`.

## Boundaries

- The only AI-writing/submission boundary is the disclosure and direct-submission
  gate above; do not reintroduce blanket bans on AI drafting manuscript,
  reviewer-response, or scholarly working prose.
- Do not use the former local research-model extension for local artifacts.
- Do not present deterministic structural evaluations as live double-blind
  evidence.
- Do not report deterministic validator, audit, exact-match, or packet-builder
  outputs as eval scores; score evals with LLM-as-judge.
- Keep AI-use ledger rows updated when AI changes externally shared teaching or
  research-workflow artifacts.
