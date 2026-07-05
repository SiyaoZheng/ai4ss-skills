---
name: goal-cli-project-setup
description: Use when connecting an existing project to goal-cli for a non-expert user. Find the finished thing, create a reliable rebuild command, write goal.toml, validate the setup, and run the first safe checks.
version: 1.0.0
---

# goal-cli Project Setup

Use this skill when a user wants an agent to make an existing project runnable
under `goal-cli`, especially when the user can judge the finished thing but does
not want to configure the build loop by hand.

## Role in the One-Prompt Flow

`llms.txt` is the public entrypoint and router. This skill is the execution
runbook. When an agent arrives from `llms.txt`, inherit the user-facing contract
from that file, then use this skill for the concrete setup decisions:

- inspect the project;
- choose the canonical artifact;
- synthesize or select the producer;
- write `goal.toml`;
- validate the setup;
- report the exact next command.

Do not send the user back to read this skill. The skill is for the agent to
execute on the user's behalf.

The deliverable is not just a `goal.toml`. The deliverable is a repeatable
thing loop:

```text
stable rebuild -> finished thing -> review -> bounded source work
```

For a non-expert user, success means they can run one command after setup and
understand what artifact to inspect. Do not leave them with a partial config
that only works if they already know the build system.

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
- If a command fails, preserve the exact failing command and the relevant output
  in your final report. Do not describe a setup as ready when validation did not
  pass.
- Do not edit unrelated README/docs/tests/source while setting up goal-cli unless
  that file is directly required for the producer or goal config.

## Workflow

### 0. Verify goal-cli and Required Tools

Start with a cheap command check:

```bash
goal-cli -h
```

If `goal-cli` is missing, verify Python 3.11+ and install from GitHub:

```bash
python3 --version
python3 -m pip install --upgrade pip
python3 -m pip install "goal-cli @ git+https://github.com/SiyaoZheng/goal-cli.git"
```

If `tik.provider = "api"` will be used, install the OpenAI extra:

```bash
python3 -m pip install "goal-cli[openai] @ git+https://github.com/SiyaoZheng/goal-cli.git"
```

If you are inside a checked-out `goal-cli` repository, prefer the local checkout:

```bash
python3 -m pip install -e '.[openai]'
```

Verify the command again:

```bash
goal-cli -h
```

For a normal non-expert setup, do not disable the no-mistakes gate just to make
the first real heartbeat easier. If `no-mistakes` is missing, either install it
using the project installation docs or report it as the blocker before any real
heartbeat.

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

Do not choose a stale output just because it already exists. The artifact must
be reproducible by `[producer].command`. If several plausible artifacts remain,
ask one short question that lists the candidates and then proceed from the
answer.

If the project does not yet have a final artifact, use the closest inspectable
product-shaped target, such as a runnable demo, generated HTML report, metrics
JSON, or a smoke report file. Avoid abstract goals like "improve the codebase"
because they cannot be checked by tik.

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
- Keep command output short but useful for debugging.
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

Before writing `goal.toml`, run the producer once if it is safe. If it fails,
fix the producer path or report the exact blocker instead of continuing with an
untested command.

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

Use `claude_code_file` when a local Claude Code artifact review is appropriate
and the artifact is a file; it needs the `claude` CLI on `PATH`:

```toml
[tik]
provider = "claude_code_file"
timeout_seconds = 1800
max_file_size_bytes = 25000000
```

Use `api` when OpenAI-compatible Responses API file upload is intended and a
Packy/OpenAI-compatible key is available through `PACKYAPI_API_KEY`,
`PACKYCODE_CODEX_KEY`, `OPENAI_API_KEY`, or `~/.config/goal-cli/api.env`.
This defaults to PackyAPI `claude-fable-5`:

```toml
[tik]
provider = "api"
timeout_seconds = 1800
store = false
```

If this API tik review needs a local skill, set `skill = "skill-name"` under
`[tik]`; do not put `/skill-name` as the first prompt line for `api`.

Tik prompts must review the artifact, not the source diff. They must end with a
JSON verdict that includes at least:

```json
{
  "artifact_ready": false,
  "blocking_objections": []
}
```

For non-expert setup, prefer deterministic checks when they clearly catch
missing, empty, malformed, or stale artifacts. Use model review only for quality
judgments that a script cannot express.

### 5. Configure Tok

Tok's successful changes must show up under source `write_dirs`. Keep that
audited source scope narrow and exclude generated output:

