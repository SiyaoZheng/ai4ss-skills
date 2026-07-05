from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConfigError, dump_config_summary, load_config, validate_config
from .runtime import RuntimeOptions, cleanup_runtime, heartbeat_run_dir, load_state, render_prompts_to_run_dir, reset_state, run_heartbeat, run_goal
from .setup_check import DoctorOptions, doctor_exit_code, format_doctor_checks, run_doctor


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
Review only the canonical artifact at {artifact_path}.
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
sandbox = "workspace-write"
codex_features = ["goals"]

[tok.prompt]
template = \"\"\"
The goal is to keep working on the source so the canonical artifact produced
by `{producer_command}` improves.

Use the attached tik review at {tik_review_path}.

Implement the review. Edit source files only. Return the schema report:
{
  "source_change_possible": true,
  "revision_strategy": "one sentence",
  "sources_changed": ["path"],
  "expected_artifact_visible_improvement": ["visible change in next artifact"],
  "remaining_artifact_bottleneck": "one sentence"
}
\"\"\"

[no_mistakes]
binary = "no-mistakes"
mode = "lightspeed"
branch_prefix = "goal-cli"
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
    parser = argparse.ArgumentParser(prog="goal-cli")
    parser.add_argument("-c", "--config", default="goal.toml", help="Path to goal.toml")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create a starter goal.toml")
    subparsers.add_parser("validate", help="Validate config and writable scopes")
    doctor_parser = subparsers.add_parser("doctor", help="Check artifact-loop setup readiness")
    doctor_parser.add_argument("--smoke-codex-goal", action="store_true", help="Run a minimal Codex /goal schema-output smoke check in a temp directory")
    doctor_parser.add_argument("--smoke-codex-file-tik", action="store_true", help="Run a minimal Codex local-file tik smoke check in a temp directory")
    doctor_parser.add_argument("--skip-openai-auth", action="store_true", help="Skip OPENAI_API_KEY readiness check for agent tik configs")
    doctor_parser.add_argument("--timeout-seconds", type=float, default=10.0, help="Timeout for setup probes except the optional Codex smoke check")
    doctor_parser.add_argument("--smoke-timeout-seconds", type=float, default=180.0, help="Timeout for optional Codex smoke checks")
    run_parser = subparsers.add_parser("run", help="Run one autonomous heartbeat")
    run_parser.add_argument("--dry-run", action="store_true", help="Render prompts without running producer, tik, or tok")
    run_parser.add_argument("--max-minutes", type=float, default=30.0, help="Maximum wall-clock minutes for this heartbeat")
    subparsers.add_parser("tik", help="Run producer plus tik, but skip tok")
    subparsers.add_parser("state", help="Print state JSON")
    subparsers.add_parser("reset", help="Remove state and stale lock; keep run artifacts")
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean interrupted heartbeat locks and optional orphan provider processes")
    cleanup_parser.add_argument("--kill-orphans", action="store_true", help="Terminate orphan goal-cli/Codex processes for this project when no live heartbeat lock exists")
    subparsers.add_parser("render-prompts", help="Render tik and tok prompts into a new run dir")

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


if __name__ == "__main__":
    raise SystemExit(main())
