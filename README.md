<p align="center">
  <img src="docs/assets/readme/ai4ss-header.svg" alt="AI4SS research infrastructure: skills, .aiss objects, validation gates, evaluation evidence, and bounded handoff" width="100%">
</p>

<div align="center">

# ai4ss-skills

### Research infrastructure for agent-assisted social science.

AI4SS turns AI-agent labor into durable research objects: route declarations,
study designs, source ledgers, data contracts, analysis manifests, method
audits, claim ledgers, slide maps, and reviewer-response matrices.

It treats the model as a worker inside a research operating system, not as the
operating system itself.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-3776AB?logo=python&logoColor=white)](https://python.org)
[![R](https://img.shields.io/badge/R-%3E%3D4.1-276DC3?logo=r&logoColor=white)](https://www.r-project.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-blueviolet?logo=anthropic)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Cursor](https://img.shields.io/badge/Cursor-compatible-000000?logo=cursor)](https://cursor.com)

**[Start Here](#start-here) | [Infrastructure](#infrastructure) | [Capabilities](#capabilities) | [Skills](#skills) | [Evidence](#evidence) | [Limits](#limits)**

</div>

<table>
  <tr>
    <td align="center"><strong>19</strong><br>installable skills</td>
    <td align="center"><strong>.aiss v0.4</strong><br>research object IR</td>
    <td align="center"><strong>9</strong><br>workflow gates</td>
    <td align="center"><strong>4</strong><br>evaluation tracks</td>
    <td align="center"><strong>92.4 / 100</strong><br>factory structural score</td>
  </tr>
</table>

## The Bet

AI agents can already produce fluent research-shaped text. That is not the
hard part. The hard part is making agent work usable inside scholarship without
losing the things research depends on: source status, design choices, data
lineage, missingness decisions, analysis readiness, method review, authorship
boundaries, and revision traceability.

This repository is a working infrastructure layer for that problem. It combines
installable skills, a unified `.aiss` research object, schema-bearing sidecars,
validators, examples, and evaluation packets. The ambition is not to make an
agent sound like a scholar. The ambition is to make its work inspectable enough
that a scholar can use, reject, revise, teach, and extend it.

| AI failure mode | Infrastructure response |
|---|---|
| Plausible topic advice with no next action | Route cards, stop reasons, minimum viable study |
| "Research design" reduced to a slogan | MIDA declarations, decision registers, diagnosands |
| Literature review as unsourced synthesis | Discovery, screening, extraction, source-status gates |
| Data cleaning remembered in prose | DDI metadata, cleaning contract, execution audit, sample flow |
| Tables detached from design | Analysis readiness gate, scripts, logs, run manifest |
| Methods issues found too late | Issue table, redesign routes, validation commands |
| Writing help that becomes ghostwriting | Claim ledger, paragraph slots, author decision points |
| Reviewer response without evidence trace | Revision matrix, manuscript locations, action status |

The big claim is infrastructural: agent-assisted social science needs durable
research objects and quality gates, not only better prompts.

## Start Here

Clone the repository and run the basic workflow validator:

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
cd ai4ss-skills
python3 scripts/validate_skillpack_workflow.py
```

| Reader | First path |
|---|---|
| Agent operating in this repo | Read [`AGENTS.md`](AGENTS.md), then the relevant `skills/<skill-name>/SKILL.md` |
| Skill user | Copy or symlink `skills/<skill-name>/` into `~/.codex/skills`, `~/.claude/skills`, or `~/.agents/skills` |
| Skill developer | Edit only the canonical `skills/` tree, then run the validation gates |
| Research-methods reviewer | Start with [`docs/skillpack_workflow_contract.md`](docs/skillpack_workflow_contract.md) and [`docs/methodology_foundations.md`](docs/methodology_foundations.md) |

The repository-local `.codex/skills` and `.agents/skills` entries are symlinks
to `../skills`. Runtime copies are installs, not a second source tree.

## Infrastructure

AI4SS has five working layers.

| Layer | What it does | Where to look |
|---|---|---|
| Skill layer | Gives agents task-specific operating procedures for social-science work | [`skills/`](skills/) |
| Research object layer | Stores route, design, source, evidence, model, bridge, check, and decision state | [`docs/examples/research_model.aiss`](docs/examples/research_model.aiss) |
| Sidecar layer | Keeps human-readable projections for classrooms, collaborators, validators, and authors | skill `examples/` and `references/` |
| Gate layer | Checks workflow contracts, design declarations, data and literature readiness, `.aiss` validity, and ledgers | [`scripts/`](scripts/) |
| Evidence layer | Runs structural evals and benchmarks so claims about the skillpack are inspectable | [`docs/factory_level_eval/`](docs/factory_level_eval/) |

The `.aiss` version `0.4` object compiles to `aiss.unified_ast.v0.4`, with
workflow declarations, evidence and source grounding, and research-model
declarations in one AST. CSV, YAML, and Markdown sidecars remain important, but
they are projections of the research object rather than competing workflow
languages.

The internal design grammar is MIDA: Model, Inquiry, Data strategy, and Answer
strategy, followed by Diagnose, Redesign, and bounded Report. That grammar is
not the whole project. It is the discipline that lets the broader workbench
stay coherent across start-up, data work, literature, analysis, methods review,
writing scaffolds, slides, and revision.

## Capabilities

AI4SS is broader than a methodology checker. It covers the work loops where
computational social scientists actually lose time, provenance, and judgment.

| Work loop | What the skillpack can do today |
|---|---|
| Research start-up | Turn a rough topic, source pile, dataset folder, or policy phenomenon into route cards, a minimum viable study, failure signals, and next actions |
| Study design | Promote a selected route into MIDA declarations, design briefs, decision registers, `.aiss` model/check objects, and analysis-plan scaffolds |
| Survey cleaning | Parse Stata/SPSS/SAS/CSV/PDF/DOCX codebooks into DDI metadata, declare recodes before execution, and mechanically run the cleaning contract |
| Data engineering | Build auditable analysis samples with scripts, sample flows, merge audits, variable provenance, and raw-to-analysis separation |
| Literature and theory | Discover, verify, screen, extract, and cluster sources; create literature matrices, theory synthesis sidecars, rival/scope maps, and compiled `.aiss` evidence |
| Analysis execution | Check analysis readiness, run first-pass tables/figures/models/coding outputs, preserve logs, and build an analysis manifest |
| Methods review | Audit design-data-output-claim alignment, inference, robustness, reproducibility, theory risks, and overclaiming |
| Reporting | Build claim ledgers, evidence inventories, writing scaffolds, slide maps, source maps, and revision matrices without taking over final author prose |
| Specialist support | Provide DID guidance, LaTeX table generation, result explanation for collaborators, R performance advice, SJTU HPC workflows, Codex delegation, and Linear issue tracking |

The practical workflow is a relay:

`rough topic -> route declarations -> MIDA declarations -> data/literature gates -> analysis readiness -> analysis manifest -> method review -> bounded claim handoff`

## What This Looks Like

If a user wants to study whether municipal digital-government platforms affect
firm green innovation, the first useful output is not an introduction. It is a
research packet: candidate routes, material gaps, first feasible data or source
action, and a stop reason.

If one route survives, the design builder promotes it into `.aiss` route and
MIDA declarations. Data and literature skills then build auditable evidence
objects. The analysis runner only executes after the readiness gate. Methods
review checks whether output and claim still refer to the same design. Writing
and slides receive claim slots and source maps, not submission-ready prose.

The same infrastructure also supports narrower jobs: a DDI survey-cleaning
harness, a literature source-verification matrix, a DID methods audit, an R
performance review, an HPC Slurm handoff, or a reviewer-response matrix.

## Skills

All installable skills live in one canonical source tree:
`skills/<skill-name>/SKILL.md`.

### Research Factory

| Stage | Skill | Owns |
|---|---|---|
| Start | [`research-starter`](skills/research-starter/SKILL.md) | candidate routes, minimum viable study, next executable action |
| Design | [`study-design-builder`](skills/study-design-builder/SKILL.md) | selected route, MIDA declarations, decision register, `.aiss` model/check |
| Data | [`research-data-builder`](skills/research-data-builder/SKILL.md) | data pipeline, sample flow, merge audit, variable provenance |
| Literature | [`literature-matrix`](skills/literature-matrix/SKILL.md) | source discovery, screening, extraction matrix, compiled evidence |
| Analysis | [`research-analysis-runner`](skills/research-analysis-runner/SKILL.md) | analysis readiness gate, first-pass outputs, analysis manifest |
| Review | [`methods-reviewer`](skills/methods-reviewer/SKILL.md) | method, data, answer, and claim alignment diagnostics |
| Report | [`academic-writing-scaffold`](skills/academic-writing-scaffold/SKILL.md), [`research-slides-builder`](skills/research-slides-builder/SKILL.md), [`reviewer-response`](skills/reviewer-response/SKILL.md) | claim ledger, source map, slide map, revision matrix, author-fillable scaffolds |

### Specialist And Tooling Skills

| Skill | Owns |
|---|---|
| [`codebook-parse`](skills/codebook-parse/SKILL.md) | DDI survey metadata SSOT from data and codebooks |
| [`cleaning-contract`](skills/cleaning-contract/SKILL.md) | declared cleaning decisions before transformation |
| [`cleaning-execute`](skills/cleaning-execute/SKILL.md) | mechanical execution of a declared cleaning contract |
| [`did-expert`](skills/did-expert/SKILL.md) | DID and panel causal inference diagnostics |
| [`latex-tables`](skills/latex-tables/SKILL.md) | publication-style LaTeX tables and HTML previews |
| [`analysis-explainer`](skills/analysis-explainer/SKILL.md) | technical result documentation for collaborators |
| [`r-performance`](skills/r-performance/SKILL.md) | R profiling, optimization, and parallelization advice |
| [`sjtu-hpc`](skills/sjtu-hpc/SKILL.md) | SJTU HPC, Slurm, queues, transfer, cleanup, and job templates |
| [`codex`](skills/codex/SKILL.md) | OpenAI Codex CLI delegation from another agent |
| [`linear-issue`](skills/linear-issue/SKILL.md) | work tracking through Linear issues |

## Validation

Run these gates from the repository root after changing the research-factory
skillpack.

| Gate | Command |
|---|---|
| Workflow contract | `python3 scripts/validate_skillpack_workflow.py` |
| Methodology foundations | `python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv` |
| AI-use ledger | `python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv` |
| `.aiss` model | `python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss` |
| Literature evidence compile | `python3 scripts/validate_literature_evidence_compile.py skills/literature-matrix/examples/valid_literature_matrix.csv` |
| Analysis readiness | `python3 scripts/validate_analysis_readiness.py skills/research-analysis-runner/examples/valid_analysis_readiness_check.csv` |
| Factory-level eval | `python3 scripts/run_factory_level_eval.py --clean` |

For DSL work, use `dsl/scripts/aiss.py` as the unified v0.4 entrypoint for
`compile`, `lint`, and `run`.

Key docs:

- [`docs/skillpack_workflow_contract.md`](docs/skillpack_workflow_contract.md)
- [`docs/ai4ss_dsl_factory_integration.md`](docs/ai4ss_dsl_factory_integration.md)
- [`docs/methodology_foundations.md`](docs/methodology_foundations.md)
- [`docs/skillpack_gap_map.md`](docs/skillpack_gap_map.md)
- [`docs/ai_use_ledger.schema.md`](docs/ai_use_ledger.schema.md)

## Evidence

These evaluations measure structure, continuity, validation gates, and boundary
discipline. They do not prove empirical truth and they do not replace expert
review.

| Evaluation | Baseline | AI4SS skill/factory | What it measures |
|---|---:|---:|---|
| Factory-level structural packet | 6.4 / 100 | 92.4 / 100 | full-chain continuity from rough topic to bounded claim handoff |
| Live skill-use evaluation | 84.4 / 100 | 94.1 / 100 | inspectable artifacts, traceability markers, validation gates, author decisions |
| Structural skill-use simulation | 39.0 / 100 | 96.2 / 100 | whether canonical artifacts and gates appear in controlled packets |
| Cleaning-contract benchmark | 53% pass rate | 100% pass rate | survey cleaning contracts on three real PI datasets |

Reports:

- [`docs/factory_level_eval/unblinded_report.md`](docs/factory_level_eval/unblinded_report.md)
- [`docs/live_blind_skill_use_eval/unblinded_report.md`](docs/live_blind_skill_use_eval/unblinded_report.md)
- [`docs/blind_skill_use_eval/unblinded_report.md`](docs/blind_skill_use_eval/unblinded_report.md)
- [`docs/evals/cleaning-contract/iteration-1/benchmark.md`](docs/evals/cleaning-contract/iteration-1/benchmark.md)

## Repository Map

| Path | Purpose |
|---|---|
| `skills/` | canonical source tree for installable skills |
| `dsl/` | `.aiss` parser, compiler, linter, and runner |
| `docs/` | contracts, methodology docs, examples, evaluation packets |
| `scripts/` | validators and evaluation generators |
| `references/` | source and DSL reference material |
| `.codex/skills`, `.agents/skills` | symlinks to `../skills` |

## Limits

The infrastructure is ambitious, but its claims are bounded.

- It does not certify that an empirical claim is true.
- It does not turn `.aiss` checker success into identification validity.
- It does not replace source reading, data inspection, ethics review, or
  author judgment.
- It does not write final manuscript prose, final reviewer-response prose, or
  final scholarly claims for the author.
- It is not yet a universal specialist-methods system. DID is covered, while
  IV, RD, RCT, survey, network, spatial, ML evaluation, qualitative interviews,
  and ethics/confidentiality review remain watchlist areas unless added as
  specialist skills.
- The strongest current factory evaluation is structural. A stronger live field
  evaluation should use independently generated outputs, independent human
  expert graders, and inter-rater reliability before unblinding.

## Contributing

Add a skill when you can name a real research failure mode and turn it into a
repeatable artifact workflow.

A good contribution should:

1. live under `skills/<skill-name>/`,
2. include a `SKILL.md` with precise trigger language,
3. define its role in the broader research infrastructure,
4. preserve upstream handoff fields when available,
5. produce inspectable artifacts rather than final scholarly claims,
6. add examples or validators when the output has a schema,
7. update the AI-use ledger when externally shared teaching or research
   workflow artifacts change.

Before opening a PR, run the validation commands above and include the exact
commands and results in the PR description.

## Cite

```bibtex
@software{ai4ss_skills_2026,
  author    = {Zheng, Siyao},
  title     = {ai4ss-skills: Agent Skills for Social Science Research},
  year      = {2026},
  url       = {https://github.com/SiyaoZheng/ai4ss-skills},
  note      = {Released at AI for Social Science (AI4SS) Online Lecture Series}
}
```

## License

GPL-3.0. Derivative works must carry the same license.

Exception: `skills/codex/` is based on
[@davila7](https://github.com/davila7)'s original Codex skill and retains its
MIT license in [`skills/codex/LICENSE`](skills/codex/LICENSE).