```toml
[tok]
provider = "codex_goal"
sandbox = "workspace-write"
write_dirs = ["src", "writing"]
codex_features = ["goals"]
```

Use `claude_code_goal` for the same pass through Claude Code; it needs the
`claude` CLI on `PATH` and ignores `codex_features`:

```toml
[tok]
provider = "claude_code_goal"
sandbox = "workspace-write"
write_dirs = ["src", "writing"]
```

Tok prompt template should say:

- what standard the artifact must meet;
- that the artifact is produced by `{producer_command}`;
- that `{tik_review_path}` is the standard to meet;
- that tok must make source changes so the next rebuilt artifact answers the
  tik review's blocking objections;
- which source directories count as the audited source-change scope;
- which outputs, data, logs, and generated files are off limits.

Do not include language that asks a human to approve, clarify, or decide during
the runtime loop.

Set `run_cwd = "."` when the tok pass may need to run project-level commands.
Use `runtime_write_dirs` for build outputs, logs, and generated artifacts that
commands may refresh. Do not put those generated directories in `write_dirs`.

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
run_cwd = "."
runtime_write_dirs = ["output", "build", "logs"]
codex_features = ["goals"]

[no_mistakes]
enabled = true
binary = "no-mistakes"
mode = "lightspeed"

[safety]
generated_dirs = ["output", "build", "dist"]
max_blocker_repeats = 3
```

Also include `[tik.prompt]` and `[tok.prompt]` sections. Use only placeholders
documented in `docs/config-schema.md`, and keep runtime prompts closed-system:
they may refer to the artifact, producer, tik ledger, source boundaries, and
operational impossibilities, but not to asking a person for approval or
clarification during the loop.

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

If using `tik.provider = "claude_code_file"`:

```bash
goal-cli doctor --smoke-claude-code-file-tik
```

If using `tok.provider = "claude_code_goal"`:

```bash
goal-cli doctor --smoke-claude-code-goal
```

Combine the smoke flags that match the configured providers; the all-Claude
stack is `--smoke-claude-code-goal --smoke-claude-code-file-tik`.

Run the producer directly once and prove the artifact exists:

```bash
scripts/goal_producer.sh
test -s path/to/artifact
```

If the producer command is not a wrapper, run that exact configured command and
then run `test -s` on `[artifact].path`.

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

### 8. Recovery Rules

Use these rules when setup does not pass on the first attempt:

- `goal-cli validate` fails: fix the config shape, placeholders, write scopes,
  or forbidden runtime prompt language before any other check.
- `goal-cli doctor` fails on a missing command: install the missing tool only
  when that is clearly in scope; otherwise report the exact missing command.
- producer fails: repair the producer command or wrapper first; do not proceed
  to tik/tok.
- artifact missing or empty: fix the producer or artifact path; do not lower the
  standard.
- Codex smoke checks fail: report the exact smoke check failure and leave the
  next command as a setup repair command, not a heartbeat.
- no-mistakes missing: install it or report it; do not silently set
  `[no_mistakes].enabled = false` for a normal user setup.

## Common Recipes

### Research PDF

- Artifact: `output/full_paper.pdf`.
- Producer: `make all` or `python3 scripts/orchestrator.py --full`.
- Tik: `codex_file` or `claude_code_file` with a journal-review prompt, or
  deterministic PDF checks.
- Tok write dirs: `writing`, `src`, `tables`, `figures` if these are source.
- Generated dirs: `output`, `build`, `cache`.

### Static Web App

- Artifact: `dist/index.html` plus any build manifest.
- Producer: `npm run build`.
- Tik: oracle smoke test if Playwright tests exist; otherwise `codex_file` or
  `claude_code_file` on a generated report file.
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
- `tok.write_dirs` are narrow source directories and the runtime can audit source
  changes there.
- `safety.generated_dirs` protects build outputs.
- `goal-cli validate` passes.
- `goal-cli doctor` reports the configured static setup as ready or the
  remaining blocker is documented with exact output.
- Optional Codex smoke checks pass when their providers are configured.
- The final response to the user names the artifact, producer command,
  verifier used, writable scopes, and exact next command. If unattended progress
  is appropriate, the next command should be `goal-cli heartbeat install ...`;
  otherwise it should be one manual `goal-cli run ...`.
- If any required check failed, the final response starts with the blocker and
  gives the smallest next command to fix it.
