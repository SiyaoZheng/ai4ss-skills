#!/usr/bin/env node
import process from "node:process";

const strict = process.argv.includes("--strict") || process.env.DEEPSEEK_SMOKE_STRICT === "true";
const apiKey = process.env.DEEPSEEK_API_KEY || "";
const baseUrl = (process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com").replace(/\/$/, "");
const model = process.env.DEEPSEEK_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const timeoutMs = Number(process.env.DEEPSEEK_SMOKE_TIMEOUT_MS || 20000);

function finish(status, payload) {
  console.log(JSON.stringify(payload, null, 2));
  process.exit(status);
}

function redact(value) {
  return String(value)
    .replace(/(Bearer\s+)[A-Za-z0-9._~+/=-]+/g, "$1[REDACTED]")
    .replace(/(sk-[A-Za-z0-9_-]{8})[A-Za-z0-9_-]+/g, "$1[REDACTED]")
    .replace(/(AKIA|LTAI)[A-Za-z0-9]+/g, "[REDACTED_ACCESS_KEY]");
}

if (!apiKey) {
  finish(strict ? 1 : 0, {
    ok: false,
    skipped: true,
    strict,
    reason: "DEEPSEEK_API_KEY is not set",
  });
}

const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), timeoutMs);

try {
  const res = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        {
          role: "system",
          content: "You are a deployment smoke test. Reply with ok.",
        },
        {
          role: "user",
          content: "Return exactly: ok",
        },
      ],
      stream: false,
      max_tokens: 8,
    }),
  });

  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = { raw: redact(text.slice(0, 500)) };
  }

  if (!res.ok) {
    finish(1, {
      ok: false,
      baseUrl,
      model,
      status: res.status,
      response: body,
    });
  }

  finish(0, {
    ok: true,
    baseUrl,
    model,
    responseId: body.id || null,
    usage: body.usage || null,
  });
} catch (err) {
  finish(1, {
    ok: false,
    baseUrl,
    model,
    error: err.message || String(err),
  });
} finally {
  clearTimeout(timer);
}
