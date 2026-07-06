#!/usr/bin/env python3
"""Local MCP bridge for Alibaba Cloud Bailian/DashScope web tools.

The remote Bailian WebSearch Streamable HTTP MCP endpoint can be unhealthy even
when the same Bailian key works for Responses API built-in tools. This bridge
keeps the Codex-facing interface as a local stdio MCP server while routing calls
through the verified DashScope OpenAI-compatible Responses API.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server import FastMCP
from openai import OpenAI


DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_WEBPARSER_SSE_URL = "https://dashscope.aliyuncs.com/api/v1/mcps/WebParser/sse"
DEFAULT_SEARCH_MODEL = "qwen3.6-plus"
DEFAULT_WEBPARSER_MODEL = "qwen3.6-plus"

mcp = FastMCP(
    "BailianBridge",
    log_level="ERROR",
    instructions=(
        "Local bridge exposing Alibaba Cloud Bailian web search, web extraction, "
        "and WebParser through DashScope Responses API."
    ),
)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for BailianBridge")
    return value


def _dashscope_client() -> OpenAI:
    return OpenAI(
        api_key=_required_env("DASHSCOPE_API_KEY"),
        base_url=os.environ.get("DASHSCOPE_RESPONSES_BASE_URL") or DASHSCOPE_BASE_URL,
    )


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            part = getattr(content, "text", None)
            if isinstance(part, str):
                chunks.append(part)
    return "\n".join(chunk for chunk in chunks if chunk).strip()


@mcp.tool(
    name="bailian_web_search",
    description=(
        "Search the live web with Alibaba Cloud Bailian DashScope Responses API. "
        "Returns a source-grounded Markdown answer with URLs and dates when the "
        "provider supplies them."
    ),
)
def bailian_web_search(query: str, max_results: int = 8, include_extraction: bool = True) -> dict[str, Any]:
    """Run live Bailian web search, optionally with page extraction enabled."""
    if not query or len(query.strip()) < 2:
        raise ValueError("query must contain at least two non-whitespace characters")
    max_results = max(1, min(int(max_results), 20))
    model = os.environ.get("DASHSCOPE_WEBSEARCH_MODEL") or DEFAULT_SEARCH_MODEL
    tools: list[dict[str, str]] = [{"type": "web_search"}]
    if include_extraction:
        tools.append({"type": "web_extractor"})
    prompt = (
        "Use the enabled Bailian web tools to answer the research query below. "
        f"Return at most {max_results} distinct sources. For each source include "
        "title, URL, publication or access date if available, and a short note on "
        "what evidence it provides. Then add a compact synthesis. Do not invent "
        "citations, URLs, dates, or empirical results.\n\n"
        f"Query: {query.strip()}"
    )
    response = _dashscope_client().responses.create(
        model=model,
        input=prompt,
        tools=tools,
    )
    return {
        "query": query,
        "provider": "Alibaba Cloud Bailian DashScope Responses API",
        "model": model,
        "tools": [tool["type"] for tool in tools],
        "result_markdown": _response_text(response),
    }


@mcp.tool(
    name="bailian_web_parse",
    description=(
        "Parse a specific webpage using Alibaba Cloud Bailian WebParser MCP via "
        "DashScope Responses API SSE."
    ),
)
def bailian_web_parse(url: str, instruction: str = "") -> dict[str, Any]:
    """Parse one URL through the official Bailian WebParser MCP service."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must be a complete http(s) URL")
    model = os.environ.get("DASHSCOPE_WEBPARSER_MODEL") or DEFAULT_WEBPARSER_MODEL
    server_url = os.environ.get("DASHSCOPE_WEBPARSER_MCP_URL") or DASHSCOPE_WEBPARSER_SSE_URL
    instruction_text = instruction.strip() or (
        "Extract the page title, canonical URL if visible, main article/body "
        "content, publication date if available, and source-grounded facts useful "
        "for social-science research."
    )
    mcp_tool = {
        "type": "mcp",
        "server_protocol": "sse",
        "server_label": "WebParser",
        "server_description": "Alibaba Cloud Bailian WebParser MCP service for webpage parsing.",
        "server_url": server_url,
        "headers": {"Authorization": "Bearer " + _required_env("DASHSCOPE_API_KEY")},
    }
    response = _dashscope_client().responses.create(
        model=model,
        input=f"Use WebParser to parse this URL: {url}\n\nInstruction: {instruction_text}",
        tools=[mcp_tool],
    )
    return {
        "url": url,
        "provider": "Alibaba Cloud Bailian WebParser MCP via DashScope Responses API",
        "model": model,
        "server_url": server_url,
        "result_markdown": _response_text(response),
    }


if __name__ == "__main__":
    mcp.run("stdio")
