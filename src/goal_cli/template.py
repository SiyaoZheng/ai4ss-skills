from __future__ import annotations

import re


PLACEHOLDER_RE = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def template_placeholders(template: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(template))


def render_template(template: str, values: dict[str, str]) -> str:
    """Replace explicit lowercase placeholders without interpreting JSON braces."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ValueError(f"template uses unknown placeholder: {{{key}}}")
        return values[key]

    return PLACEHOLDER_RE.sub(replace, template)
