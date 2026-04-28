<div align="center">

# ai4ss-skills

**Agent Skills for Social Science Research**

Give your AI coding assistant domain expertise in survey data, statistical analysis, and academic writing — without re-explaining yourself every session.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-blueviolet)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Cursor](https://img.shields.io/badge/Cursor-compatible-black)](https://cursor.com)
[![Stars](https://img.shields.io/github/stars/SiyaoZheng/ai4ss-skills?style=social)](https://github.com/SiyaoZheng/ai4ss-skills)

</div>

---

## What this looks like in practice

You're cleaning CGSS 2021. Without a skill, Claude treats `9 = 无回答` on every variable as missing — including variables where `9 = doctorate`. You fix it by hand. Again.

With `codebook-parse` installed:

```
You: parse the codebook for CGSS 2021
Claude: [auto-loads codebook-parse skill]
        Reading cgss2021.dta via haven::read_dta()...
        695 variables detected.
        WARNING: Variable A3A — val_labels() shows 9 = doctorate (valid), not missing.
                 Variable K6  — val_labels() shows 9 = professional worker (valid), not missing.
                 Variable D13 — val_labels() shows 9 = 无回答 (missing). Encoded as missing.
        Writing ddi-metadata.yaml with 695 variable entries...
        Done. 23 positive-code traps flagged for your review.
```

A plain LLM would silently drop 3-7% of your valid observations. The skill catches the trap before it reaches your regression.

---

## What are Agent Skills?

Skills are **reusable knowledge packs** that give AI assistants specialized capabilities. Unlike system prompts pasted once and forgotten, skills are:

- **Loaded on demand** — the AI decides when the skill is relevant
- **Structured** — decision trees, checklists, code templates, not prose
- **Portable** — same skill works in Claude Code, Cursor, Windsurf, and more

Think of them as tiny domain experts you install once and call automatically.

---

## Skills in this repo

| Skill | What it does | Trigger phrase |
|-------|-------------|----------------|
| 📋 [`codebook-parse`](#codebook-parse) | Parse `.dta`/`.sav`/PDF questionnaires → DDI-compliant YAML metadata | *"parse this codebook"* |
| 📊 [`latex-tables`](#latex-tables) | Generate journal-ready LaTeX regression tables | *"make a LaTeX table"* |
| 📝 [`analysis-explainer`](#analysis-explainer) | Turn statistical output into clean technical documentation | *"explain these results"* |
| ⚡ [`r-performance`](#r-performance) | Profile and optimize slow R code for HPC clusters | *"this R code is too slow"* |
| 🤖 [`codex`](#codex) | Delegate tasks to OpenAI Codex CLI for a second opinion | `codex review this file` |

---

## Skill details

### `codebook-parse`

Reads survey data files (`.dta`, `.sav`, `.sas7bdat`) and questionnaire documents (PDF, Word) and writes a single DDI Lifecycle 3.3–compliant SSOT: `ddi-metadata.yaml`.

**What it handles that plain LLMs get wrong:**

- Positive missing codes in Chinese surveys — `9 = 无回答` on one variable, `9 = doctorate` on another; classified per-variable via `val_labels()`, never globally
- Structurally inapplicable variables in comparative surveys (e.g., ABS Wave 5: questions about institutions that don't exist in China)
- `.dta` vs `.sav` label discrepancies in the same dataset

**Eval results (real PI data):**

| Dataset | With skill | Without skill |
|---------|-----------|---------------|
| CGSS 2021 (695 vars, Word questionnaire) | 7/7 | 2/7 |
| Dickson 2014 (560 vars, positive missing codes) | 6/7 | 3/7 |
| ABS Wave 5 (DTA/SAV discrepancy) | 6/7 | 0/7 |
| **Overall** | **90.5%** | **23.8%** |

---

### `latex-tables`

Generates booktabs-style LaTeX tables for regression output. Follows major journal style guides out of the box.

- `\toprule` / `\midrule` / `\bottomrule` automatically
- AEA, APSR, QJE format support
- Significance stars, standard error parentheses, decimal alignment

---

### `analysis-explainer`

Converts raw statistical output into technical documentation for collaborators.

- Records method parameters (seed, iterations, convergence criteria)
- Embeds figure references from the project
- Academic prose, not AI-generated filler

---

### `r-performance`

R performance diagnosis and optimization for researchers hitting compute walls.

- `profvis`-based bottleneck identification
- Vectorization, pre-allocation, parallelization decision tree
- Slurm / SGE / PBS cluster configuration templates

---

### `codex`

Delegates tasks to [OpenAI Codex CLI](https://github.com/openai/codex) (GPT-5.3-codex) for a second opinion or sandbox execution.

> Based on [@davila7](https://github.com/davila7/claude-code-templates)'s original codex skill (MIT).

| Mode | What happens |
|------|-------------|
| `codex review` | Read-only sandbox analysis |
| `codex edit` | Auto-applies changes in workspace-write sandbox |
| `codex resume` | Continues previous session |

**Requires:** Codex CLI installed and credentials configured.

---

## Installation

### One-liner (Claude Code)

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
mkdir -p ~/.claude/skills
for d in ai4ss-skills/*.skill; do cp -r "$d" ~/.claude/skills/"$(basename "$d" .skill)"; done
```

Verify: open Claude Code, type `/` — skills should appear in the list.

### Manual (selective install)

```bash
mkdir -p ~/.claude/skills

# Install only what you need
cp -r ai4ss-skills/codebook-parse.skill ~/.claude/skills/codebook-parse
cp -r ai4ss-skills/latex-tables.skill   ~/.claude/skills/latex-tables
cp -r ai4ss-skills/r-performance.skill  ~/.claude/skills/r-performance
cp -r ai4ss-skills/analysis-explainer.skill ~/.claude/skills/analysis-explainer
cp -r ai4ss-skills/codex.skill          ~/.claude/skills/codex
```

### Cursor

Place skill content in your project's `.cursor/rules/` directory:

```bash
mkdir -p .cursor/rules
cp ai4ss-skills/latex-tables.skill .cursor/rules/latex-tables.md
cp ai4ss-skills/r-performance.skill .cursor/rules/r-performance.md
```

### Other tools

| Tool | Path |
|------|------|
| Windsurf | `~/.windsurf/skills/` |
| Cline | `~/.cline/skills/` |
| Aider | `aider --read path/to/SKILL.md` |

---

## Skill format

Each skill is a directory containing `SKILL.md` with YAML frontmatter and a Markdown body:

```
codebook-parse.skill/
├── SKILL.md          # frontmatter + instructions
└── references/       # optional supporting docs
    ├── ddi-ssot-schema.md
    └── ...
```

```yaml
---
name: codebook-parse
description: |
  Parse survey codebooks into DDI-compliant YAML metadata.
  Use when: codebook, .dta, .sav, questionnaire, DDI, survey cleaning
---
```

The `description` field controls when the AI auto-loads the skill. Make it specific.

**Reference external files:**
```markdown
Full schema at @references/ddi-ssot-schema.md
```

**Accept arguments:**
```markdown
Target file: $ARGUMENTS
```

---

## Roadmap

| Skill | Status |
|-------|--------|
| `codebook-parse` | Released |
| `latex-tables` | Released |
| `analysis-explainer` | Released |
| `r-performance` | Released |
| `codex` | Released |
| `cleaning-contract` | Planned — declare recoding decisions in YAML before touching data |
| `cleaning-execute` | Planned — execute contract → clean CSV + R script + audit log |
| `regression-ready` | Stretch — validate clean data against analysis plan |
| `codebook-diff` | Stretch — diff two survey waves, surface variable renames and scale changes |

---

## FAQ

**The skill isn't triggering automatically.**
Add more trigger phrases to the `description` field. The AI loads skills based on semantic match.

**How do I invoke a skill manually?**
`/skill-name` in Claude Code. Example: `/latex-tables`.

**Global vs project-level skills?**

| | `~/.claude/skills/` | `.claude/skills/` |
|---|---|---|
| Scope | All projects | This project only |
| Use for | General-purpose skills | Project-specific rules |

**Skills vs AGENTS.md?**
AGENTS.md is always loaded and scoped to one project. Skills are loaded on demand and reusable across projects.

---

## License

GPL-3.0. Derivative works must carry the same license.

Exception: `codex.skill/` is based on [@davila7](https://github.com/davila7)'s work and retains its original MIT license (see `codex.skill/LICENSE`).

---

<div align="center">
  <sub>Released at AI4SS Online Lecture · 2026</sub>
</div>
