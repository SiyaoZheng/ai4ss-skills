#!/usr/bin/env python3
"""Run AutoChecklist CLI against DeepSeek V4 Pro with max reasoning effort.

This is intentionally a CLI adapter, not an AI4SS skill. It forwards to the
installed `autochecklist` command and uses a local OpenAI-compatible shim to add
DeepSeek-only transport parameters that AutoChecklist's CLI does not expose.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit, urlunsplit


DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_API_FORMAT = "chat"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_MAX_TOKENS = 32768
DEFAULT_STRUCTURED_MODE = "strict_tool"


def has_flag(argv: list[str], flag: str) -> bool:
    return any(arg == flag or arg.startswith(f"{flag}=") for arg in argv)


def add_default(argv: list[str], flag: str, value: str) -> list[str]:
    if has_flag(argv, flag):
        return argv
    return [*argv, flag, value]


def _deepseek_beta_base_url(base_url: str) -> str:
    parsed = urlsplit(base_url.rstrip("/"))
    path = parsed.path.rstrip("/")
    if path.endswith("/v1"):
        path = path[:-3]
    if not path.endswith("/beta"):
        path = f"{path}/beta"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", "")).rstrip("/")


def _sanitize_tool_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name)
    cleaned = cleaned.strip("_-") or "structured_output"
    return cleaned[:64]


def _inline_local_refs(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs") or schema.get("$def") or {}

    def visit(value: Any) -> Any:
        if isinstance(value, list):
            return [visit(item) for item in value]
        if not isinstance(value, dict):
            return value

        ref = value.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[-1]
            if name in defs:
                return visit(defs[name])
        if isinstance(ref, str) and ref.startswith("#/$def/"):
            name = ref.rsplit("/", 1)[-1]
            if name in defs:
                return visit(defs[name])

        return {
            key: visit(item)
            for key, item in value.items()
            if key not in {"$defs", "$def"}
        }

    return visit(schema)


def _normalize_schema_for_deepseek(schema: dict[str, Any]) -> dict[str, Any]:
    schema = _inline_local_refs(schema)

    def visit(value: Any) -> Any:
        if isinstance(value, list):
            return [visit(item) for item in value]
        if not isinstance(value, dict):
            return value

        out: dict[str, Any] = {}
        for key, item in value.items():
            if key == "title":
                continue
            out[key] = visit(item)

        if out.get("type") == "object":
            properties = out.get("properties")
            if isinstance(properties, dict):
                out["properties"] = {
                    prop: visit(prop_schema)
                    for prop, prop_schema in properties.items()
                }
                out["required"] = list(properties.keys())
            out["additionalProperties"] = False

        if out.get("type") == "array" and isinstance(out.get("items"), dict):
            out["items"] = visit(out["items"])

        return out

    return visit(schema)


def _json_object_payload(payload: dict[str, Any]) -> dict[str, Any]:
    fallback = dict(payload)
    fallback["response_format"] = {"type": "json_object"}
    fallback.pop("tools", None)
    fallback.pop("tool_choice", None)
    return fallback


def transform_deepseek_request(
    body: dict[str, Any],
    reasoning_effort: str,
    structured_mode: str,
) -> list[tuple[dict[str, Any], str]]:
    payload = dict(body)
    payload["model"] = body.get("model") or DEFAULT_MODEL
    payload["max_tokens"] = max(int(payload.get("max_tokens") or 0), DEFAULT_MAX_TOKENS)
    payload.pop("max_completion_tokens", None)

    response_format = payload.get("response_format")
    if isinstance(response_format, dict) and response_format.get("type") == "json_schema":
        schema_spec = response_format.get("json_schema") or {}
        schema_name = _sanitize_tool_name(str(schema_spec.get("name") or "structured_output"))
        schema = schema_spec.get("schema")
        if structured_mode == "strict_tool" and isinstance(schema, dict):
            strict_payload = dict(payload)
            strict_payload.pop("response_format", None)
            strict_payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": schema_name,
                        "description": "Return the structured JSON payload required by AutoChecklist.",
                        "strict": True,
                        "parameters": _normalize_schema_for_deepseek(schema),
                    },
                }
            ]
            strict_payload["tool_choice"] = {
                "type": "function",
                "function": {"name": schema_name},
            }
            strict_payload["thinking"] = {"type": "enabled"}
            strict_payload["reasoning_effort"] = reasoning_effort

            fallback_payload = _json_object_payload(payload)
            fallback_payload["thinking"] = {"type": "enabled"}
            fallback_payload["reasoning_effort"] = reasoning_effort
            return [(strict_payload, "beta"), (fallback_payload, "default")]

        payload = _json_object_payload(payload)

    payload["thinking"] = {"type": "enabled"}
    payload["reasoning_effort"] = reasoning_effort
    return [(payload, "default")]


class DeepSeekProMaxShim:
    def __init__(
        self,
        target_base_url: str,
        api_key: str,
        timeout: int,
        reasoning_effort: str,
        structured_mode: str,
    ) -> None:
        self.target_base_url = target_base_url.rstrip("/")
        self.beta_base_url = os.environ.get(
            "DEEPSEEK_BETA_BASE_URL",
            _deepseek_beta_base_url(self.target_base_url),
        ).rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.structured_mode = structured_mode
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> str:
        shim = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format: str, *args: Any) -> None:  # noqa: A002
                return

            def send_json(self, status: int, payload: dict[str, Any]) -> None:
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def proxy_get(self, path: str) -> None:
                request = urllib.request.Request(
                    f"{shim.target_base_url}{path}",
                    headers={"Authorization": f"Bearer {shim.api_key}"},
                )
                with urllib.request.urlopen(request, timeout=shim.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="replace"))
                self.send_json(response.status, payload)

            def do_GET(self) -> None:
                try:
                    if self.path.endswith("/models"):
                        self.proxy_get("/models")
                    else:
                        self.send_json(404, {"error": {"message": f"unsupported path: {self.path}"}})
                except Exception as exc:  # noqa: BLE001
                    self.send_json(502, {"error": {"message": str(exc)}})

            def do_POST(self) -> None:
                try:
                    if not self.path.endswith("/chat/completions"):
                        self.send_json(404, {"error": {"message": f"unsupported path: {self.path}"}})
                        return
                    content_length = int(self.headers.get("Content-Length", "0"))
                    raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
                    incoming = json.loads(raw_body)
                    candidates = transform_deepseek_request(
                        incoming,
                        shim.reasoning_effort,
                        shim.structured_mode,
                    )
                    response_payload = self.forward_chat(candidates)
                    self.send_json(200, response_payload)
                except urllib.error.HTTPError as exc:
                    body_text = exc.read().decode("utf-8", errors="replace")
                    try:
                        body = json.loads(body_text)
                    except json.JSONDecodeError:
                        body = {"error": {"message": body_text}}
                    self.send_json(exc.code, body)
                except Exception as exc:  # noqa: BLE001
                    self.send_json(502, {"error": {"message": str(exc)}})

            def forward_chat(self, candidates: list[tuple[dict[str, Any], str]]) -> dict[str, Any]:
                last_error: Exception | None = None
                for payload, target in candidates:
                    base_url = shim.beta_base_url if target == "beta" else shim.target_base_url
                    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    for attempt in range(5):
                        request = urllib.request.Request(
                            f"{base_url}/chat/completions",
                            data=data,
                            headers={
                                "Authorization": f"Bearer {shim.api_key}",
                                "Content-Type": "application/json",
                            },
                        )
                        try:
                            with urllib.request.urlopen(request, timeout=shim.timeout) as response:
                                response_payload = json.loads(response.read().decode("utf-8", errors="replace"))
                            self.normalize_tool_call_content(response_payload)
                            content = (
                                response_payload.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content")
                            )
                            if isinstance(content, str) and not content.strip():
                                last_error = RuntimeError("DeepSeek returned empty message content")
                                if attempt < 4:
                                    time.sleep(1.5 * (attempt + 1))
                                    continue
                            return response_payload
                        except urllib.error.HTTPError as exc:
                            if target == "beta" and 400 <= exc.code < 500:
                                body_text = exc.read().decode("utf-8", errors="replace")
                                last_error = RuntimeError(body_text)
                                break
                            raise
                        except Exception as exc:  # noqa: BLE001
                            last_error = exc
                            if attempt < 4:
                                time.sleep(1.5 * (attempt + 1))
                                continue
                raise RuntimeError(f"DeepSeek request failed after retries: {last_error}")

            def normalize_tool_call_content(self, response_payload: dict[str, Any]) -> None:
                choices = response_payload.get("choices")
                if not isinstance(choices, list) or not choices:
                    return
                message = choices[0].get("message")
                if not isinstance(message, dict):
                    return
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return
                tool_calls = message.get("tool_calls")
                if not isinstance(tool_calls, list) or not tool_calls:
                    return
                function = tool_calls[0].get("function", {})
                arguments = function.get("arguments")
                if isinstance(arguments, str) and arguments.strip():
                    message["content"] = arguments

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)


def build_autochecklist_args(argv: list[str], shim_url: str) -> list[str]:
    if not argv:
        return ["--help"]

    command = argv[0]
    rest = argv[1:]
    rest = add_default(rest, "--provider", "openai")
    rest = add_default(rest, "--base-url", shim_url)
    rest = add_default(rest, "--api-format", DEFAULT_API_FORMAT)

    if command in {"run", "score"}:
        rest = add_default(rest, "--scorer-model", DEFAULT_MODEL)
    if command == "score":
        rest = add_default(rest, "--scorer", "item")

    return [command, *rest]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    autochecklist = shutil.which("autochecklist")
    if not autochecklist:
        print("ERROR: autochecklist is not installed or not on PATH", file=sys.stderr)
        return 127

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY is not set", file=sys.stderr)
        return 2

    base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
    reasoning_effort = os.environ.get("DEEPSEEK_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)
    structured_mode = os.environ.get("DEEPSEEK_STRUCTURED_MODE", DEFAULT_STRUCTURED_MODE)
    timeout = int(os.environ.get("DEEPSEEK_SHIM_TIMEOUT", "300"))

    shim = DeepSeekProMaxShim(base_url, api_key, timeout, reasoning_effort, structured_mode)
    shim_url = shim.start()
    try:
        forwarded = build_autochecklist_args(args, shim_url)
        env = os.environ.copy()
        env["OPENAI_API_KEY"] = api_key
        proc = subprocess.run([autochecklist, *forwarded], env=env, check=False)
        return proc.returncode
    finally:
        shim.stop()


if __name__ == "__main__":
    raise SystemExit(main())
