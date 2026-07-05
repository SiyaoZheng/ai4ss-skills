from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConfigError, dump_config_summary, load_config, validate_config
from .runtime import RuntimeOptions, cleanup_runtime, heartbeat_run_dir, load_state, render_prompts_to_run_dir, reset_state, run_heartbeat, run_goal
from .setup_check import DoctorOptions, doctor_exit_code, format_doctor_checks, run_doctor
from .system_heartbeat import (
    MANAGER_AUTO,
    MANAGER_LAUNCHD,
    MANAGER_SYSTEMD_USER,
    SystemHeartbeatOptions,
    SystemHeartbeatResult,
    install_system_heartbeat,
    paths_system_heartbeat,
    run_system_heartbeat_tick,
    status_system_heartbeat,
    uninstall_system_heartbeat,
)


STARTER_CONFIG = '''name = "artifact-goal"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/artifact.txt"
copy_as = "artifact.txt"

[producer]
command = "make artifact"

[tik]
provider = "oracle"
command = "python3 scripts/tik.py"

[tik.verdict]
ready_field = "artifact_ready"
blockers_field = "blocking_objections"
required_fields = ["artifact_ready", "blocking_objections"]
fingerprint_fields = ["blocking_objections", "central_bottleneck"]

[tik.prompt]
text = \"\"\"
Review only the finished thing at {artifact_path}.
Write the critique plainly, then include a JSON object with this shape:
{
  "artifact_ready": false,
  "central_bottleneck": "one sentence",
  "blocking_objections": [],
  "required_next_artifact_changes": []
}
\"\"\"

[tok]
provider = "codex_goal"
write_dirs = ["src"]
# Optional: set run_cwd and runtime_write_dirs when the producer must run from
# the project root and refresh generated artifacts outside write_dirs.
# run_cwd = "."
# runtime_write_dirs = ["output", "build", "logs"]
sandbox = "workspace-write"
codex_features = ["goals"]

[tok.prompt]
template = \"\"\"
Make the editable source yield, via `{producer_command}`, an artifact that
meets the standard defined by the tik review at {tik_review_path}; success
means that artifact answers every blocking objection in that review.

Manual edits are limited to:
{writable_scopes}

Commands may run from {tok_run_cwd}; generated side effects may update:
{runtime_writable_scopes}

Do not hand-edit generated outputs, .goal/, or the artifact. Return the
required schema report after the source pass.
\"\"\"

[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
skip_steps = []

[observability]
service_name = "goal-cli"
endpoint = "http://localhost:4318/v1/traces"
timeout_seconds = 5

[safety]
generated_dirs = ["output", "build"]
max_blocker_repeats = 3
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="goal-cli",
        description="Make agents finish THE THING.",
        epilog="Omitting the command defaults to run. Use 'goal-cli <command> -h' for subcommand options.",
    )
    parser.add_argument("-c", "--config", default="goal.toml", help="Path to goal.toml (default: goal.toml)")
    subparsers = parser.add_subparsers(dest="command", title="commands")

    subparsers.add_parser("init", help="Create a starter goal.toml")
    subparsers.add_parser("validate", help="Validate config, prompt placeholders, and writable scopes")
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check whether the thing-centered setup is ready",
        description="Check whether goal-cli can rebuild and check the thing before launching a heartbeat.",
    )
    doctor_parser.add_argument("--smoke-codex-goal", action="store_true", help="Run a minimal Codex /goal schema-output smoke check in a temp directory")
    doctor_parser.add_argument("--smoke-codex-file-tik", action="store_true", help="Run a minimal Codex local-file tik smoke check in a temp directory")
    doctor_parser.add_argument("--skip-openai-auth", action="store_true", help="Skip OPENAI_API_KEY readiness check for agent tik configs")
    doctor_parser.add_argument("--timeout-seconds", type=float, default=10.0, help="Timeout for setup probes except optional Codex smoke checks")
    doctor_parser.add_argument("--smoke-timeout-seconds", type=float, default=180.0, help="Timeout for optional Codex smoke checks")
    run_parser = subparsers.add_parser(
        "run",
        help="Run one autonomous heartbeat",
        description="Run one heartbeat. The thing decides success; source changes are only a step.",
    )
    run_parser.add_argument("--dry-run", action="store_true", help="Create a run directory and render prompts without running producer, tik, or tok")
    run_parser.add_argument("--max-minutes", type=float, default=30.0, help="Maximum wall-clock minutes for the heartbeat, including providers and no-mistakes")
    subparsers.add_parser(
        "tik",
        help="Run producer plus tik review, but skip tok",
        description="Rebuild THE THING and run tik only. The command does not complete the goal or change source files.",
    )
    heartbeat_parser = subparsers.add_parser(
        "heartbeat",
        help="Install or run the system-level heartbeat",
        description="Manage an OS-level timer that triggers exactly one goal-cli heartbeat per tick.",
    )
    heartbeat_subparsers = heartbeat_parser.add_subparsers(dest="heartbeat_command", title="heartbeat commands", required=True)
    heartbeat_install = heartbeat_subparsers.add_parser(
        "install",
        help="Install and start the OS-level heartbeat timer",
        description="Install a launchd LaunchAgent on macOS or a systemd user timer on Linux.",
    )
    _add_system_heartbeat_identity_args(heartbeat_install)
    heartbeat_install.add_argument("--every-minutes", type=float, default=60.0, help="Timer interval in minutes; must be positive")
    heartbeat_install.add_argument("--max-minutes", type=float, default=30.0, help="Maximum wall-clock minutes for each heartbeat tick")
    heartbeat_install.add_argument("--no-start", action="store_true", help="Write service files but do not load or start the timer")
    heartbeat_install.add_argument("--force", action="store_true", help="Overwrite an existing goal-cli-managed service file")
    heartbeat_install.add_argument("--dry-run", action="store_true", help="Print files and commands without writing or starting anything")
    heartbeat_status = heartbeat_subparsers.add_parser("status", help="Show OS-level heartbeat service status")
    _add_system_heartbeat_identity_args(heartbeat_status)
    heartbeat_uninstall = heartbeat_subparsers.add_parser("uninstall", help="Stop and remove the OS-level heartbeat service")
    _add_system_heartbeat_identity_args(heartbeat_uninstall)
    heartbeat_uninstall.add_argument("--dry-run", action="store_true", help="Print commands and files without changing anything")
    heartbeat_paths = heartbeat_subparsers.add_parser("paths", help="Print OS-level heartbeat file and log paths")
    _add_system_heartbeat_identity_args(heartbeat_paths)
    heartbeat_tick = heartbeat_subparsers.add_parser(
        "tick",
        help="Run one hardened heartbeat tick for the OS scheduler",
        description="Clean stale heartbeat state, run exactly one heartbeat, and treat active locks as a skipped tick.",
    )
    heartbeat_tick.add_argument("--max-minutes", type=float, default=30.0, help="Maximum wall-clock minutes for this heartbeat tick")
    subparsers.add_parser("state", help="Print state JSON or the default initial state")
    subparsers.add_parser("reset", help="Remove state and stale lock while preserving run artifacts")
    cleanup_parser = subparsers.add_parser(
        "cleanup",
        help="Clean interrupted heartbeat locks and optional orphan provider processes",
        description="Remove stale heartbeat locks, mark interrupted running phases, and optionally stop orphan provider processes for this project.",
    )
    cleanup_parser.add_argument("--kill-orphans", action="store_true", help="Terminate orphan goal-cli/Codex processes for this project when no live heartbeat lock exists")
    subparsers.add_parser("render-prompts", help="Render tik and tok prompts into a new run directory")

    args = parser.parse_args(argv)
    command = args.command or "run"

    if command == "init":
        return init_config(Path(args.config))

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if command == "validate":
        return validate_command(config)
    if command == "doctor":
        return doctor_command(
            config,
            DoctorOptions(
                smoke_codex_goal=getattr(args, "smoke_codex_goal", False),
                smoke_codex_file_tik=getattr(args, "smoke_codex_file_tik", False),
                skip_openai_auth=getattr(args, "skip_openai_auth", False),
                timeout_seconds=getattr(args, "timeout_seconds", 10.0),
                smoke_timeout_seconds=getattr(args, "smoke_timeout_seconds", 180.0),
            ),
        )
    if command == "state":
        print(json.dumps(load_state(config), ensure_ascii=False, indent=2))
        return 0
    if command == "reset":
        reset_state(config)
        print(f"Reset state: {config.state_path}")
        return 0
    if command == "cleanup":
        result = cleanup_runtime(config, kill_orphans=getattr(args, "kill_orphans", False))
        for action in result.actions:
            print(action)
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        return 0
    if command == "render-prompts":
        state = load_state(config)
        run_dir = heartbeat_run_dir(config, state)
        run_dir.mkdir(parents=True, exist_ok=True)
        render_prompts_to_run_dir(config, run_dir)
        print(f"Rendered prompts: {run_dir}")
        return 0
    if command == "tik":
        result = run_heartbeat(config, RuntimeOptions(review_only=True))
        print(result.message)
        if result.run_dir:
            print(f"Run directory: {result.run_dir}")
        return result.exit_code
    if command == "heartbeat":
        return heartbeat_command(config, args)
    if command == "run":
        result = run_goal(
            config,
            RuntimeOptions(
                dry_run=getattr(args, "dry_run", False),
                max_minutes=getattr(args, "max_minutes", 30.0),
            ),
        )
        print(result.message)
        if result.run_dir:
            print(f"Run directory: {result.run_dir}")
        return result.exit_code
    parser.error(f"unknown command: {command}")
    return 2


def init_config(config_path: Path) -> int:
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    if config_path.exists():
        print(f"Refusing to overwrite existing config: {config_path}", file=sys.stderr)
        return 1
    config_path.write_text(STARTER_CONFIG, encoding="utf-8")
    print(f"Created {config_path}")
    return 0


def validate_command(config) -> int:
    issues = validate_config(config)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print(dump_config_summary(config), end="")
    return 0


def doctor_command(config, options: DoctorOptions | None = None) -> int:
    checks = run_doctor(config, options)
    output = format_doctor_checks(checks)
    exit_code = doctor_exit_code(checks)
    stream = sys.stdout if exit_code == 0 else sys.stderr
    print(output, end="", file=stream)
    return exit_code


def heartbeat_command(config, args: argparse.Namespace) -> int:
    command = args.heartbeat_command
    if command == "install":
        result = install_system_heartbeat(
            config,
            SystemHeartbeatOptions(
                manager=args.manager,
                label=args.label,
                every_minutes=args.every_minutes,
                max_minutes=args.max_minutes,
                start=not args.no_start,
                force=args.force,
                dry_run=args.dry_run,
            ),
        )
        return print_system_heartbeat_result(result)
    if command == "status":
        return print_system_heartbeat_result(status_system_heartbeat(config, manager=args.manager, label=args.label))
    if command == "uninstall":
        return print_system_heartbeat_result(uninstall_system_heartbeat(config, manager=args.manager, label=args.label, dry_run=args.dry_run))
    if command == "paths":
        return print_system_heartbeat_result(paths_system_heartbeat(config, manager=args.manager, label=args.label))
    if command == "tick":
        return print_system_heartbeat_result(run_system_heartbeat_tick(config, max_minutes=args.max_minutes))
    raise AssertionError(f"unknown heartbeat command: {command}")


def print_system_heartbeat_result(result: SystemHeartbeatResult) -> int:
    for message in result.messages:
        print(message)
    for error in result.errors:
        print(error, file=sys.stderr)
    return result.exit_code


def _add_system_heartbeat_identity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manager",
        choices=[MANAGER_AUTO, MANAGER_LAUNCHD, MANAGER_SYSTEMD_USER],
        default=MANAGER_AUTO,
        help="OS service manager to use",
    )
    parser.add_argument("--label", help="Override the generated service label")


if __name__ == "__main__":
    raise SystemExit(main())
