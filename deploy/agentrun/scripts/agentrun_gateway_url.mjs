#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/agentrun_gateway_url.mjs [options]

Options:
  --runtime NAME     Runtime name. Defaults to AGENTRUN_RUNTIME_NAME or ai4ss-skills-codex-harness.
  --endpoint NAME    Endpoint name. Defaults to AGENTRUN_ENDPOINT_NAME or default.
  --account-id ID    Account id. Defaults to AGENTRUN_ACCOUNT_ID, or derives from aliyun sts.
  --region REGION    Region. Defaults to AGENTRUN_REGION or cn-hangzhou.
  --profile NAME     Aliyun CLI profile for account-id derivation. Defaults to AGENTRUN_ALIYUN_PROFILE or default.
  -h, --help         Show this help.

Prints the AgentRun data-link base URL for this gateway. Smoke scripts append
gateway routes such as /readyz and /sessions to this URL.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    runtime: process.env.AGENTRUN_RUNTIME_NAME || "ai4ss-skills-codex-harness",
    endpoint: process.env.AGENTRUN_ENDPOINT_NAME || "default",
    accountId: process.env.AGENTRUN_ACCOUNT_ID || "",
    region: process.env.AGENTRUN_REGION || "cn-hangzhou",
    profile: process.env.AGENTRUN_ALIYUN_PROFILE || "default",
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--runtime") {
      opts.runtime = argv[++i];
    } else if (arg === "--endpoint") {
      opts.endpoint = argv[++i];
    } else if (arg === "--account-id") {
      opts.accountId = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else if (arg === "--profile") {
      opts.profile = argv[++i];
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return opts;
}

function deriveAccountId(opts) {
  const result = spawnSync(
    "aliyun",
    ["sts", "GetCallerIdentity", "--profile", opts.profile, "--region", opts.region],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (result.status !== 0) {
    const stderr = result.stderr.trim().replace(/[A-Za-z0-9+/=_-]{32,}/g, "[REDACTED]");
    throw new Error(`failed to derive account id: ${stderr || `exit ${result.status}`}`);
  }
  const parsed = JSON.parse(result.stdout);
  if (!parsed.AccountId) throw new Error("aliyun sts GetCallerIdentity did not return AccountId");
  return String(parsed.AccountId);
}

try {
  const opts = parseArgs(process.argv.slice(2));
  const accountId = opts.accountId || deriveAccountId(opts);
  const encodedRuntime = encodeURIComponent(opts.runtime);
  const encodedEndpoint = encodeURIComponent(opts.endpoint);
  process.stdout.write(`https://${accountId}.agentrun-data.${opts.region}.aliyuncs.com/agent-runtimes/${encodedRuntime}/endpoints/${encodedEndpoint}/invocations\n`);
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  process.exit(1);
}
