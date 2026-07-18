#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_SMOKE_TIMEOUT_MS || 20000);
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const affinityHeader = process.env.AGENTRUN_SESSION_AFFINITY_HEADER || "x-agentrun-session-id";
const affinityKey = process.env.AGENTRUN_SESSION_AFFINITY_KEY || randomUUID();
const expectedMcpServers = (process.env.CODEX_EXPECTED_MCP_SERVERS || "")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean);

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

const ready = await fetchJson("/readyz", { method: "GET", headers: {} });
if (expectedMcpServers.length) {
  const configured = new Set(ready.mcpServers || []);
  const missing = expectedMcpServers.filter((name) => !configured.has(name));
  if (missing.length) {
    throw new Error(`missing expected MCP servers: ${missing.join(", ")}; readyz=${JSON.stringify(ready)}`);
  }
}
const created = await fetchJson("/sessions", {
  method: "POST",
  body: JSON.stringify({ cwd: "." }),
});

const sessionPath = `/sessions/${created.id}`;

try {
  const initialized = await fetchJson(`${sessionPath}/request`, {
    method: "POST",
    body: JSON.stringify({
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "ai4ss-skills-agentrun-gateway-smoke",
          title: "ai4ss-skills AgentRun gateway smoke",
          version: "0.1.0",
        },
      },
    }),
  });

  await fetchJson(`${sessionPath}/messages`, {
    method: "POST",
    body: JSON.stringify({ method: "initialized", params: {} }),
  });

  const threadStarted = await fetchJson(`${sessionPath}/request`, {
    method: "POST",
    body: JSON.stringify({
      id: 2,
      method: "thread/start",
      params: {
        model: smokeModel,
        cwd: ".",
      },
    }),
  });

  if (!threadStarted.response?.result?.thread?.id) {
    throw new Error(`thread/start did not return a thread id: ${JSON.stringify(threadStarted)}`);
  }

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    ready,
    sessionId: created.id,
    initialized: initialized.response?.result ? "ok" : initialized.response,
    model: smokeModel,
    threadId: threadStarted.response.result.thread.id,
  }, null, 2));
} finally {
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
