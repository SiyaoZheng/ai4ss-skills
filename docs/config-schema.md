# goal.toml Schema

`goal.toml` defines one thing-centered goal. The runtime state belongs under
`.goal/`; the finished thing is the only success standard.

## Top-Level Fields

```toml
name = "artifact-goal"
state_dir = ".goal"
runs_dir = ".goal/runs"

[project]
root = "."
```

- `name`: stable goal name written to state and heartbeat files.
- `state_dir`: directory for `state.json`, `heartbeat.json`, and the lock.
- `runs_dir`: per-heartbeat logs, prompts, verdicts, schemas, and reports.
- `[project].root`: optional project root. Relative paths in the rest of the
  config resolve from this root; it defaults to the directory containing
  `goal.toml`.

## Artifact

```toml
[artifact]
path = "output/artifact.pdf"
copy_as = "full_paper.pdf"
```

- `path`: finished thing produced by the rebuild command.
- `copy_as`: optional filename used when passing the artifact to tik.

## Producer

```toml
[producer]
command = "make all"
```

The producer must rebuild the finished thing from source. Completion is never
accepted from source edits alone.

## Tik

Tik has three public modes.

```toml
[tik]
provider = "oracle"
command = "python3 scripts/tik.py"
```

Use `oracle` for deterministic scripts, tests, metrics, or other machine
checks. The command receives:

- `GOAL_ARTIFACT`
- `GOAL_TIK_PROMPT`
- `GOAL_RUN_DIR`

```toml
[tik]
provider = "agent"
model = "gpt-5.5-pro"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096
store = false
```

Use `agent` for model-based artifact critique. The configured artifact is copied
to a temporary directory before critique, then uploaded to the OpenAI Responses
API as an `input_file`.

```toml
[tik]
provider = "codex_file"
# model = "optional model override"
timeout_seconds = 1800
max_file_size_bytes = 25000000
```

Use `codex_file` for Codex-based artifact critique without Responses file
upload. The configured artifact is copied into a temporary directory, Codex is
launched with that directory as its workspace under a read-only sandbox, with no
project source directories added to the session, and with ephemeral session
state.
If the configured tik prompt starts with a slash skill such as `/apsr-review`,
goal-cli keeps that slash command as the first stdin line.

Tik output must contain a JSON object with the configured verdict fields:

```toml
[tik.verdict]
ready_field = "artifact_ready"
blockers_field = "blocking_objections"
required_fields = ["artifact_ready", "blocking_objections"]
fingerprint_fields = ["blocking_objections", "central_bottleneck"]
```

The default verdict shape is:

```json
{
  "artifact_ready": false,
  "central_bottleneck": "one sentence",
  "blocking_objections": [],
  "required_next_artifact_changes": [],
  "current_artifact_sha256": "optional current artifact sha256"
}
```

Freshness fields are optional but enforced when present. If a verdict says
`review_matches_current_pdf = false`, or if `current_pdf_sha256`,
`current_artifact_sha256`, `reviewed_pdf_sha256`, or
`reviewed_artifact_sha256` does not match the runtime artifact hash, the run
records `blocked_stale_tik_review` and asks for a fresh tik pass before tok.

Each tik pass writes `tik.md` in the run directory. That Markdown ledger is the
machine handoff to tok: it includes artifact metadata, the raw tik memo, and the
parsed tik verdict JSON. Tok normally receives the review as a file attachment
through `{tik_review_path}` rather than inline prompt text, so long reviews do
not inflate the `/goal` prompt.

## Tok

The production Tok mode is `codex_goal`.

```toml
[tok]
provider = "codex_goal"
write_dirs = ["src", "data"]
run_cwd = "."
runtime_write_dirs = ["output", "build", "logs"]
sandbox = "workspace-write"
codex_features = ["goals"]
```

`codex_goal` launches `codex exec` with `/goal`, `--enable goals`, and the tok
report schema. Tok treats every pass as the last pass: read `tik.md`, edit only
`write_dirs`, make the strongest source repair, and stop.
`write_dirs` must stay inside the project root and must not overlap `.git`,
state directories, run directories, generated directories, or the canonical
artifact.

`run_cwd` controls the working directory passed to `codex exec -C`. It defaults
to the first `write_dirs` entry for backward compatibility. Set it to `"."`
when the producer or diagnostics must be launched from the project root.

