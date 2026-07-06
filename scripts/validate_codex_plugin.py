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
EXPECTED_SKILL_COUNT = 22
IQS_MCP_SERVERS = {
    "IQSWebSearch": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-search",
    "IQSLiteSearch": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-litesearch",
    "IQSReadPage": "https://iqs-mcp.aliyuncs.com/mcp-servers/iqs-mcp-server-readpage",
}


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


def validate_hooks(root: Path, plugin_path: Path, plugin: dict) -> list[str]:
    errors: list[str] = []
    expected_hooks = "./hooks/hooks.json"
    hooks_value = plugin.get("hooks")
    if hooks_value != expected_hooks:
        errors.append(f"{plugin_path}: `hooks` must point at {expected_hooks}")
        return errors

    hooks_path = (root / expected_hooks).resolve()
    try:
        hooks_path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{plugin_path}: hooks path must stay inside plugin root")
        return errors

    try:
        hooks = load_json(hooks_path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    events = hooks.get("hooks")
    if not isinstance(events, dict):
        errors.append(f"{hooks_path}: `hooks` must be an object")
        return errors

    pre_tool_use = events.get("PreToolUse")
    if not isinstance(pre_tool_use, list) or not pre_tool_use:
        errors.append(f"{hooks_path}: hooks.PreToolUse must be a non-empty list")
        return errors

    expected_command = "python3 ${PLUGIN_ROOT}/hooks/guard_generated_outputs.py"
    found_guard = False
    for group in pre_tool_use:
        if not isinstance(group, dict):
            continue
        matcher = group.get("matcher")
        matcher_covers_guard_tools = (
            isinstance(matcher, str) and "Bash" in matcher and "apply_patch" in matcher
        )
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            continue
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            if handler.get("command") == expected_command:
                found_guard = True
                if not matcher_covers_guard_tools:
                    errors.append(f"{hooks_path}: generated-output guard matcher must cover Bash and apply_patch")
                if handler.get("type") != "command":
                    errors.append(f"{hooks_path}: generated-output guard hook type must be command")
                timeout = handler.get("timeout")
                if not isinstance(timeout, int) or timeout <= 0 or timeout > 30:
                    errors.append(f"{hooks_path}: generated-output guard timeout must be 1..30 seconds")

    if not found_guard:
        errors.append(f"{hooks_path}: missing generated-output guard command")

    guard_script = root / "hooks" / "guard_generated_outputs.py"
    if not guard_script.is_file():
        errors.append(f"{guard_script}: generated-output guard script is missing")

    return errors


def validate_mcp_servers(root: Path, plugin_path: Path, plugin: dict) -> list[str]:
    errors: list[str] = []
    expected_mcp = "./.mcp.json"
    mcp_value = plugin.get("mcpServers")
    if mcp_value != expected_mcp:
        errors.append(f"{plugin_path}: `mcpServers` must point at {expected_mcp}")
        return errors

    mcp_path = (root / expected_mcp).resolve()
    try:
        mcp_path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{plugin_path}: mcpServers path must stay inside plugin root")
        return errors

    try:
        config = load_json(mcp_path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        errors.append(f"{mcp_path}: `mcpServers` must be an object")
        return errors

    for name, url in IQS_MCP_SERVERS.items():
        server = servers.get(name)
        if not isinstance(server, dict):
            errors.append(f"{mcp_path}: missing {name} MCP server")
            continue
        if server.get("type") != "http":
            errors.append(f"{mcp_path}: {name}.type must be http")
        if server.get("url") != url:
            errors.append(f"{mcp_path}: {name}.url must be the official IQS MCP endpoint")
        env_headers = server.get("env_http_headers")
        if env_headers != {"X-API-Key": "ALIYUN_IQS_API_KEY"}:
            errors.append(f"{mcp_path}: {name} must read X-API-Key from ALIYUN_IQS_API_KEY")
        headers = server.get("headers")
        if isinstance(headers, dict) and any("sk-" in str(value) for value in headers.values()):
            errors.append(f"{mcp_path}: {name} must not store API keys in headers")

    websearch = servers.get("WebSearch")
    if not isinstance(websearch, dict):
        errors.append(f"{mcp_path}: missing WebSearch MCP server")
    else:
        if websearch.get("type") != "stdio":
            errors.append(f"{mcp_path}: WebSearch.type must be stdio")
        if websearch.get("command") != "sh":
            errors.append(f"{mcp_path}: WebSearch.command must be sh")
        args = websearch.get("args")
        if not isinstance(args, list) or len(args) != 2 or args[0] != "-lc":
            errors.append(f"{mcp_path}: WebSearch.args must be a sh -lc bridge bootstrap")
        else:
            bootstrap = args[1]
            required_fragments = (
                "scripts/bailian_mcp_bridge.py",
                "PYTHON:-python3",
                "/opt/homebrew/bin",
            )
            for fragment in required_fragments:
                if fragment not in bootstrap:
                    errors.append(f"{mcp_path}: WebSearch bridge bootstrap must contain {fragment!r}")
        env_vars = websearch.get("env_vars")
        required_env = {
            "DASHSCOPE_API_KEY",
            "DASHSCOPE_RESPONSES_BASE_URL",
            "DASHSCOPE_WEBSEARCH_MODEL",
            "DASHSCOPE_WEBPARSER_MODEL",
            "DASHSCOPE_WEBPARSER_MCP_URL",
        }
        if not isinstance(env_vars, list) or not required_env.issubset(set(env_vars)):
            errors.append(f"{mcp_path}: WebSearch.env_vars must include {sorted(required_env)!r}")
        headers = websearch.get("headers")
        if isinstance(headers, dict) and any("sk-" in str(value) for value in headers.values()):
            errors.append(f"{mcp_path}: WebSearch must not store API keys in headers")
        bridge_script = root / "scripts" / "bailian_mcp_bridge.py"
        if not bridge_script.is_file():
            errors.append(f"{bridge_script}: Bailian bridge script is missing")

    browser_use = servers.get("browser-use")
    if not isinstance(browser_use, dict):
        errors.append(f"{mcp_path}: missing browser-use MCP server")
    else:
        if browser_use.get("type") != "stdio":
            errors.append(f"{mcp_path}: browser-use.type must be stdio")
        if browser_use.get("command") != "sh":
            errors.append(f"{mcp_path}: browser-use.command must be sh")
        args = browser_use.get("args")
        if not isinstance(args, list) or len(args) != 2 or args[0] != "-lc":
            errors.append(f"{mcp_path}: browser-use.args must be a sh -lc bootstrap")
        else:
            bootstrap = args[1]
            required_fragments = (
                'OPENAI_API_KEY="$DASHSCOPE_API_KEY"',
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
                'BROWSER_USE_LLM_MODEL="qwen-plus"',
                'uvx --from "browser-use[cli]" browser-use --mcp',
            )
            for fragment in required_fragments:
                if fragment not in bootstrap:
                    errors.append(f"{mcp_path}: browser-use bootstrap must contain {fragment!r}")
        env_vars = browser_use.get("env_vars")
        required_env = {
            "DASHSCOPE_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_BASE_URL",
            "BROWSER_USE_LLM_MODEL",
            "ANTHROPIC_API_KEY",
            "BROWSER_USE_API_KEY",
        }
        if not isinstance(env_vars, list) or not required_env.issubset(set(env_vars)):
            errors.append(f"{mcp_path}: browser-use.env_vars must include {sorted(required_env)!r}")

    return errors


def validate_plugin(root: Path) -> list[str]:
    errors: list[str] = []
    plugin_path = root / ".codex-plugin" / "plugin.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"

    try:
        plugin = load_json(plugin_path)
    except ValueError as exc:
        return [str(exc)]

    required_strings = ("name", "version", "description", "license", "skills", "hooks", "mcpServers")
    for key in required_strings:
        if not isinstance(plugin.get(key), str) or not plugin[key].strip():
            errors.append(f"{plugin_path}: `{key}` must be a non-empty string")

    if plugin.get("name") != "ai4ss-skills":
        errors.append(f"{plugin_path}: `name` must be ai4ss-skills")
    if not isinstance(plugin.get("version"), str) or not SEMVER_RE.match(plugin["version"]):
        errors.append(f"{plugin_path}: `version` must be semantic version x.y.z")
    if plugin.get("skills") != "./skills/":
        errors.append(f"{plugin_path}: `skills` must point at ./skills/")
    errors.extend(validate_hooks(root, plugin_path, plugin))
    errors.extend(validate_mcp_servers(root, plugin_path, plugin))

    interface = plugin.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{plugin_path}: `interface` must be an object")
    else:
        for key in ("displayName", "shortDescription", "developerName", "category"):
            if not isinstance(interface.get(key), str) or not interface[key].strip():
                errors.append(f"{plugin_path}: interface.`{key}` must be a non-empty string")
        capabilities = interface.get("capabilities")
        if capabilities != ["MCP", "Read", "Write"]:
            errors.append(f"{plugin_path}: interface.`capabilities` must be ['MCP', 'Read', 'Write']")

    skills_dir = (root / str(plugin.get("skills", ""))).resolve()
    if not skills_dir.is_dir():
        errors.append(f"{plugin_path}: skills path does not exist: {skills_dir}")
    else:
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))
        if len(skill_files) != EXPECTED_SKILL_COUNT:
            errors.append(f"{skills_dir}: expected {EXPECTED_SKILL_COUNT} SKILL.md files, found {len(skill_files)}")
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
