# Skills

This directory is the canonical source for every installable AI4SS skill. The empirical center of the
collection is quantitative social science, especially political science.

Each skill lives at:

```text
skills/<skill-name>/SKILL.md
```

A skill may also contain:

```text
skills/<skill-name>/
├── SKILL.md
├── agents/
├── assets/
├── examples/
├── references/
└── scripts/
```

These supporting directories are optional. References should deepen the substantive or methodological
judgment of the skill. Scripts are appropriate when the task genuinely requires computation; they are
not a substitute for research reasoning.

## Research orientation

The core skills are written from the standpoint of an empirical political scientist. They begin with
questions, theories, institutions, measures, comparisons, and evidence. They do not assume that every
study is causal, but they encourage precise causal questions and contemporary identification strategies
where those are warranted.

The skills are distinct and composable rather than stages in a compulsory workflow. No skill should
contain routing, approval, handoff, or researcher-confirmation mechanics. Those concerns belong to an
external harness when one is used. Likewise, `.aiss`, schemas, gates, and run manifests are not required
parts of a research skill.

## Skill index

### Empirical research

| Skill | Responsibility |
|---|---|
| [`research-starter`](research-starter/SKILL.md) | Research problem, theoretical stakes, rival explanations, and initial empirical possibilities |
| [`literature-matrix`](literature-matrix/SKILL.md) | Current and foundational Chinese- and English-language literature discovery, verification, comparison, and synthesis |
| [`study-design-builder`](study-design-builder/SKILL.md) | Inferential purpose, measurement, comparison, analysis strategy, feasibility, and design revision |
| [`public-data-sources`](public-data-sources/SKILL.md) | Public-data discovery and assessment by construct, population, unit, coverage, access, and provenance |
| [`research-data-builder`](research-data-builder/SKILL.md) | Sample construction, linkage, operationalization, missingness, measurement, and analytical data |
| [`research-analysis-runner`](research-analysis-runner/SKILL.md) | Descriptive analysis, estimation, diagnostics, sensitivity, and revision of the empirical interpretation |
| [`analysis-explainer`](analysis-explainer/SKILL.md) | Substantive interpretation of statistical quantities, comparisons, uncertainty, and conflicting results |
| [`methods-reviewer`](methods-reviewer/SKILL.md) | Independent methodological reconstruction, decisive criticism, targeted reanalysis, and feasible repair |
| [`did-expert`](did-expert/SKILL.md) | Difference-in-differences estimands, comparisons, assumptions, estimators, diagnostics, and sensitivity |
| [`academic-writing-scaffold`](academic-writing-scaffold/SKILL.md) | Central point, argument structure, working prose, claim discipline, and substantive revision |
| [`reviewer-response`](reviewer-response/SKILL.md) | Research revision under peer criticism and evidence-based disagreement |
| [`top-journal-figures`](top-journal-figures/SKILL.md) | Empirical figures as transparent visual arguments |
| [`latex-tables`](latex-tables/SKILL.md) | Honest and readable empirical tables |
| [`research-slides-builder`](research-slides-builder/SKILL.md) | Research talks organized for live scholarly scrutiny |

### Survey data

| Skill | Responsibility |
|---|---|
| [`codebook-parse`](codebook-parse/SKILL.md) | Survey and codebook parsing into DDI-oriented metadata |
| [`cleaning-contract`](cleaning-contract/SKILL.md) | Declared survey recoding and cleaning decisions |
| [`cleaning-execute`](cleaning-execute/SKILL.md) | Execution of a declared cleaning contract |

### Computing and repository utilities

| Skill | Responsibility |
|---|---|
| [`r-performance`](r-performance/SKILL.md) | R profiling, performance diagnosis, and parallelization |
| [`sjtu-hpc`](sjtu-hpc/SKILL.md) | SJTU HPC, Slurm, transfer, and cluster jobs |
| [`codex`](codex/SKILL.md) | Codex CLI delegation for coding work |
| [`linear-issue`](linear-issue/SKILL.md) | Repository work tracking in Linear |

## Editing rules

- Edit the source under `skills/`, not `.codex/skills` or `.agents/skills`; both are symlinks to this
  directory.
- Preserve existing skill names unless a repository-wide change has been agreed.
- Use scholarly language. Avoid generic AI voice, software-architecture metaphors, and formal fields
  that do not improve the research judgment.
- Keep method-specific depth in specialist skills. Do not flatten DID or future IV and RD guidance into
  a generic design checklist.
- Keep the computing layer thin unless software behavior itself changes the inference.

After changing a skill, verify the plugin manifests from the repository root:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/validate_claude_plugin.py
```
