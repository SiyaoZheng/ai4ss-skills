# Stateless AutoChecklist Contract

## Input Boundary

The reviewer may inspect only these explicit inputs:

- manuscript file
- checklist Markdown or structured checklist JSON
- CLI config values
- optional reader evidence JSON
- optional `.aiss` path used only as metadata for downstream handoff

Conversation history, memory, old review files, and unstated project knowledge
are not evidence. The runner records `conversation_context_used=false` in every
manifest.

## Snapshot Schema

`review_state.json` is a disposable snapshot, not durable research-factory
state. It contains:

- `schema`: `ai4ss.manuscript_review_state.v0.1`
- `review_id`: hash of manuscript hash, checklist hash, and config hash
- `manifest`: paths, byte counts, hashes, config, and truncation status
- `summary`: item counts and `next_skill_route`
- `suite_summary`: counts by suite code
- `items`: one row per checklist item with status and route

## Status Reducer

Use these statuses only:

| Status | Meaning |
|---|---|
| `PASS` | The explicit input evidence satisfies the item. |
| `FAIL` | The item is absent, unclear, contradicted, or not defensible. |
| `NEEDS_EVIDENCE` | The item was selected but no scorer/evidence was run. |
| `REQUIRES_READER` | The item is an `(R)` reader-test item without supplied reader evidence. |
| `ERROR` | The runner could not evaluate the item because the tool call failed. |

For AutoChecklist output, map `yes` to `PASS` and `no` to `FAIL`. Keep the
reasoning as `llm_observation`; do not convert it into source-grounded evidence
unless the manuscript span is explicitly quoted or cited by a later repair step.

## Reader Evidence

Reader evidence is optional JSON keyed by checklist item id:

```json
{
  "INTRO-004": {
    "status": "PASS",
    "reader": "reader-a",
    "note": "Reader identified the hook and main puzzle after two paragraphs."
  }
}
```

Only `PASS` and `FAIL` are accepted for reader evidence. Missing `(R)` items stay
`REQUIRES_READER`.

## Route Map

Default route by suite:

| Suite | Route |
|---|---|
| `RQ` | `study-design-builder` |
| `TITLE`, `ABS`, `INTRO`, `CONC`, `APP`, `STY`, `FMT`, `REV`, `FINAL` | `academic-writing-scaffold` |
| `LIT`, `CITE` | `literature-matrix` |
| `DATA` | `research-data-builder` |
| `ID` | `methods-reviewer` |
| `RES` | `analysis-explainer` |
| `TAB` | `latex-tables` |
| `FIG` | `top-journal-figures` |

When several failures exist, prioritize design and evidence failures before
style and final-readiness failures: `DATA`, `ID`, `RES`, `TAB`, `FIG`, `LIT`,
`CITE`, `RQ`, `ABS`, `INTRO`, `CONC`, `TITLE`, `APP`, `STY`, `FMT`, `REV`,
`FINAL`.

## Full-Auto Handling

In automatic harnesses, do not block on reader tests. Report the reader queue,
route fixable manuscript failures first, and set `next_skill_route=none` only
when no automated failure remains.
