"""Helpers for exposing the OpenAI bundled LaTeX plugin to AI4SS harnesses."""

from __future__ import annotations

import os
import re
from pathlib import Path

from inspect_ai.tool import Skill, read_skills


LATEX_PLUGIN_SKILL_NAMES = (
    "latex-doctor",
    "latex-compile",
    "texlive-runtime-installer",
)

LATEX_PLUGIN_SCRIPT_NAMES = (
    "compile_latex.py",
    "detect_tectonic.py",
    "detect_texlive.py",
    "install_texlive.py",
    "latex_doctor.py",
)

DISABLE_ENV = "AI4SS_DISABLE_LATEX_PLUGIN_SKILLS"
ROOT_ENV = "AI4SS_LATEX_PLUGIN_ROOT"


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def _version_key(path: Path) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", path.name)]
    return tuple(parts) if parts else (0,)


def _looks_like_latex_plugin_root(path: Path) -> bool:
    return (
        (path / ".codex-plugin" / "plugin.json").is_file()
        and (path / "scripts").is_dir()
        and all((path / "skills" / name / "SKILL.md").is_file() for name in LATEX_PLUGIN_SKILL_NAMES)
    )


def bundled_latex_plugin_root() -> Path | None:
    """Return the newest installed OpenAI bundled LaTeX plugin root, if present."""
    override = os.environ.get(ROOT_ENV)
    if override:
        path = Path(override).expanduser().resolve()
        if not _looks_like_latex_plugin_root(path):
            raise FileNotFoundError(f"{ROOT_ENV} does not point to a usable LaTeX plugin root: {path}")
        return path

    cache_root = Path.home() / ".codex" / "plugins" / "cache" / "openai-bundled" / "latex"
    if not cache_root.is_dir():
        return None

    candidates = [path for path in cache_root.iterdir() if path.is_dir() and _looks_like_latex_plugin_root(path)]
    if not candidates:
        return None
    return sorted(candidates, key=_version_key, reverse=True)[0].resolve()


def _plugin_scripts(plugin_root: Path) -> dict[str, Path]:
    scripts: dict[str, Path] = {}
    for name in LATEX_PLUGIN_SCRIPT_NAMES:
        path = plugin_root / "scripts" / name
        if path.is_file():
            scripts[name] = path
    return scripts


def _harness_instructions(skill: Skill) -> str:
    return f"""## AI4SS Harness Packaging Note

This skill is sourced from the OpenAI bundled LaTeX plugin and installed by the
AI4SS Inspect harness as a self-contained skill. The plugin scripts are attached
under this installed skill's `scripts/` directory in the sandbox.

In the APSR PDF harness, the workspace is `/workspace` and the installed skill
directory is normally `/workspace/.codex/skills/{skill.name}`. Use commands such
as:

```bash
python3 /workspace/.codex/skills/latex-doctor/scripts/latex_doctor.py
python3 /workspace/.codex/skills/latex-compile/scripts/compile_latex.py /workspace/paper/full_draft.tex --compiler texlive --engine xelatex
python3 /workspace/.codex/skills/texlive-runtime-installer/scripts/install_texlive.py
```

The APSR PDF Docker image already includes TeX Live. Do not run
`--install-managed-full` unless the task explicitly authorizes a managed TeX Live
download.

{skill.instructions}"""


def bundled_latex_plugin_skills(*, required: bool = False) -> list[Skill]:
    """Return self-contained Skill objects for the installed OpenAI LaTeX plugin.

    Inspect installs skill directories independently, so the OpenAI plugin's
    root-level scripts must be attached to each skill object before passing them
    to `codex_cli(skills=...)`.
    """
    if _truthy(os.environ.get(DISABLE_ENV)):
        return []

    plugin_root = bundled_latex_plugin_root()
    if plugin_root is None:
        if required:
            raise FileNotFoundError("OpenAI bundled LaTeX plugin is not installed.")
        return []

    scripts = _plugin_scripts(plugin_root)
    missing_scripts = sorted(set(LATEX_PLUGIN_SCRIPT_NAMES) - set(scripts))
    if missing_scripts:
        message = f"LaTeX plugin is missing scripts: {', '.join(missing_scripts)}"
        if required:
            raise FileNotFoundError(message)
        return []

    skills = read_skills([plugin_root / "skills" / name for name in LATEX_PLUGIN_SKILL_NAMES])
    return [
        skill.model_copy(
            update={
                "instructions": _harness_instructions(skill),
                "scripts": scripts,
                "metadata": {
                    **(skill.metadata or {}),
                    "source_plugin": "openai-bundled/latex",
                    "source_plugin_version": plugin_root.name,
                },
            }
        )
        for skill in skills
    ]
