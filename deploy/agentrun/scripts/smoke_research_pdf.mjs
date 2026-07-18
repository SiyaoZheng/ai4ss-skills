#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import process from "node:process";

const baseUrl = (process.env.GATEWAY_URL || "http://127.0.0.1:9000").replace(/\/$/, "");
const token = process.env.CODEX_GATEWAY_BEARER_TOKEN || "";
const agentrunApiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
const timeoutMs = Number(process.env.CODEX_RESEARCH_PDF_TIMEOUT_MS || 600000);
const smokeModel = process.env.CODEX_SMOKE_MODEL || process.env.CODEX_MODEL || "deepseek-v4-flash";
const affinityHeader = process.env.AGENTRUN_SESSION_AFFINITY_HEADER || "x-agentrun-session-id";
const affinityKey = process.env.AGENTRUN_SESSION_AFFINITY_KEY || randomUUID();
const seed = process.env.CODEX_RESEARCH_SEED
  || "地方政府采用生成式 AI 辅助政务服务是否会改善居民对公共服务公平性的感知？";
const artifactStem = process.env.CODEX_RESEARCH_PDF_STEM || "research-paper-draft";
const remoteDir = process.env.CODEX_RESEARCH_PDF_REMOTE_DIR || "/workspace/output/pdf";
const remoteTex = `${remoteDir}/${artifactStem}.tex`;
const remotePdf = `${remoteDir}/${artifactStem}.pdf`;
const remoteText = `${remoteDir}/${artifactStem}.txt`;
const localDir = process.env.CODEX_RESEARCH_PDF_OUTPUT_DIR
  || path.resolve(process.cwd(), "deploy/agentrun/.generated/pdf-smoke");

const completionMarker = "RESEARCH_PDF_COMPLETE";

// Driver-only checks: these terms must never be required from the writer. They
// are orchestration vocabulary, not paper vocabulary.
const forbiddenTerms = [
  ".aiss",
  "AI4SS",
  "MIDA",
  "skillpack",
  "harness",
  "workflow",
  "Workflow",
  "last_skill",
  "ask_author",
  "author_decision",
  "author_decisions",
  "needs_author",
  "current_run_status",
  "no_synthetic_demo_analysis",
  "external_claim_scope",
  "next_skill_route",
  "required_gate",
  "failure_signal",
  "redesign_option",
  "Source Gate",
  "Repair Loop",
  "Bounded Claim Ledger",
  "AI Use Ledger",
  "Completion Certificate",
  "\\cite",
  "\\bibitem",
  "thebibliography",
  "synthetic data",
  "simulated data",
  "toy data",
  "placeholder data",
  "demo analysis",
  "synthetic analysis",
  "State Council",
  "Oster 2019",
  "Status: PENDING",
  "NO_GATES_PASSED",
];
const forbiddenPatterns = [
  ["synthetic-data-family", /synthetic[^.\n;]{0,80}\bdata\b/i],
  ["simulated-data-family", /simulated[^.\n;]{0,80}\bdata\b/i],
  ["placeholder-data-family", /placeholder[^.\n;]{0,80}\bdata\b/i],
  ["toy-data-family", /toy[^.\n;]{0,80}\b(data|analysis)\b/i],
  ["demo-fallback-family", /demo[^.\n;]{0,80}\b(data|analysis)\b/i],
];

const paperBrief = {
  workingTitle: "Generative AI in Local Public Services and the Fairness Problem",
  oneSentenceIdea: seed,
  paperType: "standalone social-science working paper focused on research design, measurement, and bounded analytical claims",
  audience: "public administration, computational social science, and political methodology readers",
  thesis: [
    "The substantive question is important because generative AI can alter how residents experience administrative responsiveness, voice, consistency, and distributive fairness.",
    "The current paper should not claim an empirical treatment effect.",
    "The contribution is a defensible design paper: it clarifies the estimand, measurement strategy, identification risks, and the evidence that would be needed before causal claims are possible.",
  ],
  suppliedEvidenceObjects: [
    {
      id: "E1",
      label: "Research question",
      content: "Does local-government use of generative AI assistance in resident-facing public services change residents' perceived procedural and distributive fairness?",
    },
    {
      id: "E2",
      label: "Core constructs",
      content: "Treatment: exposure to a resident-facing generative AI service assistant. Outcomes: procedural fairness, distributive fairness, responsiveness, perceived voice, and consistency of service handling.",
    },
    {
      id: "E3",
      label: "Candidate mechanisms",
      content: "Responsiveness may improve perceived fairness by shortening response time and improving answer consistency. Voice may weaken if residents perceive automated service as less attentive or less contestable.",
    },
    {
      id: "E4",
      label: "Preferred empirical design",
      content: "A future data-bearing study would compare residents before and after service rollout across treated and not-yet-treated localities, with locality and time controls, pre-specified measurement scales, and sensitivity analysis for adoption selection.",
    },
    {
      id: "E5",
      label: "Current evidence boundary",
      content: "No verified locality-level rollout dataset, resident survey, administrative service log, or named external source is supplied in this packet. Therefore the paper must remain a design and measurement article, not an empirical effect-estimation article.",
    },
    {
      id: "E6",
      label: "Analytical object for this draft",
      content: "The analysis can classify claim strength, identification threats, measurement threats, and minimum data requirements. It can produce tables for constructs, hypotheses, design risks, and upgrade evidence needed for a future empirical paper.",
    },
  ],
  writingRules: [
    "Write as a standalone paper, not as a report about an automation system or generation process.",
    "Do not reveal or discuss hidden orchestration, internal state machines, routing labels, code, validators, or task management.",
    "Use only the supplied evidence objects for substantive claims.",
    "Do not invent external documents, source names, URLs, datasets, policy claims, statistics, or named citations.",
    "Do not use LaTeX citation or bibliography commands.",
    "The paper may include a References section only if it says that external references are intentionally deferred until source verification; do not list fabricated references.",
    "Use conventional academic sectioning and write in polished prose rather than checklist form.",
    "Include at least two compact tables that make the research object concrete.",
  ],
};

