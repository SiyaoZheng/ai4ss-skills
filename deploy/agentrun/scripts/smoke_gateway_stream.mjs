#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_SMOKE_TIMEOUT_MS || 20000);
const affinityHeader = process.env.AGENTRUN_SESSION_AFFINITY_HEADER || "x-agentrun-session-id";
const affinityKey = process.env.AGENTRUN_SESSION_AFFINITY_KEY || randomUUID();

function headers(extra = {}) {
  return {
    "content-type": "application/json",
    ...(agentrunApiKey ? { "x-api-key": agentrunApiKey } : {}),
    ...(affinityHeader ? { [affinityHeader]: affinityKey } : {}),
    ...(token ? { authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function fetchJson(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}${path}`, {
      ...options,
      signal: controller.signal,
      headers: headers(options.headers || {}),
    });
    const body = await res.json();
    if (!res.ok) {
      throw new Error(`${options.method || "GET"} ${path} failed: ${res.status} ${JSON.stringify(body)}`);
    }
    return body;
  } finally {
    clearTimeout(timer);
  }
}

function waitForSseMessage(response, predicate) {
  return new Promise(async (resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout waiting for SSE event")), timeoutMs);
    try {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx = buffer.indexOf("\n\n");
        while (idx !== -1) {
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const dataLine = block.split("\n").find((line) => line.startsWith("data: "));
          if (dataLine) {
            const event = JSON.parse(dataLine.slice("data: ".length));
            if (predicate(event)) {
              clearTimeout(timer);
              await reader.cancel().catch(() => {});
              resolve(event);
              return;
            }
          }
          idx = buffer.indexOf("\n\n");
        }
      }
      clearTimeout(timer);
      reject(new Error("SSE stream ended before expected event"));
    } catch (err) {
      clearTimeout(timer);
      reject(err);
    }
  });
}

const created = await fetchJson("/sessions", {
  method: "POST",
  body: JSON.stringify({ cwd: "." }),
});

const sessionPath = `/sessions/${created.id}`;

try {
  const streamResponse = await fetch(`${baseUrl}${sessionPath}/events`, {
    method: "GET",
    headers: headers({ accept: "text/event-stream" }),
  });
  if (!streamResponse.ok || !streamResponse.body) {
    throw new Error(`events stream failed: ${streamResponse.status}`);
  }

  const eventPromise = waitForSseMessage(streamResponse, (event) => {
    return event.type === "message" && event.message?.id === 1;
  });

  const initialized = await fetchJson(`${sessionPath}/request`, {
    method: "POST",
    body: JSON.stringify({
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "ai4ss-skills-agentrun-stream-smoke",
          title: "ai4ss-skills AgentRun stream smoke",
          version: "0.1.0",
        },
      },
    }),
  });

  const streamedEvent = await eventPromise;

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    sessionId: created.id,
    responseResult: initialized.response?.result ? "ok" : initialized.response,
    streamedMessageId: streamedEvent.message.id,
  }, null, 2));
} finally {
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
