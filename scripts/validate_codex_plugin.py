#!/usr/bin/env python3
"""Validate the local Codex plugin wrapper for the AI4SS skillpack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---", re.DOTALL)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{path}: file does not exist") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    for line in match.group("body").splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def validate_plugin(root: Path) -> list[str]:
    errors: list[str] = []
    plugin_path = root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"

    try:
        plugin = load_json(plugin_path)
    except ValueError as exc:
        return [str(exc)]

    required_strings = ("name", "version", "description", "license", "skills")
    for key in required_strings:
        if not isinstance(plugin.get(key), str) or not plugin[key].strip():
            errors.append(f"{plugin_path}: `{key}` must be a non-empty string")

    if plugin.get("name") != "ai4ss-skills":
        errors.append(f"{plugin_path}: `name` must be ai4ss-skills")
    if not isinstance(plugin.get("version"), str) or not SEMVER_RE.match(plugin["version"]):
        errors.append(f"{plugin_path}: `version` must be semantic version x.y.z")
    if plugin.get("skills") != "./skills/":
        errors.append(f"{plugin_path}: `skills` must point at ./skills/")

    interface = plugin.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{plugin_path}: `interface` must be an object")
    else:
        for key in ("displayName", "shortDescription", "developerName", "category"):
            if not isinstance(interface.get(key), str) or not interface[key].strip():
                errors.append(f"{plugin_path}: interface.`{key}` must be a non-empty string")
        capabilities = interface.get("capabilities")
        if capabilities != ["Read", "Write"]:
            errors.append(f"{plugin_path}: interface.`capabilities` must be ['Read', 'Write']")

    skills_dir = (root / str(plugin.get("skills", ""))).resolve()
    if not skills_dir.is_dir():
        errors.append(f"{plugin_path}: skills path does not exist: {skills_dir}")
    else:
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))
        if len(skill_files) != 21:
            errors.append(f"{skills_dir}: expected 21 SKILL.md files, found {len(skill_files)}")
        for skill_md in skill_files:
            expected_name = skill_md.parent.name
            actual_name = frontmatter_name(skill_md)
            if actual_name != expected_name:
                errors.append(f"{skill_md}: frontmatter name {actual_name!r} must match folder {expected_name!r}")

    try:
        marketplace = load_json(marketplace_path)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            errors.append(f"{marketplace_path}: `plugins` must contain exactly one entry")
        else:
            entry = plugins[0]
            if not isinstance(entry, dict):
                errors.append(f"{marketplace_path}: plugin entry must be an object")
            else:
                if entry.get("name") != plugin.get("name"):
                    errors.append(f"{marketplace_path}: plugin entry name must match plugin.json name")
                source = entry.get("source")
                if not isinstance(source, dict):
                    errors.append(f"{marketplace_path}: plugin source must be an object")
                else:
                    if source.get("source") != "local":
                        errors.append(f"{marketplace_path}: source.source must be local")
                    if source.get("path") != "./":
                        errors.append(f"{marketplace_path}: source.path must be ./")
                    resolved_source = (root / str(source.get("path", ""))).resolve()
                    if (resolved_source / ".codex-plugin" / "plugin.json").resolve() != plugin_path.resolve():
                        errors.append(f"{marketplace_path}: source.path must resolve to the local plugin root")
                policy = entry.get("policy")
                if not isinstance(policy, dict):
                    errors.append(f"{marketplace_path}: policy must be an object")
                else:
                    if policy.get("installation") != "AVAILABLE":
                        errors.append(f"{marketplace_path}: policy.installation must be AVAILABLE")
                    if policy.get("authentication") != "ON_INSTALL":
                        errors.append(f"{marketplace_path}: policy.authentication must be ON_INSTALL")

    gitignore_path = root / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    for required in ("!.agents/plugins/", "!.agents/plugins/marketplace.json"):
        if required not in gitignore_text:
            errors.append(f"{gitignore_path}: missing unignore rule `{required}`")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.root.resolve()
    errors = validate_plugin(root)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS Codex plugin validation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
