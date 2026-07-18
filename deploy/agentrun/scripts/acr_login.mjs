#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/acr_login.mjs [options]

Options:
  --registry HOST      Registry host, for example registry.cn-hangzhou.aliyuncs.com.
                       Defaults to ACR_REGISTRY or the host in AGENTRUN_IMAGE.
  --image IMAGE        Image reference used to derive registry host. Defaults to AGENTRUN_IMAGE.
  --instance-id ID     ACR Enterprise Edition instance id. Defaults to ACR_INSTANCE_ID.
  --profile NAME       Aliyun CLI profile for Enterprise temporary token. Defaults to ACR_ALIYUN_PROFILE or default.
  --region REGION      Aliyun region. Defaults to ACR_REGION or AGENTRUN_REGION or cn-hangzhou.
  -h, --help           Show this help.

Enterprise mode:
  Set --instance-id or ACR_INSTANCE_ID. The script calls
  aliyun cr get-authorization-token and pipes the temporary token to docker login.

Personal/manual mode:
  Omit instance id and set ACR_USERNAME plus ACR_PASSWORD. The password is piped
  to docker login and is never printed.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    image: process.env.AGENTRUN_IMAGE || "",
    registry: process.env.ACR_REGISTRY || "",
    instanceId: process.env.ACR_INSTANCE_ID || "",
    profile: process.env.ACR_ALIYUN_PROFILE || process.env.AGENTRUN_ALIYUN_PROFILE || "default",
    region: process.env.ACR_REGION || process.env.AGENTRUN_REGION || "cn-hangzhou",
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--registry") {
      opts.registry = argv[++i];
    } else if (arg === "--image") {
      opts.image = argv[++i];
    } else if (arg === "--instance-id") {
      opts.instanceId = argv[++i];
    } else if (arg === "--profile") {
      opts.profile = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  if (!opts.registry && opts.image) {
    opts.registry = opts.image.split("/")[0] || "";
  }
  if (!opts.registry || !opts.registry.includes(".")) {
    throw new Error("registry host is required; set --registry, ACR_REGISTRY, or AGENTRUN_IMAGE");
  }
  return opts;
}

function getEnterpriseCredential(opts) {
  const result = spawnSync(
    "aliyun",
    [
      "cr",
      "get-authorization-token",
      "--instance-id",
      opts.instanceId,
      "--profile",
      opts.profile,
      "--region",
      opts.region,
    ],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (result.status !== 0) {
    const stderr = result.stderr.trim().replace(/[A-Za-z0-9+/=_-]{32,}/g, "[REDACTED]");
    throw new Error(`failed to get ACR authorization token: ${stderr || `exit ${result.status}`}`);
  }
  const parsed = JSON.parse(result.stdout);
  if (!parsed.TempUsername || !parsed.AuthorizationToken) {
    throw new Error("ACR GetAuthorizationToken response did not include TempUsername and AuthorizationToken");
  }
  return {
    username: parsed.TempUsername,
    password: parsed.AuthorizationToken,
    expiresAt: parsed.ExpireTime ? new Date(Number(parsed.ExpireTime)).toISOString() : "",
  };
}

function dockerLogin(registry, username, password) {
  const child = spawn("docker", ["login", "--username", username, "--password-stdin", registry], {
    stdio: ["pipe", "inherit", "inherit"],
  });
  child.stdin.end(`${password}\n`);
  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 1);
  });
}

function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    usage(2);
  }

  if (opts.instanceId) {
    const credential = getEnterpriseCredential(opts);
    process.stderr.write(`info: logging in to ${opts.registry} with ACR temporary credential`);
    if (credential.expiresAt) process.stderr.write(` expiring at ${credential.expiresAt}`);
    process.stderr.write("\n");
    dockerLogin(opts.registry, credential.username, credential.password);
    return;
  }

  const username = process.env.ACR_USERNAME || "";
  const password = process.env.ACR_PASSWORD || "";
  if (!username || !password) {
    throw new Error("ACR_USERNAME and ACR_PASSWORD are required when ACR_INSTANCE_ID is not set");
  }
  process.stderr.write(`info: logging in to ${opts.registry} with ACR_USERNAME\n`);
  dockerLogin(opts.registry, username, password);
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  process.exit(1);
}
