# AI4SS Research Workspace Contract

Every research-factory project should use one workspace root:

```text
/workspace/
  Makefile
  .ai4ss/
    research_model.aiss
    checks/
    handoffs/
    scratch/
  data/
    raw/
    intermediate/
    processed/
  scripts/
  output/
    tables/
    figures/
    models/
    logs/
  paper/
```

This document is the single source of truth for research-factory paths. Skill
files should reference it rather than repeating the full directory tree.

## Canonical Paths

- `Makefile` is the only orchestration entrypoint. Agents should edit source
  files and run `make <target>`, not run pipeline stages directly.
- `.ai4ss/research_model.aiss` is the only durable AI4SS workflow-state file.
  It stores route, MIDA, source, artifact, empirical, check, decision, claim,
  event, and handoff declarations.
  - Use `python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` to
    inspect the deterministic state-machine projection.
  - Use `python3 dsl/scripts/aiss.py transition .ai4ss/research_model.aiss
    --event '<json>'` to preview or append reducer events.
  - `event` declarations record runtime facts such as skill starts,
    completions, failures, heartbeat observations, and watchdog recovery facts.
    They do not replace semantic `route`, `mida`, `decision`, evidence, check,
    artifact, or claim declarations.
  - `goal-cli` owns external watchdog behavior, timers, locks, heartbeats, and
    process recovery. A research workspace may reference those observations in
    `.aiss` events, but must not make watchdog state a separate workflow-state
    file.
- `.ai4ss/checks/` stores validation reports such as
  `ai4ss_check_report.txt`.
- `.ai4ss/handoffs/` stores optional machine-readable handoff packets when a
  chat-visible handoff is not enough.
- `.ai4ss/scratch/` stores non-canonical skill projections or temporary
  planning notes. Scratch files must not become downstream workflow state.
- `data/raw/` stores acquired source data and source metadata.
- `scripts/` stores all data, analysis, table, figure, and paper build code.
- `paper/` stores manuscript source files and the final PDF.

## Generated Paths

These paths are derived outputs and must be regenerated through `make`:

- `data/intermediate/`
- `data/processed/`
- `output/tables/`
- `output/figures/`
- `output/models/`
- `output/logs/`
- `paper/*.pdf`
- LaTeX auxiliary files under `paper/`

Do not directly patch, write, or move files into those paths. Edit `Makefile`,
`scripts/`, `paper/*.tex`, `data/raw/`, or `.ai4ss/research_model.aiss`, then
run the relevant Make target.

## Forbidden Legacy Layouts

- Do not write workflow state to `docs/research_model.aiss`.
- Do not create root-level `research_model.aiss`.
- Do not use `outputs/`; use `output/`.
- Do not use `output/audit/`; put audit logs, row-count reports, and diagnostics
  in `output/logs/`, with durable declarations in `.ai4ss/research_model.aiss`.
- Do not use `data/interim/` or `data/analysis/`; use `data/intermediate/` and
  `data/processed/`.
- Do not create detached CSV/Markdown sidecars as workflow state. If the state
  matters across skills, declare it in `.ai4ss/research_model.aiss` and point to
  generated files from that object.

## Make Targets

The standard targets are:

- `make dirs`
- `make data`
- `make analysis`
- `make tables`
- `make figures`
- `make paper`
- `make check`
- `make all`

`make all` must build the data pipeline, analysis artifacts, tables, figures,
and `paper/full_draft.pdf` from a clean workspace.
