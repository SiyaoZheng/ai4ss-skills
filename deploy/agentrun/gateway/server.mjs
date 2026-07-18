#!/usr/bin/env node
import http from "node:http";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { copyFileSync, createReadStream, existsSync, mkdirSync, rmSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const host = process.env.HOST || "0.0.0.0";
const port = numberEnv("PORT", 9000);
const codexBin = process.env.CODEX_BIN || "codex";
const workspaceRoot = path.resolve(process.env.CODEX_WORKSPACE_DIR || "/workspace");
const idleMs = numberEnv("SESSION_IDLE_MS", 15 * 60 * 1000);
const maxSessions = numberEnv("MAX_SESSIONS", 16);
const eventBufferLimit = numberEnv("SESSION_EVENT_BUFFER", 200);
const bearerToken = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const allowUnauthenticated = process.env.ALLOW_UNAUTHENTICATED === "true";
const deepSeekBaseUrl = (process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com").replace(/\/$/, "");
const deepSeekResponsesAdapter = process.env.DEEPSEEK_RESPONSES_ADAPTER !== "false";
const deepSeekThinking = process.env.DEEPSEEK_THINKING || "disabled";
const baseCodexHome = process.env.CODEX_HOME || path.join(process.env.HOME || "/tmp", ".codex");
const sessionHomeRoot = process.env.CODEX_SESSION_HOME_ROOT || path.join(process.env.HOME || "/tmp", ".codex-sessions");
const keepSessionHome = process.env.KEEP_CODEX_SESSION_HOME === "true";
const mcpServers = (process.env.CODEX_MCP_ENABLED_NAMES || "")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean);

const sessions = new Map();

function numberEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function json(res, status, value) {
  const body = JSON.stringify(value);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "cache-control": "no-store",
  });
  res.end(body);
}

function text(res, status, value) {
  res.writeHead(status, {
    "content-type": "text/plain; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(value);
}

function isReady() {
  return {
    ok: (allowUnauthenticated || Boolean(bearerToken)) && existsSync(workspaceRoot),
    authConfigured: allowUnauthenticated || Boolean(bearerToken),
    unauthenticatedMode: allowUnauthenticated,
    workspaceRoot,
    codexBin,
    sessions: sessions.size,
    maxSessions,
    deepSeekResponsesAdapter,
    sessionHomeRoot,
    mcpServers,
  };
}

function authorized(req) {
  if (allowUnauthenticated) return true;
  if (!bearerToken) return false;
  const auth = req.headers.authorization || "";
  const apiKey = req.headers["x-api-key"] || req.headers["x-codex-gateway-token"] || "";
  return auth === `Bearer ${bearerToken}` || apiKey === bearerToken;
}

function safeCwd(requested) {
  if (!requested) return workspaceRoot;
  const resolved = path.resolve(workspaceRoot, requested);
  if (resolved === workspaceRoot || resolved.startsWith(`${workspaceRoot}${path.sep}`)) {
    return resolved;
  }
  throw new Error("cwd must stay inside CODEX_WORKSPACE_DIR");
}

function safeWorkspacePath(requested) {
  if (!requested) {
    const err = new Error("path query parameter is required");
    err.status = 400;
    throw err;
  }
  const resolved = path.resolve(workspaceRoot, requested);
  if (resolved === workspaceRoot || resolved.startsWith(`${workspaceRoot}${path.sep}`)) {
    return resolved;
  }
  const err = new Error("artifact path must stay inside CODEX_WORKSPACE_DIR");
  err.status = 400;
  throw err;
}

function contentTypeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".pdf") return "application/pdf";
  if (ext === ".txt" || ext === ".log" || ext === ".tex" || ext === ".md") return "text/plain; charset=utf-8";
  if (ext === ".json") return "application/json; charset=utf-8";
  if (ext === ".csv") return "text/csv; charset=utf-8";
  return "application/octet-stream";
}

async function readBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 1024 * 1024) throw new Error("request body too large");
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  const textBody = Buffer.concat(chunks).toString("utf8");
  return textBody ? JSON.parse(textBody) : {};
}

function isLoopback(remoteAddress = "") {
  return [
    "127.0.0.1",
    "::1",
    "::ffff:127.0.0.1",
    "localhost",
  ].includes(remoteAddress);
}

