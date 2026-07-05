---
name: goal-cli-project-setup
description: Use when connecting an existing project to goal-cli for a non-expert user. Find the finished thing, create a reliable rebuild command, write goal.toml, validate the setup, and run the first safe checks.
version: 1.0.0
---

# goal-cli Project Setup

Use this skill when a user wants an agent to make an existing project runnable
under `goal-cli`, especially when the user can judge the finished thing but does
not want to configure the build loop by hand.

The deliverable is not just a `goal.toml`. The deliverable is a repeatable
thing loop:

```text
stable rebuild -> finished thing -> review -> bounded source work
```

## When to Use

- A user asks to "set up goal-cli" for a project.
- A user provides a repository and a desired output such as a PDF, site,
  workbook, report, model metric, or slide deck.
- A user wants an agent to create the rebuild command and `goal.toml`.
- A user has a finished thing they can inspect but does not know the build system.

Do not use this skill for generic task planning, ordinary code review, or a
project that has no inspectable thing.

## Operating Rules

- Address the user by name if the host profile supplies one.
- Prefer live project evidence over README claims.
- Do not edit raw data, generated outputs, build products, `.git/`, or `.goal/`
  unless the user explicitly asked for that exact operation.
- Ask the user only when the finished thing cannot be inferred safely.
- Keep the producer deterministic, idempotent, and easy to rerun.
- Completion belongs to the rebuilt thing and tik verdict, not to the tok
  agent's explanation.
- Treat every tok pass as source changes only. Tok must not declare the
  thing-level goal complete.

## Workflow

### 1. Inspect the Project

Collect evidence before editing:

```bash
pwd
git status --short --branch
rg --files \
  -g '!node_modules/**' \
  -g '!.git/**' \
  -g '!*.jsonl' \
  -g '!*.sqlite*' \
  | sed -n '1,160p'
```

Look for:

- existing artifacts: `output/`, `outputs/`, `dist/`, `build/`, `reports/`,
  `paper.pdf`, `slides.pdf`, `index.html`, `.xlsx`, `.parquet`, metrics files;
- build entrypoints: `Makefile`, `justfile`, `package.json`, `pyproject.toml`,
  `requirements.txt`, `renv.lock`, `environment.yml`, `Dockerfile`,
  `.github/workflows/`, `README`, `scripts/`, `notebooks/`;
- source surfaces: `src/`, `writing/`, `analysis/`, `notebooks/`, `app/`,
  `pages/`, `content/`, `slides/`, `tex/`;
- generated surfaces that tok must not edit.

### 2. Choose the Canonical Artifact

Pick exactly one artifact path for `[artifact].path`.

Good artifacts are product-shaped and user-inspectable:

- publication PDF: `outputs/writing/full_paper.pdf`;
- slide deck: `dist/slides.pdf` or `dist/deck.html`;
- static site: `dist/index.html`;
- data report: `reports/final.xlsx` or `reports/summary.html`;
- benchmark: `outputs/eval/metrics.json`;
- package smoke report: `build/goal-smoke.txt`.

If multiple candidates exist, prefer the one mentioned by the user, the one
documented as final, or the one downstream of the broadest build command.

### 3. Synthesize the Producer

The producer is the command `goal-cli` will run on every heartbeat. It must
rebuild the finished thing from source.

Use an existing build command when it is already stable:

- `make all`
- `make paper`
- `npm run build`
- `python3 scripts/orchestrator.py --full`
- `quarto render`
- `Rscript scripts/build.R`

When the existing build path is unclear or multi-step, create a wrapper such as
`scripts/goal_producer.sh` or `scripts/build_goal_artifact.py`. Prefer a shell
wrapper for simple command composition and a Python wrapper only when structured
checks or path handling matter.

Producer wrapper requirements:

- `set -euo pipefail` for shell wrappers.
- Resolve paths from the project root.
- Run the minimal commands needed to rebuild the artifact.
- Verify the configured artifact exists at the end.
- Print artifact path, size, modification time, and sha256 when available.
- Exit non-zero if the artifact is missing or empty.
- Avoid network calls unless the project already requires them.
- Do not mutate raw data or commit files.

Example `scripts/goal_producer.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

make all

artifact="output/full_paper.pdf"
test -s "$artifact"

if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "$artifact"
fi
ls -lh "$artifact"
```

Make it executable:

```bash
chmod +x scripts/goal_producer.sh
```

Then set:

```toml
[producer]
command = "scripts/goal_producer.sh"
```

### 4. Configure Tik

Choose the smallest evaluator that can reject bad artifacts.

Use `oracle` when a deterministic script can decide:

```toml
[tik]
provider = "oracle"
command = "python3 scripts/tik.py"
```

