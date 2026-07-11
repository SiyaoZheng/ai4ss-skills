<p align="center">
  <img src="docs/assets/readme/ai4ss-logo.png" alt="AI4SS 智輔社科大篆印章标志" width="120">
</p>

<div align="center">

# ai4ss-skills

### Research skills for empirical social science.

A collection of skills for doing the substantive work of quantitative political science:
formulating questions, reading literatures, developing designs, finding and constructing data,
analyzing evidence, reviewing methods, writing, revising, and presenting research.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Codex Plugin](https://img.shields.io/badge/Codex-plugin-10A37F)](.codex-plugin/plugin.json)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-blueviolet)](.claude-plugin/plugin.json)

**[Purpose](#purpose) · [Install](#install) · [Research skills](#research-skills) · [Using the skills](#using-the-skills) · [Development](#development)**

</div>

## Purpose

Good empirical research depends on judgment: whether a question matters, whether a proposed
comparison is informative, whether a measure represents the intended concept, whether the available
data support the target population and period, and whether an interpretation is warranted by the
evidence. These skills are written around those decisions.

The empirical center of the collection is political science. Its main orientation is contemporary
quantitative research, including causal inference in the potential-outcomes tradition, but it does not
assume that every worthwhile study is causal. Descriptive, measurement, interpretive, and
theory-developing work should be judged by the questions they actually ask.

Several principles run across the research skills:

- Begin with the political phenomenon and the scholarly problem, not a preferred method or software
  package.
- Read the relevant literature before declaring a contribution. Search both Chinese- and
  English-language scholarship when the subject requires it, and verify important claims in the
  underlying work.
- Treat institutional knowledge, case knowledge, measurement, sampling, and data construction as part
  of research design.
- State causal targets and identifying comparisons precisely. Do not require a DAG or an SCM framing
  when the study proceeds in another causal-inference tradition.
- Let weak data, failed diagnostics, and contrary findings change the design or claim.
- Treat feasibility and likely informativeness as matters for reasoned assessment. Formal power or
  simulation belongs only where the design and assumptions make it meaningful.
- Keep statistical computing subordinate to the estimand, comparison, measurement, and evidence.
- Write with the restraint of a scholar: distinguish what is established, suggested, uncertain, and
  not identified.

The skills do not form a compulsory pipeline. Each owns a distinct research task and can be used on
its own. A project may return to the same skill several times as its question, evidence, and argument
develop.

## Install

Clone the repository:

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
cd ai4ss-skills
```

### Codex

```bash
codex plugin marketplace add /path/to/ai4ss-skills
codex plugin add ai4ss-skills@ai4ss-skills-local
```

The Codex manifest is [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json). The repository-local
marketplace entry is [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json).

### Claude Code

```bash
claude plugin marketplace add /path/to/ai4ss-skills
claude plugin install ai4ss-skills@ai4ss-skills-local
```

The Claude Code manifest and marketplace entry are under [`.claude-plugin/`](.claude-plugin/).

### Individual skills

Where a runtime accepts directory-format skills directly, copy or symlink the selected
`skills/<skill-name>/` directory into that runtime's skill directory. The canonical source is always
[`skills/`](skills/); `.codex/skills` and `.agents/skills` are repository-local symlinks, not duplicate
source trees.

## Research skills

### Developing a study

| Skill | Research task |
|---|---|
| [`research-starter`](skills/research-starter/SKILL.md) | Develop a topic, empirical pattern, policy change, source collection, or dataset into a consequential research problem. |
| [`literature-matrix`](skills/literature-matrix/SKILL.md) | Find, verify, read, compare, and synthesize current and foundational Chinese- and English-language scholarship. |
| [`study-design-builder`](skills/study-design-builder/SKILL.md) | Develop a defensible empirical design from the question, theory, institutional setting, and available evidence. |
| [`public-data-sources`](skills/public-data-sources/SKILL.md) | Locate and assess public data by construct, population, unit, coverage, comparability, access, and provenance. |
| [`research-data-builder`](skills/research-data-builder/SKILL.md) | Construct analytical data whose sample, links, variables, and missingness correspond to the inquiry. |

### Analyzing and judging evidence

| Skill | Research task |
|---|---|
| [`research-analysis-runner`](skills/research-analysis-runner/SKILL.md) | Conduct empirical analysis iteratively, using descriptive evidence, estimation, diagnostics, and sensitivity to revise the interpretation. |
| [`analysis-explainer`](skills/analysis-explainer/SKILL.md) | Explain statistical results in terms of the research question, quantities, comparisons, uncertainty, and limits. |
| [`methods-reviewer`](skills/methods-reviewer/SKILL.md) | Reconstruct a study's inferential argument, identify decisive vulnerabilities, run targeted checks, and propose feasible repairs. |
| [`did-expert`](skills/did-expert/SKILL.md) | Evaluate identification and inference in difference-in-differences and related panel designs. |

### Writing, revision, and presentation

| Skill | Research task |
|---|---|
| [`academic-writing-scaffold`](skills/academic-writing-scaffold/SKILL.md) | Develop and revise a political-science argument and working prose in light of the evidence. |
| [`reviewer-response`](skills/reviewer-response/SKILL.md) | Treat peer criticism as a further round of research and revise the study and working response accordingly. |
| [`top-journal-figures`](skills/top-journal-figures/SKILL.md) | Develop empirical figures that make the relevant comparison, magnitude, uncertainty, and limitations visible. |
| [`latex-tables`](skills/latex-tables/SKILL.md) | Construct honest, readable tables whose rows and columns express a substantive comparison. |
| [`research-slides-builder`](skills/research-slides-builder/SKILL.md) | Develop a research talk whose argument and evidence can be followed and criticized by a live audience. |

### Specialized data and computing support

| Skill | Use |
|---|---|
| [`codebook-parse`](skills/codebook-parse/SKILL.md) | Parse survey data and codebooks into DDI-oriented metadata. |
| [`cleaning-contract`](skills/cleaning-contract/SKILL.md) | Declare survey recoding and cleaning decisions before transformation. |
| [`cleaning-execute`](skills/cleaning-execute/SKILL.md) | Apply a declared survey-cleaning contract and retain the resulting audit information. |
| [`r-performance`](skills/r-performance/SKILL.md) | Diagnose and improve R performance when computation is the bottleneck. |
| [`sjtu-hpc`](skills/sjtu-hpc/SKILL.md) | Work with SJTU HPC, Slurm, transfer, and cluster jobs. |

The repository also includes [`codex`](skills/codex/SKILL.md) and
[`linear-issue`](skills/linear-issue/SKILL.md) as development utilities. They are not part of the
empirical-research core.

## Using the skills

Invoke the skill that owns the present intellectual task and give it the actual research materials.
For example:

```text
Use $research-starter to develop this policy change into a research problem and identify the
strongest rival explanations.

Use $literature-matrix to find and synthesize the current Chinese- and English-language scholarship
on this question, including disagreements in theory, measurement, and design.

Use $did-expert to assess the estimand, comparison groups, treatment timing, identifying assumptions,
diagnostics, and interpretation in this study.
```

The useful result is not a generic checklist. It is a research judgment grounded in the materials at
hand: a revised question, a better comparison, a measurement decision, an account of conflicting
evidence, a narrower claim, or a clearer argument.

## Scope and limits

These skills can improve the quality and discipline of research work, but they cannot establish that
an empirical claim is true. In particular, they do not replace close reading, knowledge of the case,
inspection of the data, ethical review, or responsibility for the final argument.

Method-specific guidance is necessarily design-specific. The collection currently includes a deep
DID skill. Instrumental variables, regression discontinuity, experiments, surveys, networks, spatial
analysis, and other designs should receive their own specialist treatment rather than being compressed
into a generic methods checklist.

This repository also contains experimental DSL, evaluation, and harness code developed in related
projects. Those systems are separate from the intellectual content of the skills. `.aiss` declarations,
workflow gates, manifests, routing, and approval logic are not prerequisites for using or extending the
research skills.

## Development

### Source layout

- Every installable skill lives under `skills/<skill-name>/`.
- `skills/` is the only source tree. Do not add top-level `*.skill` archives or duplicate skill
  directories under runtime-specific paths.
- A skill's `SKILL.md` states its research task and judgment. Supporting references should add
  substantive or methodological depth, not another control system.
- Keep skill names stable unless a deliberate repository-wide change is required.

### Writing and revising skills

A research skill should:

1. begin from a recognizable scholarly problem;
2. explain what evidence must be inspected and why;
3. identify the consequential judgments, assumptions, and alternatives;
4. show how findings can revise the question, design, measure, analysis, or claim;
5. use the language of empirical social science rather than software orchestration; and
6. keep computing guidance as thin as the research task permits.

Do not place harness concerns inside a skill. Routing, approval, cross-skill handoffs, schemas,
validators, run manifests, and researcher-confirmation mechanics belong to the surrounding system when
such a system is needed.

### Checks

After changing skills or plugin metadata, run:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/validate_claude_plugin.py
```

The experimental DSL and harness have their own tests. Run those only when changing those subsystems;
they are not acceptance criteria for the scholarly content of a skill.

## Repository map

| Path | Purpose |
|---|---|
| [`skills/`](skills/) | Canonical source for installable skills |
| [`.codex-plugin/`](.codex-plugin/) | Codex plugin manifest |
| [`.claude-plugin/`](.claude-plugin/) | Claude Code plugin manifest and marketplace |
| [`docs/`](docs/) | Background, evaluation, and experimental subsystem documentation |
| [`dsl/`](dsl/) | Experimental `.aiss` language implementation |
| [`scripts/`](scripts/) | Plugin checks and experimental subsystem utilities |
| [`references/`](references/) | External standards and reference material used by selected skills or subsystems |

## Cite

```bibtex
@software{ai4ss_skills_2026,
  author    = {Zheng, Siyao},
  title     = {ai4ss-skills: Research Skills for Empirical Social Science},
  year      = {2026},
  url       = {https://github.com/SiyaoZheng/ai4ss-skills},
  note      = {Released at AI for Social Science (AI4SS) Online Lecture Series}
}
```

## License

GPL-3.0. Derivative works must carry the same license.

Exception: `skills/codex/` is based on
[@davila7](https://github.com/davila7)'s original Codex skill and retains its MIT license in
[`skills/codex/LICENSE`](skills/codex/LICENSE).
