#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_TOOL_READ_TIMEOUT_MS || 120000);
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const affinityHeader = process.env.AGENTRUN_SESSION_AFFINITY_HEADER || "x-agentrun-session-id";
const affinityKey = process.env.AGENTRUN_SESSION_AFFINITY_KEY || randomUUID();
const workspaceFile = process.env.CODEX_TOOL_READ_FILE || "/workspace/skills/research-starter/SKILL.md";
const localMirror = process.env.CODEX_TOOL_READ_LOCAL_MIRROR || "skills/research-starter/SKILL.md";

function firstHeading(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  return text.split(/\r?\n/).find((line) => /^#\s+/.test(line)) || "";
}

const expectedHeading = process.env.CODEX_TOOL_READ_EXPECTED_HEADING
  || firstHeading(path.resolve(process.cwd(), localMirror));

const prompt = process.env.CODEX_TOOL_READ_PROMPT || `
Use the available local workspace/file-reading tools to read this exact file:

${workspaceFile}

Do not answer from memory. Do not infer from the prompt. After reading the file,
return exactly one line in this format:

TOOL_READ_OK: ${expectedHeading}
`.trim();

function headers(extra = {}) {
  return {
    "content-type": "application/json",
    ...(agentrunApiKey ? { "x-api-key": agentrunApiKey } : {}),
    ...(affinityHeader ? { [affinityHeader]: affinityKey } : {}),
    ...(token ? { authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function fetchJson(urlPath, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}${urlPath}`, {
      ...options,
      signal: controller.signal,
      headers: headers(options.headers || {}),
    });
    const body = await res.json();
    if (!res.ok) {
      throw new Error(`${options.method || "GET"} ${urlPath} failed: ${res.status} ${JSON.stringify(body)}`);
    }
    return body;
  } finally {
    clearTimeout(timer);
  }
}

function summarizeMessage(message) {
  const params = message?.params || {};
  const item = params.item || params.event || params.turn || params;
  const detail = params.message
    || params.reason
    || params.error?.message
    || item?.error?.message
    || item?.statusReason
    || null;
  return {
    method: message?.method,
    type: item?.type || item?.item?.type || null,
    title: item?.title || item?.name || item?.item?.name || null,
    status: item?.status || null,
    detail,
  };
}

function waitForTurnCompleted(response, threadId) {
  return new Promise(async (resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout waiting for turn/completed")), timeoutMs);
    let text = "";
    const methodCounts = {};
    const toolLikeEvents = [];
    const warnings = [];
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
          const dataLine = block.split(/\r?\n/).find((line) => line.startsWith("data: "));
          if (dataLine) {
            const event = JSON.parse(dataLine.slice("data: ".length));
            const message = event.message;
            if (message?.method) {
              methodCounts[message.method] = (methodCounts[message.method] || 0) + 1;
              if (message.method === "warning" && warnings.length < 20) {
                warnings.push(summarizeMessage(message));
              }
              if (/(tool|shell|exec|command|mcp|patch)/i.test(message.method)
                || /(tool|shell|exec|command|mcp|patch)/i.test(JSON.stringify(message.params || {}))) {
                if (toolLikeEvents.length < 20) toolLikeEvents.push(summarizeMessage(message));
              }
            }
            if (message?.method === "item/agentMessage/delta") {
              text += message.params?.delta || "";
            }
            if (message?.method === "turn/completed" && message.params?.threadId === threadId) {
              clearTimeout(timer);
              await reader.cancel().catch(() => {});
              resolve({ message, text, methodCounts, toolLikeEvents, warnings });
              return;
            }
          }
          idx = buffer.indexOf("\n\n");
        }
      }
      clearTimeout(timer);
      reject(new Error("SSE stream ended before turn/completed"));
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

  const initialized = await fetchJson(`${sessionPath}/request`, {
    method: "POST",
    body: JSON.stringify({
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "ai4ss-skills-agentrun-tool-read-smoke",
          title: "ai4ss-skills AgentRun tool read smoke",
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

  const threadId = threadStarted.response?.result?.thread?.id;
  if (!threadId) {
    throw new Error(`thread/start did not return a thread id: ${JSON.stringify(threadStarted)}`);
  }

  const turnCompleted = waitForTurnCompleted(streamResponse, threadId);

  const turnStarted = await fetchJson(`${sessionPath}/request?timeoutMs=30000`, {
    method: "POST",
    body: JSON.stringify({
      id: 3,
      method: "turn/start",
      params: {
        threadId,
        model: smokeModel,
        input: [
          {
            type: "text",
            text: prompt,
            text_elements: [],
          },
        ],
      },
    }),
  });

  const completed = await turnCompleted;
  const turn = completed.message.params.turn;
  if (turn.status !== "completed") {
    throw new Error(`turn completed with status ${turn.status}: ${JSON.stringify(turn.error || {})}`);
  }

  if (!completed.text.includes(`TOOL_READ_OK: ${expectedHeading}`)) {
    throw new Error(
      `tool-read output did not include expected marker ${JSON.stringify(expectedHeading)}; `
      + `preview=${JSON.stringify(completed.text.slice(0, 800))}`,
    );
  }
  if (/DSML|tool_calls|<\|/.test(completed.text)) {
    throw new Error(`model emitted raw tool-call markup instead of completing the turn: ${completed.text.slice(0, 800)}`);
  }

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    sessionId: created.id,
    initialized: initialized.response?.result ? "ok" : initialized.response,
    threadId,
    turnId: turnStarted.response?.result?.turn?.id || turn.id,
    model: smokeModel,
    workspaceFile,
    expectedHeading,
    text: completed.text.trim(),
    toolLikeEvents: completed.toolLikeEvents,
    warnings: completed.warnings,
    methodCounts: completed.methodCounts,
  }, null, 2));
} finally {
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
