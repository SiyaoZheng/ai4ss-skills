#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const IMAGE_PLACEHOLDER = "registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>";
const ACCOUNT_ID_PLACEHOLDER = "<account-id>";
const ACR_USERNAME_PLACEHOLDER = "<acr-username>";
const ACR_PASSWORD_PLACEHOLDER = "<acr-password>";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/render_runtime.mjs --template runtime.yaml --out out.yaml --image IMAGE [options]

Options:
  --template PATH       Runtime YAML template.
  --out PATH            Rendered YAML path.
  --image IMAGE         Concrete image reference.
  --include-secret-env  Comma-separated env names to inject from process env.
                        Defaults to AGENTRUN_SECRET_ENV_KEYS when set.
  --allow-missing       Do not fail when an included env name is missing.
  -h, --help            Show this help.

This renderer keeps source templates secret-free. Secret env values are only
written to the requested output file, so use a temp file for cloud apply.
When the template contains ACR Personal registry placeholders, set ACR_USERNAME.
ACR_PASSWORD can come from env, or from macOS Keychain service
ACR_KEYCHAIN_SERVICE (default: aliyun-acr-personal-cn-hangzhou).
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    template: "",
    out: "",
    image: "",
    secretEnvKeys: process.env.AGENTRUN_SECRET_ENV_KEYS || "",
    allowMissing: process.env.AGENTRUN_ALLOW_MISSING_SECRET_ENV === "1",
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--template") {
      opts.template = argv[++i];
    } else if (arg === "--out") {
      opts.out = argv[++i];
    } else if (arg === "--image") {
      opts.image = argv[++i];
    } else if (arg === "--include-secret-env") {
      opts.secretEnvKeys = argv[++i];
    } else if (arg === "--allow-missing") {
      opts.allowMissing = true;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  if (!opts.template) throw new Error("--template is required");
  if (!opts.out) throw new Error("--out is required");
  if (!opts.image) throw new Error("--image is required");
  if (opts.image.includes("<namespace>") || opts.image.includes("<tag>")) {
    throw new Error("--image still contains placeholders");
  }
  return opts;
}

function yamlSingleQuote(value) {
  if (value.includes("\n") || value.includes("\r")) {
    throw new Error("secret env values must be single-line strings");
  }
  return `'${value.replaceAll("'", "''")}'`;
}

function injectEnv(yaml, envEntries) {
  if (envEntries.length === 0) return yaml;
  const lines = yaml.split("\n");
  const envIndex = lines.findIndex((line) => line.trim() === "env:");
  if (envIndex === -1) throw new Error("template is missing spec.env block");

  const existing = new Set();
  for (const line of lines.slice(envIndex + 1)) {
    const match = line.match(/^ {4}([A-Za-z_][A-Za-z0-9_]*):/);
    if (match) existing.add(match[1]);
    if (/^ {2}\S/.test(line)) break;
  }

  const injected = [];
  for (const [key, value] of envEntries) {
    if (existing.has(key)) {
      throw new Error(`template already defines env.${key}; refusing to overwrite`);
    }
    injected.push(`    ${key}: ${yamlSingleQuote(value)}`);
  }
  lines.splice(envIndex + 1, 0, ...injected);
  return lines.join("\n");
}

function renderAccountScopedFields(yaml) {
  const executionRoleArn = process.env.AGENTRUN_EXECUTION_ROLE_ARN || "";
  let rendered = yaml;
  if (executionRoleArn) {
    rendered = rendered.replace(/^(\s*executionRoleArn:\s*).+$/m, `$1${executionRoleArn}`);
  }
  if (rendered.includes(ACCOUNT_ID_PLACEHOLDER)) {
    const accountId = process.env.AGENTRUN_ACCOUNT_ID || "";
    if (!accountId) {
      throw new Error("AGENTRUN_ACCOUNT_ID is required to render <account-id>");
    }
    rendered = rendered.replaceAll(ACCOUNT_ID_PLACEHOLDER, accountId);
  }
  return rendered;
}

function readAcrPasswordFromKeychain(username) {
  if (process.platform !== "darwin") return "";
  const service = process.env.ACR_KEYCHAIN_SERVICE || "aliyun-acr-personal-cn-hangzhou";
  const result = spawnSync(
    "security",
    ["find-generic-password", "-s", service, "-a", username, "-w"],
    { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
  );
  if (result.status !== 0) return "";
  return result.stdout.trim();
}

function renderRegistryAuth(yaml) {
  if (!yaml.includes(ACR_USERNAME_PLACEHOLDER) && !yaml.includes(ACR_PASSWORD_PLACEHOLDER)) {
    return yaml;
  }
  const username = process.env.ACR_USERNAME || "";
  if (!username) {
    throw new Error("ACR_USERNAME is required to render <acr-username>");
  }
  const password = process.env.ACR_PASSWORD || readAcrPasswordFromKeychain(username);
  if (!password) {
    throw new Error("ACR_PASSWORD is required to render <acr-password>");
  }
  return yaml
    .replaceAll(ACR_USERNAME_PLACEHOLDER, yamlSingleQuote(username))
    .replaceAll(ACR_PASSWORD_PLACEHOLDER, yamlSingleQuote(password));
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const raw = fs.readFileSync(opts.template, "utf8");
  let rendered = raw.replaceAll(IMAGE_PLACEHOLDER, opts.image);
  rendered = renderAccountScopedFields(rendered);
  rendered = renderRegistryAuth(rendered);
  if (rendered.includes("<namespace>") || rendered.includes("<tag>")) {
    throw new Error("rendered YAML still contains image placeholders");
  }
  if (rendered.includes(ACCOUNT_ID_PLACEHOLDER)) {
    throw new Error("rendered YAML still contains account id placeholder");
  }
  if (rendered.includes(ACR_USERNAME_PLACEHOLDER) || rendered.includes(ACR_PASSWORD_PLACEHOLDER)) {
    throw new Error("rendered YAML still contains ACR registry placeholders");
  }

  const envEntries = [];
  const keys = opts.secretEnvKeys
    .split(",")
    .map((key) => key.trim())
    .filter(Boolean);
  for (const key of keys) {
    const value = process.env[key] || "";
    if (!value) {
      if (opts.allowMissing) continue;
      throw new Error(`${key} is required for secret env injection`);
    }
    envEntries.push([key, value]);
  }
  rendered = injectEnv(rendered, envEntries);

  fs.mkdirSync(path.dirname(opts.out), { recursive: true });
  fs.writeFileSync(opts.out, rendered);
  const target = opts.out.startsWith(os.tmpdir()) ? "temporary runtime YAML" : opts.out;
  process.stderr.write(`info: rendered ${target}${envEntries.length ? " with secret env injection" : ""}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  process.exit(1);
}