function deepSeekChatCompletionsUrl() {
  return `${deepSeekBaseUrl}/chat/completions`;
}

function normalizeChatRole(role) {
  if (role === "assistant") return "assistant";
  if (role === "system" || role === "developer") return "system";
  return "user";
}

function textFromContent(content) {
  if (content == null) return "";
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map((part) => textFromContent(part)).filter(Boolean).join("\n");
  }
  if (typeof content === "object") {
    if (typeof content.text === "string") return content.text;
    if (typeof content.content === "string") return content.content;
    if (Array.isArray(content.content)) return textFromContent(content.content);
    if (typeof content.input_text === "string") return content.input_text;
    if (typeof content.output_text === "string") return content.output_text;
  }
  return "";
}

function jsonString(value) {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function contentPartsToText(content) {
  if (!Array.isArray(content)) return textFromContent(content);
  return content.map((part) => textFromContent(part)).filter(Boolean).join("\n");
}

function toolOutputContent(output) {
  const text = textFromContent(output);
  if (text) return text;
  return jsonString(output);
}

function normalizeToolCallId(item) {
  return item.call_id || item.tool_call_id || item.id || `call_${randomUUID().replaceAll("-", "")}`;
}

function responseToolMapKey(namespace, name) {
  return `${namespace || ""}\0${name || ""}`;
}

function safeChatFunctionName(name) {
  const cleaned = String(name || "")
    .trim()
    .replace(/[^A-Za-z0-9_-]/g, "_")
    .replace(/^_+|_+$/g, "");
  if (cleaned) return cleaned.slice(0, 64);
  return `tool_${randomUUID().replaceAll("-", "").slice(0, 24)}`;
}

function uniqueChatFunctionName(baseName, usedNames) {
  const base = safeChatFunctionName(baseName);
  if (!usedNames.has(base)) {
    usedNames.add(base);
    return base;
  }
  let counter = 2;
  while (usedNames.has(`${base}_${counter}`)) counter += 1;
  const unique = `${base}_${counter}`;
  usedNames.add(unique);
  return unique;
}

function chatFunctionNameFromResponsesItem(item, responseToolNameMap) {
  const name = item.name || item.function?.name || "";
  const namespace = item.namespace || item.function?.namespace || "";
  return responseToolNameMap.get(responseToolMapKey(namespace, name))
    || responseToolNameMap.get(responseToolMapKey("", name))
    || name;
}

function messagesFromResponsesBody(body, responseToolNameMap = new Map()) {
  const messages = [];
  const instructions = textFromContent(body.instructions);
  if (instructions) {
    messages.push({ role: "system", content: instructions });
  }

  const pendingAssistant = {
    content: "",
    toolCalls: [],
  };

  function flushPendingAssistant() {
    if (!pendingAssistant.toolCalls.length) return;
    messages.push({
      role: "assistant",
      content: pendingAssistant.content || null,
      tool_calls: pendingAssistant.toolCalls,
    });
    pendingAssistant.content = "";
    pendingAssistant.toolCalls = [];
  }

  const input = body.input;
  if (typeof input === "string") {
    messages.push({ role: "user", content: input });
  } else if (Array.isArray(input)) {
    for (const item of input) {
      if (typeof item === "string") {
        messages.push({ role: "user", content: item });
        continue;
      }
      if (!item || typeof item !== "object") continue;
      if (
        item.call_id
        && (
          item.type === "function_call_output"
          || item.type === "tool_call_output"
          || String(item.type || "").endsWith("_output")
          || Object.hasOwn(item, "output")
        )
      ) {
        flushPendingAssistant();
        messages.push({
          role: "tool",
          tool_call_id: normalizeToolCallId(item),
          content: toolOutputContent(item.output),
        });
        continue;
      }
      if (item.type === "function_call") {
        const content = item.content ? contentPartsToText(item.content) : "";
        if (content) {
          pendingAssistant.content = pendingAssistant.content
            ? `${pendingAssistant.content}\n${content}`
            : content;
        }
        pendingAssistant.toolCalls.push({
          id: normalizeToolCallId(item),
          type: "function",
          function: {
            name: chatFunctionNameFromResponsesItem(item, responseToolNameMap),
            arguments: jsonString(item.arguments),
          },
        });
        continue;
      }
      const content = textFromContent(item.content ?? item.text ?? item.input);
      if (!content) continue;
      flushPendingAssistant();
      messages.push({
        role: normalizeChatRole(item.role),
        content,
      });
    }
  }
  flushPendingAssistant();

  if (!messages.length) {
    messages.push({ role: "user", content: "Continue." });
  }

  return messages;
}

function functionToolFromResponsesTool(tool, namespace, usedNames, toolNameMap) {
  if (!tool || typeof tool !== "object") return null;
  const name = tool.name || tool.function?.name;
  if (tool.type !== "function" || !name) return null;
  const chatName = uniqueChatFunctionName(namespace ? `${namespace}__${name}` : name, usedNames);
  toolNameMap.set(chatName, {
    name,
    namespace: namespace || "",
  });
  if (!name) return null;
  const functionSpec = {
    name: chatName,
    description: tool.description || tool.function?.description || "",
    parameters: tool.parameters || tool.function?.parameters || { type: "object", properties: {} },
  };
  if (process.env.DEEPSEEK_TOOL_STRICT === "true") {
    if (tool.strict != null) functionSpec.strict = Boolean(tool.strict);
    if (tool.function?.strict != null) functionSpec.strict = Boolean(tool.function.strict);
  }
  return {
    type: "function",
    function: functionSpec,
  };
}

function collectFunctionTools(tool, namespace, usedNames, toolNameMap, responseToolNameMap, output) {
  if (!tool || typeof tool !== "object") return;
  if (tool.type === "namespace" && Array.isArray(tool.tools)) {
    const childNamespace = namespace ? `${namespace}__${tool.name || "namespace"}` : tool.name || namespace;
    for (const child of tool.tools) {
      collectFunctionTools(child, childNamespace, usedNames, toolNameMap, responseToolNameMap, output);
    }
    return;
  }
  const converted = functionToolFromResponsesTool(tool, namespace, usedNames, toolNameMap);
  if (converted) {
    responseToolNameMap.set(responseToolMapKey(namespace, tool.name || tool.function?.name), converted.function.name);
    output.push(converted);
  }
}

function toolsFromResponsesBody(body) {
  const tools = [];
  const toolNameMap = new Map();
  const responseToolNameMap = new Map();
  const usedNames = new Set();
  if (Array.isArray(body.tools)) {
    for (const tool of body.tools) {
      collectFunctionTools(tool, "", usedNames, toolNameMap, responseToolNameMap, tools);
    }
  }
  return { tools, toolNameMap, responseToolNameMap };
}

function toolChoiceFromResponsesBody(body) {
  const choice = body.tool_choice;
  if (!choice || choice === "auto" || choice === "none" || choice === "required") return choice;
  if (choice.type === "function" && choice.name) {
    return { type: "function", function: { name: choice.name } };
  }
  if (choice.type === "function" && choice.function?.name) {
    return { type: "function", function: { name: choice.function.name } };
  }
  return undefined;
}

function deepSeekRequestConfig(body) {
  const { tools, toolNameMap, responseToolNameMap } = toolsFromResponsesBody(body);
  const out = {
    model: body.model || process.env.CODEX_MODEL || "deepseek-v4-flash",
    messages: messagesFromResponsesBody(body, responseToolNameMap),
    stream: body.stream !== false,
    thinking: { type: deepSeekThinking },
  };

  if (tools.length) out.tools = tools;
  const toolChoice = toolChoiceFromResponsesBody(body);
  if (toolChoice) out.tool_choice = toolChoice;
  if (body.parallel_tool_calls != null) out.parallel_tool_calls = Boolean(body.parallel_tool_calls);
  if (Number.isFinite(body.max_output_tokens)) out.max_tokens = body.max_output_tokens;
  if (Number.isFinite(body.temperature)) out.temperature = body.temperature;
  if (Number.isFinite(body.top_p)) out.top_p = body.top_p;
  if (body.response_format) out.response_format = body.response_format;
  if (body.stop) out.stop = body.stop;

  return { chatBody: out, toolNameMap };
}

function createSessionHome(id) {
  const sessionHome = path.join(sessionHomeRoot, id);
  mkdirSync(sessionHome, { recursive: true });
  const sourceConfig = path.join(baseCodexHome, "config.toml");
  const targetConfig = path.join(sessionHome, "config.toml");
  if (existsSync(sourceConfig) && !existsSync(targetConfig)) {
    copyFileSync(sourceConfig, targetConfig);
  }
  return sessionHome;
}

function responseUsageFromDeepSeek(usage) {
  return {
    input_tokens: usage?.prompt_tokens || 0,
    input_tokens_details: {
      cached_tokens: usage?.prompt_cache_hit_tokens || usage?.prompt_tokens_details?.cached_tokens || 0,
    },
    output_tokens: usage?.completion_tokens || 0,
    output_tokens_details: {
      reasoning_tokens: usage?.completion_tokens_details?.reasoning_tokens || 0,
    },
    total_tokens: usage?.total_tokens || 0,
  };
}

function messageOutputItem({ id, status, textValue }) {
  return {
    id,
    type: "message",
    status,
    role: "assistant",
    content: [
      {
        type: "output_text",
        text: textValue || "",
        annotations: [],
        logprobs: [],
      },
    ],
  };
}

function functionCallOutputItem({ id, callId, name, namespace, argumentsValue, status = "completed" }) {
  const item = {
    id,
    type: "function_call",
    status,
    call_id: callId,
    name,
    arguments: argumentsValue || "",
  };
  if (namespace) item.namespace = namespace;
  return item;
}

function buildResponseObject({ id, model, status, outputItems = [], createdAt, completedAt, usage }) {
  return {
    id,
    object: "response",
    created_at: createdAt,
    completed_at: completedAt || null,
    error: null,
    incomplete_details: null,
    instructions: null,
    metadata: {},
    model,
    output: outputItems,
    parallel_tool_calls: true,
    temperature: null,
    tool_choice: "auto",
    tools: [],
    top_p: null,
    status,
    usage: responseUsageFromDeepSeek(usage),
  };
}

function writeResponsesEvent(res, event) {
  res.write(`event: ${event.type}\n`);
  res.write(`data: ${JSON.stringify(event)}\n\n`);
}

async function proxyDeepSeekResponses(req, res) {
  if (!deepSeekResponsesAdapter) {
    return json(res, 404, { error: "DeepSeek Responses adapter is disabled" });
  }
  if (!isLoopback(req.socket.remoteAddress)) {
    return json(res, 403, { error: "DeepSeek Responses adapter is loopback-only" });
  }

  const authHeader = req.headers.authorization || (process.env.DEEPSEEK_API_KEY ? `Bearer ${process.env.DEEPSEEK_API_KEY}` : "");
  if (!authHeader) {
    return json(res, 401, { error: "DEEPSEEK_API_KEY is required" });
  }

  const requestBody = await readBody(req);
  const { chatBody, toolNameMap } = deepSeekRequestConfig(requestBody);
  const responseId = `resp_${randomUUID().replaceAll("-", "")}`;
  const createdAt = Math.floor(Date.now() / 1000);

  if (chatBody.stream === false) {
    const upstream = await fetch(deepSeekChatCompletionsUrl(), {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: authHeader,
      },
      body: JSON.stringify(chatBody),
    });
    const upstreamBody = await upstream.json().catch(async () => ({ error: await upstream.text() }));
    if (!upstream.ok) {
      return json(res, upstream.status, { error: "DeepSeek chat completion failed", upstream: upstreamBody });
    }
    const message = upstreamBody.choices?.[0]?.message || {};
    const outputItems = [];
    const textValue = message.content || "";
    if (textValue) {
      outputItems.push(messageOutputItem({
        id: `msg_${responseId}`,
        status: "completed",
        textValue,
      }));
    }
    for (const toolCall of message.tool_calls || []) {
      const mapped = toolNameMap.get(toolCall.function?.name || "") || { name: toolCall.function?.name || "" };
      outputItems.push(functionCallOutputItem({
        id: `fc_${randomUUID().replaceAll("-", "")}`,
        callId: toolCall.id || `call_${randomUUID().replaceAll("-", "")}`,
        name: mapped.name,
        namespace: mapped.namespace,
        argumentsValue: toolCall.function?.arguments || "",
      }));
    }
    return json(res, 200, buildResponseObject({
      id: responseId,
      model: upstreamBody.model || chatBody.model,
      status: "completed",
      outputItems,
      createdAt,
      completedAt: Math.floor(Date.now() / 1000),
      usage: upstreamBody.usage,
    }));
  }

  const upstream = await fetch(deepSeekChatCompletionsUrl(), {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: authHeader,
    },
    body: JSON.stringify({
      ...chatBody,
      stream: true,
      stream_options: { include_usage: true },
    }),
  });

  if (!upstream.ok || !upstream.body) {
    const upstreamText = await upstream.text().catch(() => "");
    return json(res, upstream.status || 502, {
      error: "DeepSeek streaming chat completion failed",
      upstream: redact(upstreamText.slice(0, 500)),
    });
  }

  res.writeHead(200, {
    "content-type": "text/event-stream; charset=utf-8",
    "cache-control": "no-store",
    connection: "keep-alive",
  });

  let sequence = 0;
  let textValue = "";
  let usage = null;
  const outputItems = [];
  let messageItem = null;
  let messageContentStarted = false;
  const toolCalls = new Map();
  const baseResponse = buildResponseObject({
    id: responseId,
    model: chatBody.model,
    status: "in_progress",
    outputItems,
    createdAt,
    usage,
  });
  writeResponsesEvent(res, { type: "response.created", sequence_number: sequence++, response: baseResponse });
  writeResponsesEvent(res, { type: "response.in_progress", sequence_number: sequence++, response: baseResponse });

  const reader = upstream.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  function ensureMessageItem() {
    if (messageItem) return messageItem;
    const outputIndex = outputItems.length;
    messageItem = {
      id: `msg_${responseId}`,
      type: "message",
      status: "in_progress",
      role: "assistant",
      content: [],
      outputIndex,
    };
    outputItems.push(messageItem);
    writeResponsesEvent(res, {
      type: "response.output_item.added",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: outputIndex,
      item: {
        id: messageItem.id,
        type: "message",
        status: "in_progress",
        role: "assistant",
        content: [],
      },
    });
    return messageItem;
  }

  function ensureMessageContent() {
    const item = ensureMessageItem();
    if (messageContentStarted) return item;
    messageContentStarted = true;
    writeResponsesEvent(res, {
      type: "response.content_part.added",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: item.outputIndex,
      content_index: 0,
      item_id: item.id,
      part: {
        type: "output_text",
        text: "",
        annotations: [],
        logprobs: [],
      },
    });
    return item;
  }

  function ensureToolCall(deltaToolCall) {
    const index = Number.isInteger(deltaToolCall.index) ? deltaToolCall.index : toolCalls.size;
    if (toolCalls.has(index)) return toolCalls.get(index);
    const outputIndex = outputItems.length;
    const item = {
      id: `fc_${randomUUID().replaceAll("-", "")}`,
      type: "function_call",
      status: "in_progress",
      call_id: deltaToolCall.id || `call_${randomUUID().replaceAll("-", "")}`,
      name: deltaToolCall.function?.name || "",
      upstreamName: deltaToolCall.function?.name || "",
      arguments: "",
      outputIndex,
    };
    const mapped = toolNameMap.get(item.upstreamName) || { name: item.upstreamName };
    item.name = mapped.name;
    item.namespace = mapped.namespace;
    toolCalls.set(index, item);
    outputItems.push(item);
    writeResponsesEvent(res, {
      type: "response.output_item.added",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: outputIndex,
      item: functionCallOutputItem({
        id: item.id,
        callId: item.call_id,
        name: mapped.name,
        namespace: mapped.namespace,
        argumentsValue: "",
        status: "in_progress",
      }),
    });
    return item;
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let eventBoundary = buffer.indexOf("\n\n");
    while (eventBoundary !== -1) {
      const eventBlock = buffer.slice(0, eventBoundary);
      buffer = buffer.slice(eventBoundary + 2);
      for (const line of eventBlock.split(/\r?\n/)) {
        if (!line.startsWith("data:")) continue;
        const data = line.slice("data:".length).trim();
        if (!data || data === "[DONE]") continue;
        let chunk = null;
        try {
          chunk = JSON.parse(data);
        } catch {
          continue;
        }
        if (chunk.usage) usage = chunk.usage;
        const delta = chunk.choices?.[0]?.delta?.content || "";
        if (delta) {
          const item = ensureMessageContent();
          textValue += delta;
          writeResponsesEvent(res, {
            type: "response.output_text.delta",
            response_id: responseId,
            sequence_number: sequence++,
            output_index: item.outputIndex,
            content_index: 0,
            item_id: item.id,
            delta,
            logprobs: [],
          });
        }
        for (const toolCallDelta of chunk.choices?.[0]?.delta?.tool_calls || []) {
          const toolItem = ensureToolCall(toolCallDelta);
          if (toolCallDelta.id && toolItem.call_id.startsWith("call_")) toolItem.call_id = toolCallDelta.id;
          if (toolCallDelta.function?.name) {
            if (!toolItem.upstreamName) {
              toolItem.upstreamName = toolCallDelta.function.name;
            } else if (toolItem.upstreamName !== toolCallDelta.function.name) {
              toolItem.upstreamName += toolCallDelta.function.name;
            }
            const mapped = toolNameMap.get(toolItem.upstreamName) || { name: toolItem.upstreamName };
            toolItem.name = mapped.name;
            toolItem.namespace = mapped.namespace;
          }
          const argumentsDelta = toolCallDelta.function?.arguments || "";
          if (!argumentsDelta) continue;
          toolItem.arguments += argumentsDelta;
          writeResponsesEvent(res, {
            type: "response.function_call_arguments.delta",
            response_id: responseId,
            sequence_number: sequence++,
            item_id: toolItem.id,
            output_index: toolItem.outputIndex,
            delta: argumentsDelta,
          });
        }
      }
      eventBoundary = buffer.indexOf("\n\n");
    }
  }

  if (messageItem) {
    const finalPart = { type: "output_text", text: textValue, annotations: [], logprobs: [] };
    writeResponsesEvent(res, {
      type: "response.output_text.done",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: messageItem.outputIndex,
      content_index: 0,
      item_id: messageItem.id,
      text: textValue,
      logprobs: [],
    });
    writeResponsesEvent(res, {
      type: "response.content_part.done",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: messageItem.outputIndex,
      content_index: 0,
      item_id: messageItem.id,
      part: finalPart,
    });
    const finalMessage = messageOutputItem({
      id: messageItem.id,
      status: "completed",
      textValue,
    });
    outputItems[messageItem.outputIndex] = finalMessage;
    writeResponsesEvent(res, {
      type: "response.output_item.done",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: messageItem.outputIndex,
      item: finalMessage,
    });
  }
  for (const toolItem of toolCalls.values()) {
    const finalToolCall = functionCallOutputItem({
      id: toolItem.id,
      callId: toolItem.call_id,
      name: toolItem.name,
      namespace: toolItem.namespace,
      argumentsValue: toolItem.arguments,
      status: "completed",
    });
    writeResponsesEvent(res, {
      type: "response.function_call_arguments.done",
      response_id: responseId,
      sequence_number: sequence++,
      item_id: toolItem.id,
      output_index: toolItem.outputIndex,
      arguments: toolItem.arguments,
    });
    outputItems[toolItem.outputIndex] = finalToolCall;
    writeResponsesEvent(res, {
      type: "response.output_item.done",
      response_id: responseId,
      sequence_number: sequence++,
      output_index: toolItem.outputIndex,
      item: finalToolCall,
    });
  }
  writeResponsesEvent(res, {
    type: "response.completed",
    response_id: responseId,
    sequence_number: sequence++,
    response: buildResponseObject({
      id: responseId,
      model: chatBody.model,
      status: "completed",
      outputItems,
      createdAt,
      completedAt: Math.floor(Date.now() / 1000),
      usage,
    }),
  });
  res.write("data: [DONE]\n\n");
  res.end();
}

