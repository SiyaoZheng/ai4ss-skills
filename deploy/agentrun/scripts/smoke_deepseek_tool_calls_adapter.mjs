#!/usr/bin/env node
import http from "node:http";
import { spawn } from "node:child_process";
import process from "node:process";

const timeoutMs = Number(process.env.DEEPSEEK_TOOL_CALL_SMOKE_TIMEOUT_MS || 30000);
const gatewayScript = new URL("../gateway/server.mjs", import.meta.url).pathname;

function finish(status, payload) {
  console.log(JSON.stringify(payload, null, 2));
  process.exit(status);
}

function listen(server, port = 0) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => resolve(server.address().port));
  });
}

function closeServer(server) {
  return new Promise((resolve) => server.close(() => resolve()));
}

async function freePort() {
  const server = http.createServer();
  const port = await listen(server);
  await closeServer(server);
  return port;
}

async function waitForReady(url, child) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    if (child.exitCode != null) {
      throw new Error(`gateway exited early with code ${child.exitCode}`);
    }
    try {
      const res = await fetch(url);
      if (res.ok) return await res.json();
      lastError = new Error(`readyz returned ${res.status}`);
    } catch (err) {
      lastError = err;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw lastError || new Error("timeout waiting for gateway");
}

async function readSse(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const events = [];
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
        if (data !== "[DONE]") events.push(JSON.parse(data));
      }
      idx = buffer.indexOf("\n\n");
    }
  }
  return events;
}

let upstreamRequest = null;
const upstreamRequests = [];
const upstream = http.createServer(async (req, res) => {
  if (req.method !== "POST" || req.url !== "/chat/completions") {
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
    return;
  }

  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  upstreamRequest = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  upstreamRequests.push(upstreamRequest);

  res.writeHead(200, {
    "content-type": "text/event-stream; charset=utf-8",
    "cache-control": "no-store",
  });

  const base = {
    id: "chatcmpl_fake_tool_call",
    object: "chat.completion.chunk",
    created: Math.floor(Date.now() / 1000),
    model: upstreamRequest.model || "deepseek-v4-flash",
  };
  const send = (payload) => res.write(`data: ${JSON.stringify({ ...base, ...payload })}\n\n`);

  if (upstreamRequest.messages?.some((message) => message.role === "tool")) {
    send({ choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }] });
    send({ choices: [{ index: 0, delta: { content: "done" }, finish_reason: null }] });
    send({
      choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
      usage: { prompt_tokens: 19, completion_tokens: 1, total_tokens: 20 },
    });
    res.write("data: [DONE]\n\n");
    res.end();
    return;
  }

  send({ choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }] });
  send({
    choices: [{
      index: 0,
      delta: {
        tool_calls: [{
          index: 0,
          id: "call_fake_read",
          type: "function",
          function: { name: "research__read_file", arguments: "" },
        }],
      },
      finish_reason: null,
    }],
  });
  send({
    choices: [{
      index: 0,
      delta: {
        tool_calls: [{
          index: 0,
          function: { arguments: "{\"filePath\":\"" },
        }],
      },
      finish_reason: null,
    }],
  });
  send({
    choices: [{
      index: 0,
      delta: {
        tool_calls: [{
          index: 0,
          function: { arguments: "/workspace/AGENTS.md\"}" },
        }],
      },
      finish_reason: null,
    }],
  });
  send({
    choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }],
    usage: { prompt_tokens: 11, completion_tokens: 7, total_tokens: 18 },
  });
  res.write("data: [DONE]\n\n");
  res.end();
});

let gateway = null;
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), timeoutMs);

