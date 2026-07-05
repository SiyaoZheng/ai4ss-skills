# Installing goal-cli

This project is a local Python CLI. It is normally installed from the checked-out
repository, then pointed at a project-specific `goal.toml`.

## Requirements

- Python 3.11 or newer.
- Git.
- Codex CLI on `PATH` for the production tok and `codex_file` tik.
- `OPENAI_API_KEY` when `tik.provider = "agent"`.
- `no-mistakes`.
- An OTLP-compatible OpenTelemetry receiver when you want external trace
  storage. Without one, the default runtime writes local JSONL traces.

## Development Install

From the `goal-cli` repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

For agent tik providers:

```bash
python3 -m pip install -e '.[openai]'
```

Verify the command resolves:

```bash
goal-cli -h
goal-cli run -h
goal-cli doctor -h
goal-cli cleanup -h
goal-cli heartbeat install -h
```

## User Install

For a user-level install from this checkout:

```bash
python3 -m pip install --user -e .
```

Make sure the user script directory is on `PATH`. On macOS this is often:

```bash
export PATH="$HOME/Library/Python/3.11/bin:$PATH"
```

If multiple Python versions are installed, prefer the virtualenv development
install so `goal-cli`, `openai`, and test dependencies all come from the same
environment.

## Install no-mistakes

`goal-cli` does not implement its own review/test/lint/PR gate. It uses
`kunchenguid/no-mistakes` and drives it non-interactively.

Official installer:

```bash
curl -fsSL https://raw.githubusercontent.com/kunchenguid/no-mistakes/main/docs/install.sh | sh
```

Go install:

```bash
go install github.com/kunchenguid/no-mistakes/cmd/no-mistakes@latest
export PATH="$HOME/go/bin:$PATH"
```

Verify:

```bash
no-mistakes --version
no-mistakes axi run --help
```

The `axi run --help` output must include `--intent`, `--yes`, and `--skip`.

## Install an Observability Receiver

OpenTelemetry tracing is on by default. `goal-cli` first tries to send OTLP HTTP
traces to:

```text
http://localhost:4318/v1/traces
```

When that receiver is not reachable and no OTLP endpoint was explicitly set
through the environment, `goal-cli` falls back to agent-readable local JSONL at:

```text
.goal/observability/traces.jsonl
```

Use an existing OTLP-compatible tool when you want external trace storage. For
collector-managed local traces, use OpenTelemetry Collector Contrib with the file
exporter:

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

Then inspect either the collector output:

```bash
python3 -m json.tool .goal/observability/traces.json | head -n 80
```

or the built-in fallback:

```bash
head -n 1 .goal/observability/traces.jsonl | python3 -m json.tool
```

Other OTLP backends also work, including Phoenix, SigNoz, HyperDX, Honeycomb,
Grafana Tempo, and any OpenTelemetry Collector pipeline. They are not required
for agent-side observability.

To point `goal-cli` at another receiver, use either config:

```toml
[observability]
endpoint = "http://localhost:4318/v1/traces"
```

or standard OpenTelemetry environment variables:

```bash
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:4318/v1/traces"
export OTEL_SERVICE_NAME="goal-cli"
```

Environment-provided OTLP endpoints are treated as explicit operator intent and
are not replaced by the local fallback.

Disable tracing only for isolated tests or diagnostics:

```bash
export OTEL_TRACES_EXPORTER=none
```

## Create a Goal Config

Create a starter config:

```bash
goal-cli init
```

If a coding agent is doing setup for a non-expert user, start from the root
[`llms.txt`](../llms.txt) prompt or the
[`goal-cli-project-setup`](../skills/goal-cli-project-setup/SKILL.md) skill.
That setup path includes producer synthesis, `goal.toml` generation, and safe
validation checks before the first real heartbeat.

Then edit `goal.toml` so:

- `[artifact].path` is the one canonical product.
- `[producer].command` rebuilds that artifact from sources.
- `[tik]` either runs a deterministic oracle command, an OpenAI file-upload
  agent review, or a Codex local-file review.
- `[tok].write_dirs` contains only source directories the tok may edit.
- `[tok].run_cwd`, when set, is where the tok process starts commands.
- `[tok].runtime_write_dirs` contains generated directories that commands may
  refresh without making them source-edit scopes.
- `[no_mistakes].intent`, when set, describes the non-interactive gate intent.
- `[safety].generated_dirs` lists generated outputs the tok must not edit.

For a PDF-first research project, start from:

