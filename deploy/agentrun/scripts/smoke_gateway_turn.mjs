#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_TURN_SMOKE_TIMEOUT_MS || 90000);
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const prompt = process.env.CODEX_TURN_SMOKE_PROMPT || "Return exactly: ok";
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

function waitForTurnCompleted(response, threadId) {
  return new Promise(async (resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout waiting for turn/completed")), timeoutMs);
    let textPreview = "";
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
            if (message?.method === "item/agentMessage/delta") {
              textPreview += message.params?.delta || "";
            }
            if (message?.method === "turn/completed" && message.params?.threadId === threadId) {
              clearTimeout(timer);
              await reader.cancel().catch(() => {});
              resolve({ message, textPreview });
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
          name: "ai4ss-skills-agentrun-turn-smoke",
          title: "ai4ss-skills AgentRun turn smoke",
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

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    sessionId: created.id,
    initialized: initialized.response?.result ? "ok" : initialized.response,
    threadId,
    turnId: turnStarted.response?.result?.turn?.id || turn.id,
    model: smokeModel,
    textPreview: completed.textPreview.slice(0, 120),
  }, null, 2));
} finally {
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
