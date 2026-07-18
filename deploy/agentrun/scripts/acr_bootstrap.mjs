#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/acr_bootstrap.mjs [options]

Options:
  --image IMAGE            Target image. Defaults to AGENTRUN_IMAGE.
  --instance-id ID         ACR instance id. Defaults to ACR_INSTANCE_ID.
  --profile NAME           Aliyun CLI profile. Defaults to ACR_ALIYUN_PROFILE or default.
  --region REGION          Aliyun region. Defaults to ACR_REGION or AGENTRUN_REGION or cn-hangzhou.
  --repo-type TYPE         PUBLIC or PRIVATE. Defaults to PRIVATE.
  --summary TEXT           Repository summary.
  --auto-create-repo BOOL  true or false for namespace setting. Defaults to true.
  --yes                    Create missing namespace/repository.
  -h, --help               Show this help.

This command bootstraps namespace/repository only inside an existing ACR
Enterprise instance. ACR Personal Edition namespace/repository creation is a
console workflow; use ACR_USERNAME/ACR_PASSWORD plus acr-login for that path.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    image: process.env.AGENTRUN_IMAGE || "",
    instanceId: process.env.ACR_INSTANCE_ID || "",
    profile: process.env.ACR_ALIYUN_PROFILE || process.env.AGENTRUN_ALIYUN_PROFILE || "default",
    region: process.env.ACR_REGION || process.env.AGENTRUN_REGION || "cn-hangzhou",
    repoType: process.env.ACR_REPO_TYPE || "PRIVATE",
    summary: process.env.ACR_REPO_SUMMARY || "ai4ss-skills Codex AgentRun harness",
    autoCreateRepo: process.env.ACR_AUTO_CREATE_REPO || "true",
    yes: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--image") {
      opts.image = argv[++i];
    } else if (arg === "--instance-id") {
      opts.instanceId = argv[++i];
    } else if (arg === "--profile") {
      opts.profile = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else if (arg === "--repo-type") {
      opts.repoType = argv[++i];
    } else if (arg === "--summary") {
      opts.summary = argv[++i];
    } else if (arg === "--auto-create-repo") {
      opts.autoCreateRepo = argv[++i];
    } else if (arg === "--yes") {
      opts.yes = true;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  opts.repoType = opts.repoType.toUpperCase();
  if (!["PUBLIC", "PRIVATE"].includes(opts.repoType)) {
    throw new Error("--repo-type must be PUBLIC or PRIVATE");
  }
  if (!["true", "false"].includes(String(opts.autoCreateRepo))) {
    throw new Error("--auto-create-repo must be true or false");
  }
  return opts;
}

function parseImage(image) {
  if (!image) throw new Error("AGENTRUN_IMAGE is required");
  if (image.includes("<namespace>") || image.includes("<tag>")) {
    throw new Error("AGENTRUN_IMAGE still contains template placeholders");
  }
  const parts = image.split("/");
  if (parts.length !== 3 || !parts[0].includes(".")) {
    throw new Error("AGENTRUN_IMAGE must look like registry.<region>.aliyuncs.com/<namespace>/<repo>:<tag>");
  }
  const repoAndTag = parts[2];
  const tagIndex = repoAndTag.lastIndexOf(":");
  if (tagIndex === -1) throw new Error("AGENTRUN_IMAGE must include an explicit tag");
  const repository = repoAndTag.slice(0, tagIndex);
  if (!parts[1] || !repository) {
    throw new Error("AGENTRUN_IMAGE must include namespace and repository");
  }
  return {
    registry: parts[0],
    namespace: parts[1],
    repository,
  };
}

function redact(value) {
  return String(value || "").replace(/[A-Za-z0-9+/=_-]{32,}/g, "[REDACTED]");
}

function aliyun(args, opts) {
  const result = spawnSync(
    "aliyun",
    [...args, "--profile", opts.profile, "--region", opts.region],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (result.status !== 0) {
    const details = redact(result.stderr || result.stdout || `exit ${result.status}`);
    throw new Error(`aliyun ${args.join(" ")} failed: ${details.trim()}`);
  }
  const stdout = result.stdout.trim();
  if (!stdout) return {};
  try {
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`aliyun ${args.join(" ")} returned non-JSON output: ${error.message}`);
  }
}

function listNamespace(opts, namespace) {
  const response = aliyun(
    [
      "cr",
      "list-namespace",
      "--instance-id",
      opts.instanceId,
      "--namespace-name",
      namespace,
      "--page-size",
      "100",
    ],
    opts,
  );
  const namespaces = Array.isArray(response.Namespaces) ? response.Namespaces : [];
  return namespaces.some((item) => item.NamespaceName === namespace);
}

function listRepository(opts, namespace, repository) {
  const response = aliyun(
    [
      "cr",
      "list-repository",
      "--instance-id",
      opts.instanceId,
      "--repo-namespace-name",
      namespace,
      "--repo-name",
      repository,
      "--repo-status",
      "NORMAL",
      "--page-size",
      "100",
    ],
    opts,
  );
  const repositories = Array.isArray(response.Repositories) ? response.Repositories : [];
  return repositories.some((item) => item.RepoNamespaceName === namespace && item.RepoName === repository);
}

function createNamespace(opts, namespace) {
  return aliyun(
    [
      "cr",
      "create-namespace",
      "--instance-id",
      opts.instanceId,
      "--namespace-name",
      namespace,
      "--auto-create-repo",
      opts.autoCreateRepo,
      "--default-repo-type",
      opts.repoType,
    ],
    opts,
  );
}

function createRepository(opts, namespace, repository) {
  return aliyun(
    [
      "cr",
      "create-repository",
      "--instance-id",
      opts.instanceId,
      "--repo-name",
      repository,
      "--repo-namespace-name",
      namespace,
      "--repo-type",
      opts.repoType,
      "--summary",
      opts.summary,
      "--detail",
      opts.summary,
      "--tag-immutability",
      "false",
    ],
    opts,
  );
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const image = parseImage(opts.image);
  process.stdout.write("ai4ss-skills ACR bootstrap\n");
  process.stdout.write(`registry=${image.registry}\nnamespace=${image.namespace}\nrepository=${image.repository}\nregion=${opts.region}\n`);

  if (!opts.instanceId) {
    process.stdout.write("fail: ACR_INSTANCE_ID is required for this enterprise-only bootstrap helper\n");
    process.stdout.write("info: for ACR Personal Edition, create the personal instance, namespace, and repository in the console, then set ACR_USERNAME/ACR_PASSWORD and run deploy.sh acr-login\n");
    process.exit(1);
  }

  const namespaceExists = listNamespace(opts, image.namespace);
  if (namespaceExists) {
    process.stdout.write(`ok: namespace ${image.namespace} exists\n`);
  } else if (!opts.yes) {
    process.stdout.write(`plan: create namespace ${image.namespace}; rerun with --yes to mutate ACR\n`);
    process.exit(1);
  } else {
    createNamespace(opts, image.namespace);
    process.stdout.write(`ok: created namespace ${image.namespace}\n`);
  }

  const repositoryExists = listRepository(opts, image.namespace, image.repository);
  if (repositoryExists) {
    process.stdout.write(`ok: repository ${image.namespace}/${image.repository} exists\n`);
  } else if (!opts.yes) {
    process.stdout.write(`plan: create repository ${image.namespace}/${image.repository}; rerun with --yes to mutate ACR\n`);
    process.exit(1);
  } else {
    createRepository(opts, image.namespace, image.repository);
    process.stdout.write(`ok: created repository ${image.namespace}/${image.repository}\n`);
  }

  process.stdout.write("summary: ACR namespace/repository ready\n");
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${redact(error.message)}\n`);
  process.exit(1);
}
