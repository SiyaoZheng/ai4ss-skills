<p align="center">
  <img src="docs/assets/readme/ai4ss-header.svg" alt="AI4SS research infrastructure: skills, .aiss objects, validation gates, evaluation evidence, and bounded handoff" width="100%">
</p>

<div align="center">

# ai4ss-skills

### Research infrastructure for agent-assisted social science.

AI4SS turns agent work into durable research objects: route declarations,
study designs, source-evidence declarations, data contracts, analysis artifacts,
methods diagnostics, bounded claims, presentation artifacts, and reviewer
decision traces.

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
    <td align="center"><strong>22</strong><br>installable skills</td>
    <td align="center"><strong>.aiss v0.4</strong><br>state-machine IR</td>
    <td align="center"><strong>12</strong><br>workflow gates</td>
    <td align="center"><strong>5</strong><br>evaluation tracks</td>
    <td align="center"><strong>78.7 / 100</strong><br>factory structural score</td>
  </tr>
</table>

## What This Is

AI agents are already good at producing fluent research-shaped text. That is
not the hard part. The hard part is making agent work usable inside scholarship
without losing the things research depends on: source status, design choices,
data lineage, missingness decisions, analysis readiness, methods review,
authorship boundaries, and revision traceability.

This repository is a working infrastructure layer for that problem. It combines
installable agent skills, a unified `.aiss` research object, validators,
examples, and evaluation packets. The goal is not to make an agent sound like a
scholar. The goal is to make its work inspectable enough that a scholar can use,
reject, revise, teach, and extend it.

| AI failure mode | AI4SS response |
|---|---|
| Plausible topic advice with no next action | `.aiss` route declarations, continuation plans, minimum viable study |
| "Research design" reduced to a slogan | MIDA declarations, decision registers, diagnosands |
| Literature review as unsourced synthesis | `.aiss` source-evidence declarations and source-status gates |
| Data cleaning remembered in prose | DDI metadata, cleaning contract, execution audit, `.aiss` row-loss checks |
| Tables detached from design | `.aiss` readiness checks, scripts, logs, analysis artifacts |
| Methods issues found too late | `.aiss` diagnostic checks, redesign routes, validation commands |
| Writing help that hides AI involvement | Bounded claim declarations, AI-use disclosure, paragraph drafts, submission gate |
| Reviewer response without traceability | Reviewer-request decisions, manuscript locations, action status |

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
canonical `skills/` tree. It also ships `.mcp.json` with research-runtime MCP
servers. The primary official web-discovery path is Alibaba Cloud IQS:
`IQSWebSearch` (`common_search`), `IQSLiteSearch` (`web_search`), and
`IQSReadPage` (`readpage_basic` / `readpage_scrape`). These servers read
`X-API-Key` from `ALIYUN_IQS_API_KEY`, matching the official IQS MCP
streamable HTTP configuration. Set it either as an environment variable or in
the official IQS skills env file:

```bash
mkdir -p ~/.alibabacloud/iqs
printf 'ALIYUN_IQS_API_KEY=your-api-key\n' > ~/.alibabacloud/iqs/env
```

The wrapper also exposes Alibaba Cloud Bailian web discovery as `WebSearch`.
Because the official remote Streamable HTTP WebSearch endpoint can fail
handshake while the same key works through DashScope Responses API, the Codex
plugin uses a local stdio bridge (`scripts/bailian_mcp_bridge.py`) by default.
That bridge reads `DASHSCOPE_API_KEY` and exposes `bailian_web_search`, backed by
DashScope Responses API `web_search` plus `web_extractor`, and
`bailian_web_parse`, backed by the official Bailian WebParser MCP SSE service.
The APSR PDF eval injects this local bridge whenever `DASHSCOPE_API_KEY` exists,
so a failing remote MCP endpoint is not passed to the agent runtime.
Alibaba Cloud WebParser is available after opening the official `网页解析` MCP
service. Its console-provided external configuration is SSE
(`https://dashscope.aliyuncs.com/api/v1/mcps/WebParser/sse`); the bridge calls
that SSE service through the verified DashScope OpenAI-compatible Responses API
path (`DASHSCOPE_RESPONSES_BASE_URL`, `DASHSCOPE_WEBPARSER_MCP_URL`,
`DASHSCOPE_WEBPARSER_MODEL`, and `DASHSCOPE_WEBSEARCH_MODEL`) rather than
injecting an incompatible SSE server directly into Codex runtime.
Browser automation is provided by the open-source
`browser-use` MCP server, started with
`uvx --from browser-use[cli] browser-use --mcp` and passes through provider
environment variables such as `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`,
`BROWSER_USE_LLM_MODEL`, `ANTHROPIC_API_KEY`, and `BROWSER_USE_API_KEY` when
present. For browser-use agent mode, the launcher maps `DASHSCOPE_API_KEY` to
the `OPENAI_API_KEY` seen by browser-use, sets the OpenAI-compatible base URL to
`https://dashscope.aliyuncs.com/compatible-mode/v1`, and uses `qwen-plus`,
because that path supports the structured output expected by the official
browser-use MCP server. If DashScope is unavailable, it can still map
`DEEPSEEK_API_KEY` to `OPENAI_API_KEY` with `https://api.deepseek.com/v1`, but
the APSR PDF eval is configured to use the verified DashScope/Qwen path when the
Bailian key exists. Its Docker sandbox also installs browser-use and a Chromium
browser for direct browser-control tools. Do not commit API keys to this
repository.

