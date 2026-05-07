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

**[📦 Skills](#-skills) · [⚡ Install](#-installation) · [📊 Benchmarks](#-benchmarks) · [🗺️ Roadmap](#-roadmap) · [🤝 Contributing](#-contributing) · [📄 Cite](#-cite)**

</div>

---

## 🆕 News

| Date | Update |
|------|--------|
| 2026-05 | `cleaning-contract` and `cleaning-execute` released — full DDI 3-stage cleaning harness (declare → execute → audit) |
| 2026-05 | `cleaning-contract` eval results: **100%** with-skill vs **53%** without-skill on 3 real PI datasets |
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

Evaluated on real PI datasets. Each (eval × config) executed once.

### `codebook-parse` (variable classification, missing code detection, label reconciliation)

| Dataset | Variables | Challenge | With skill | Without skill |
|---------|-----------|-----------|:----------:|:-------------:|
| CGSS 2021 | 695 | Positive missing codes (Word questionnaire) | **7/7** | 2/7 |
| Dickson 2014 | 560 | Positive missing codes | **6/7** | 3/7 |
| ABS Wave 5 | — | DTA/SAV label discrepancy | **6/7** | 0/7 |
| **Overall** | | | **90.5%** | **23.8%** |

### `cleaning-contract` (recoding declaration, missing-code traps, weight assignment)

| Dataset | Challenge | With skill | Without skill |
|---------|-----------|:----------:|:-------------:|
| CGSS 2021 | Shared recodes, scale reversal, weight assignment | **6/6** | 1/6 |
| Dickson 2014 | Positive missing trap (A3A `9=doctorate` vs Q23 `9=refused`) | **6/6** | 4/6 |
| ABS Wave 5 | Structural inapplicables (China `-1`), universe filter | **4/4** | 3/4 |
| **Overall** | | **100%** | **53%** |

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

> **Skill format**: most `*.skill` files in this repo are **zip archives**
> (one exception: `codex.skill` is a directory). The install commands below
> handle both — they unzip archives and copy directories. After install,
> `~/.claude/skills/<skill-name>/SKILL.md` should exist.

### One-liner (Claude Code)

```bash
git clone https://github.com/SiyaoZheng/ai4ss-skills.git
mkdir -p ~/.claude/skills
for s in ai4ss-skills/*.skill; do
  name=$(basename "$s" .skill)
  if [ -d "$s" ]; then
    cp -r "$s" ~/.claude/skills/"$name"          # directory-format skill
  else
    rm -rf ~/.claude/skills/"$name"
    unzip -q "$s" -d ~/.claude/skills/            # zip-format skill (extracts as <name>/)
  fi
done
```

Verify: open Claude Code, type `/` — skills appear in the autocomplete list.

### Selective install

```bash
mkdir -p ~/.claude/skills

# Zip-format skills (most of them):
unzip -q ai4ss-skills/codebook-parse.skill    -d ~/.claude/skills/
unzip -q ai4ss-skills/cleaning-contract.skill -d ~/.claude/skills/
unzip -q ai4ss-skills/cleaning-execute.skill  -d ~/.claude/skills/
unzip -q ai4ss-skills/latex-tables.skill      -d ~/.claude/skills/
unzip -q ai4ss-skills/r-performance.skill     -d ~/.claude/skills/
unzip -q ai4ss-skills/analysis-explainer.skill -d ~/.claude/skills/

# Directory-format skill:
cp -r ai4ss-skills/codex.skill ~/.claude/skills/codex
```

### Cursor

Cursor expects flat `.md` rules. Extract just the SKILL.md from each zip:

```bash
mkdir -p .cursor/rules
for s in latex-tables r-performance; do
  unzip -p ai4ss-skills/${s}.skill ${s}/SKILL.md > .cursor/rules/${s}.md
done
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
| `cleaning-contract` | ✅ Released | Declare recoding decisions in YAML before touching data |
| `cleaning-execute` | ✅ Released | Execute contract → clean CSV + R script + audit log |
| `regression-ready` | ⬜ Stretch | Validate clean data against analysis plan |
| `codebook-diff` | ⬜ Stretch | Diff two survey waves, surface variable renames and scale changes |

---

## 🤝 Contributing

Skills are just Markdown + YAML. If you work with CFPS, ANES, ESS, or any other survey series and have domain traps that LLMs routinely miss — a skill is the right place to encode that knowledge.

1. Fork this repo
2. Create `your-skill-name.skill/SKILL.md` following the format above
3. Add eval evidence (even informal benchmarks help)
4. Open a PR

See [SKILL.md format](#-skill-format) for the full spec.

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
