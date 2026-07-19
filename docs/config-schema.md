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

Tik has five public modes.

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
provider = "checklist"
command = "python3 scripts/checklist_review.py"
```

Use `checklist` for command-backed checklist review providers. It has the same
command contract as `oracle`, but gives checklist-oriented tik output a distinct
provider type in ledgers, state, and multi-provider configurations.

```toml
[tik]
provider = "api"
# Defaults to claude-fable-5 on PackyAPI.
# model = "claude-fable-5"
# base_url = "https://www.packyapi.com/v1"
# Optional: inline a local SKILL.md before calling the API.
skill = "apsr-review"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096
store = false
```

Use `api` for API-based artifact critique. By default, this calls the
OpenAI-compatible PackyAPI endpoint with `claude-fable-5`. The current
implementation copies the configured artifact to a temporary directory before
critique, then uploads it through the Responses API as an `input_file`.

API credentials are resolved in this order:

- `PACKYAPI_API_KEY`, `PACKYCODE_CODEX_KEY`, then `OPENAI_API_KEY`;
- `~/.config/goal-cli/api.env` with one of those names;
- an explicit `GOAL_CLI_API_ENV_FILE` path, which replaces the default file.

`base_url` is optional. If omitted, goal-cli uses `PACKYAPI_BASE_URL`,
`OPENAI_BASE_URL`, or `https://www.packyapi.com/v1`.

When `skill` is set, goal-cli resolves it as either a direct path to a
`SKILL.md` file/directory or as a skill name under:

- `skills/<name>/SKILL.md` in the project root;
- `~/.codex/skills/<name>/SKILL.md`;
- `~/.agents/skills/<name>/SKILL.md`;
- `~/.claude/skills/<name>/SKILL.md`.

The resolved `SKILL.md` is inlined into the API text prompt. The API provider
does not execute slash commands, so prompts for `provider = "api"` must not
start with `/apsr-review` or any other slash skill.

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

```toml
[tik]
provider = "claude_code_file"
# model = "optional model override"
timeout_seconds = 1800
max_file_size_bytes = 25000000
```

Use `claude_code_file` for Claude Code-based artifact critique. The configured
artifact is copied into a temporary directory, `claude --print` is launched
with that directory as its working directory, with no project source
directories in the workspace, and with `Write`, `Edit`, `NotebookEdit`, and
`Bash` explicitly disallowed so the pass is read-only. The memo is extracted
from the `result` field of the `--output-format json` envelope.

### Multiple Tik Providers

Tik can run several providers in parallel. Keep shared prompt and verdict
schema under `[tik]`, then configure each provider with `[[tik.providers]]`:

```toml
[tik]
timeout_seconds = 1800
max_file_size_bytes = 25000000

[[tik.providers]]
label = "codex"
provider = "codex_file"
model = "optional model override"

[[tik.providers]]
label = "claude"
provider = "claude_code_file"
model = "optional model override"

[[tik.providers]]
label = "checklist"
provider = "checklist"
command = "python3 scripts/checklist_review.py"

[tik.prompt]
text = "Review only the finished thing at {artifact_path}."
```

Each provider inherits top-level tik defaults unless the provider table
overrides them. Supported override fields are the same as single-provider tik
fields: `provider`, `label`, `model`, `command`, `skill`, `base_url`, `binary`,
`engine`, `timeout`, `timeout_seconds`, `max_file_size_bytes`,
`max_output_tokens`, `store`, and `prompt`.

The heartbeat waits for every configured tik provider. If any provider fails,
returns unparseable JSON, or reviews the wrong artifact hash, the heartbeat
blocks before tok. If all providers return usable verdicts, goal-cli writes one
aggregate `tik.md` handoff for tok. The aggregate verdict is ready only when
every provider is ready; otherwise the provider review text is carried forward
as Markdown for tok.

For `codex_file` and `claude_code_file`, if the configured tik prompt starts
with a slash skill such as `/apsr-review`, goal-cli keeps that slash command as
the first stdin line for the reviewing CLI. For `api`, use `tik.skill` instead.