```bash
cp /Users/siyaozheng/Documents/goal-cli/examples/scientificity/goal.toml ./goal.toml
```

Then adjust artifact paths, write dirs, tik provider settings, and the producer
command for that repository.

## no-mistakes Gate

The no-mistakes integration has no interactive mode. It is enabled by default;
every non-dry-run heartbeat starts from a checkpointed clean Git worktree, and
successful source-change or completion transitions are gated before the runtime
continues.

```toml
[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
intent = "Rebuild, review, update source, and keep the Git worktree clean."
skip_steps = []
timeout_seconds = 0
```

When enabled, goal-cli always:

1. stays on the current branch and treats it as the single-person mainline;
2. ignores `.goal/` runtime files through `.git/info/exclude`;
3. commits dirty project files as a checkpoint;
4. runs `no-mistakes init`;
5. runs `no-mistakes axi run --intent ... --yes [--skip ...]`.

`mode = "lightspeed"` is the default. It still uses no-mistakes, but passes
`--skip review,test,document,lint,push,pr,ci` so routine heartbeats do not pay
the full review/test/docs/lint/PR/CI latency. Use `mode = "full"` for the full
pipeline, or `mode = "fast"` to keep local quality steps but skip push/PR/CI.

If Git, no-mistakes, or the gate fails, the run exits as
`blocked_no_mistakes_failed`.

If the heartbeat wall-clock budget expires during no-mistakes preparation or
the gate, the run records `budget_limited` and can be continued by a later
heartbeat.

Use `enabled = false` only for isolated tests or diagnostics that intentionally
do not run inside a Git repository.

## System-Level Heartbeat

For unattended progress, install a per-user OS timer:

```bash
goal-cli heartbeat install --every-minutes 60 --max-minutes 30
```

On macOS this writes a LaunchAgent under `~/Library/LaunchAgents/`. On Linux it
writes a systemd user service and timer under
`${XDG_CONFIG_HOME:-~/.config}/systemd/user/`. The generated service uses the
absolute `goal.toml` path, starts in the project root, and writes scheduler logs
under `.goal/system-heartbeat/`.

The timer does not create a multi-cycle CLI mode. Each OS tick invokes:

```bash
goal-cli -c /absolute/path/to/goal.toml heartbeat tick --max-minutes 30
```

`heartbeat tick` cleans stale interrupted runtime state, runs one heartbeat, and
exits successfully when it finds an already-active heartbeat lock. That keeps
normal timer overlap from becoming a system-service failure.

Useful management commands:

```bash
goal-cli heartbeat paths
goal-cli heartbeat status
goal-cli heartbeat uninstall
```

## Observability Defaults

The starter config includes:

```toml
[observability]
service_name = "goal-cli"
endpoint = "http://localhost:4318/v1/traces"
timeout_seconds = 5
```

Each heartbeat emits spans for heartbeat progress, producer, artifact load,
tik, tok, and no-mistakes gate. `goal-cli` does not include a collector,
database, queue, dashboard, or trace storage; those are supplied by the OTLP
backend.

## Validate and Run

Static validation:

```bash
goal-cli validate
```

Use a non-default config path by placing the global option before the command:

```bash
goal-cli -c path/to/goal.toml validate
goal-cli -c path/to/goal.toml run --max-minutes 30
```

Setup readiness:

```bash
goal-cli doctor
```

With observability enabled, doctor also checks that the OpenTelemetry packages
are importable and reports the same export plan used at runtime: OTLP when the
endpoint is reachable or explicitly configured through the environment, local
JSONL fallback otherwise.

Prove the Codex tok path in a temporary workspace:

```bash
goal-cli doctor --smoke-codex-goal
```

For `tik.provider = "codex_file"`, prove the local-file tik path too:

```bash
goal-cli doctor --smoke-codex-goal --smoke-codex-file-tik
```

Run one heartbeat:

```bash
goal-cli run --max-minutes 30
```

Inspect state:

```bash
goal-cli state
```

Reset runtime state without deleting run artifacts:

```bash
goal-cli reset
```

Clean up after an interrupted heartbeat:

```bash
goal-cli cleanup
```

If a Ctrl-C left orphan provider processes for this project, use:

```bash
goal-cli cleanup --kill-orphans
```

## Running From Source Without Installing

For one-off testing from another project:

```bash
PYTHONPATH=/Users/siyaozheng/Documents/goal-cli/src \
python3 -m goal_cli.cli -c goal.toml run
```

This uses the checked-out source tree directly.
