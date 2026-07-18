#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const DEFAULT_RUNTIME_BUILD = "deploy/agentrun/runtime-build.yaml";

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  node deploy/agentrun/scripts/registry_preflight.mjs [options]

Options:
  --mode MODE              local-push, cloud-build, or both.
                           Defaults to AGENTRUN_REGISTRY_PREFLIGHT_MODE or both.
  --image IMAGE            Target image. Defaults to AGENTRUN_IMAGE.
  --runtime-build FILE     Runtime build YAML. Defaults to ${DEFAULT_RUNTIME_BUILD}.
  --profile NAME           Aliyun CLI profile for ACR discovery. Defaults to ACR_ALIYUN_PROFILE or default.
  --region REGION          Aliyun region. Defaults to ACR_REGION or AGENTRUN_REGION or cn-hangzhou.
  --strict                 Treat cloud-build missing registry credentials as an error.
  -h, --help               Show this help.

This command checks registry prerequisites without printing credentials and
without creating cloud resources.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const opts = {
    mode: process.env.AGENTRUN_REGISTRY_PREFLIGHT_MODE || "both",
    image: process.env.AGENTRUN_IMAGE || "",
    runtimeBuild: process.env.AGENTRUN_RUNTIME_BUILD_TEMPLATE || DEFAULT_RUNTIME_BUILD,
    profile: process.env.ACR_ALIYUN_PROFILE || process.env.AGENTRUN_ALIYUN_PROFILE || "default",
    region: process.env.ACR_REGION || process.env.AGENTRUN_REGION || "cn-hangzhou",
    strict: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") usage(0);
    if (arg === "--mode") {
      opts.mode = argv[++i];
    } else if (arg === "--image") {
      opts.image = argv[++i];
    } else if (arg === "--runtime-build") {
      opts.runtimeBuild = argv[++i];
    } else if (arg === "--profile") {
      opts.profile = argv[++i];
    } else if (arg === "--region") {
      opts.region = argv[++i];
    } else if (arg === "--strict") {
      opts.strict = true;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!["local-push", "cloud-build", "both"].includes(opts.mode)) {
    throw new Error("--mode must be local-push, cloud-build, or both");
  }
  return opts;
}

function parseImage(image) {
  if (!image) {
    throw new Error("AGENTRUN_IMAGE is required");
  }
  if (image.includes("<namespace>") || image.includes("<tag>")) {
    throw new Error("AGENTRUN_IMAGE still contains runtime template placeholders");
  }
  const parts = image.split("/");
  if (parts.length < 3 || !parts[0].includes(".")) {
    throw new Error("AGENTRUN_IMAGE must include a registry host, namespace, repository, and tag");
  }
  const registry = parts[0];
  const imageTail = parts.slice(1).join("/");
  if (!imageTail.includes(":")) {
    throw new Error("AGENTRUN_IMAGE must include an explicit tag");
  }
  return { registry, imageTail };
}

function readDockerConfig() {
  const configPath = path.join(os.homedir(), ".docker", "config.json");
  if (!existsSync(configPath)) {
    return { path: configPath, exists: false, auths: {}, credHelpers: {}, credsStore: "" };
  }
  try {
    const parsed = JSON.parse(readFileSync(configPath, "utf8"));
    return {
      path: configPath,
      exists: true,
      auths: parsed.auths || {},
      credHelpers: parsed.credHelpers || {},
      credsStore: parsed.credsStore || "",
    };
  } catch (error) {
    return { path: configPath, exists: true, parseError: error.message, auths: {}, credHelpers: {}, credsStore: "" };
  }
}

function hasDockerAuth(dockerConfig, registry) {
  if (dockerConfig.parseError) return false;
  if (dockerConfig.auths[registry]) return true;
  if (dockerConfig.auths[`https://${registry}`]) return true;
  if (dockerConfig.credHelpers[registry]) return true;
  if (dockerConfig.credsStore) return true;
  return false;
}

function runtimeBuildHasLiteralRegistryAuth(runtimeBuild) {
  if (!existsSync(runtimeBuild)) {
    return false;
  }
  const text = readFileSync(runtimeBuild, "utf8");
  const cloudBuildIndex = text.indexOf("cloudBuild:");
  if (cloudBuildIndex === -1) return false;
  const cloudBuildText = text.slice(cloudBuildIndex);
  return /(^|\n)\s+registry:\s*(\n|$)/.test(cloudBuildText)
    && /(^|\n)\s+username:\s*\S+/.test(cloudBuildText)
    && /(^|\n)\s+password:\s*\S+/.test(cloudBuildText);
}