Tik output must contain a JSON object with the configured verdict fields:

```toml
[tik.verdict]
ready_field = "artifact_ready"
required_fields = ["artifact_ready"]
```

The default verdict shape is:

```json
{
  "artifact_ready": false
}
```

Freshness fields are optional but enforced when present. If a verdict says
`review_matches_current_pdf = false`, or if `current_pdf_sha256`,
`current_artifact_sha256`, `reviewed_pdf_sha256`, or
`reviewed_artifact_sha256` does not match the runtime artifact hash, the run
records `blocked_invalid_review_evidence` and asks for a fresh tik pass before
tok.

Each tik pass writes `tik.md` in the run directory. In single-provider mode,
that file contains the provider review with the control JSON stripped out. In
multi-provider mode, provider-specific ledgers are written beside it, and
`tik.md` contains the aggregate Markdown review text. The parsed JSON is private
runtime state in `tik_verdict.json`; it decides whether tok can run, but it is
not the tok handoff. Tok normally receives the Markdown review as a file
attachment through `{tik_review_path}` rather than inline prompt text, so long
reviews do not inflate the `/goal` prompt.

## Tok

Tok has three public modes: `codex_goal`, `codex_app_server`, and
`claude_code_goal`.

```toml
[tok]
provider = "codex_goal"
write_dirs = ["src", "data"]
run_cwd = "."
runtime_write_dirs = ["output", "build", "logs"]
sandbox = "workspace-write"
codex_features = ["goals"]
```

`codex_goal` launches `codex exec` with `/goal` and `--enable goals`. Tok treats
every pass as the last pass: read `tik.md`, use the tik review as the standard
to meet, edit source under `write_dirs`, and leave source ready for the next
artifact to answer the review's blocking objections.
`write_dirs` are the protocol and audit boundary for source edits, not a hard
OS sandbox guarantee when `run_cwd` or trusted sandbox modes grant broader local
authority. The runtime snapshots these directories before and after tok, records
the actual changed paths, and keeps the loop active if no source files changed.
`write_dirs` must stay inside the project root and must not overlap
`.git`, state directories, run directories, generated directories, or the
canonical artifact.

`run_cwd` controls the working directory passed to `codex exec -C`. It defaults
to the first `write_dirs` entry for backward compatibility. Set it to `"."`
when the producer or diagnostics must be launched from the project root.

```toml
[tok]
provider = "codex_app_server"
write_dirs = ["src", "data"]
run_cwd = "."
runtime_write_dirs = ["output", "build", "logs"]
sandbox = "workspace-write"
```

`codex_app_server` launches `codex app-server --stdio`, starts an ephemeral
thread, sets a real thread goal through `thread/goal/set`, and runs the work
pass through `turn/start`. The runtime waits for `turn/completed`, then writes
its own audit report to `tok_report.json`. It uses the same attachment
integrity check and source-change audit as `codex_goal`.

```toml
[tok]
provider = "claude_code_goal"
write_dirs = ["src", "data"]
run_cwd = "."
runtime_write_dirs = ["output", "build", "logs"]
sandbox = "workspace-write"
```

`claude_code_goal` launches `claude --print` and treats a successful JSON
envelope as provider completion; it does not request structured model output.
The runtime writes its own audit report to `tok_report.json`. The same
`write_dirs`, `run_cwd`, and `runtime_write_dirs` semantics apply: the working
directory is `run_cwd`, and every other write scope plus the run attachments
directory is granted through `--add-dir`.
`codex_features` only affects the `codex_goal` exec path; it is ignored for
`codex_app_server` and `claude_code_goal`.

The `sandbox` field maps onto Claude Code permissions:

| `sandbox` | Claude Code flags |
| --- | --- |
| `read-only` | `--disallowedTools Write,Edit,MultiEdit,NotebookEdit,Bash` |
| `workspace-write` | `--permission-mode acceptEdits --allowedTools Bash` |
| `danger-full-access` | `--dangerously-skip-permissions` |