const prompt = `
You are writing a standalone social-science working paper from a supplied paper brief.
Treat the brief as the complete evidence available to you. Your job is to write the paper,
not to explain how the brief was produced.

Paper brief:
${JSON.stringify(paperBrief, null, 2)}

Output requirements:
1. Create a complete LaTeX article at ${remoteTex}.
2. Compile it to PDF at ${remotePdf}.
3. Extract the PDF text to ${remoteText}.
4. Use portable pdflatex-compatible ASCII LaTeX. Avoid packages that are often missing.
5. The paper must read like a real working paper: title, abstract, introduction, conceptual framework,
   research design, evidence base, analysis, limitations, conclusion, and optional references note.
6. Keep the paper self-contained and polished. Do not write a checklist, task report, or meta-report.
7. Create at least two tables inside the paper.
8. Run: latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=${remoteDir} ${remoteTex}
9. Run: pdfinfo ${remotePdf}
10. Run: pdftotext ${remotePdf} ${remoteText}
11. If compilation fails, fix the LaTeX and retry until the PDF exists.
12. Final assistant message must be exactly one JSON object on one line, with no Markdown fence:
{"status":"${completionMarker}","tex":"${remoteTex}","pdf":"${remotePdf}","text":"${remoteText}"}
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

async function fetchArtifact(remotePath, localPath) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}/artifacts?path=${encodeURIComponent(remotePath)}`, {
      method: "GET",
      signal: controller.signal,
      headers: headers({ accept: "*/*" }),
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new Error(`GET /artifacts failed for ${remotePath}: ${res.status} ${body}`);
    }
    const arrayBuffer = await res.arrayBuffer();
    fs.mkdirSync(path.dirname(localPath), { recursive: true });
    fs.writeFileSync(localPath, Buffer.from(arrayBuffer));
    return {
      remotePath,
      localPath,
      bytes: fs.statSync(localPath).size,
      contentType: res.headers.get("content-type"),
    };
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

function openEventStream(sessionPath) {
  const eventHeaders = headers({ accept: "text/event-stream" });
  const args = [
    "-sS",
    "-N",
    "--no-buffer",
    "--fail-with-body",
    "--connect-timeout",
    "30",
    "--max-time",
    String(Math.ceil(timeoutMs / 1000) + 60),
  ];
  for (const [key, value] of Object.entries(eventHeaders)) {
    args.push("-H", `${key}: ${value}`);
  }
  args.push(`${baseUrl}${sessionPath}/events`);

  const child = spawn("curl", args, { stdio: ["ignore", "pipe", "pipe"] });
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  const stream = { child, stderr: "" };
  child.stderr.on("data", (chunk) => {
    stream.stderr += chunk;
    if (stream.stderr.length > 4000) stream.stderr = stream.stderr.slice(-4000);
  });
  return stream;
}

function closeEventStream(stream) {
  if (stream?.child && !stream.child.killed) {
    stream.child.kill("SIGTERM");
  }
}

function waitForTurnCompleted(eventStream, threadId) {
  return new Promise(async (resolve, reject) => {
    let timer;
    let settled = false;
    let text = "";
    const methodCounts = {};
    const toolLikeEvents = [];
    const warnings = [];
    let buffer = "";

    function fail(error) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      closeEventStream(eventStream);
      reject(error);
    }

    function complete(message) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      closeEventStream(eventStream);
      resolve({ message, text, methodCounts, toolLikeEvents, warnings });
    }

    function consumeChunk(chunk) {
      buffer += chunk;
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
              if (toolLikeEvents.length < 30) toolLikeEvents.push(summarizeMessage(message));
            }
          }
          if (message?.method === "item/agentMessage/delta") {
            text += message.params?.delta || "";
          }
          if (message?.method === "turn/completed" && message.params?.threadId === threadId) {
            complete(message);
            return;
          }
        }
        idx = buffer.indexOf("\n\n");
      }
    }

    timer = setTimeout(() => fail(new Error("timeout waiting for turn/completed")), timeoutMs);

    try {
      eventStream.child.stdout.on("data", consumeChunk);
      eventStream.child.once("error", fail);
      eventStream.child.once("close", (code, signal) => {
        if (!settled) {
          fail(new Error(`SSE stream ended before turn/completed: code=${code} signal=${signal || ""} stderr=${eventStream.stderr.slice(-1200)}`));
        }
      });
    } catch (err) {
      fail(err);
    }
  });
}

