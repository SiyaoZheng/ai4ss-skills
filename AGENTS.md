# AGENTS.md

This repository is the development home for AI4SS skills.

## Skill Layout

- Legacy released skills may live as top-level `*.skill` zip-package files or
  directory-format skills such as `codex.skill/` and `sjtu-hpc.skill/`.
- The AI4SS research-factory Codex skillpack lives in `.codex/skills/`.
- `.agents/skills` should remain a symlink to `../.codex/skills`; edit the
  `.codex/skills` source, not a duplicate copy.
- The research-factory skillpack uses `.aiss` as the local research-model
  extension. Upstream `aiss_*` names are script names only.

## Research Factory Spine

Maintain the research-factory skills as one workflow:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/check ->
literature/data gates -> analysis readiness -> analysis manifest ->
bounded claim handoff
```

The methodology spine is:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

AI assistance must not directly write final manuscript prose, final reviewer
response prose, or final scholarly claims. Skills should create inspectable
research objects, ledgers, manifests, diagnostics, and author decision points.

## Validation

Run these checks after changing the research-factory skillpack:

```bash
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss
python3 scripts/validate_literature_evidence_compile.py .codex/skills/literature-matrix/examples/valid_literature_matrix.csv
python3 scripts/validate_analysis_readiness.py .codex/skills/research-analysis-runner/examples/valid_analysis_readiness_check.csv
python3 scripts/run_factory_level_eval.py --clean
```

The `.aiss` validators use the unified v0.4 DSL entrypoint in this repo:
`dsl/scripts/aiss.py compile`, `aiss.py lint`, and `aiss.py run`.

## Boundaries

- Do not turn research-factory skills into paper-writing skills.
- Do not use the former local research-model extension for local artifacts.
- Do not present deterministic structural evaluations as live double-blind
  evidence.
- Keep AI-use ledger rows updated when AI changes externally shared teaching or
  research-workflow artifacts.
