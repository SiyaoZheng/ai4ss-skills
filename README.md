<p align="center">
  <img src="docs/assets/readme/ai4ss-logo.png" alt="AI4SS 智輔社科大篆印章标志" width="120">
</p>

<div align="center">

# ai4ss-skills

### Research infrastructure for agent-assisted social science.

AI4SS turns agent work into durable research objects: route declarations,
study designs, source ledgers, data contracts, analysis manifests, methods
diagnostics, claim ledgers, slide maps, and reviewer-response matrices.

It treats the model as a worker inside a research operating system, not as the
operating system itself.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-3776AB?logo=python&logoColor=white)](https://python.org)
[![R](https://img.shields.io/badge/R-%3E%3D4.1-276DC3?logo=r&logoColor=white)](https://www.r-project.org/)
[![Codex Plugin](https://img.shields.io/badge/Codex-plugin-10A37F)](.codex-plugin/plugin.json)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-blueviolet)](.claude-plugin/plugin.json)

**[Install](#install) | [Workflow](#workflow) | [Skills](#skills) | [Validation](#validation) | [Evidence](#evidence) | [Boundaries](#boundaries)**

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

## What This Is

AI agents are already good at producing fluent research-shaped text. That is
not the hard part. The hard part is making agent work usable inside scholarship
without losing the things research depends on: source status, design choices,
data lineage, missingness decisions, analysis readiness, methods review,
authorship boundaries, and revision traceability.

This repository is a working infrastructure layer for that problem. It combines
installable agent skills, a unified `.aiss` research object, sidecar schemas,
validators, examples, and evaluation packets. The goal is not to make an agent
sound like a scholar. The goal is to make its work inspectable enough that a
scholar can use, reject, revise, teach, and extend it.

| AI failure mode | AI4SS response |
|---|---|
| Plausible topic advice with no next action | Route cards, stop reasons, minimum viable study |
| "Research design" reduced to a slogan | MIDA declarations, decision registers, diagnosands |
| Literature review as unsourced synthesis | Discovery ledgers, screening matrices, source-status gates |
| Data cleaning remembered in prose | DDI metadata, cleaning contract, execution audit, sample flow |
| Tables detached from design | Analysis readiness gate, scripts, logs, run manifest |
| Methods issues found too late | Issue table, redesign routes, validation commands |
| Writing help that becomes ghostwriting | Claim ledger, paragraph slots, author decision points |
| Reviewer response without traceability | Revision matrix, manuscript locations, action status |

The core claim is infrastructural: agent-assisted social science needs durable
research objects and quality gates, not only better prompts.

## Install

Clone the repository:

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
cd ai4ss-skills
```

### Codex

The Codex plugin wrapper lives at `.codex-plugin/plugin.json` and points at the
canonical `skills/` tree. The local marketplace entry is
`.agents/plugins/marketplace.json`.

```bash
codex plugin marketplace add /path/to/ai4ss-skills
codex plugin add ai4ss-skills@ai4ss-skills-local
```

Validate the Codex wrapper:

```bash
python3 scripts/validate_codex_plugin.py
```

### Claude Code

The Claude Code plugin wrapper lives at `.claude-plugin/plugin.json` and points
at the same canonical `skills/` tree. The local marketplace entry is
`.claude-plugin/marketplace.json`.

```bash
claude plugin marketplace add /path/to/ai4ss-skills
claude plugin install ai4ss-skills@ai4ss-skills-local
```

Validate the Claude Code wrapper:

```bash
python3 scripts/validate_claude_plugin.py
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict .claude-plugin/marketplace.json
```

### Direct Skill Installs

Plugin install is the preferred path. If a runtime only supports directory
skills, copy or symlink selected `skills/<skill-name>/` directories into that
runtime's skill directory.

The repository-local `.codex/skills` and `.agents/skills` entries are symlinks
to `../skills`. They are convenience links for local development, not a second
source tree.

## Workflow

The research-factory spine is:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
literature/data gates -> analysis readiness -> analysis manifest ->
bounded claim handoff
```

The methodology spine is:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

In practice:

| Stage | Scholar question | Primary skill | Durable output |
|---|---|---|---|
| Start | What can this become? | `research-starter` | Route cards, stop reason, next executable action |
| Design | What exactly is the study? | `study-design-builder` | Selected route, MIDA declarations, decision register, `.aiss` model/check |
| Data | Can the data support the design? | `research-data-builder` | Sample flow, merge audit, variable provenance, data pipeline |
| Literature | What is the source-backed evidence? | `literature-matrix` | Discovery ledger, screening/extraction matrix, compiled evidence |
| Analysis | Is this ready to run? | `research-analysis-runner` | Readiness check, scripts, outputs, analysis run manifest |
| Review | Are method and claim aligned? | `methods-reviewer` | Issues, redesign options, author decisions |
| Report | How does the author communicate safely? | `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response` | Claim ledger, source map, slide map, revision matrix |

The workflow is a relay, not a chain of prose requests. Each stage should
preserve identifiers, source paths, known gaps, validation commands, and
interpretation boundaries so the next stage can inspect what happened.

## Core Objects

AI4SS has five working layers.

| Layer | What it does | Where to look |
|---|---|---|
| Skill layer | Gives agents task-specific operating procedures | [`skills/`](skills/) |
| Research object layer | Stores route, design, source, evidence, model, bridge, check, and decision state | [`docs/examples/research_model.aiss`](docs/examples/research_model.aiss) |
| Sidecar layer | Keeps human-readable or validator-friendly projections | skill `examples/` and `references/` |
| Gate layer | Checks workflow contracts, readiness, evidence, `.aiss` validity, and ledgers | [`scripts/`](scripts/) |
| Evidence layer | Runs structural evals and benchmarks | [`docs/factory_level_eval/`](docs/factory_level_eval/) |

### `.aiss`

The local `.aiss` version `0.4` object compiles to
`aiss.unified_ast.v0.4`. It can carry:

- `route` declarations
- seven MIDA declarations
- `decision` declarations
- source spans
- claims, concepts, attributes, causal relations, empirical objects, and bridges
- checks and derived diagnostics

CSV, YAML, and Markdown sidecars remain important. They are projections of the
research object rather than competing workflow languages.

### MIDA

MIDA keeps design work concrete:

| Component | Minimum meaning |
|---|---|
| Model | Units, constructs, mechanisms, assumptions, scope conditions |
| Inquiry | Causal estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| Data strategy | Sampling, source selection, measurement, extraction, linkage, missingness, and source-screening rules |
| Answer strategy | Estimator, coding rule, synthesis rule, diagnostic comparison, table shell, or qualitative inference procedure |
| Diagnose | Bias, precision, measurement risk, source-status risk, row loss, reproducibility, and claim-support mismatch |
| Redesign | Smaller first loop, revised measure, added source, changed estimator, stronger comparison, or abandoned route |
| Report boundary | Claim ledger, source map, AI-use ledger, author decision point, and communication boundary |

## Skills

All installable skills live under `skills/<skill-name>/`. `skills/` is the only
source tree.

### Research Factory Skills

| Skill | When to use it | Owns |
|---|---|---|
| [`research-starter`](skills/research-starter/SKILL.md) | Rough topic, source pile, vague policy phenomenon, or "what can I do next?" | Route cards, minimum viable study, next action |
| [`study-design-builder`](skills/study-design-builder/SKILL.md) | Turn a selected route into an executable design | MIDA declarations, estimand map, decision register, `.aiss` model/check |
| [`research-data-builder`](skills/research-data-builder/SKILL.md) | Build or repair an auditable analysis sample | Data pipeline, sample flow, merge audit, variable provenance |
| [`literature-matrix`](skills/literature-matrix/SKILL.md) | Discover, screen, and extract source-backed literature evidence | Candidate discovery, screening/extraction matrix, compiled evidence |
| [`research-analysis-runner`](skills/research-analysis-runner/SKILL.md) | Run first-pass outputs after readiness checks | Readiness check, scripts, tables, figures, logs, run manifest |
| [`methods-reviewer`](skills/methods-reviewer/SKILL.md) | Audit design, data, answer, and claim alignment | Methods issues, redesign routes, author decisions |
| [`academic-writing-scaffold`](skills/academic-writing-scaffold/SKILL.md) | Prepare author-fillable writing scaffolds | Claim ledger, argument map, paragraph slots, citation gaps |
| [`research-slides-builder`](skills/research-slides-builder/SKILL.md) | Convert verified evidence into presentation structure | Slide map, source map, visual result narrative |
| [`reviewer-response`](skills/reviewer-response/SKILL.md) | Convert reviews into a traceable revision plan | Revision matrix, manuscript locations, response scaffold |

### Specialist And Tooling Skills

| Skill | Owns |
|---|---|
| [`codebook-parse`](skills/codebook-parse/SKILL.md) | DDI survey metadata SSOT from data and codebooks |
| [`cleaning-contract`](skills/cleaning-contract/SKILL.md) | Declared recoding decisions before data transformation |
| [`cleaning-execute`](skills/cleaning-execute/SKILL.md) | Mechanical execution of a declared cleaning contract |
| [`did-expert`](skills/did-expert/SKILL.md) | DID and panel causal inference diagnostics |
| [`latex-tables`](skills/latex-tables/SKILL.md) | Publication-style LaTeX tables and HTML previews |
| [`analysis-explainer`](skills/analysis-explainer/SKILL.md) | Technical result documentation for collaborators |
| [`r-performance`](skills/r-performance/SKILL.md) | R profiling, optimization, and parallelization advice |
| [`sjtu-hpc`](skills/sjtu-hpc/SKILL.md) | SJTU HPC, Slurm, queues, transfer, cleanup, and job templates |
| [`codex`](skills/codex/SKILL.md) | OpenAI Codex CLI delegation from another agent |
| [`linear-issue`](skills/linear-issue/SKILL.md) | Work tracking through Linear issues |

## Validation

Run the full validation suite from the repository root after changing the
research-factory skillpack:

```bash
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss
python3 scripts/validate_literature_evidence_compile.py skills/literature-matrix/examples/valid_literature_matrix.csv
python3 scripts/validate_analysis_readiness.py skills/research-analysis-runner/examples/valid_analysis_readiness_check.csv
python3 scripts/run_factory_level_eval.py --clean
```

Run plugin wrapper validation after changing package metadata:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/validate_claude_plugin.py
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict .claude-plugin/marketplace.json
```

For DSL work, use the unified v0.4 entrypoint:

```bash
python3 dsl/scripts/aiss.py compile docs/examples/research_model.aiss
python3 dsl/scripts/aiss.py lint docs/examples/research_model.aiss
python3 dsl/scripts/aiss.py run docs/examples/research_model.aiss
```

Key contracts:

- [`docs/skillpack_workflow_contract.md`](docs/skillpack_workflow_contract.md)
- [`docs/ai4ss_dsl_factory_integration.md`](docs/ai4ss_dsl_factory_integration.md)
- [`docs/methodology_foundations.md`](docs/methodology_foundations.md)
- [`docs/methodology_source_matrix.csv`](docs/methodology_source_matrix.csv)
- [`docs/ai_use_ledger.schema.md`](docs/ai_use_ledger.schema.md)
- [`docs/skillpack_gap_map.md`](docs/skillpack_gap_map.md)

## Evidence

These evaluations measure structure, continuity, validation gates, and boundary
discipline. They do not prove empirical truth and they do not replace expert
review.

| Evaluation | Baseline | AI4SS skill/factory | What it measures |
|---|---:|---:|---|
| Factory-level structural packet | 6.4 / 100 | 92.4 / 100 | Continuity from rough topic to bounded claim handoff |
| Live skill-use evaluation | 84.4 / 100 | 94.1 / 100 | Inspectable artifacts, traceability markers, validation gates, author decisions |
| Structural skill-use simulation | 39.0 / 100 | 96.2 / 100 | Whether canonical artifacts and gates appear in controlled packets |
| Cleaning-contract benchmark | 53% pass rate | 100% pass rate | Survey cleaning contracts on three real PI datasets |

Reports:

- [`docs/factory_level_eval/unblinded_report.md`](docs/factory_level_eval/unblinded_report.md)
- [`docs/live_blind_skill_use_eval/unblinded_report.md`](docs/live_blind_skill_use_eval/unblinded_report.md)
- [`docs/blind_skill_use_eval/unblinded_report.md`](docs/blind_skill_use_eval/unblinded_report.md)
- [`docs/evals/cleaning-contract/iteration-1/benchmark.md`](docs/evals/cleaning-contract/iteration-1/benchmark.md)

The appropriate interpretation is narrow. These packets show that the local
workflow has an evaluable factory-level contract and that skill-guided outputs
can improve traceability in controlled settings. They do not show that a live
agent will always use the factory correctly, that empirical claims are true, or
that `.aiss` checker success establishes identification validity.

## Repository Map

| Path | Purpose |
|---|---|
| [`skills/`](skills/) | Canonical source tree for installable skills |
| [`dsl/`](dsl/) | `.aiss` parser, compiler, linter, and runner |
| [`scripts/`](scripts/) | Validators, evidence compilers, and evaluation generators |
| [`docs/`](docs/) | Contracts, methodology docs, examples, evaluation packets |
| [`references/`](references/) | Source and DSL reference material |
| [`.codex-plugin/`](.codex-plugin/) | Codex plugin manifest |
| [`.claude-plugin/`](.claude-plugin/) | Claude Code plugin manifest and marketplace |
| [`.agents/plugins/`](.agents/plugins/) | Codex repo-scoped marketplace |
| [`.codex/skills`](.codex/skills), [`.agents/skills`](.agents/skills) | Local symlinks to `../skills` |

## Boundaries

AI4SS is intentionally bounded.

- It does not certify that an empirical claim is true.
- It does not turn `.aiss` checker success into identification validity.
- It does not replace source reading, data inspection, ethics review, or author
  judgment.
- It does not directly write final manuscript prose, final reviewer-response
  prose, or final scholarly claims.
- It does not treat deterministic structural evaluations as live double-blind
  evidence.
- It is not yet a universal specialist-methods system. DID is covered; IV, RD,
  RCT, survey, network, spatial, ML evaluation, qualitative interviews, and
  ethics/confidentiality review remain watchlist areas unless added as
  specialist skills.

The rule for outward-facing scholarship is simple: AI may create inspectable
research objects, ledgers, manifests, diagnostics, and author decision points.
The author owns final claims.

## Development

### Layout Rules

- All installable skills live as directory-format skills under `skills/<skill-name>/`.
- `skills/` is the only source tree. Do not add new top-level `*.skill`
  archives or sibling `*.skill/` directories.
- `.codex/skills` and `.agents/skills` should remain symlinks to `../skills`.
- The research-factory skillpack uses `.aiss` as the local research-model
  extension. Upstream `aiss_*` names are script names only.
- Keep plugin wrappers thin. They should point at `skills/`, not duplicate it.

### Adding Or Changing A Skill

A good contribution should:

1. live under `skills/<skill-name>/`,
2. include `SKILL.md` with precise trigger language,
3. define its role in the research-factory spine,
4. preserve upstream handoff fields when available,
5. produce inspectable artifacts rather than final scholarly claims,
6. include examples or validators when the output has a schema,
7. update the AI-use ledger when externally shared teaching or research
   workflow artifacts change.

Before opening a PR, run the validation commands above and include exact command
results in the PR description.

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
