# Inspect Agent-Runtime DDI Harness Eval: Round 1

This is the first completed official Inspect AI agent-runtime evaluation for
the AI4SS DDI survey-cleaning harness. It is not a subprocess smoke test: the
run used an Inspect `Task`, a multi-sample dataset, an Inspect SWE Codex CLI
solver, a Docker sandbox, a deterministic scorer, and an Inspect `.eval` log.

## Run

- Task: `evals/ddi_harness/task.py@ddi_harness`
- Model provider: `openai-api/deepseek/deepseek-v4-pro`
- Solver: `inspect_swe/codex_cli`
- Solver model config: `gpt-5.3-codex`
- Skills passed to the solver: `skills/codebook-parse`, `skills/cleaning-contract`, `skills/cleaning-execute`
- Sandbox: Docker, `evals/ddi_harness/Dockerfile`
- Scorer: `ddi_harness_oracle`
- Formal log: `/tmp/ai4ss-inspect-logs/official-round1c/2026-07-04T16-36-19-00-00_ddi-harness_RwMPE7TRQD5ZKYKFcEn7fa.eval`
- Summary JSON: `docs/evals/ddi-harness/inspect-round1-summary.json`

Command:

```bash
PATH=/tmp/ai4ss-inspect-venv/bin:$PATH \
DEEPSEEK_BASE_URL=https://api.deepseek.com \
python3 scripts/run_agent_runtime_harness_eval.py \
  --runtime codex \
  --retry-log /tmp/ai4ss-inspect-logs/official-round1b/2026-07-04T16-16-09-00-00_ddi-harness_RwMPE7TRQD5ZKYKFcEn7fa.eval \
  --log-dir /tmp/ai4ss-inspect-logs/official-round1c \
  --summary-json /tmp/ai4ss-inspect-logs/official-round1c/summary.json \
  -- --max-samples 1
```

The source retry log was a real 3-sample run that had been interrupted after
2/3 completed samples. `inspect eval-retry` resumed the incomplete official log
and produced a successful completed log.

## Result

| Sample | What It Checks | Score |
|---|---|---:|
| `positive_missing_and_execution_order` | Positive missing code before reverse coding, valid 9 in another variable, weight normalization, post-rename derivation | 1.0 |
| `range_missing_and_valid_sentinel` | Range-style missing value, valid sentinel-looking code, region universe filter, weight normalization | 1.0 |
| `derive_after_rename_and_drop` | Filtering before derivation, missing treatment, rename and reverse-code order, dropped audit field | 1.0 |

Overall:

- Inspect status: `success`
- Total samples: 3
- Completed samples: 3
- Scored samples: 3
- Unscored samples: 0
- Accuracy: 1.0
- Token usage: 2,653,165 total tokens; 126,192 input; 50,557 output; 2,476,416 cache-read; 23,665 reasoning.

## Interpretation

This result proves that, for the three controlled DDI fixtures in
`evals/ddi_harness/task.py`, a live Codex CLI agent runtime can use the three
AI4SS DDI skills inside an official Inspect SWE sandbox and produce artifacts
that satisfy the deterministic oracle. The oracle verifies that:

- `fixture-cleaning.R` exists and reruns successfully inside the sandbox.
- `fixture-clean.csv` matches the expected rows and column order.
- `ddi-metadata.yaml` contains a non-empty `cleaning_contract`.
- `processing_events` includes a `CleaningOperation` event referencing
  `fixture-clean.csv`.

The result does not prove broad DDI coverage beyond these fixtures. Future
rounds should add harder cases, including labelled-file ingestion, multi-wave
metadata, DDI category schemes reused across variables, range missingness with
open intervals, and deliberately ambiguous coding choices that must be
auto-inferred, audited, and disclosed rather than guessed silently.

## Iteration From This Round

Before the completed run, the previous official log was `cancelled` after 2/3
samples. The runner was updated to support official `inspect eval-retry` and to
summarize Inspect sample IDs correctly from log reductions. No DDI skill logic
change was required after the completed run because all three current samples
passed the deterministic scorer.