function aliyunAcrDiscovery(opts) {
  const aliyun = spawnSync("aliyun", ["version"], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  if (aliyun.status !== 0) {
    return { available: false, reason: "aliyun CLI not available" };
  }

  const result = spawnSync(
    "aliyun",
    ["cr", "list-instance", "--profile", opts.profile, "--region", opts.region],
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
  if (result.status !== 0) {
    return {
      available: false,
      reason: (result.stderr || result.stdout || `exit ${result.status}`).trim().replace(/[A-Za-z0-9+/=_-]{32,}/g, "[REDACTED]"),
    };
  }
  try {
    const parsed = JSON.parse(result.stdout);
    const instances = Array.isArray(parsed.Instances) ? parsed.Instances : [];
    return {
      available: true,
      count: Number(parsed.TotalCount ?? instances.length),
      instanceIds: instances.map((item) => item.InstanceId).filter(Boolean),
    };
  } catch (error) {
    return { available: false, reason: `could not parse aliyun cr list-instance output: ${error.message}` };
  }
}

function reporter() {
  let failures = 0;
  let warnings = 0;
  return {
    ok(message) {
      process.stdout.write(`ok: ${message}\n`);
    },
    warn(message) {
      warnings += 1;
      process.stdout.write(`warn: ${message}\n`);
    },
    fail(message) {
      failures += 1;
      process.stdout.write(`fail: ${message}\n`);
    },
    finish() {
      process.stdout.write(`summary: failures=${failures} warnings=${warnings}\n`);
      return failures === 0 ? 0 : 1;
    },
  };
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const out = reporter();
  process.stdout.write(`ai4ss-skills AgentRun registry preflight\nmode=${opts.mode}\n`);

  let parsedImage;
  try {
    parsedImage = parseImage(opts.image);
    out.ok(`target image ${opts.image}`);
    out.ok(`registry host ${parsedImage.registry}`);
  } catch (error) {
    out.fail(error.message);
    process.exit(out.finish());
  }

  if (parsedImage.registry.endsWith(".aliyuncs.com")) {
    const acr = aliyunAcrDiscovery(opts);
    if (!acr.available) {
      out.warn(`ACR discovery skipped or failed: ${acr.reason}`);
    } else if (acr.count > 0) {
      out.ok(`ACR Enterprise instances visible in ${opts.region}: ${acr.count}`);
      if (process.env.ACR_INSTANCE_ID && !acr.instanceIds.includes(process.env.ACR_INSTANCE_ID)) {
        out.warn("ACR_INSTANCE_ID is set but was not returned by cr list-instance in this region");
      }
    } else {
      out.warn(`no ACR Enterprise instances visible in ${opts.region}; this is fine for ACR Personal Edition if the personal namespace/repository exists in the console`);
    }
  }

  const dockerConfig = readDockerConfig();
  if (!dockerConfig.exists) {
    out.warn(`Docker config missing at ${dockerConfig.path}`);
  } else if (dockerConfig.parseError) {
    out.warn(`Docker config could not be parsed: ${dockerConfig.parseError}`);
  } else if (hasDockerAuth(dockerConfig, parsedImage.registry)) {
    out.ok("Docker config has a registry auth path for local push");
  } else {
    out.warn("Docker config has no auths, credential helper, or credential store for the target registry");
  }

  const hasAcrEeLogin = Boolean(process.env.ACR_INSTANCE_ID);
  const hasManualAcrLogin = Boolean(process.env.ACR_USERNAME && process.env.ACR_PASSWORD);
  if (opts.mode === "local-push" || opts.mode === "both") {
    if (hasAcrEeLogin) {
      out.ok("ACR_INSTANCE_ID is set; acr-login can request a temporary ACR token");
    } else if (hasManualAcrLogin) {
      out.ok("ACR_USERNAME and ACR_PASSWORD are set for local docker login");
    } else if (hasDockerAuth(dockerConfig, parsedImage.registry)) {
      out.ok("local docker push can use existing Docker registry auth");
    } else {
      out.fail("no local image push auth path found; for ACR Personal Edition set ACR_USERNAME/ACR_PASSWORD or docker login to the target registry");
    }
  }

  const hasBuilderEnvAuth = Boolean(process.env.DOCKER_IMAGE_BUILDER_USERNAME && process.env.DOCKER_IMAGE_BUILDER_PASSWORD);
  const hasBuilderYamlAuth = runtimeBuildHasLiteralRegistryAuth(opts.runtimeBuild);
  if (opts.mode === "cloud-build" || opts.mode === "both") {
    if (hasBuilderEnvAuth) {
      out.ok("DOCKER_IMAGE_BUILDER_USERNAME and DOCKER_IMAGE_BUILDER_PASSWORD are set for AgentRun cloud-build");
    } else if (hasBuilderYamlAuth) {
      out.ok("runtime-build YAML contains literal cloudBuild.registry auth");
    } else if (opts.strict) {
      out.fail("no explicit docker-image-builder registry auth found; set DOCKER_IMAGE_BUILDER_USERNAME/PASSWORD or cloudBuild.registry");
    } else {
      out.warn("no explicit docker-image-builder registry auth found; cloud-build only works if the target registry accepts the builder's available credentials");
    }
  }

  process.exit(out.finish());
}

try {
  main();
} catch (error) {
  process.stderr.write(`error: ${error.message}\n`);
  usage(2);
}