function createSession(options = {}) {
  if (sessions.size >= maxSessions) {
    const err = new Error("maximum session count reached");
    err.status = 429;
    throw err;
  }

  const id = randomUUID();
  const cwd = safeCwd(options.cwd);
  const codexHome = createSessionHome(id);
  const args = ["app-server", "--listen", "stdio://"];
  const child = spawn(codexBin, args, {
    cwd,
    env: {
      ...process.env,
      CODEX_WORKSPACE_DIR: workspaceRoot,
      CODEX_HOME: codexHome,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });

  const session = {
    id,
    cwd,
    child,
    codexHome,
    createdAt: new Date().toISOString(),
    lastActivity: Date.now(),
    stdoutBuffer: "",
    eventBuffer: [],
    subscribers: new Set(),
    pending: new Map(),
    exit: null,
  };

  child.stdout.setEncoding("utf8");
  child.stdout.on("data", (chunk) => handleStdout(session, chunk));
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk) => {
    for (const line of chunk.split(/\r?\n/).filter(Boolean)) {
      console.error(JSON.stringify({
        level: "warn",
        sessionId: id,
        stream: "stderr",
        message: redact(line),
      }));
    }
  });
  child.on("exit", (code, signal) => {
    session.exit = { code, signal, at: new Date().toISOString() };
    broadcast(session, {
      type: "exit",
      ts: new Date().toISOString(),
      exit: session.exit,
    });
    for (const pending of session.pending.values()) {
      pending.reject(new Error(`codex app-server exited: code=${code} signal=${signal}`));
    }
    session.pending.clear();
    if (!keepSessionHome) {
      rmSync(session.codexHome, { recursive: true, force: true });
    }
  });

  sessions.set(id, session);
  return session;
}

