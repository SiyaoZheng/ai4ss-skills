# AGENTS.md

This repository is the development home for AI4SS skills.

## Skill layout

- All installable skills live under `skills/<skill-name>/`.
- `skills/` is the only source tree. Do not add top-level `*.skill` archives or duplicate skill
  directories.
- `.codex/skills` and `.agents/skills` remain symlinks to `../skills`; edit the source, not the links.
- Keep existing skill names and the top-level skill architecture unless a repository-wide change has
  been explicitly requested.

## Domain

The collection is written for empirical social scientists, especially political scientists. The core
skills should embody the practice of contemporary quantitative research: formulating consequential
questions, reading literatures, developing designs, finding and constructing data, analyzing evidence,
reviewing methods, writing, revising, and presenting research.

Research judgment comes before software procedure. Attend to the political setting, relevant actors and
institutions, theoretical mechanism, rival explanations, measurement, sampling, comparison, estimand,
uncertainty, scope, and the limits of the available evidence.

Contemporary causal inference is encouraged where the question is causal, principally in the
potential-outcomes and research-design traditions. Do not require DAGs or an SCM formulation. Do not
force descriptive, measurement, interpretive, or theory-developing work into a causal template.

## Writing skills

- Write in the restrained language of a scholar. Avoid generic AI voice, motivational filler,
  engineering metaphors, and product-management terminology.
- Organize instructions around the inquiry and the judgments needed to answer it, not around abstract
  stages or required fields.
- Use real research materials. Inspect sources, data, code, results, drafts, or reviews before drawing
  conclusions.
- Let contrary evidence, weak measurement, poor comparison support, and failed diagnostics revise the
  question, design, analysis, or claim.
- Literature work must search current and foundational public Chinese- and English-language sources
  when relevant, and verify consequential claims in the underlying work.
- In observational research, treat likely informativeness and feasibility as a reasoned assessment.
  Require formal power or simulation only when the design and assumptions make it defensible.
- Keep R and other computing guidance thin. Explain implementation only where it changes the validity,
  interpretation, or reproducibility of the research.
- Preserve deep method-specific knowledge in specialist skills such as `did-expert`. Future IV, RD, and
  other specialist skills should receive the same treatment rather than being folded into a generic
  methods checklist.

## Division of responsibility

Each skill owns a distinct substantive task. Skills may be used together, but they do not constitute a
compulsory workflow and should not contain cross-skill routing or handoff instructions.

Approval, researcher confirmation, orchestration, run state, and cross-skill control belong to an
external harness. `.aiss` declarations, schemas, gates, validators, manifests, and workflow state do
not belong in the substantive instructions of a research skill. The repository may contain
experimental DSL, harness, and evaluation code, but those subsystems are separate from the
intellectual content of the skills.

Specialized mechanical utilities, including the DDI cleaning skills, may use structured contracts when
the task itself requires them. Do not generalize those contracts into the architecture of the research
skills.

## Validation

After changing skills or plugin metadata, run:

```bash
python3 scripts/validate_codex_plugin.py
python3 scripts/validate_claude_plugin.py
```

Check that every referenced skill-local file exists and that Markdown links resolve. Run DSL, harness,
or evaluation tests only when changing those subsystems; they are not acceptance criteria for scholarly
skill content.

## Boundaries

- Do not claim that a skill establishes empirical truth or identification validity.
- Do not invent literature, data, results, institutional facts, or completed revisions.
- Do not present deterministic structural checks as expert evaluation.
- Preserve uncertainty, contrary evidence, reasonable disagreement, and unresolved research choices.