Like Codex `workspace-write`, the mapping is a protocol boundary, not a hard OS
sandbox: `acceptEdits` auto-accepts file edits in the granted directories and
`Bash` runs unsandboxed commands. Source-diff and mutation files are audit
evidence, not goal-cli hard gates.

`runtime_write_dirs` is intentionally separate from `write_dirs`. It grants the
tok process access to directories that may be updated by commands it runs, such
as `output`, `build`, or `logs`, without declaring those directories as source
edit scopes. Runtime write dirs may overlap generated directories and the
artifact output directory, but they must stay inside the project root and must
not be the project root, `.git`, the goal config, or goal state/run directories.
Tok may run the producer command or other commands for source validation. If
those commands try to rewrite the configured artifact, the edit prohibition is
enforced by Codex/Claude hooks. goal-cli records before/after hashes in
`tok_artifact_provenance.json` and does not attempt restore logic.

`tok_report.json` is runtime-owned audit metadata, not model output. It keeps
this compatibility shape:

```json
{
  "source_change_possible": true,
  "revision_strategy": "one sentence",
  "expected_artifact_visible_improvement": ["visible change in next artifact"],
  "remaining_artifact_bottleneck": "one sentence"
}
```

Tok does not report changed file paths or whether source changes are possible.
The runtime writes the local evidence to
`tok_source_changes.json` and stores it in state as
`last_tok.actual_sources_changed`.

## Hard Gate Policy

goal-cli only hard-gates invalid review evidence: conditions where tok cannot
trust the producer/tik evidence it would act on:

- invalid configuration or setup validation failure;
- producer failure or missing configured artifact;
- tik provider failure, unparseable tik verdict, or stale tik review.

The following are deliberately not hard gates. goal-cli records them and then
keeps the heartbeat loop active:

- tok provider failure or timeout;
- tok writes outside declared source/runtime scopes;
- transient generated side effects under `runtime_write_dirs`;
- attempted artifact writes, which should be blocked by Codex/Claude hooks and
  are recorded by goal-cli if they occur;
- repeated tik objections;
- tok completing without source changes;
- no-mistakes setup, checkpoint, or review failure.

These conditions may matter to a project owner, but goal-cli intentionally does
not decide them. It does not escalate them, ask for judgment, or stop the loop.
If a project wants to enforce tok edit prohibitions, enforce them in
Codex/Claude hooks. goal-cli only stops on producer/tik evidence validity.

## no-mistakes Checkpoint

`goal-cli` can use `kunchenguid/no-mistakes` for heartbeat checkpoints.

