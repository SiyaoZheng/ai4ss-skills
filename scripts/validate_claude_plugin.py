#!/usr/bin/env python3
"""Validate the local Claude Code plugin wrapper for the AI4SS skillpack."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---", re.DOTALL)
PLUGIN_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


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


def validate_relative_path(value: object, field: str, root: Path, errors: list[str]) -> list[Path]:
    values = value if isinstance(value, list) else [value]
    resolved: list[Path] = []
    for item in values:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field}: path entries must be non-empty strings")
            continue
        if not item.startswith("./"):
            errors.append(f"{field}: path `{item}` must start with ./")
            continue
        if "\\" in item or "../" in item:
            errors.append(f"{field}: path `{item}` must not use backslashes or parent traversal")
            continue
        path = (root / item).resolve()
        if not path.exists():
            errors.append(f"{field}: path does not exist: {item}")
            continue
        resolved.append(path)
    return resolved


def validate_plugin(root: Path) -> list[str]:
    errors: list[str] = []
    plugin_path = root / ".claude-plugin" / "plugin.json"
    marketplace_path = root / ".claude-plugin" / "marketplace.json"

    try:
        plugin = load_json(plugin_path)
    except ValueError as exc:
        return [str(exc)]

    if plugin.get("$schema") != "https://anthropic.com/claude-code/plugin.schema.json":
        errors.append(f"{plugin_path}: missing Claude Code plugin schema URL")
    if plugin.get("name") != "ai4ss-skills":
        errors.append(f"{plugin_path}: `name` must be ai4ss-skills")
    if not isinstance(plugin.get("name"), str) or not PLUGIN_NAME_RE.match(plugin["name"]):
        errors.append(f"{plugin_path}: `name` must be kebab-case")
    if not isinstance(plugin.get("version"), str) or not SEMVER_RE.match(plugin["version"]):
        errors.append(f"{plugin_path}: `version` must be semantic version x.y.z")
    if not isinstance(plugin.get("description"), str) or not (50 <= len(plugin["description"]) <= 200):
        errors.append(f"{plugin_path}: `description` should be 50-200 characters")
    if plugin.get("license") != "GPL-3.0":
        errors.append(f"{plugin_path}: `license` must be GPL-3.0")

    author = plugin.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        errors.append(f"{plugin_path}: author.name must be a non-empty string")

    skills_value = plugin.get("skills")
    if skills_value != ["./skills"]:
        errors.append(f"{plugin_path}: `skills` must be [\"./skills\"]")
    skill_roots = validate_relative_path(skills_value, "plugin.skills", root, errors)

    skill_files: list[Path] = []
    for skill_root in skill_roots:
        skill_files.extend(sorted(skill_root.glob("*/SKILL.md")))
    if len(skill_files) != 21:
        errors.append(f"{root / 'skills'}: expected 21 SKILL.md files, found {len(skill_files)}")
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
        if marketplace.get("name") != "ai4ss-skills-local":
            errors.append(f"{marketplace_path}: `name` must be ai4ss-skills-local")
        owner = marketplace.get("owner")
        if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip():
            errors.append(f"{marketplace_path}: owner.name must be a non-empty string")
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
                if entry.get("description") != plugin.get("description"):
                    errors.append(f"{marketplace_path}: plugin entry description must match plugin.json description")
                if entry.get("source") != "./":
                    errors.append(f"{marketplace_path}: plugin source must be ./")
                if (root / str(entry.get("source", "")) / ".claude-plugin" / "plugin.json").resolve() != plugin_path.resolve():
                    errors.append(f"{marketplace_path}: plugin source must resolve to the local plugin root")

    if shutil.which("claude"):
        for path in (plugin_path, marketplace_path):
            result = subprocess.run(
                ["claude", "plugin", "validate", "--strict", str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
                errors.append(f"`claude plugin validate --strict {path}` failed:\n{output}")

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
    print("PASS Claude Code plugin validation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