The wrapper also ships `hooks/hooks.json`, a PreToolUse guard
that blocks direct writes to generated research outputs such as
`data/intermediate/`, `data/processed/`, `output/tables/`, `output/figures/`,
`output/models/`, `output/logs/`, legacy `outputs/`, legacy `output/audit/`,
and generated paper files; regenerate those artifacts through `make` targets.
The local marketplace entry is `.agents/plugins/marketplace.json`.

```bash
codex plugin marketplace add /path/to/ai4ss-skills
codex plugin add ai4ss-skills@ai4ss-skills-local
```

Validate the Codex wrapper:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/test_ai4ss_plugin_hooks.py
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
observed public-source acquisition -> observed-data sample construction/check ->
literature evidence gates -> .aiss analysis readiness -> .aiss analysis artifacts ->
transparency package -> bounded claim handoff -> AI-disclosed manuscript package
```

The methodology spine is:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

In practice:

| Stage | Scholar question | Primary skill | Durable output |
|---|---|---|---|
| Start | What can this become? | `research-starter` | `.aiss` route declarations, continuation plan, next executable action |
| Design | What exactly is the study? | `study-design-builder` | Selected route, MIDA declarations, decision register, `.aiss` model/check |
| Source acquisition | Where do real observed data come from? | `public-data-sources` | Source route, access status, official docs, request template, provenance |
| Data sample | Can acquired observed data support the design? | `research-data-builder` | `.aiss` source/artifact/empirical declarations, row provenance, row-loss checks, data pipeline |
| Literature | What is the source-backed evidence? | `literature-matrix` | `.aiss` source-evidence declarations and source-status checks |
| Analysis | Is this ready to run? | `research-analysis-runner` | `.aiss` readiness checks, scripts, outputs, analysis artifacts |
| Figures | Are the paper figures top-journal ready and stylistically coherent? | `top-journal-figures` | R/ggplot2 code, shared style profile, helper-tool transparency, vector figure exports, captions, source notes, visual-integrity checks |
| Review | Are method and claim aligned? | `methods-reviewer` | Issues, redesign options, automation decisions |
| Manuscript review | Does the draft pass fixed writing tests? | `manuscript-reviewer` | Context-sealed manifest, AutoChecklist observations, fail-first routes, reader-test queue |
| Report/package | How does the author communicate and submit safely? | `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response` | Bounded claims, source map, TOP disclosure matrix, replication-package status, presentation artifacts, reviewer decisions |

The workflow is a relay, not a chain of prose requests. Each stage should
preserve identifiers, source paths, known gaps, validation commands, and
interpretation boundaries so the next stage can inspect what happened.

## Core Objects

AI4SS has five working layers.

| Layer | What it does | Where to look |
|---|---|---|
| Skill layer | Gives agents task-specific operating procedures | [`skills/`](skills/) |
| Research object layer | Stores semantic declarations and event-sourced runtime facts, then projects deterministic research-factory state | [`docs/examples/research_model.aiss`](docs/examples/research_model.aiss) |
| Source artifact layer | Keeps cited PDFs, logs, scripts, tables, figures, and author notes outside workflow state | project source folders |
| Gate layer | Checks workflow contracts, readiness, evidence, `.aiss` validity, and ledgers | [`scripts/`](scripts/) |
| Evidence layer | Runs structural evals and benchmarks | [`docs/factory_level_eval/`](docs/factory_level_eval/) |

### `.aiss`

The local `.aiss` version `0.4` object compiles to
`aiss.unified_ast.v0.4` and projects to `aiss.machine_state.v0.4`. It can
carry:

- `route` declarations
- seven MIDA declarations
- `decision` declarations
- source spans
- claims, concepts, attributes, causal relations, empirical objects, and bridges
- checks, transparency status, replication-package status, and derived diagnostics
- `event` declarations for skill starts, completions, failures, heartbeat
  observations, watchdog recoveries, and other runtime facts

CSV files, YAML files, and derived Markdown notes are not workflow state.
Agents may reference external source artifacts from `.aiss`, but handoff
contracts must live in checked `.aiss` declarations.

The state-machine boundary is deliberate:

```bash
python3 dsl/scripts/aiss.py state docs/examples/research_model.aiss
python3 dsl/scripts/aiss.py transition docs/examples/research_model.aiss --event '{"type":"heartbeat_seen","source":"goal-cli"}'
```

`route`, `mida`, and `decision` declarations are durable semantic research
state. `event` declarations are the append-only runtime fact log used by the
deterministic reducer. `.aiss` does not own timers, process locks, subprocess
cleanup, or scheduled retries; those remain `goal-cli` responsibilities.

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
| Report boundary | Claim ledger, source map, AI-use ledger, transparency disclosures, replication-package status, automation assumption register, and communication boundary |

## Skills

All installable skills live under `skills/<skill-name>/`. `skills/` is the only
source tree.

### Research Factory Skills

| Skill | When to use it | Owns |
|---|---|---|
| [`research-starter`](skills/research-starter/SKILL.md) | Rough topic, source pile, vague policy phenomenon, or "what can I do next?" | `.aiss` route declarations, minimum viable study, next action |
| [`study-design-builder`](skills/study-design-builder/SKILL.md) | Turn a selected route into an executable design | MIDA declarations, estimand map, decision register, `.aiss` model/check |
| [`public-data-sources`](skills/public-data-sources/SKILL.md) | Find, verify, and acquire real observed public or authorized data sources | Access class, official docs, source artifacts, provenance, source checks |
| [`research-data-builder`](skills/research-data-builder/SKILL.md) | Build or repair an auditable analysis sample from acquired observed sources | Data pipeline plus `.aiss` source/artifact/empirical/check declarations |
| [`literature-matrix`](skills/literature-matrix/SKILL.md) | Discover, screen, and extract source-backed literature evidence | Candidate discovery, screening/extraction matrix, compiled evidence |
| [`research-analysis-runner`](skills/research-analysis-runner/SKILL.md) | Run first-pass outputs after readiness checks | `.aiss` readiness checks, scripts, tables, figures, logs, analysis artifacts |
| [`top-journal-figures`](skills/top-journal-figures/SKILL.md) | Produce and audit AER/APSR-style paper figures with ggplot2 | R/ggplot2 scripts, shared style profile, helper-tool transparency, vector figures, captions, source notes, visual-integrity checks |
| [`methods-reviewer`](skills/methods-reviewer/SKILL.md) | Audit design, data, answer, and claim alignment | Methods issues, redesign routes, automation decisions |
| [`manuscript-reviewer`](skills/manuscript-reviewer/SKILL.md) | Run stateless AutoChecklist TDD reviews on manuscript drafts | Manifest hashes, AutoChecklist observations, fail-first routes, reader-test queue |
| [`academic-writing-scaffold`](skills/academic-writing-scaffold/SKILL.md) | Prepare AI-disclosed manuscript work | Claim ledger, argument map, paragraph slots, working drafts, citation gaps, submission gate |
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
| [`inspect-agent-eval`](skills/inspect-agent-eval/SKILL.md) | Official Inspect AI / Inspect SWE agent-runtime harness evaluations |

## Validation

Run the full validation suite from the repository root after changing the
research-factory skillpack:

```bash
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_research_workspace_contract.py
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss
python3 scripts/run_factory_level_eval.py --clean
python3 scripts/run_skill_handoff_audit_fixtures.py
```

Use the `.aiss` state-machine commands directly when changing reducer,
transition, or watchdog-facing behavior:

```bash
python3 dsl/scripts/aiss.py state docs/examples/research_model.aiss
python3 dsl/scripts/aiss.py transition docs/examples/research_model.aiss --event '{"type":"skill_started","skill":"research-starter","at":"2026-07-05T00:00:00Z"}'
```

Run the live agent-runtime harness eval separately when changing the DDI
survey-cleaning skills. It uses the existing Inspect AI + `inspect_swe`
Codex CLI agent bridge, launches a real Codex CLI agent in an isolated sandbox,
routes model calls through DeepSeek V4 Pro
(`openai-api/deepseek/deepseek-v4-pro`), reruns the produced R script and
exact CSV/provenance checks as judge evidence, and grades the sandbox artifacts
with an LLM-as-judge scorer. It requires `DEEPSEEK_API_KEY` and a running
Docker daemon:

```bash
python3 -m pip install -r evals/ddi_harness/requirements.txt
python3 scripts/run_agent_runtime_harness_eval.py --runtime codex --judge-model openai-api/deepseek/deepseek-v4-pro
```

Run the research-factory relay handoff eval separately when changing
cross-skill workflow state, MIDA/decision routing, or `.aiss` handoff
contracts. It uses the same official Inspect AI + `inspect_swe` Codex CLI
agent-runtime pattern, includes no-skills and single-skill ablations, and
scores sandbox `.aiss` output with an LLM-as-judge scorer. The deterministic
handoff audit is retained as diagnostic metadata and judge evidence only:

```bash
python3 -m pip install -r evals/factory_relay/requirements.txt
python3 scripts/run_factory_relay_eval.py --conditions no_skills,single_skill,full_skills,broken_handoff,shuffled_order --judge-model openai-api/deepseek/deepseek-v4-pro
```

Run the one-idea-to-data-backed-APSR-draft PDF eval separately when changing
end-to-end manuscript production behavior. The agent receives only the idea sentence,
`Idea: Does neighborhood service-center exposure change resident civic trust?`,
and the scorer reads only `paper/full_draft.pdf`. The agent is expected to
autonomously discover public sources, acquire real observed public or authorized
data, construct the observed analysis sample, run empirical analysis, and make
data provenance, measurement choices, results, and limitations visible in that
PDF. Intermediate `.aiss`, logs, tables, figures, scripts, and TeX files may be
created by the agent but are not scoring evidence:

```bash
python3 -m pip install -r evals/factory_e2e_apsr_pdf/requirements.txt
python3 scripts/run_factory_e2e_apsr_pdf_eval.py --conditions no_skills,full_research_factory_skills
```

When the OpenAI bundled LaTeX plugin is installed locally, the full-skill APSR
PDF condition also exposes its `latex-doctor`, `latex-compile`, and
`texlive-runtime-installer` skills to the Codex runtime. Set
`AI4SS_DISABLE_LATEX_PLUGIN_SKILLS=1` to disable this or
`AI4SS_LATEX_PLUGIN_ROOT=/path/to/openai-bundled/latex/<version>` to pin a
specific plugin copy.

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

- [`docs/research_workspace_contract.md`](docs/research_workspace_contract.md)
- [`docs/skillpack_workflow_contract.md`](docs/skillpack_workflow_contract.md)
- [`docs/ai4ss_dsl_factory_integration.md`](docs/ai4ss_dsl_factory_integration.md)
- [`docs/methodology_foundations.md`](docs/methodology_foundations.md)
- [`docs/methodology_source_matrix.csv`](docs/methodology_source_matrix.csv)
- [`docs/ai_use_ledger.schema.md`](docs/ai_use_ledger.schema.md)
- [`docs/skillpack_gap_map.md`](docs/skillpack_gap_map.md)

## Evidence

These evaluations and diagnostics measure structure, continuity, validation
gates, and boundary discipline. Current eval scores must come from
LLM-as-judge. Deterministic checks, packet builders, and exact-match benchmarks
are diagnostics or judge evidence; they do not prove empirical truth and they
do not replace expert review.

| Evaluation | Baseline | AI4SS skill/factory | What it measures |
|---|---:|---:|---|
| Factory-level structural packet | pending LLM judge | pending LLM judge | Continuity from rough topic to AI-disclosed manuscript package |
| Live skill-use evaluation | archival pre-policy score | archival pre-policy score | Inspectable artifacts, traceability markers, validation gates, assumption registers |
| Structural skill-use simulation | diagnostic packet only | diagnostic packet only | Whether canonical artifacts and gates appear in controlled packets |
| Cleaning-contract benchmark | diagnostic pass rate | diagnostic pass rate | Survey cleaning contracts on three real PI datasets |
| Agent-runtime DDI harness eval | archival pre-judge run | current LLM-as-judge scorer uses exact script/CSV/provenance evidence | Whether a live agent can use the DDI harness skills inside official Inspect samples |
| Agent-runtime factory relay eval | historical audit-derived score | superseded by LLM-as-judge scorer with handoff-audit metadata | Whether live agents preserve `.aiss` route/MIDA/decision/artifact/check/claim handoffs across skill boundaries |
| Agent-runtime APSR PDF eval | historical no-skills 82 / 100 | historical full research-factory skills 85 / 100 | Whether a live agent can turn one idea sentence into a data-backed `paper/full_draft.pdf`; scored only by an Inspect LLM judge reading that PDF |

Reports:

- [`docs/factory_level_eval/unblinded_report.md`](docs/factory_level_eval/unblinded_report.md)
- [`docs/live_blind_skill_use_eval/unblinded_report.md`](docs/live_blind_skill_use_eval/unblinded_report.md)
- [`docs/blind_skill_use_eval/unblinded_report.md`](docs/blind_skill_use_eval/unblinded_report.md)
- [`docs/evals/cleaning-contract/iteration-1/benchmark.md`](docs/evals/cleaning-contract/iteration-1/benchmark.md)
- [`docs/evals/ddi-harness/inspect-round1.md`](docs/evals/ddi-harness/inspect-round1.md)
- [`docs/evals/factory-relay/deterministic-handoff-audit.md`](docs/evals/factory-relay/deterministic-handoff-audit.md)
- [`docs/evals/factory-relay/inspect-relay-summary.md`](docs/evals/factory-relay/inspect-relay-summary.md)
- [`docs/evals/factory-e2e-apsr-pdf/inspect-summary.md`](docs/evals/factory-e2e-apsr-pdf/inspect-summary.md)

The appropriate interpretation is narrow. These packets show that the local
workflow has an evaluable factory-level contract and that skill-guided outputs
can improve traceability in controlled settings. They do not show that a live
agent will always use the factory correctly, that empirical claims are true, or
that `.aiss` checker success establishes identification validity. The first
factory relay runtime round did not show positive marginal gain from installing
the full skill chain on the single tested scenario; it exposed residual
handoff-routing failures that should be treated as actionable skillpack issues.
The first APSR PDF runtime round used an older design-stage endpoint. The
current endpoint is stricter: pure design-stage PDFs are capped unless the PDF
visibly documents real observed data acquisition, observed sample construction,
and actual analysis results. Synthetic, simulated, hypothetical, illustrative,
generated, DGP-created, random-draw, benchmark-calibrated, or
literature-parameter-imputed empirical data fail the scorer before model
judging.

Current eval policy: reported eval scores must come from LLM-as-judge. Exact
CSV comparisons, R script reruns, `.aiss` linting, handoff audits, and
structural packet builders remain useful diagnostics and judge evidence, but
they are not the score.

## Repository Map

| Path | Purpose |
|---|---|
| [`skills/`](skills/) | Canonical source tree for installable skills |
| [`dsl/`](dsl/) | `.aiss` parser, compiler, linter, and runner |
| [`scripts/`](scripts/) | Validators, evidence compilers, and evaluation generators |
| [`evals/`](evals/) | Inspect AI agent-runtime evaluations |
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
- Its only manuscript-facing AI boundary is disclosure and submission gating:
  skills may draft, revise, audit, and assemble working manuscript or
  reviewer-response text, but must not present output as submission-ready or as
  having no AI involvement unless AI contribution disclosure, human
  accountability, and outlet-policy checks are explicit.
- It does not treat deterministic structural evaluations as live double-blind
  evidence.
- It does not report deterministic validators, exact-match checks, handoff
  audits, or packet builders as eval scores; eval scoring is LLM-as-judge.
- It does not replace `goal-cli` as the external watchdog, timer, lock owner,
  heartbeat observer, or process-recovery owner. `.aiss` records and reduces
  runtime facts; it does not execute or supervise processes.
- It is not yet a universal specialist-methods system. DID is covered; IV, RD,
  RCT, survey, network, spatial, ML evaluation, qualitative interviews, and
  ethics/confidentiality review remain watchlist areas unless added as
  specialist skills.

The rule for outward-facing scholarship is simple: AI participation is allowed
across the workflow, including working prose, but the manuscript package must
carry AI-use disclosure, human accountability, direct-submission status, and
policy-check status before it can be treated as submission-ready.

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
5. produce inspectable artifacts and disclosed AI-assisted working text rather
   than submission-ready text with hidden AI involvement,
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