```toml
[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
intent = "Rebuild, review, update source, and keep Git clean."
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
- `branch_prefix`: accepted for older configs but ignored. goal-cli is a
  single-person mainline workflow and does not create feature branches.
- `intent`: optional text passed to `no-mistakes axi run --intent`. If omitted,
  goal-cli generates a thing-centered intent from the goal name.
- `skip_steps`: optional no-mistakes pipeline steps for `--skip`, such as
  `["test", "lint"]`. These are added to the selected `mode` preset.
- `timeout_seconds`: process timeout for `no-mistakes` commands; `0` means no
  timeout.
- `checkpoint_message`: Git commit message template. Available placeholders are
  `{goal_name}`, `{iteration}`, and `{phase}`.

When enabled, goal-cli prepares the repo before a non-dry-run heartbeat by
ignoring `.goal/` in `.git/info/exclude` and checkpointing dirty project
changes on the current branch. After successful tok and completion heartbeats,
it checkpoints again. On non-default branches it then runs `no-mistakes init`
and:

```bash
no-mistakes axi run --intent "<configured or generated intent>" --yes [--skip ...]
```

On default branches such as `main` or `master`, goal-cli keeps the
single-person mainline branch, records `no_mistakes_default_branch_skipped`,
and does not invoke `no-mistakes axi run`, because no-mistakes refuses to
validate default branches and asks users to create a feature branch.

Missing Git setup, a missing no-mistakes binary, or a failed no-mistakes check
is recorded in `last_no_mistakes` and history, then ignored by the runtime
state machine. This is deliberate: no-mistakes evidence is useful, but it is
not a hard gate.

If the heartbeat wall-clock budget is exhausted during no-mistakes preparation
or checkpoint work, the runtime records the no-mistakes status in state/history
and keeps the heartbeat active.

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
- `goal_cli.no_mistakes.checkpoint`

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
- `max_blocker_repeats`: repeated identical tik objections are counted and
  marked as ignored; they do not block the run.
- `lock_stale_seconds`: stale lock age.
- `max_history_items`: retained state history entries.

## Runtime States

State is stored in `.goal/state.json`; each run also writes heartbeat and
provider evidence under `.goal/runs/`.

| Status | Meaning |
| --- | --- |
| `active` | The goal can continue on a later heartbeat. |
| `healthy` | The rebuilt artifact currently passes tik and waits for its next inspection. |
| `blocked` | The last bounded attempt could not proceed safely; perpetual mode will retry or reframe. |
| `stopped` | An operator explicitly stopped the perpetual goal; `resume` makes it due again. |
| `complete` | The rebuilt artifact passed tik. |
| `blocked_invalid_review_evidence` | Producer/tik evidence is missing, failed, unparseable, or stale, so tok cannot safely act on it. |

`healthy`, `blocked`, and `stopped` are perpetual-only states. In perpetual
mode an old `complete` checkpoint is migrated idempotently to `healthy`;
non-perpetual goals keep the existing terminal `complete` behavior.

Non-gating observations such as repeated blockers, no source changes, provider
failures, and no-mistakes failures remain in history, provenance files, and
`last_*` state fields while the status stays `active`.

## Perpetual Mode and Capability Leases

Perpetual execution is explicit opt-in. It keeps one substantive goal alive as
bounded heartbeats; it does not invent work after the artifact becomes healthy.

```toml
[perpetual]
enabled = true
substantive_goal = "Make the paper's measurement argument withstand the fixed reviewer objections."
healthy_interval_seconds = 21600
active_interval_seconds = 1800
provider_backoff_seconds = [300, 1800, 7200]
reframe_angles = [
  "repair the evidence chain",
  "revisit measurement or analysis",
  "improve reader-facing exposition",
]

[lease]
version = "paper-lease-v1"
allow_shell = true
allow_network = false
tools = ["Rscript"]

[[lease.rules]]
effect = "allow"
operations = ["create", "modify", "delete", "rename"]
paths = ["manuscript/**", "analysis/**"]

[[lease.rules]]
effect = "allow"
operations = ["create", "modify"]
paths = ["output/paper.pdf"]

