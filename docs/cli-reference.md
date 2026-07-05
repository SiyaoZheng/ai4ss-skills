# goal-cli CLI Reference

`goal-cli` is an `argparse` CLI. The parser generates `-h` and `--help`
output from the same command definitions used at runtime.

## Top Level

Omitting the command defaults to `run`. Global options must appear before the
subcommand.

```text
usage: goal-cli [-h] [-c CONFIG]
                {init,validate,doctor,run,tik,state,reset,cleanup,render-prompts} ...

Make coding agents keep proving the thing is getting better.

options:
  -h, --help            show this help message and exit
  -c, --config CONFIG   Path to goal.toml (default: goal.toml)

commands:
  {init,validate,doctor,run,tik,state,reset,cleanup,render-prompts}
    init                Create a starter goal.toml
    validate            Validate config, prompt placeholders, and writable
                        scopes
    doctor              Check whether the thing-centered setup is ready
    run                 Run one autonomous heartbeat
    tik                 Run producer plus tik review, but skip tok
    state               Print state JSON or the default initial state
    reset               Remove state and stale lock while preserving run
                        artifacts
    cleanup             Clean interrupted heartbeat locks and optional orphan
                        provider processes
    render-prompts      Render tik and tok prompts into a new run directory

Omitting the command defaults to run. Use 'goal-cli <command> -h' for
subcommand options.
```

## Run

```text
usage: goal-cli run [-h] [--dry-run] [--max-minutes MAX_MINUTES]

Run one heartbeat. The thing decides success; source repair is only a step.

options:
  -h, --help            show this help message and exit
  --dry-run             Create a run directory and render prompts without
                        running producer, tik, or tok
  --max-minutes MAX_MINUTES
                        Maximum wall-clock minutes for the heartbeat,
                        including providers and no-mistakes
```

## Doctor

```text
usage: goal-cli doctor [-h] [--smoke-codex-goal] [--smoke-codex-file-tik]
                       [--skip-openai-auth]
                       [--timeout-seconds TIMEOUT_SECONDS]
                       [--smoke-timeout-seconds SMOKE_TIMEOUT_SECONDS]

Check whether goal-cli can rebuild and check the thing before launching a
heartbeat.

options:
  -h, --help            show this help message and exit
  --smoke-codex-goal    Run a minimal Codex /goal schema-output smoke check in
                        a temp directory
  --smoke-codex-file-tik
                        Run a minimal Codex local-file tik smoke check in a
                        temp directory
  --skip-openai-auth    Skip OPENAI_API_KEY readiness check for agent tik
                        configs
  --timeout-seconds TIMEOUT_SECONDS
                        Timeout for setup probes except optional Codex smoke
                        checks
  --smoke-timeout-seconds SMOKE_TIMEOUT_SECONDS
                        Timeout for optional Codex smoke checks
```

## Tik

```text
usage: goal-cli tik [-h]

Rebuild the artifact and run tik only. The command does not complete the goal
or repair sources.

options:
  -h, --help  show this help message and exit
```

## Cleanup

```text
usage: goal-cli cleanup [-h] [--kill-orphans]

Remove stale heartbeat locks, mark interrupted running phases, and optionally
stop orphan provider processes for this project.

options:
  -h, --help      show this help message and exit
  --kill-orphans  Terminate orphan goal-cli/Codex processes for this project
                  when no live heartbeat lock exists
```

## Command Summary

| Command | Effect |
| --- | --- |
| `goal-cli init` | Create a starter `goal.toml`; refuses to overwrite an existing config. |
| `goal-cli validate` | Load config and print a JSON summary if config policy passes. |
| `goal-cli doctor` | Run static readiness probes and optional Codex smoke checks. |
| `goal-cli run` | Execute exactly one heartbeat. |
| `goal-cli tik` | Run producer plus tik only; do not invoke tok. |
| `goal-cli state` | Print current state JSON or the default initial state. |
| `goal-cli reset` | Remove state and lock files; preserve run artifacts. |
| `goal-cli cleanup` | Clean stale/interrupted heartbeat state. |
| `goal-cli render-prompts` | Render tik and tok prompts into a new run directory. |
