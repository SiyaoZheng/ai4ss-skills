#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  AGENTRUN_RUNTIME_API_KEY=... node deploy/agentrun/scripts/create_inbound_credential.mjs [options]

Options:
  --name NAME        Credential name. Defaults to ai4ss-codex-harness-inbound.
  --profile NAME     Aliyun CLI profile. Defaults to AGENTRUN_ALIYUN_PROFILE or default.
  --region REGION    Region. Defaults to AGENTRUN_REGION or cn-hangzhou.
  --header-key NAME  Header key for platform access. Defaults to X-API-Key.
  --dry-run          Print the redacted request without creating a credential.
  -h, --help         Show this help.

The secret value is read from AGENTRUN_RUNTIME_API_KEY and redacted from CLI
output. The credential protects the AgentRun platform endpoint; it does not
inject application env secrets into the container.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    name: process.env.AGENTRUN_INBOUND_CREDENTIAL_NAME || "ai4ss-codex-harness-inbound",
    profile: process.env.AGENTRUN_ALIYUN_PROFILE || "default",
    region: process.env.AGENTRUN_REGION || "cn-hangzhou",
    headerKey: process.env.AGENTRUN_INBOUND_HEADER_KEY || "X-API-Key",
    dryRun: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--name") {
      opts.name = argv[++i];
    } else if (arg === "--profile") {
      opts.profile = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else if (arg === "--header-key") {
      opts.headerKey = argv[++i];
    } else if (arg === "--dry-run") {
      opts.dryRun = true;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return opts;
}

function redact(output, secret) {
  let redacted = output;
  if (secret) redacted = redacted.split(secret).join("[REDACTED]");
  return redacted
    .replace(/(LTAI[0-9A-Za-z]+)/g, "[REDACTED]")
    .replace(/[A-Za-z0-9+/=_-]{48,}/g, "[REDACTED]")
    .replace(/(access_key_id|access_key_secret|AccessKeyId|AccessKeySecret|secret|token|password)/gi, "[REDACTED]");
}

function credentialExists(opts) {
  const result = spawnSync(
    "aliyun",
    [
      "agentrun",
      "get-credential",
      "--profile",
      opts.profile,
      "--region",
      opts.region,
      "--credential-name",
      opts.name,
    ],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  return result.status === 0;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const apiKey = process.env.AGENTRUN_RUNTIME_API_KEY || "";
  if (!apiKey) throw new Error("AGENTRUN_RUNTIME_API_KEY is required");

  const exists = credentialExists(opts);
  const args = [
    "agentrun",
    exists ? "update-credential" : "create-credential",
    "--profile",
    opts.profile,
    "--region",
    opts.region,
    "--credential-name",
    opts.name,
  ];
  if (!exists) {
    args.push(
      "--credential-auth-type",
      "api_key",
      "--credential-source-type",
      "internal",
    );
  }
  args.push(
    "--credential-secret",
    apiKey,
    "--credential-public-config",
    `headerKey=${opts.headerKey} prefix=`,
    "--enabled",
    "true",
  );
  if (opts.dryRun) args.push("--cli-dry-run");

  const result = spawnSync("aliyun", args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  process.stdout.write(redact(result.stdout, apiKey));
  process.stderr.write(redact(result.stderr, apiKey));
  if (result.status !== 0) process.exit(result.status ?? 1);
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  process.exit(1);
}