[[lease.rules]]
effect = "deny"
operations = ["create", "modify", "delete", "rename"]
paths = [".github/**", "**/*checklist*", "**/*audit*"]
```

- `substantive_goal` defaults to the top-level goal `name`. Its exact text and
  the lease `version` are bound on the first perpetual run and cannot change
  during that run.
- `healthy_interval_seconds` defaults to 6 hours.
- `active_interval_seconds` defaults to 30 minutes for active and blocked work.
- `provider_backoff_seconds` defaults to 5 minutes, 30 minutes, and 2 hours,
  capped at the final value. A successful provider call resets the sequence.
- `reframe_angles` is a bounded list of substantive approaches. Provider
  failures retain the pending angle; a substantive blocked or zero-delta
  attempt consumes it and selects a different recent angle next time.
- `allow_shell`, `allow_network`, and `tools` are checked before a ToK provider
  starts. A missing tool or capability that cannot be contained fails closed.
- Lease rules use safe repository-relative paths or globs. Deny rules override
  allow rules. A rename requires both its source and destination to be
  authorized. If any mutation in a batch is unauthorized, none are applied.

Producer and command-backed tik also run from isolated copies in perpetual
mode. Authorized producer output passes through the same drift check, durable
journal, and repository lock as model edits. Command-tik file effects are
discarded. Existing dirty and untracked files are included in the isolated
baseline and are not overwritten when canonical content has drifted.

Operational evidence remains in the ordinary runtime state rather than a new
governance artifact:

- `goal_binding`: immutable substantive goal identity and lease version;
- `next_due_at` and `call_state`: scheduling and the last bounded call result;
- `attempt_supervisor`: bounded recent attempt evidence plus deterministic
  aggregate outcome and angle counts;
- `last_transaction`: stable attempt ID, mutation identities, and journal path;
- state `history`: recovery, stop/resume, and lifecycle events.

Use `goal-cli stop` to persistently stop without marking the goal complete.
`goal-cli resume` clears that operator stop and makes the next heartbeat due.
On restart, transaction recovery and state reconciliation run before any new
producer or provider inspection.

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
- oracle/checklist tik command availability where applicable;
- Codex CLI availability when `tok.provider = "codex_goal"`,
  `tok.provider = "codex_app_server"`, or `tik.provider = "codex_file"`;
- Claude Code CLI availability and `claude` flag support (`--print`,
  `--output-format`, `--disallowedTools`, `--model`, plus `--add-dir` and
  `--permission-mode` when `tok.provider =
  "claude_code_goal"`) when a Claude Code provider is configured;
- OpenTelemetry package availability and the runtime telemetry export plan
  (OTLP when reachable or explicitly environment-configured, local JSONL
  fallback otherwise);
- `codex exec` support for `--enable`, `--add-dir`, `--sandbox`, and
  `--skip-git-repo-check` when `tok.provider = "codex_goal"`, plus
  `--output-last-message` and `--ephemeral` when `tik.provider = "codex_file"`;
- `codex app-server --help` support for `--stdio` when `tok.provider =
  "codex_app_server"`;
- API tik `openai` package and API key readiness when `tik.provider = "api"`.

The default summary reports `static_setup`. If it is ready, `goal-cli run` has
the local setup required to start the producer/tik/tok loop for the
finished thing.

For an opt-in tok smoke check:

```bash
goal-cli doctor --smoke-codex-goal
```

The smoke check starts a minimal internal Codex `/goal` in a temporary writable
directory and asks it to create a temporary source file. It does not touch
project sources.

For `tok.provider = "codex_app_server"`, run the Codex app-server smoke
instead:

```bash
goal-cli doctor --smoke-codex-app-server
```

That smoke check uses `codex app-server --stdio`, creates an ephemeral thread,
sets a thread goal, starts a turn, and validates that a temporary source file is
created in a temporary workspace.

For `tok.provider = "claude_code_goal"`, run the Claude Code tok smoke instead:

```bash
goal-cli doctor --smoke-claude-code-goal
```

For `tik.provider = "codex_file"`, also pass `--smoke-codex-file-tik`; for
`tik.provider = "claude_code_file"`, pass `--smoke-claude-code-file-tik`.
Combine the tok and tik smoke flags that match the configured providers:

```bash
goal-cli doctor --smoke-codex-goal --smoke-codex-file-tik
goal-cli doctor --smoke-codex-app-server --smoke-codex-file-tik
goal-cli doctor --smoke-claude-code-goal --smoke-claude-code-file-tik
```

The tik smoke checks copy a tiny temporary artifact into a single-file
workspace, run the same local-file tik adapter used at runtime, and
validate the configured tik verdict fields. `one_click_artifact_loop` is only
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

Install an OS-level timed heartbeat:

```bash
goal-cli heartbeat install --max-minutes 600
goal-cli heartbeat status
```

The default service wake-up is 5 minutes for perpetual goals so the shortest
provider backoff can be honored, and remains 30 minutes for legacy goals.
Every tick first checks `next_due_at`; work that is not due exits without
producer, tik, or tok calls. Each due tick invokes one bounded `heartbeat tick`,
which cleans stale runtime state and then executes the same one-heartbeat
runtime as `goal-cli run`.

## Runtime Units

- `heartbeat`: one autonomous producer/tik/tok pass.
- `run`: one CLI invocation that executes exactly one heartbeat.
- `heartbeat tick`: one scheduler-safe invocation that cleans stale runtime
  state, runs one heartbeat, and exits successfully if another heartbeat is
  already active.
- `heartbeat install`: OS scheduler setup for repeated bounded ticks; scheduling
  inside perpetual state decides whether a wake-up performs work.
