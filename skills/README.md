# Skills

This directory is the canonical source tree for every installable AI4SS skill.

Each skill lives at:

```text
skills/<skill-name>/SKILL.md
```

Optional skill-local support files stay inside the same directory:

```text
skills/<skill-name>/
├── SKILL.md
├── agents/
├── assets/
├── examples/
├── references/
└── scripts/
```

Compatibility entrypoints:

- `.codex/skills` is a symlink to `../skills`.
- `.agents/skills` is a symlink to `../skills`.

Do not create a second source tree under `.codex/skills`, `.agents/skills`, or
top-level `*.skill` archives. If a skill needs to be packaged for a specific
runtime, generate that package from this directory.

## Skill Index

| Skill | Area |
|-------|------|
| `academic-writing-scaffold` | Research workflow |
| `analysis-explainer` | Reporting |
| `cleaning-contract` | Survey data |
| `cleaning-execute` | Survey data |
| `codebook-parse` | Survey data |
| `codex` | Tooling |
| `did-expert` | Methods |
| `latex-tables` | Reporting |
| `linear-issue` | Tooling |
| `literature-matrix` | Research workflow |
| `methods-reviewer` | Research workflow |
| `r-performance` | Compute |
| `research-analysis-runner` | Research workflow |
| `research-data-builder` | Research workflow |
| `research-slides-builder` | Research workflow |
| `research-starter` | Research workflow |
| `reviewer-response` | Research workflow |
| `sjtu-hpc` | Compute |
| `study-design-builder` | Research workflow |
