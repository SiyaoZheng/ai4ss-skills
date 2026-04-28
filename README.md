<div align="center">

# ai4ss-skills

### Agent Skills for Social Science Research

**Stop re-explaining your data to your AI assistant.**
Install once. Works automatically. Survives context resets.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![R](https://img.shields.io/badge/R-%3E%3D4.1-276DC3?logo=r&logoColor=white)](https://www.r-project.org/)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-3776AB?logo=python&logoColor=white)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-blueviolet?logo=anthropic)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Cursor](https://img.shields.io/badge/Cursor-compatible-000000?logo=cursor)](https://cursor.com)
[![Stars](https://img.shields.io/github/stars/SiyaoZheng/ai4ss-skills?style=social)](https://github.com/SiyaoZheng/ai4ss-skills/stargazers)

**[📦 Skills](#-skills) · [⚡ Install](#-installation) · [📊 Benchmarks](#-benchmarks) · [🗺️ Roadmap](#️-roadmap) · [🤝 Contributing](#-contributing) · [📄 Cite](#-cite)**

</div>

---

## 🆕 News

| Date | Update |
|------|--------|
| 2026-04 | `codebook-parse`, `latex-tables`, `analysis-explainer`, `r-performance`, `codex` released |
| 2026-04 | Eval results published: **90.5%** accuracy on real PI datasets vs **23.8%** without skills |
| 2026-04 | Launched at AI for Social Science (AI4SS) Online Lecture Series |

---

## 🔥 What This Fixes

You're cleaning CGSS 2021. Without a skill, your AI treats `9 = 无回答` as missing on *every variable* — including `A3A` where `9 = doctorate`.
You lose 3–7% of valid observations. Silently. The regression runs. The paper is wrong.

**With `codebook-parse` installed:**

```
You: parse the codebook for CGSS 2021
Claude: [auto-loads codebook-parse skill]
        Reading cgss2021.dta via haven::read_dta()...
        695 variables detected.
        ⚠ Variable A3A — val_labels() shows 9 = doctorate (valid), not missing.
        ⚠ Variable K6  — val_labels() shows 9 = professional worker (valid), not missing.
        ✓ Variable D13 — val_labels() shows 9 = 无回答 (missing). Encoded as missing.
        Writing ddi-metadata.yaml with 695 variable entries...
        Done. 23 positive-code traps flagged for your review.
```

The skill catches the trap before it reaches your regression.

---

## 💡 Why Skills?

Skills are **reusable knowledge packs** — not system prompts.

| | System Prompt | Agent Skill |
|--|--------------|-------------|
| Persistence | Lost on context reset | Survives every session |
| Loading | Always-on, burns tokens | On-demand, auto-triggered |
| Structure | Prose instructions | Decision trees + code templates |
| Portability | Locked to one tool | Claude Code, Cursor, Windsurf, Aider |
| Sharing | Copy-paste | `git clone` + one script |

Think of them as tiny domain experts you install once and call automatically.

---

## 📦 Skills

| Skill | What it does | Trigger |
|-------|-------------|---------|
| 📋 [`codebook-parse`](#-codebook-parse) | Parse `.dta`/`.sav`/PDF questionnaires → DDI-compliant YAML metadata | *"parse this codebook"* |
| 📊 [`latex-tables`](#-latex-tables) | Generate journal-ready LaTeX regression tables | *"make a LaTeX table"* |
| 📝 [`analysis-explainer`](#-analysis-explainer) | Turn statistical output into clean technical documentation | *"explain these results"* |
| ⚡ [`r-performance`](#-r-performance) | Profile and optimize slow R code for HPC clusters | *"this R code is too slow"* |
| 🤖 [`codex`](#-codex) | Delegate tasks to OpenAI Codex CLI for a second opinion | `codex review this file` |

---

## 📊 Benchmarks

Evaluated on real PI datasets. Tasks: variable classification, missing code detection, label reconciliation.

| Dataset | Variables | Challenge | With skill | Without skill |
|---------|-----------|-----------|:----------:|:-------------:|
| CGSS 2021 | 695 | Positive missing codes (Word questionnaire) | **7/7** | 2/7 |
| Dickson 2014 | 560 | Positive missing codes | **6/7** | 3/7 |
| ABS Wave 5 | — | DTA/SAV label discrepancy | **6/7** | 0/7 |
| **Overall** | | | **90.5%** | **23.8%** |

---

## 🔍 Skill Details

### 📋 `codebook-parse`

Reads survey data files (`.dta`, `.sav`, `.sas7bdat`) and questionnaire documents (PDF, Word) and writes a single DDI Lifecycle 3.3–compliant SSOT: `ddi-metadata.yaml`.

**What it handles that plain LLMs get wrong:**

- **Positive missing codes** — `9 = 无回答` on one variable, `9 = doctorate` on another; classified per-variable via `val_labels()`, never globally
- **Structurally inapplicable variables** — comparative surveys (e.g., ABS Wave 5: questions about institutions that don't exist in China)
- **Format discrepancies** — `.dta` vs `.sav` label conflicts in the same dataset

---

### 📊 `latex-tables`

Generates booktabs-style LaTeX tables for regression output. Follows major journal style guides out of the box.

- `\toprule` / `\midrule` / `\bottomrule` automatically
- AEA, APSR, QJE format support
- Significance stars, standard error parentheses, decimal alignment

---

### 📝 `analysis-explainer`

Converts raw statistical output into technical documentation for collaborators.

- Records method parameters (seed, iterations, convergence criteria)
- Embeds figure references from the project
- Academic prose, not AI-generated filler

---

### ⚡ `r-performance`

R performance diagnosis and optimization for researchers hitting compute walls.

- `profvis`-based bottleneck identification
- Vectorization, pre-allocation, parallelization decision tree
- Slurm / SGE / PBS cluster configuration templates

---

### 🤖 `codex`

Delegates tasks to [OpenAI Codex CLI](https://github.com/openai/codex) for a second opinion or sandbox execution.

> Based on [@davila7](https://github.com/davila7/claude-code-templates)'s original codex skill (MIT).

| Mode | What happens |
|------|-------------|
| `codex review` | Read-only sandbox analysis |
| `codex edit` | Auto-applies changes in workspace-write sandbox |
| `codex resume` | Continues previous session |

**Requires:** Codex CLI installed and credentials configured.

---

## ⚡ Installation

### One-liner (Claude Code)

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
mkdir -p ~/.claude/skills
for d in ai4ss-skills/*.skill; do cp -r "$d" ~/.claude/skills/"$(basename "$d" .skill)"; done
```

Verify: open Claude Code, type `/` — skills appear in the autocomplete list.

### Selective install

```bash
mkdir -p ~/.claude/skills
cp -r ai4ss-skills/codebook-parse.skill  ~/.claude/skills/codebook-parse
cp -r ai4ss-skills/latex-tables.skill    ~/.claude/skills/latex-tables
cp -r ai4ss-skills/r-performance.skill   ~/.claude/skills/r-performance
cp -r ai4ss-skills/analysis-explainer.skill ~/.claude/skills/analysis-explainer
cp -r ai4ss-skills/codex.skill           ~/.claude/skills/codex
```

### Cursor

```bash
mkdir -p .cursor/rules
cp ai4ss-skills/latex-tables.skill   .cursor/rules/latex-tables.md
cp ai4ss-skills/r-performance.skill  .cursor/rules/r-performance.md
```

### Other tools

| Tool | Install path |
|------|-------------|
| Windsurf | `~/.windsurf/skills/` |
| Cline | `~/.cline/skills/` |
| Aider | `aider --read path/to/SKILL.md` |

---

## 🛠️ Skill Format

```
codebook-parse.skill/
├── SKILL.md          # YAML frontmatter + instructions
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

The `description` field controls auto-loading. Make it specific — the AI matches on semantic similarity.

**Reference external files:** `@references/ddi-ssot-schema.md`
**Accept arguments:** `$ARGUMENTS`

**Global vs project-level:**

| | `~/.claude/skills/` | `.claude/skills/` |
|--|--------------------|--------------------|
| Scope | All projects | This project only |
| Use for | General-purpose skills | Project-specific rules |

---

## 🗺️ Roadmap

| Skill | Status | Description |
|-------|--------|-------------|
| `codebook-parse` | ✅ Released | |
| `latex-tables` | ✅ Released | |
| `analysis-explainer` | ✅ Released | |
| `r-performance` | ✅ Released | |
| `codex` | ✅ Released | |
| `cleaning-contract` | 🔵 Planned | Declare recoding decisions in YAML before touching data |
| `cleaning-execute` | 🔵 Planned | Execute contract → clean CSV + R script + audit log |
| `regression-ready` | ⬜ Stretch | Validate clean data against analysis plan |
| `codebook-diff` | ⬜ Stretch | Diff two survey waves, surface variable renames and scale changes |

---

## 🤝 Contributing

Skills are just Markdown + YAML. If you work with CFPS, ANES, ESS, or any other survey series and have domain traps that LLMs routinely miss — a skill is the right place to encode that knowledge.

1. Fork this repo
2. Create `your-skill-name.skill/SKILL.md` following the format above
3. Add eval evidence (even informal benchmarks help)
4. Open a PR

See [SKILL.md format](#️-skill-format) for the full spec.

---

## ❓ FAQ

**The skill isn't triggering automatically.**
Add more trigger phrases to the `description` field. The AI loads skills based on semantic similarity to your message.

**How do I invoke a skill manually?**
Type `/skill-name` in Claude Code. Example: `/latex-tables`.

**Skills vs AGENTS.md?**
AGENTS.md is always loaded, scoped to one project. Skills are loaded on demand, reusable across projects.

---

## 📄 Cite

If you use these skills in research, please cite:

```bibtex
@software{ai4ss_skills_2026,
  author    = {Zheng, Siyao},
  title     = {ai4ss-skills: Agent Skills for Social Science Research},
  year      = {2026},
  url       = {https://github.com/SiyaoZheng/ai4ss-skills},
  note      = {Released at AI for Social Science (AI4SS) Online Lecture Series}
}
```

---

## License

GPL-3.0. Derivative works must carry the same license.

Exception: `codex.skill/` is based on [@davila7](https://github.com/davila7)'s work and retains its original MIT license (see `codex.skill/LICENSE`).

---

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=SiyaoZheng/ai4ss-skills&type=Date)](https://star-history.com/#SiyaoZheng/ai4ss-skills&Date)

<sub>Released at AI4SS Online Lecture · 2026</sub>

</div>