function redact(line) {
  return line
    .replace(/(Bearer\s+)[A-Za-z0-9._~+/=-]+/g, "$1[REDACTED]")
    .replace(/(sk-[A-Za-z0-9_-]{8})[A-Za-z0-9_-]+/g, "$1[REDACTED]")
    .replace(/(AKIA|LTAI)[A-Za-z0-9]+/g, "[REDACTED_ACCESS_KEY]");
}

function handleStdout(session, chunk) {
  session.stdoutBuffer += chunk;
  let newlineIndex = session.stdoutBuffer.indexOf("\n");
  while (newlineIndex !== -1) {
    const rawLine = session.stdoutBuffer.slice(0, newlineIndex).trim();
    session.stdoutBuffer = session.stdoutBuffer.slice(newlineIndex + 1);
    if (rawLine) handleJsonLine(session, rawLine);
    newlineIndex = session.stdoutBuffer.indexOf("\n");
  }
}

function handleJsonLine(session, rawLine) {
  let message = null;
  try {
    message = JSON.parse(rawLine);
  } catch {
    message = { raw: rawLine };
  }

  const event = {
    type: "message",
    ts: new Date().toISOString(),
    message,
  };
  session.eventBuffer.push(event);
  while (session.eventBuffer.length > eventBufferLimit) session.eventBuffer.shift();
  session.lastActivity = Date.now();
  broadcast(session, event);

  if (message && Object.hasOwn(message, "id") && session.pending.has(message.id)) {
    const pending = session.pending.get(message.id);
    session.pending.delete(message.id);
    pending.resolve(message);
  }
}