Use `codex_file` when a local Codex artifact review is appropriate and the
artifact is a file:

```toml
[tik]
provider = "codex_file"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096
```

Use `agent` only when OpenAI Responses API file upload is intended and
`OPENAI_API_KEY` is available:

```toml
[tik]
provider = "agent"
model = "gpt-5.5-pro"
timeout_seconds = 1800
store = false
```

Tik prompts must review the artifact, not the source diff. They must end with a
JSON verdict that includes at least:

```json
{
  "artifact_ready": false,
  "blocking_objections": []
}
```

### 5. Configure Tok

Tok changes source only. Keep `write_dirs` narrow and exclude generated output:

```toml
[tok]
provider = "codex_goal"
sandbox = "workspace-write"
write_dirs = ["src", "writing"]
codex_features = ["goals"]
```

Tok prompt template should say:

- what standard the artifact must meet;
- that the artifact is produced by `{producer_command}`;
- that `{tik_review_path}` is the standard to meet;
- that tok must make source changes so the next rebuilt artifact answers the
  tik review's blocking objections;
- which source directories are writable;
- which outputs, data, logs, and generated files are off limits.

Do not include language that asks a human to approve, clarify, or decide during
the runtime loop.

### 6. Write `goal.toml`

Start from `goal-cli init` when no config exists, or edit the existing
`goal.toml` carefully.

Minimum shape:

```toml
name = "artifact-goal"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.pdf"
copy_as = "artifact.pdf"

[producer]
command = "scripts/goal_producer.sh"

[tik]
provider = "codex_file"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096

[tik.verdict]
ready_field = "artifact_ready"
blockers_field = "blocking_objections"
required_fields = ["artifact_ready", "blocking_objections"]
fingerprint_fields = ["blocking_objections"]

[tok]
provider = "codex_goal"
sandbox = "workspace-write"
write_dirs = ["src"]
codex_features = ["goals"]

[no_mistakes]
enabled = true
binary = "no-mistakes"
mode = "lightspeed"

[safety]
generated_dirs = ["output", "build", "dist"]
max_blocker_repeats = 3
```

### 7. Validate Before Running

Run these checks from the target project:

```bash
goal-cli validate
goal-cli doctor
```

If using Codex tok:

```bash
goal-cli doctor --smoke-codex-goal
```

If using `tik.provider = "codex_file"`:

```bash
goal-cli doctor --smoke-codex-goal --smoke-codex-file-tik
```

Run the producer directly once and prove the artifact exists:

```bash
scripts/goal_producer.sh
test -s path/to/artifact
```

Run a dry prompt render before the first real heartbeat:

```bash
goal-cli run --dry-run
```

Only run a real heartbeat when setup checks pass:

```bash
goal-cli run --max-minutes 30
goal-cli state
```

For unattended progress, install the system-level heartbeat instead of leaving
a foreground loop running:

```bash
goal-cli heartbeat install --every-minutes 30 --max-minutes 30
goal-cli heartbeat status
```

## Common Recipes

### Research PDF

- Artifact: `output/full_paper.pdf`.
- Producer: `make all` or `python3 scripts/orchestrator.py --full`.
- Tik: `codex_file` with a journal-review prompt or deterministic PDF checks.
- Tok write dirs: `writing`, `src`, `tables`, `figures` if these are source.
- Generated dirs: `output`, `build`, `cache`.

### Static Web App

- Artifact: `dist/index.html` plus any build manifest.
- Producer: `npm run build`.
- Tik: oracle smoke test if Playwright tests exist; otherwise `codex_file` on a
  generated report file.
- Tok write dirs: `src`, `app`, `components`, `pages`, `public` only when
  source assets live there.
- Generated dirs: `dist`, `build`, `.next`, `coverage`.

### Data Report

- Artifact: `reports/final.html`, `reports/final.pdf`, or `reports/final.xlsx`.
- Producer: project script that rebuilds report from committed inputs.
- Tik: deterministic schema and reconciliation checks where possible.
- Tok write dirs: analysis scripts and report source.
- Generated dirs: report outputs and caches.

## Definition of Done

- The finished thing is named and exists after the producer runs.
- The producer is a stable command or wrapper checked into the project.
- `goal.toml` points at the producer and artifact.
- `tok.write_dirs` are narrow source directories.
- `safety.generated_dirs` protects build outputs.
- `goal-cli validate` passes.
- `goal-cli doctor` reports the configured static setup as ready or the
  remaining blocker is documented with exact output.
- Optional Codex smoke checks pass when their providers are configured.
- The final response to the user names the artifact, producer command,
  verifier used, writable scopes, and exact next command. If unattended progress
  is appropriate, the next command should be `goal-cli heartbeat install ...`;
  otherwise it should be one manual `goal-cli run ...`.