`runtime_write_dirs` is intentionally separate from `write_dirs`. It grants the
tok process access to directories that may be updated by commands it runs, such
as `output`, `build`, or `logs`, without declaring those directories as manual
source-edit scopes. Runtime write dirs may overlap generated directories and
the artifact output directory, but they must stay inside the project root and
must not be the project root, `.git`, the goal config, or goal state/run
directories.

Tok reports must match this JSON shape:

```json
{
  "source_change_possible": true,
  "revision_strategy": "one sentence",
  "sources_changed": ["path"],
  "expected_artifact_visible_improvement": ["visible change in next artifact"],
  "remaining_artifact_bottleneck": "one sentence"
}
```

If no source change is possible, tok reports
`"source_change_possible": false`; the runtime records
`blocked_no_source_change_possible`.

## no-mistakes Gate

`goal-cli` can use `kunchenguid/no-mistakes` as the Git gate for heartbeat
checkpoints.

```toml
[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
branch_prefix = "goal-cli"
intent = "Rebuild, review, repair source, and keep Git clean."
skip_steps = []
timeout_seconds = 0
checkpoint_message = "goal-cli checkpoint: {goal_name} heartbeat {iteration} {phase}"
```

- `enabled`: defaults to `true`. Set it to `false` only for isolated tests or
  diagnostics that intentionally run outside Git.
- `binary`: executable used for `no-mistakes`.
- `mode`: no-mistakes pipeline preset. Defaults to `lightspeed`, which passes
  `--skip review,test,document,lint,push,pr,ci`. `fast` skips only
  `push,pr,ci`. `full` runs no-mistakes without preset skips.
- `branch_prefix`: prefix for the feature branch created when the repo is on the
  default branch, because `no-mistakes axi run` refuses default branches.
- `intent`: optional text passed to `no-mistakes axi run --intent`. If omitted,
  goal-cli generates a thing-centered intent from the goal name.
- `skip_steps`: optional no-mistakes pipeline steps for `--skip`, such as
  `["test", "lint"]`. These are added to the selected `mode` preset.
- `timeout_seconds`: process timeout for `no-mistakes` commands; `0` means no
  timeout.
- `checkpoint_message`: Git commit message template. Available placeholders are
  `{goal_name}`, `{iteration}`, and `{phase}`.

When enabled, goal-cli prepares the repo before a non-dry-run heartbeat by ignoring
`.goal/` in `.git/info/exclude`, auto-branching if needed, and checkpointing
dirty project changes. After successful tok and completion heartbeats, it
checkpoints again, runs `no-mistakes init`, and then runs:

```bash
no-mistakes axi run --intent "<configured or generated intent>" --yes [--skip ...]
```

Missing Git setup, a missing no-mistakes binary, or a failed gate records
`blocked_no_mistakes_failed`.

If the heartbeat wall-clock budget is exhausted during no-mistakes preparation
or gating, the runtime records `budget_limited` with `next_action = "tik"` so a
later heartbeat can continue from file state.

## Observability

OpenTelemetry tracing is enabled by default and exports standard OTLP HTTP
traces. `goal-cli` only instruments runtime stages; collectors, storage, and
dashboards come from existing OpenTelemetry-compatible tools. If the configured
OTLP receiver is not reachable and no OTLP endpoint was explicitly set through
the environment, `goal-cli` writes local fallback traces to
`.goal/observability/traces.jsonl`. For collector-managed agent-side
observation, use `docs/otel-collector-file.yaml` with OpenTelemetry Collector
Contrib and read `.goal/observability/traces.json`.

```toml
[observability]
service_name = "goal-cli"
endpoint = "http://localhost:4318/v1/traces"
timeout_seconds = 5
```

- `enabled`: defaults to `true`.
- `service_name`: OpenTelemetry `service.name` resource attribute.
- `endpoint`: OTLP HTTP traces endpoint used when
  `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` and `OTEL_EXPORTER_OTLP_ENDPOINT` are not
  set.
- `timeout_seconds`: OTLP exporter timeout used when OpenTelemetry timeout env
  vars are not set.

Standard OpenTelemetry environment variables are respected. Set
`OTEL_TRACES_EXPORTER=none` or `OTEL_SDK_DISABLED=true` for isolated tests.
Environment-provided OTLP endpoints are treated as explicit operator intent and
are not replaced by the local JSONL fallback.

Emitted spans include:

- `goal_cli.heartbeat.run`
- `goal_cli.heartbeat`
- `goal_cli.producer`
- `goal_cli.artifact.load`
- `goal_cli.tik`
- `goal_cli.tok`
- `goal_cli.no_mistakes.prepare`
- `goal_cli.no_mistakes.gate`