try {
  const upstreamPort = await listen(upstream);
  const gatewayPort = await freePort();

  gateway = spawn(process.execPath, [gatewayScript], {
    env: {
      ...process.env,
      HOST: "127.0.0.1",
      PORT: String(gatewayPort),
      ALLOW_UNAUTHENTICATED: "true",
      DEEPSEEK_API_KEY: "fake-key",
      DEEPSEEK_BASE_URL: `http://127.0.0.1:${upstreamPort}`,
      CODEX_WORKSPACE_DIR: process.cwd(),
      DEEPSEEK_TOOL_STRICT: "false",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let stderr = "";
  gateway.stderr.setEncoding("utf8");
  gateway.stderr.on("data", (chunk) => {
    stderr += chunk;
  });

  const baseUrl = `http://127.0.0.1:${gatewayPort}`;
  await waitForReady(`${baseUrl}/readyz`, gateway);

  const res = await fetch(`${baseUrl}/internal/deepseek/v1/responses`, {
    method: "POST",
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      authorization: "Bearer fake-key",
    },
    body: JSON.stringify({
      model: "deepseek-v4-flash",
      stream: true,
      input: "Read the project AGENTS.md.",
      tools: [{
        type: "namespace",
        name: "research",
        description: "Research workflow tools.",
        tools: [{
          type: "function",
          name: "read_file",
          description: "Read a workspace file.",
          parameters: {
            type: "object",
            properties: { filePath: { type: "string" } },
            required: ["filePath"],
            additionalProperties: false,
          },
          strict: true,
        }],
      }],
      tool_choice: "auto",
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`adapter request failed ${res.status}: ${await res.text()}`);
  }

  const events = await readSse(res);
  const upstreamTool = upstreamRequest?.tools?.[0]?.function;
  const done = events.find((event) => event.type === "response.output_item.done" && event.item?.type === "function_call");
  const argsDone = events.find((event) => event.type === "response.function_call_arguments.done");
  const completed = events.find((event) => event.type === "response.completed");

  if (!upstreamRequest) throw new Error("fake upstream did not receive a request");
  if (upstreamTool?.name !== "research__read_file") {
    throw new Error(`unexpected upstream tool name: ${JSON.stringify(upstreamRequest.tools)}`);
  }
  if (Object.hasOwn(upstreamTool, "strict")) {
    throw new Error("strict leaked to DeepSeek tool definition without DEEPSEEK_TOOL_STRICT=true");
  }
  if (!events.some((event) => event.type === "response.function_call_arguments.delta")) {
    throw new Error("missing response.function_call_arguments.delta");
  }
  if (!argsDone?.arguments?.includes("/workspace/AGENTS.md")) {
    throw new Error(`missing arguments done payload: ${JSON.stringify(argsDone)}`);
  }
  if (done?.item?.call_id !== "call_fake_read" || done.item.name !== "read_file" || done.item.namespace !== "research") {
    throw new Error(`function call item was not restored to Responses namespace shape: ${JSON.stringify(done)}`);
  }
  if (!completed) throw new Error("missing response.completed");

  const followup = await fetch(`${baseUrl}/internal/deepseek/v1/responses`, {
    method: "POST",
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      authorization: "Bearer fake-key",
    },
    body: JSON.stringify({
      model: "deepseek-v4-flash",
      stream: true,
      input: [
        {
          type: "function_call",
          call_id: "call_fake_read",
          name: "read_file",
          arguments: "{\"filePath\":\"/workspace/AGENTS.md\"}",
        },
        {
          type: "shell_call_output",
          call_id: "call_fake_read",
          output: [{
            stdout: "# Agent Instructions\n",
            stderr: "",
            outcome: { type: "exit", exit_code: 0 },
          }],
        },
      ],
    }),
  });
  if (!followup.ok || !followup.body) {
    throw new Error(`follow-up adapter request failed ${followup.status}: ${await followup.text()}`);
  }
  await readSse(followup);
  const followupToolMessage = upstreamRequests.at(-1)?.messages?.find((message) => message.role === "tool");
  if (followupToolMessage?.tool_call_id !== "call_fake_read"
    || !followupToolMessage.content.includes("# Agent Instructions")) {
    throw new Error(`follow-up shell output was not converted to a Chat tool message: ${JSON.stringify(upstreamRequests.at(-1)?.messages)}`);
  }

  const multiFollowup = await fetch(`${baseUrl}/internal/deepseek/v1/responses`, {
    method: "POST",
    signal: controller.signal,
    headers: {
      "content-type": "application/json",
      authorization: "Bearer fake-key",
    },
    body: JSON.stringify({
      model: "deepseek-v4-flash",
      stream: true,
      input: [
        {
          type: "function_call",
          call_id: "call_fake_one",
          name: "read_file",
          namespace: "research",
          arguments: "{\"filePath\":\"/workspace/AGENTS.md\"}",
        },
        {
          type: "function_call",
          call_id: "call_fake_two",
          name: "read_file",
          namespace: "research",
          arguments: "{\"filePath\":\"/workspace/skills/research-starter/SKILL.md\"}",
        },
        {
          type: "shell_call_output",
          call_id: "call_fake_one",
          output: [{ stdout: "# Agent Instructions\n", stderr: "", outcome: { type: "exit", exit_code: 0 } }],
        },
        {
          type: "shell_call_output",
          call_id: "call_fake_two",
          output: [{ stdout: "# Research Starter\n", stderr: "", outcome: { type: "exit", exit_code: 0 } }],
        },
      ],
      tools: [{
        type: "namespace",
        name: "research",
        description: "Research workflow tools.",
        tools: [{
          type: "function",
          name: "read_file",
          description: "Read a workspace file.",
          parameters: {
            type: "object",
            properties: { filePath: { type: "string" } },
            required: ["filePath"],
            additionalProperties: false,
          },
          strict: true,
        }],
      }],
    }),
  });
  if (!multiFollowup.ok || !multiFollowup.body) {
    throw new Error(`multi follow-up adapter request failed ${multiFollowup.status}: ${await multiFollowup.text()}`);
  }
  await readSse(multiFollowup);
  const multiMessages = upstreamRequests.at(-1)?.messages || [];
  const assistantToolMessages = multiMessages.filter((message) => message.role === "assistant" && Array.isArray(message.tool_calls));
  const multiToolMessages = multiMessages.filter((message) => message.role === "tool");
  if (assistantToolMessages.length !== 1 || assistantToolMessages[0].tool_calls.length !== 2) {
    throw new Error(`multi follow-up function calls were not coalesced into one assistant tool_calls message: ${JSON.stringify(multiMessages)}`);
  }
  if (assistantToolMessages[0].tool_calls.some((toolCall) => toolCall.function.name !== "research__read_file")) {
    throw new Error(`multi follow-up namespace tool names were not restored for Chat history: ${JSON.stringify(assistantToolMessages[0])}`);
  }
  if (multiToolMessages.length !== 2
    || !multiToolMessages.some((message) => message.tool_call_id === "call_fake_one")
    || !multiToolMessages.some((message) => message.tool_call_id === "call_fake_two")) {
    throw new Error(`multi follow-up outputs were not converted to Chat tool messages: ${JSON.stringify(multiMessages)}`);
  }

  finish(0, {
    ok: true,
    upstreamTool,
    functionCall: done.item,
    followupToolMessage,
    multiFollowupAssistant: assistantToolMessages[0],
    multiFollowupToolMessages: multiToolMessages,
    eventTypes: events.map((event) => event.type),
  });
} catch (err) {
  finish(1, {
    ok: false,
    error: err.message || String(err),
  });
} finally {
  clearTimeout(timer);
  controller.abort();
  if (gateway && gateway.exitCode == null) {
    gateway.kill("SIGTERM");
    setTimeout(() => {
      if (gateway.exitCode == null) gateway.kill("SIGKILL");
    }, 1000).unref();
  }
  await closeServer(upstream).catch(() => {});
}
