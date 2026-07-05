# goal-cli

`goal-cli` is an artifact-centered runtime for autonomous project loops.

The goal is always a concrete product: a PDF, report, benchmark result, site,
package, dataset, model checkpoint, or another canonical artifact. A cycle does
one bounded pass:

1. run the producer command,
2. verify the canonical artifact exists,
3. run `tik`, which writes the artifact critique into `tik.md`,
4. run one bounded `tok` source-repair pass only if `tik` fails the artifact,
5. continue until completion, blocking, or run budget exhaustion.

`tok` never completes the goal directly. Only a later `tik` over a reproduced
artifact can mark the goal complete.

## Quick Start

```bash
python3 -m pip install -e .
goal-cli init
goal-cli validate
goal-cli doctor
goal-cli run
goal-cli state
```

See [docs/artifact-goal-notes.md](docs/artifact-goal-notes.md) for the design
notes, [docs/installation.md](docs/installation.md) for local installation,
[docs/config-schema.md](docs/config-schema.md) for `goal.toml`, and
[examples/scientificity/goal.toml](examples/scientificity/goal.toml) for a
PDF-first research workflow.

## Runtime Architecture

The implementation keeps four internal seams narrow:

- Git Gate: `NoMistakesGate` owns clean checkpoints, feature branches,
  lightspeed/full skip presets, readiness flags, and `no-mistakes axi run`.
- Artifact Cycle: `ArtifactCycleRecorder` owns cycle state, history,
  heartbeat emission, terminal transitions, and no-mistakes state recording.
- Tok Execution: `tok_execution` owns the Codex `/goal` prompt, JSON Schema,
  command construction, report validation, and diagnostic files.
- Readiness/Telemetry: `doctor` and runtime share the same tok execution path
  and `TelemetryExportPlan`, so setup checks describe the path the runtime will
  actually use.

## no-mistakes Gate

`goal-cli` hands each committed checkpoint to
[`kunchenguid/no-mistakes`](https://github.com/kunchenguid/no-mistakes). The
gate is enabled by default:

```toml
[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
```

When enabled, each non-dry-run cycle starts from a clean Git worktree. If the
repo is on the default branch, goal-cli creates a `goal-cli/...` feature branch.
If the worktree is dirty, goal-cli commits a checkpoint, then successful `tok`
or completion cycles run `no-mistakes axi run --intent ... --yes`.
Runtime state under `.goal/` is kept out of commits through `.git/info/exclude`.

The default `mode = "lightspeed"` uses no-mistakes' native `--skip` support to
avoid the high-latency `review`, `test`, `document`, `lint`, `push`, `pr`, and
`ci` steps. Set `mode = "full"` when a release branch needs the complete
no-mistakes pipeline.

There is no interactive no-mistakes mode in goal-cli. Missing Git setup, a
missing binary, or a failed gate stops the run with
`blocked_no_mistakes_failed`; otherwise the gate is driven unattended. Use
`enabled = false` only for isolated tests or diagnostics outside Git.

## Observability

OpenTelemetry tracing is enabled by default. `goal-cli` emits standard OTLP
HTTP spans for the cycle, heartbeat, producer, artifact load, `tik`, `tok`,
and no-mistakes gate. It does not implement a collector, storage
layer, or dashboard. If the configured OTLP receiver is not reachable and no
OTLP endpoint was explicitly set through the environment, `goal-cli` falls back
to local agent-readable JSONL traces at `.goal/observability/traces.jsonl`.

By default traces go to:

```toml
[observability]
service_name = "goal-cli"
endpoint = "http://localhost:4318/v1/traces"
timeout_seconds = 5
```

Run any OTLP-compatible backend or collector on that endpoint when you want
external trace storage. For collector-managed local traces, use the existing
OpenTelemetry Collector Contrib image with the file exporter:

```bash
mkdir -p .goal/observability
cp docs/otel-collector-file.yaml .goal/observability/otel-collector.yaml
docker run --rm --name goal-cli-otel \
  -p 4318:4318 \
  -v "$PWD/.goal/observability:/observability" \
  -v "$PWD/.goal/observability/otel-collector.yaml:/etc/otelcol-contrib/config.yaml:ro" \
  otel/opentelemetry-collector-contrib:latest \
  --config=/etc/otelcol-contrib/config.yaml
```

Then run `goal-cli cycle` or `goal-cli run` and inspect either the collector
output in `.goal/observability/` or the fallback `.goal/observability/traces.jsonl`.
Standard OpenTelemetry environment variables such as
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_SERVICE_NAME`, and `OTEL_TRACES_EXPORTER=none` are respected.

## Core Commands

- `goal-cli init` creates a starter `goal.toml`.
- `goal-cli validate` checks config, artifact paths, and writable scopes.
- `goal-cli run` runs cycles until the goal completes, blocks, or exhausts the run budget.
- `goal-cli cycle` runs exactly one producer/tik/tok cycle.
- `goal-cli tik` runs producer plus tik without a tok pass.
- `goal-cli render-prompts` writes rendered tik and tok prompts.
- `goal-cli state` prints `.goal/state.json` or the default initial state.
- `goal-cli reset` removes state and stale locks, preserving run artifacts.
- `goal-cli doctor` checks whether the configured artifact loop is ready for one-command execution.

## Setup Readiness

`goal-cli doctor` answers the static setup question: can this config start
`goal-cli run` with valid paths, commands, writable scopes, and Codex CLI
capabilities?

The default doctor is non-destructive. It validates config and writable-scope
safety, checks that artifact/state/run paths can be created, verifies configured
producer and oracle tik executables where the shell command is statically
knowable, checks Codex CLI availability, and verifies that `codex exec` supports
the flags required for schema-checked `codex_goal` execution.

For agent tik providers, doctor also checks that the `openai` Python package is
importable and that `OPENAI_API_KEY` is set. Use `--skip-openai-auth` only when
the auth layer is intentionally supplied outside the environment.

Use this deeper probe when setup should prove the one-click internal tok
path too:

```bash
goal-cli doctor --smoke-codex-goal
```

The smoke check launches a minimal Codex `/goal` tok in a temporary workspace,
validates the schema-shaped tok report, and does not touch project sources.
`one_click_artifact_loop` is only marked ready after this tok path is proven.

## Runtime Rule

After the producer, the runtime has two sequential roles:

- `tik`: reviews the canonical artifact and writes a Markdown ledger at
  `tik.md`. Public tik modes are `oracle` for deterministic scripts, tests, and
  metrics; and `agent` for model critique.
- `tok`: consumes the whole `tik.md` ledger and performs one bounded source
  repair. The default tok mode is `codex_goal`, an internal Codex `/goal`.

Runtime prompts should describe a closed operational system: artifact, producer,
tik ledger, writable scopes, state, and budgets. Tok prompts are launched as
internal Codex goals through the `codex_goal` provider. They should not include
an approval path or imply that a person can decide the goal during the loop.

Tok reports are machine-checked JSON. A successful source revision reports:

```json
{
  "source_change_possible": true,
  "revision_strategy": "one sentence",
  "sources_changed": ["path"],
  "expected_artifact_visible_improvement": ["visible change in next artifact"],
  "remaining_artifact_bottleneck": "one sentence"
}
```

Only the next reproduced artifact and tik pass can complete the goal.
