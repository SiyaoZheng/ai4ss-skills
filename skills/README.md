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

Current count: 22 installable skills.

Research-factory skills share one runtime contract: durable semantic state lives
in `.aiss` declarations, runtime facts are appended as `.aiss` `event`
declarations, and `python3 dsl/scripts/aiss.py state <file>` projects the
current state-machine view. `goal-cli` remains the external watchdog, timer,
lock owner, and heartbeat executor; skills should record observations and
handoffs, not take over process supervision.

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
| `inspect-agent-eval` | Evaluation |
| `latex-tables` | Reporting |
| `literature-matrix` | Research workflow |
| `methods-reviewer` | Research workflow |
| `public-data-sources` | Research workflow |
| `r-performance` | Compute |
| `research-analysis-runner` | Research workflow |
| `research-data-builder` | Research workflow |
| `research-slides-builder` | Research workflow |
| `research-starter` | Research workflow |
| `reviewer-response` | Research workflow |
| `sjtu-hpc` | Compute |
| `study-design-builder` | Research workflow |
| `top-journal-figures` | Research workflow |