function validatePdf(localPdf, localText, localTex, finalText) {
  const pdfBytes = fs.readFileSync(localPdf);
  if (pdfBytes.length < 5000 || pdfBytes.subarray(0, 5).toString("ascii") !== "%PDF-") {
    throw new Error(`PDF artifact is invalid or too small: ${localPdf}, bytes=${pdfBytes.length}`);
  }
  const extracted = fs.readFileSync(localText, "utf8");
  const tex = fs.readFileSync(localTex, "utf8");
  const combined = `${extracted}\n${tex}`;
  const lowered = combined.toLowerCase();
  const finalLowered = finalText.toLowerCase();
  const forbidden = [
    ...forbiddenTerms.filter((term) => lowered.includes(term.toLowerCase())),
    ...forbiddenPatterns.filter(([, pattern]) => pattern.test(combined)).map(([label]) => label),
    ...[
      deprecatedAuthorRoute,
      "author_decision",
      "author_decisions",
      "needs_author",
    ].filter((term) => finalLowered.includes(term.toLowerCase())),
  ];
  const required = [
    "MIDA Declaration",
    "Model",
    "Inquiry",
    "Data strategy",
    "Answer strategy",
    "Diagnose",
    "Redesign",
    "Report boundary",
    "Source Gate Register",
    "Repair Loop Register",
    "next_skill_route=last_skill",
    "required_gate",
    "failure_signal",
    "redesign_option",
    "Executed Analysis Object",
    "Methods Review",
    "Bounded Claim Ledger",
    "Required Gates",
    "AI Use Ledger",
    "Workflow Completion Certificate",
    "current_run_status=complete",
    "no_synthetic_demo_analysis=true",
    "external_claim_scope=workflow_internal_only",
  ].filter((term) => !combined.includes(term));
  if (forbidden.length || required.length) {
    throw new Error(`PDF validation failed; forbidden=${forbidden.join(", ") || "(none)"}; missing=${required.join(", ") || "(none)"}`);
  }
  return {
    pdfBytes: pdfBytes.length,
    textBytes: Buffer.byteLength(extracted),
    texBytes: Buffer.byteLength(tex),
    textPreview: extracted.replace(/\s+/g, " ").slice(0, 500),
  };
}

const created = await fetchJson("/sessions", {
  method: "POST",
  body: JSON.stringify({ cwd: "." }),
});

const sessionPath = `/sessions/${created.id}`;
let eventStream;

try {
  eventStream = openEventStream(sessionPath);

  const initialized = await fetchJson(`${sessionPath}/request`, {
    method: "POST",
    body: JSON.stringify({
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "ai4ss-skills-agentrun-research-pdf-smoke",
          title: "ai4ss-skills AgentRun research PDF smoke",
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

  const turnCompleted = waitForTurnCompleted(eventStream, threadId);

  await fetchJson(`${sessionPath}/request?timeoutMs=30000`, {
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
  if (!completed.text.includes("AI4SS_RESEARCH_PDF_COMPLETE")) {
    throw new Error(`missing completion marker; preview=${JSON.stringify(completed.text.slice(0, 1200))}`);
  }

  const localTex = path.join(localDir, `${artifactStem}.tex`);
  const localPdf = path.join(localDir, `${artifactStem}.pdf`);
  const localText = path.join(localDir, `${artifactStem}.txt`);
  const localAssistantText = path.join(localDir, `${artifactStem}.assistant.txt`);
  fs.mkdirSync(localDir, { recursive: true });
  fs.writeFileSync(localAssistantText, completed.text);
  const downloads = [
    await fetchArtifact(remoteTex, localTex),
    await fetchArtifact(remotePdf, localPdf),
    await fetchArtifact(remoteText, localText),
  ];
  const validation = validatePdf(localPdf, localText, localTex, completed.text);

  console.log(JSON.stringify({
    ok: true,
    baseUrl,
    sessionId: created.id,
    initialized: initialized.response?.result ? "ok" : initialized.response,
    threadId,
    turnId: turn.id,
    model: smokeModel,
    remote: { tex: remoteTex, pdf: remotePdf, text: remoteText },
    local: { tex: localTex, pdf: localPdf, text: localText, assistantText: localAssistantText },
    downloads,
    validation,
    warnings: completed.warnings,
    toolLikeEvents: completed.toolLikeEvents,
    methodCounts: completed.methodCounts,
  }, null, 2));
} finally {
  closeEventStream(eventStream);
  await fetch(`${baseUrl}${sessionPath}`, {
    method: "DELETE",
    headers: headers(),
  }).catch(() => {});
}
