#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_RESEARCH_WORKFLOW_TIMEOUT_MS || 300000);
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const affinityHeader = process.env.AGENTRUN_SESSION_AFFINITY_HEADER || "x-agentrun-session-id";
const affinityKey = process.env.AGENTRUN_SESSION_AFFINITY_KEY || randomUUID();
const seed = process.env.CODEX_RESEARCH_SEED
  || "地方政府采用生成式 AI 辅助政务服务是否会改善居民对公共服务公平性的感知？";
const outputPath = process.env.CODEX_RESEARCH_WORKFLOW_OUTPUT || "";
const embedLocalSkills = process.env.CODEX_RESEARCH_EMBED_LOCAL_SKILLS !== "false";

const skillContextPaths = [
  "AGENTS.md",
  "skills/research-starter/SKILL.md",
  "skills/study-design-builder/SKILL.md",
  "skills/literature-matrix/SKILL.md",
  "skills/research-data-builder/SKILL.md",
  "skills/research-analysis-runner/SKILL.md",
  "skills/analysis-explainer/SKILL.md",
];

function readSkillContext() {
  if (!embedLocalSkills) return "";
  const root = process.cwd();
  return skillContextPaths.map((relativePath) => {
    const absolutePath = path.join(root, relativePath);
    const content = fs.readFileSync(absolutePath, "utf8");
    return `\n\n===== ${relativePath} =====\n${content}`;
  }).join("");
}

const embeddedSkillContext = readSkillContext();
const deprecatedAuthorRoute = ["ask", "author"].join("_");
const terminalRoute = "last_skill";
const forbiddenWorkflowTerms = [
  deprecatedAuthorRoute,
  "author_decision",
  "author_decisions",
  "Author Decision Points",
  "synthetic data",
  "simulated data",
  "toy data",
  "placeholder data",
  "demo analysis",
  "Status: PENDING",
  "NO_GATES_PASSED",
  "current_run_status=pending",
  "current_run_status=blocked",
];
const forbiddenWorkflowPatterns = [
  ["synthetic-data-family", /synthetic[^.\n;]{0,80}\bdata\b/i],
  ["simulated-data-family", /simulated[^.\n;]{0,80}\bdata\b/i],
  ["placeholder-data-family", /placeholder[^.\n;]{0,80}\bdata\b/i],
  ["toy-data-family", /toy[^.\n;]{0,80}\b(data|analysis)\b/i],
  ["demo-fallback-family", /demo[^.\n;]{0,80}\b(data|analysis)\b/i],
];

const promptBase = process.env.CODEX_RESEARCH_WORKFLOW_PROMPT || `
从下面这一句话开始，在云端 Codex app-server 里跑通一个 compact 但完整的 AI4SS research workflow。

一句话研究想法：${seed}

要求：
1. 使用下方嵌入的 AGENTS.md 和 SKILL.md 内容作为规范；不要尝试发起工具调用，不要输出 DSML/tool_calls/XML 调用片段。
2. 不给未经验证的最终学术结论；输出 inspectable research objects、ledgers、manifests、diagnostics、required gate points。
3. 若需要实时外部事实，只能把强版本列为 upgrade_gate，不要编造来源。当前 run 必须通过 redesign 收敛到一个可完成的 bounded inquiry。
4. 不要只复述你读懂了说明；必须直接产出 workflow artifact。
5. 禁止把缺失数据替换为人造、演示、占位或玩具材料；没有真实分析数据时，改做真实可用 artifact 的非估计型分析。
6. 输出 Markdown，且只输出 Markdown。必须包含这些顶级小节：
   - Seed
   - Route Declaration
   - MIDA Declaration
   - Study Design Object
   - Source Gate Register
   - Data Builder Manifest
   - Analysis Readiness Manifest
   - Repair Loop Register
   - Executed Analysis Object
   - Methods Review
   - Bounded Claim Handoff
   - AI Use Ledger
   - Workflow Completion Certificate
7. Repair Loop Register 必须包含精确字段 next_skill_route=last_skill、required_gate、failure_signal、redesign_option，并说明 redesign 后如何继续完成当前 run。
8. Workflow Completion Certificate 必须包含精确字段：current_run_status=complete 和 no_synthetic_demo_analysis=true。
9. 最后一行输出精确标记：AI4SS_WORKFLOW_COMPLETE

嵌入的规范上下文：
${embeddedSkillContext}
`.trim();

const prompt = `${promptBase}

额外输出 contract：
- 最终 Markdown 中禁止出现字符串 ${deprecatedAuthorRoute}。
- 原本需要 ${deprecatedAuthorRoute} 的地方，直接输出 ${terminalRoute}。
- 如果某个字段要求机器可执行的 next_skill_route，不要写 ${deprecatedAuthorRoute}；写 ${terminalRoute}。
- 不要在正文中用否定句列举 forbidden fallback phrases；只在 Workflow Completion Certificate 中写 current_run_status=complete 和 no_synthetic_demo_analysis=true。
- 不要写“no X data/material was used”这类句子；用字段 no_synthetic_demo_analysis=true 即可。
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

function waitForTurnCompleted(response, threadId) {
  return new Promise(async (resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout waiting for turn/completed")), timeoutMs);
    let text = "";
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
              text += message.params?.delta || "";
            }
            if (message?.method === "turn/completed" && message.params?.threadId === threadId) {
              clearTimeout(timer);
              await reader.cancel().catch(() => {});
              resolve({ message, text });
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

function validateWorkflow(text) {
  const required = [
    "Seed",
    "Route Declaration",
    "MIDA Declaration",
    "Study Design Object",
    "Source Gate Register",
    "Data Builder Manifest",
    "Analysis Readiness Manifest",
    "Repair Loop Register",
    "next_skill_route=last_skill",
    "required_gate",
    "failure_signal",
    "redesign_option",
    "Executed Analysis Object",
    "Methods Review",
    "Bounded Claim Handoff",
    "AI Use Ledger",
    "Workflow Completion Certificate",
    "current_run_status=complete",
    "no_synthetic_demo_analysis=true",
    "AI4SS_WORKFLOW_COMPLETE",
  ];
  const missing = required.filter((item) => !text.includes(item));
  const lowered = text.toLowerCase();
  const forbidden = [
    ...forbiddenWorkflowTerms.filter((item) => lowered.includes(item.toLowerCase())),
    ...forbiddenWorkflowPatterns.filter(([, pattern]) => pattern.test(text)).map(([label]) => label),
  ];
  return { missing, forbidden };
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
          name: "ai4ss-skills-agentrun-research-workflow-smoke",
          title: "ai4ss-skills AgentRun research workflow smoke",
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

  if (outputPath) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, completed.text);
  }

  const { missing, forbidden } = validateWorkflow(completed.text);
  if (missing.length || forbidden.length) {
    throw new Error(
      `research workflow output validation failed; missing=${missing.join(", ") || "(none)"}; `
      + `forbidden=${forbidden.join(", ") || "(none)"}; `
      + `outputPath=${outputPath || "(not written)"}; preview=${JSON.stringify(completed.text.slice(0, 1200))}`,
    );
  }

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    sessionId: created.id,
    initialized: initialized.response?.result ? "ok" : initialized.response,
    threadId,
    turnId: turnStarted.response?.result?.turn?.id || turn.id,
    model: smokeModel,
    seed,
    outputPath: outputPath || null,
    outputChars: completed.text.length,
    preview: completed.text.slice(0, 1200),
  }, null, 2));
} finally {
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
