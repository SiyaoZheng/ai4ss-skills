#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_REGION = "cn-hangzhou";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/with_aliyun_profile_env.mjs [options] -- <command> [args...]

Options:
  --profile NAME       Aliyun CLI profile to read. Defaults to AGENTRUN_ALIYUN_PROFILE or default.
  --region REGION     AgentRun region. Defaults to AGENTRUN_REGION or ${DEFAULT_REGION}.
  --account-id ID     Aliyun account id. When omitted, derived with aliyun sts GetCallerIdentity.
  --config PATH       Aliyun CLI config path. Defaults to ~/.aliyun/config.json.
  -h, --help          Show this help.

The script exports AGENTRUN_ACCESS_KEY_ID, AGENTRUN_ACCESS_KEY_SECRET,
AGENTRUN_ACCOUNT_ID, AGENTRUN_REGION, and matching ALIBABA_CLOUD_* values only
to the child process. OAuth/STS profiles are supported when the Aliyun CLI
profile contains a refreshed access key, secret, and STS token. It never prints
secrets.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    profile: process.env.AGENTRUN_ALIYUN_PROFILE || "default",
    region: process.env.AGENTRUN_REGION || DEFAULT_REGION,
    accountId: process.env.AGENTRUN_ACCOUNT_ID || "",
    configPath: path.join(os.homedir(), ".aliyun", "config.json"),
    command: [],
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--") {
      opts.command = argv.slice(i + 1);
      return opts;
    }
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--profile") {
      opts.profile = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else if (arg === "--account-id") {
      opts.accountId = argv[++i];
    } else if (arg === "--config") {
      opts.configPath = argv[++i];
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return opts;
}

function readAliyunProfile(configPath, profileName) {
  const cliResult = spawnSync(
    "aliyun",
    ["configure", "get", "--profile", profileName, "--config-path", configPath],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (cliResult.status === 0 && cliResult.stdout.trim()) {
    const profile = JSON.parse(cliResult.stdout);
    if (!profile.access_key_id || !profile.access_key_secret) {
      throw new Error(`Aliyun profile ${profileName} is missing access_key_id/access_key_secret`);
    }
    if (profile.mode !== "AK" && !profile.sts_token) {
      throw new Error(`Aliyun profile ${profileName} uses mode ${profile.mode} but has no sts_token; refresh the profile with aliyun configure or use an AK profile.`);
    }
    return profile;
  }

  const raw = fs.readFileSync(configPath, "utf8");
  const config = JSON.parse(raw);
  const profiles = Array.isArray(config.profiles) ? config.profiles : [];
  const profile = profiles.find((item) => item.name === profileName);
  if (!profile) {
    const names = profiles.map((item) => item.name).join(", ") || "(none)";
    throw new Error(`Aliyun profile ${profileName} not found in ${configPath}; available: ${names}`);
  }
  if (!profile.access_key_id || !profile.access_key_secret) {
    throw new Error(`Aliyun profile ${profileName} is missing access_key_id/access_key_secret`);
  }
  if (profile.mode !== "AK" && !profile.sts_token) {
    throw new Error(`Aliyun profile ${profileName} uses mode ${profile.mode} but has no sts_token; refresh the profile with aliyun configure or use an AK profile.`);
  }
  return profile;
}

function deriveAccountId(profileName, region) {
  const result = spawnSync(
    "aliyun",
    ["sts", "GetCallerIdentity", "--profile", profileName, "--region", region],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (result.status !== 0) {
    const stderr = result.stderr.trim().replace(/[A-Za-z0-9+/=_-]{32,}/g, "[REDACTED]");
    throw new Error(`failed to derive account id with aliyun sts GetCallerIdentity: ${stderr || `exit ${result.status}`}`);
  }
  const parsed = JSON.parse(result.stdout);
  if (!parsed.AccountId) {
    throw new Error("aliyun sts GetCallerIdentity did not return AccountId");
  }
  return String(parsed.AccountId);
}

function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    usage(2);
  }

  if (opts.command.length === 0) {
    process.stderr.write("error: child command is required after --\n");
    usage(2);
  }

  const accountId = opts.accountId || deriveAccountId(opts.profile, opts.region);
  const profile = readAliyunProfile(opts.configPath, opts.profile);
  const tokenEnv = profile.sts_token
    ? {
        AGENTRUN_SECURITY_TOKEN: profile.sts_token,
        ALIBABA_CLOUD_SECURITY_TOKEN: profile.sts_token,
        ALIBABA_CLOUD_STS_TOKEN: profile.sts_token,
      }
    : {};
  const env = {
    ...process.env,
    AGENTRUN_ACCESS_KEY_ID: profile.access_key_id,
    AGENTRUN_ACCESS_KEY_SECRET: profile.access_key_secret,
    AGENTRUN_ACCOUNT_ID: accountId,
    AGENTRUN_REGION: opts.region,
    ALIBABA_CLOUD_ACCESS_KEY_ID: profile.access_key_id,
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: profile.access_key_secret,
    ALIBABA_CLOUD_REGION_ID: opts.region,
    ...tokenEnv,
  };

  process.stderr.write(`info: running with Aliyun profile ${opts.profile}, account ${accountId}, region ${opts.region}\n`);
  const child = spawn(opts.command[0], opts.command.slice(1), {
    env,
    stdio: "inherit",
  });
  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 1);
  });
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  process.exit(1);
}