function broadcast(session, event) {
  const payload = `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;
  for (const res of session.subscribers) {
    res.write(payload);
  }
}

function sendMessage(session, message) {
  if (session.exit) {
    const err = new Error("session process already exited");
    err.status = 409;
    throw err;
  }
  session.lastActivity = Date.now();
  session.child.stdin.write(`${JSON.stringify(message)}\n`);
}

function requestMessage(session, message, timeoutMs) {
  if (!Object.hasOwn(message, "id")) {
    sendMessage(session, message);
    return Promise.resolve({ accepted: true });
  }
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      session.pending.delete(message.id);
      reject(new Error(`timeout waiting for response id ${message.id}`));
    }, timeoutMs);
    session.pending.set(message.id, {
      resolve: (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      reject: (err) => {
        clearTimeout(timer);
        reject(err);
      },
    });
    sendMessage(session, message);
  });
}

function stopSession(session, reason = "requested") {
  sessions.delete(session.id);
  broadcast(session, {
    type: "closing",
    ts: new Date().toISOString(),
    reason,
  });
  for (const res of session.subscribers) {
    res.end();
  }
  session.subscribers.clear();
  if (!session.exit) {
    session.child.kill("SIGTERM");
    setTimeout(() => {
      if (!session.exit) session.child.kill("SIGKILL");
    }, 3000).unref();
  }
}

function parseSessionPath(urlPath) {
  const match = urlPath.match(/^\/sessions\/([^/]+)(?:\/([^/]+))?$/);
  if (!match) return null;
  const session = sessions.get(match[1]);
  return { id: match[1], action: match[2] || "", session };
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

    if (req.method === "GET" && url.pathname === "/healthz") {
      return text(res, 200, "ok\n");
    }

    if (req.method === "GET" && url.pathname === "/readyz") {
      const ready = isReady();
      return json(res, ready.ok ? 200 : 503, ready);
    }

    if (req.method === "POST" && url.pathname === "/internal/deepseek/v1/responses") {
      return await proxyDeepSeekResponses(req, res);
    }

    if (!authorized(req)) {
      return json(res, bearerToken || allowUnauthenticated ? 401 : 503, {
        error: bearerToken || allowUnauthenticated
          ? "unauthorized"
          : "CODEX_GATEWAY_BEARER_TOKEN is required unless ALLOW_UNAUTHENTICATED=true",
      });
    }

    if (req.method === "GET" && url.pathname === "/sessions") {
      return json(res, 200, {
        sessions: Array.from(sessions.values()).map((session) => ({
          id: session.id,
          cwd: session.cwd,
          createdAt: session.createdAt,
          lastActivity: new Date(session.lastActivity).toISOString(),
          exit: session.exit,
        })),
      });
    }

    if (req.method === "GET" && url.pathname === "/artifacts") {
      const artifactPath = safeWorkspacePath(url.searchParams.get("path") || "");
      if (!existsSync(artifactPath)) {
        return json(res, 404, { error: "artifact not found" });
      }
      const stat = statSync(artifactPath);
      if (!stat.isFile()) {
        return json(res, 400, { error: "artifact path must point to a file" });
      }
      res.writeHead(200, {
        "content-type": contentTypeFor(artifactPath),
        "content-length": stat.size,
        "cache-control": "no-store",
        "content-disposition": `attachment; filename="${path.basename(artifactPath).replace(/"/g, "")}"`,
      });
      return createReadStream(artifactPath).pipe(res);
    }

    if (req.method === "POST" && url.pathname === "/sessions") {
      const body = await readBody(req);
      const session = createSession(body);
      return json(res, 201, { id: session.id, cwd: session.cwd, createdAt: session.createdAt });
    }

    const parsed = parseSessionPath(url.pathname);
    if (parsed && !parsed.session) {
      return json(res, 404, { error: "session not found", id: parsed.id });
    }

    if (parsed && req.method === "DELETE" && !parsed.action) {
      stopSession(parsed.session);
      return json(res, 200, { stopped: true, id: parsed.id });
    }

    if (parsed && req.method === "GET" && parsed.action === "events") {
      res.writeHead(200, {
        "content-type": "text/event-stream; charset=utf-8",
        "cache-control": "no-store",
        connection: "keep-alive",
      });
      res.write(": connected\n\n");
      parsed.session.subscribers.add(res);
      for (const event of parsed.session.eventBuffer) {
        res.write(`event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`);
      }
      req.on("close", () => parsed.session.subscribers.delete(res));
      return;
    }

    if (parsed && req.method === "POST" && parsed.action === "messages") {
      const body = await readBody(req);
      sendMessage(parsed.session, body);
      return json(res, 202, { accepted: true, sessionId: parsed.id, id: body.id ?? null });
    }

    if (parsed && req.method === "POST" && parsed.action === "request") {
      const body = await readBody(req);
      const timeoutMs = Number(url.searchParams.get("timeoutMs") || 15000);
      const response = await requestMessage(parsed.session, body, timeoutMs);
      return json(res, 200, { sessionId: parsed.id, response });
    }

    return json(res, 404, { error: "not found" });
  } catch (err) {
    const status = err.status || (err instanceof SyntaxError ? 400 : 500);
    return json(res, status, { error: err.message || String(err) });
  }
});

setInterval(() => {
  const now = Date.now();
  for (const session of sessions.values()) {
    if (now - session.lastActivity > idleMs) {
      stopSession(session, "idle-timeout");
    }
  }
}, Math.min(idleMs, 60_000)).unref();

server.listen(port, host, () => {
  console.log(JSON.stringify({
    level: "info",
    message: "ai4ss Codex harness gateway listening",
    host,
    port,
    workspaceRoot,
    codexBin,
    authConfigured: allowUnauthenticated || Boolean(bearerToken),
    unauthenticatedMode: allowUnauthenticated,
    mcpServers,
  }));
});

process.on("SIGTERM", () => {
  for (const session of sessions.values()) stopSession(session, "sigterm");
  server.close(() => process.exit(0));
});
