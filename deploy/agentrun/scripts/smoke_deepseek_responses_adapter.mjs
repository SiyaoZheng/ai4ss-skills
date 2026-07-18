#!/usr/bin/env node
import process from "node:process";

const baseUrl = (process.env.DEEPSEEK_RESPONSES_ADAPTER_URL || "http://127.0.0.1:9000/internal/deepseek/v1").replace(/\/$/, "");
const apiKey = process.env.DEEPSEEK_API_KEY || "";
const model = process.env.DEEPSEEK_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const timeoutMs = Number(process.env.DEEPSEEK_SMOKE_TIMEOUT_MS || 30000);
const strict = process.argv.includes("--strict") || process.env.DEEPSEEK_SMOKE_STRICT === "true";

function finish(status, payload) {
  console.log(JSON.stringify(payload, null, 2));
  process.exit(status);
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
  const res = await fetch(`${baseUrl}/responses`, {
    method: "POST",
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      stream: true,
      input: "Return exactly: ok",
      max_output_tokens: 16,
    }),
  });

  if (!res.ok || !res.body) {
    const body = await res.text().catch(() => "");
    throw new Error(`adapter failed ${res.status}: ${body.slice(0, 300)}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  let text = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx = buffer.indexOf("\n\n");
    while (idx !== -1) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLine = block.split(/\r?\n/).find((line) => line.startsWith("data: "));
      if (dataLine) {
        const data = dataLine.slice("data: ".length);
        if (data !== "[DONE]") {
          const event = JSON.parse(data);
          if (event.type === "response.output_text.delta") text += event.delta || "";
          if (event.type === "response.completed") completed = true;
        }
      }
      idx = buffer.indexOf("\n\n");
    }
  }

  if (!completed) {
    throw new Error("adapter stream ended without response.completed");
  }

  finish(0, {
    ok: true,
    baseUrl,
    model,
    completed,
    textPreview: text.slice(0, 80),
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
