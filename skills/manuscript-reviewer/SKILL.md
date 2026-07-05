---
name: manuscript-reviewer
description: >
  Stateless AutoChecklist-based manuscript review skill for AI4SS paper drafts.
  Use when a draft, PDF, title/abstract/introduction, or full manuscript needs
  TDD-style checklist review, fail-first issue routing, reader-test separation,
  or a context-independent review snapshot. Triggers: "manuscript review",
  "paper checklist", "审稿 skill", "论文审查", "TDD checklist", "AutoChecklist",
  "投稿前审查", "fail-first review".
---

# Manuscript Reviewer

Run a fixed paper-writing checklist against a manuscript as a context-sealed
review snapshot, then route failures to the right AI4SS repair skill.

## Stateless Rule

This skill must not use chat history, memory, or unstated project context as
evidence. Every run starts from explicit input files, computes hashes for the
manuscript, checklist, and scoring config, and writes a fresh `review_state.json`.
Prior review outputs may be compared by the user, but they are never loaded as
state for a new verdict.

## AutoChecklist Boundary

AutoChecklist is a CLI/package backend, not an AI4SS skill. Use it only as the
scorer for fixed checklist items. Do not let it generate or mutate the DP16276
checklist. Treat `(R)` reader-test items as a separate queue unless explicit
reader evidence is supplied.

## Methodology Foundation

This skill sits at the MIDA `Diagnose` and `Report` boundary. It does not decide
whether the empirical design is valid; it checks whether the manuscript makes
the research question, data, identification, results, contribution, and limits
readable and defensible. In a research-factory workspace, findings should be
converted into `.aiss` `check` or `decision` declarations by the downstream skill.

## .aiss State Machine

When `.ai4ss/research_model.aiss` is provided, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before choosing
or returning the fail-first `next_skill_route`. Starts, completions, failures,
and watchdog heartbeat observations should be recorded as `.aiss` `event`
declarations or returned as deterministic `aiss.py transition --event ...`
fragments. Events do not replace semantic updates: checklist failures and
repair routes must still become context-sealed review output and, when inside
the research factory, downstream `.aiss` `check` or `decision` declarations.

## Workflow Contract

- Upstream inputs: manuscript file, fixed checklist file or structured checklist
  JSON, optional `.ai4ss/research_model.aiss` object, optional reader-test
  evidence JSON, target journal or draft-stage notes.
- Produces: sealed input manifest, parsed checklist inventory, AutoChecklist
  observations, fail-first review report, reader-test queue, suite summaries,
  and repair routes.
- Handoff fields: `review_id`, `manuscript_sha256`, `checklist_sha256`,
  `config_sha256`, `suite_code`, `item_id`, `verification_tag`, `status`,
  `evidence_status`, `reasoning`, `severity`, `repair_hint`,
  `ai4ss_model_path`, `check`, `decision`, `next_skill_route`.
- Downstream routes: `study-design-builder`, `public-data-sources`,
  `research-data-builder`, `research-analysis-runner`, `methods-reviewer`,
  `analysis-explainer`, `latex-tables`, `top-journal-figures`,
  `literature-matrix`, `academic-writing-scaffold`, `reviewer-response`, or
  `none`.

## Routing Boundaries

Use this skill for manuscript-facing review: title, abstract, introduction,
literature positioning, data description, identification exposition, results
presentation, tables, figures, style, formatting, and final-readiness checks.
Do not use it as the first source-acquisition, data-building, estimator-choice,
or proof-of-identification tool. Route those failures to the relevant specialist
skill after the checklist has localized the issue.

## Workflow

```text
Step -1: Seal the run
-> Read only explicit manuscript/checklist/config inputs.
-> Compute the manifest hashes before scoring.
-> Record conversation_context_used=false.

Step 0: Parse the checklist
-> Use scripts/parse_dp16276_checklist.py for the DP16276 TDD checklist.
-> Preserve item ids, suite codes, and verification tags `(M)`, `(H)`, `(R)`.

Step 1: Score
-> Run `manuscript-reviewer review`; it calls `autochecklist score` by default
   with `--scorer item`, `--provider openai`, `--api-format chat`, and explicit
   `--input-key input --target-key target`. The AutoChecklist CLI uses PackyAPI
   Fable via `PACKYCODE_CODEX_KEY` as its LLM backend.
-> Full-manuscript runs are the default final-review path. Use
   `--scorer-mode batch` only as an explicit cheap drafting shortcut for small
   scoped suite checks.
-> Use `--mode scaffold` only to verify parsing and produce an unscored queue.

Step 2: Reduce
-> Map scorer YES/NO to PASS/FAIL for `(M)` and `(H)` items.
-> Keep `(R)` as REQUIRES_READER unless reader evidence names the item.
-> Summarize failures by suite and choose the strongest `next_skill_route`.

Step 3: Repair handoff
-> Fix highest-priority FAIL items first.
-> Convert research-factory findings into `.aiss` checks or decisions through
   the downstream skill; `review_state.json` itself is not durable workflow state.
```

## Output Shape

Return the review id, manifest hashes, total PASS/FAIL/REQUIRES_READER counts,
top fail-first items, reader-test queue, chosen `next_skill_route`, and commands
run. For each failure, include item id, suite, assertion, evidence status,
AutoChecklist reasoning when available, and the repair skill.

## Script Utilities

- Parse a Markdown checklist:
  `manuscript-reviewer parse <checklist.md> -o <checklist.json> --expect-items 302`
- Produce a context-sealed scaffold without model calls:
  `manuscript-reviewer review --manuscript <draft.md> --checklist <checklist.md> --outdir <review-dir> --scaffold`
- Run full AutoChecklist CLI scoring with PackyAPI Fable as the backend:
  `manuscript-reviewer review --manuscript <draft.md> --checklist <checklist.json> --outdir <review-dir>`
- Run a cheap drafting probe only when explicitly requested:
  `manuscript-reviewer review --manuscript <draft.md> --checklist <checklist.json> --outdir <review-dir> --suites TITLE,ABS --scorer-mode batch`
- Check local CLI and PackyAPI readiness:
  `manuscript-reviewer doctor`

## Reference Files

| File | Content | Read when |
|---|---|---|
| [stateless-autochecklist-contract.md](references/stateless-autochecklist-contract.md) | Review-state schema, status reducer, reader-test handling, and route map | Running or extending the reviewer |
| [autochecklist-adapter.md](references/autochecklist-adapter.md) | AutoChecklist dependency boundary, prompt policy, and installation notes | Changing scorer behavior |