## Prompt Placeholders

Tik prompts may use:

- `{goal_name}`
- `{artifact_path}`
- `{artifact_sha256}`
- `{producer_command}`

Tok prompts may use:

- `{goal_name}`
- `{producer_command}`
- `{artifact_path}`
- `{artifact_sha256}`
- `{tik_review_path}`
- `{writable_scopes}`
- `{runtime_writable_scopes}`
- `{tok_run_cwd}`
- `{run_dir}`

Runtime prompts must stay closed-system. They may describe the artifact,
producer, tik ledger, source boundaries, budgets, and operational
impossibilities. They must not include a person-facing approval, clarification,
or decision path.

## Safety

```toml
[safety]
generated_dirs = ["output", "build"]
max_blocker_repeats = 3
lock_stale_seconds = 21600
max_history_items = 50
```

- `generated_dirs`: protected generated outputs; tok write scopes cannot
  overlap them.
- `max_blocker_repeats`: repeated identical tik objections block the run.
- `lock_stale_seconds`: stale lock age.
- `max_history_items`: retained state history entries.

## Runtime States

State is stored in `.goal/state.json`; each run also writes heartbeat and
provider evidence under `.goal/runs/`.

| Status | Meaning |
| --- | --- |
| `active` | The goal can continue on a later heartbeat. |
| `complete` | The rebuilt artifact passed tik. |
| `blocked_producer_failed` | The producer command failed. |
| `blocked_artifact_missing` | The producer finished but `[artifact].path` was missing. |
| `blocked_tik_failed` | The tik provider failed before producing a memo. |
| `blocked_unparseable_tik` | Tik output did not contain the configured verdict JSON. |
| `blocked_stale_tik_review` | Tik reviewed a stale artifact hash or declared the review stale. |
| `blocked_tok_failed` | The tok provider failed or returned an invalid schema report. |
| `blocked_no_source_change_possible` | Tok reported that no source repair is possible. |
| `blocked_repeated_same_objection` | The configured blocker fingerprint repeated too many times. |
| `blocked_no_mistakes_failed` | Git setup, checkpointing, or no-mistakes gating failed. |
| `budget_limited` | The heartbeat wall-clock budget expired during no-mistakes work. |

## Setup Readiness

Run:

```bash
goal-cli doctor
```

Doctor is the static readiness gate for configured artifact execution. It
checks:

- config validity, prompt placeholders, closed-system prompt language, and
  writable-scope safety;
- artifact, state, and run directory creatability;
- configured producer command availability where the shell command is statically
  knowable;
- oracle tik command availability where applicable;
- Codex CLI availability;
- OpenTelemetry package availability and the runtime telemetry export plan
  (OTLP when reachable or explicitly environment-configured, local JSONL
  fallback otherwise);
- `codex exec` support for `--output-schema`, `--output-last-message`,
  `--enable`, `--add-dir`, `--sandbox`, and `--ephemeral` when
  `tik.provider = "codex_file"`;
- agent tik `openai` package and `OPENAI_API_KEY` readiness when
  `tik.provider = "agent"`.

The default summary reports `static_setup`. If it is ready, `goal-cli run` has
the local setup required to start the producer/tik/tok loop for the
finished thing.

For an opt-in tok smoke check:

```bash
goal-cli doctor --smoke-codex-goal
```

The smoke check starts a minimal internal Codex `/goal` in a temporary writable
directory and validates the schema-shaped tok report. It does not touch
project sources.

For `tik.provider = "codex_file"`, also run:

```bash
goal-cli doctor --smoke-codex-goal --smoke-codex-file-tik
```

The second smoke check copies a tiny temporary artifact into a single-file
Codex workspace, runs the same local-file tik adapter used at runtime, and
validates the configured tik verdict fields. `one_click_artifact_loop` is only
ready after all required smoke checks for the configured providers pass.

Clean up an interrupted heartbeat:

```bash
goal-cli cleanup
```

The cleanup command removes a stale heartbeat lock whose process is already
dead and marks a running heartbeat as interrupted. To also terminate orphan
goal-cli/Codex processes that still reference the current project, use:

```bash
goal-cli cleanup --kill-orphans
```

## Runtime Units

- `heartbeat`: one autonomous producer/tik/tok pass.
- `run`: one CLI invocation that executes exactly one heartbeat.
