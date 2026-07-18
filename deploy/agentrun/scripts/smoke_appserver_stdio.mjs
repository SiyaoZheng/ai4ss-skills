#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import process from "node:process";

const codexBin = process.env.CODEX_BIN || "codex";
const cwd = path.resolve(process.env.CODEX_WORKSPACE_DIR || process.cwd());
const timeoutMs = Number(process.env.CODEX_SMOKE_TIMEOUT_MS || 15000);
const tmpHome = mkdtempSync(path.join(tmpdir(), "ai4ss-codex-smoke-"));
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";

const child = spawn(codexBin, ["app-server", "--listen", "stdio://"], {
  cwd,
  env: {
    ...process.env,
    CODEX_HOME: tmpHome,
  },
  stdio: ["pipe", "pipe", "pipe"],
});

let stdoutBuffer = "";
let stderr = "";
const waiters = new Map();

const timer = setTimeout(() => {
  finish(1, { ok: false, error: "timeout", stderr: redact(stderr) });
}, timeoutMs);

child.stdout.setEncoding("utf8");
child.stdout.on("data", (chunk) => {
  stdoutBuffer += chunk;
  let idx = stdoutBuffer.indexOf("\n");
  while (idx !== -1) {
    const line = stdoutBuffer.slice(0, idx).trim();
    stdoutBuffer = stdoutBuffer.slice(idx + 1);
    if (line) handleLine(line);
    idx = stdoutBuffer.indexOf("\n");
  }
});

child.stderr.setEncoding("utf8");
child.stderr.on("data", (chunk) => {
  stderr += chunk;
});

child.on("exit", (code, signal) => {
  if (waiters.size) {
    finish(1, { ok: false, error: "codex app-server exited early", code, signal, stderr: redact(stderr) });
  }
});

function handleLine(line) {
  let message;
  try {
    message = JSON.parse(line);
  } catch {
    return;
  }
  if (Object.hasOwn(message, "id") && waiters.has(message.id)) {
    const resolve = waiters.get(message.id);
    waiters.delete(message.id);
    resolve(message);
  }
}

function send(message) {
  child.stdin.write(`${JSON.stringify(message)}\n`);
}

function request(message) {
  return new Promise((resolve) => {
    waiters.set(message.id, resolve);
    send(message);
  });
}

function redact(value) {
  return value
    .replace(/(Bearer\s+)[A-Za-z0-9._~+/=-]+/g, "$1[REDACTED]")
    .replace(/(sk-[A-Za-z0-9_-]{8})[A-Za-z0-9_-]+/g, "$1[REDACTED]")
    .replace(/(AKIA|LTAI)[A-Za-z0-9]+/g, "[REDACTED_ACCESS_KEY]");
}

function finish(status, payload) {
  clearTimeout(timer);
  child.kill("SIGTERM");
  setTimeout(() => child.kill("SIGKILL"), 1000).unref();
  rmSync(tmpHome, { recursive: true, force: true });
  console.log(JSON.stringify(payload, null, 2));
  process.exit(status);
}

try {
  const initialized = await request({
    id: 1,
    method: "initialize",
    params: {
      clientInfo: {
        name: "ai4ss-skills-agentrun-smoke",
        title: "ai4ss-skills AgentRun smoke",
        version: "0.1.0",
      },
    },
  });

  if (initialized.error) {
    finish(1, { ok: false, phase: "initialize", response: initialized, stderr: redact(stderr) });
  }

  send({ method: "initialized", params: {} });

  const threadStarted = await request({
    id: 2,
    method: "thread/start",
    params: {
      model: smokeModel,
      cwd,
    },
  });

  if (threadStarted.error || !threadStarted.result?.thread?.id) {
    finish(1, { ok: false, phase: "thread/start", response: threadStarted, stderr: redact(stderr) });
  }

  finish(0, {
    ok: true,
    codexBin,
    cwd,
    model: smokeModel,
    threadId: threadStarted.result.thread.id,
  });
} catch (err) {
  finish(1, { ok: false, error: err.message || String(err), stderr: redact(stderr) });
}
