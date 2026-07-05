# goal-cli CLI Reference

`goal-cli` is an `argparse` CLI. The parser generates `-h` and `--help`
output from the same command definitions used at runtime.

## Top Level

Omitting the command defaults to `run`. Global options must appear before the
subcommand.

```text
usage: goal-cli [-h] [-c CONFIG]
                {init,validate,doctor,run,tik,heartbeat,state,reset,cleanup,render-prompts} ...

Make agents finish THE THING.

options:
  -h, --help            show this help message and exit
  -c, --config CONFIG   Path to goal.toml (default: goal.toml)

commands:
  {init,validate,doctor,run,tik,heartbeat,state,reset,cleanup,render-prompts}
    init                Create a starter goal.toml
    validate            Validate config, prompt placeholders, and writable
                        scopes
    doctor              Check whether the thing-centered setup is ready
    run                 Run one autonomous heartbeat
    tik                 Run producer plus tik review, but skip tok
    heartbeat           Install or run the system-level heartbeat
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

Run one heartbeat. The thing decides success; source changes are only a step.

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

Rebuild THE THING and run tik only. The command does not complete the goal
or change source files.

options:
  -h, --help  show this help message and exit
```

## System-Level Heartbeat

The system-level heartbeat installs an OS timer. Each tick still runs exactly
one `goal-cli` heartbeat; it does not add multi-cycle behavior inside the CLI.

```text
usage: goal-cli heartbeat [-h] {install,status,uninstall,paths,tick} ...

Manage an OS-level timer that triggers exactly one goal-cli heartbeat per
tick.

options:
  -h, --help            show this help message and exit

heartbeat commands:
  {install,status,uninstall,paths,tick}
    install             Install and start the OS-level heartbeat timer
    status              Show OS-level heartbeat service status
    uninstall           Stop and remove the OS-level heartbeat service
    paths               Print OS-level heartbeat file and log paths
    tick                Run one hardened heartbeat tick for the OS scheduler
```

```text
usage: goal-cli heartbeat install [-h] [--manager {auto,launchd,systemd-user}]
                                  [--label LABEL]
                                  [--every-minutes EVERY_MINUTES]
                                  [--max-minutes MAX_MINUTES] [--no-start]
                                  [--force] [--dry-run]

Install a launchd LaunchAgent on macOS or a systemd user timer on Linux.

options:
  -h, --help            show this help message and exit
  --manager {auto,launchd,systemd-user}
                        OS service manager to use
  --label LABEL         Override the generated service label
  --every-minutes EVERY_MINUTES
                        Timer interval in minutes; must be positive
  --max-minutes MAX_MINUTES
                        Maximum wall-clock minutes for each heartbeat tick
  --no-start            Write service files but do not load or start the timer
  --force               Overwrite an existing goal-cli-managed service file
  --dry-run             Print files and commands without writing or starting
                        anything
```

```text
usage: goal-cli heartbeat tick [-h] [--max-minutes MAX_MINUTES]

Clean stale heartbeat state, run exactly one heartbeat, and treat active locks
as a skipped tick.

options:
  -h, --help            show this help message and exit
  --max-minutes MAX_MINUTES
                        Maximum wall-clock minutes for this heartbeat tick
```

`goal-cli heartbeat install` writes a per-user LaunchAgent on macOS and a
per-user systemd service/timer on Linux. The generated service calls
`goal-cli -c /absolute/path/to/goal.toml heartbeat tick --max-minutes ...`,
uses the project root as its working directory, and writes service logs under
`.goal/system-heartbeat/`.

`heartbeat tick` first runs runtime cleanup for stale locks/interrupted phases,
then calls the same one-heartbeat runtime as `goal-cli run`. If another
heartbeat is currently active, the tick exits successfully after logging a
skipped tick so the OS scheduler does not mark normal overlap as a failure.

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
| `goal-cli heartbeat install` | Install a per-user OS timer for repeated one-heartbeat ticks. |
| `goal-cli heartbeat status` | Show the OS timer status and managed file paths. |
| `goal-cli heartbeat uninstall` | Stop and remove the OS timer files for this project. |
| `goal-cli state` | Print current state JSON or the default initial state. |
| `goal-cli reset` | Remove state and lock files; preserve run artifacts. |
| `goal-cli cleanup` | Clean stale/interrupted heartbeat state. |
| `goal-cli render-prompts` | Render tik and tok prompts into a new run directory. |
