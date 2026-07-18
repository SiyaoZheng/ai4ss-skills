# ai4ss-skills Codex harness on AgentRun

This directory contains the deployable scaffold for running the ai4ss-skills
Codex app-server harness on Alibaba Cloud AgentRun AgentRuntime.

The deployment shape is:

```text
AgentRun AgentRuntime container
  -> gateway/server.mjs
  -> local codex app-server --listen stdio://
  -> Codex model_provider=deepseek
  -> ai4ss-skills workspace at /workspace
```

The gateway intentionally proxies Codex app-server over local `stdio` rather
than exposing Codex's experimental WebSocket listener to the public network.
The image includes a workspace snapshot under
`/opt/ai4ss-codex-harness/workspace-snapshot`; `entrypoint.sh` seeds
`CODEX_WORKSPACE_DIR` from that snapshot only when the target workspace is empty.

## Files

- `Dockerfile`: production-oriented container image for the gateway and Codex
  CLI.
- `entrypoint.sh`: writes the managed Codex config for the mounted workspace and
  DeepSeek model provider before starting the gateway.
- `gateway/server.mjs`: authenticated HTTP/SSE gateway around local Codex
  app-server child processes.
- `runtime.yaml`: minimal AgentRun `AgentRuntime` manifest for an existing ACR
  Personal image, rendered with private registry pull auth at deploy time.
- `runtime-build.yaml`: AgentRun cloud-build variant.
- `runtime-nas.example.yaml`: NAS-backed variant for persistent session homes
  and optional persistent workspace edits.
- `scripts/deploy.sh`: build/push/render/apply/status command wrapper that
  uses `agentrun` when the short `ar` alias is unavailable.
- `scripts/with_aliyun_profile_env.mjs`: runs AgentRun CLI commands with
  credentials derived from an existing Aliyun AK profile without printing
  secrets.
- `scripts/acr_login.mjs`: Docker login helper for ACR Enterprise temporary
  tokens or personal/manual registry credentials.
- `scripts/acr_bootstrap.mjs`: checks or creates namespace/repository inside an
  existing ACR instance when `ACR_INSTANCE_ID` is available.
- `scripts/registry_preflight.mjs`: verifies image naming, Docker/ACR local
  push auth, and AgentRun cloud-build registry auth before any build/apply.
- `scripts/redact_agentrun_output.mjs`: redacts secrets from AgentRun render or
  diagnostic JSON before printing.
- `scripts/bootstrap_secrets.mjs`: creates ignored local deployment secrets for
  gateway auth and AgentRun platform API-key auth.
- `scripts/create_inbound_credential.mjs`: creates or dry-runs an AgentRun
  API-key credential for protecting the platform endpoint.
- `scripts/agentrun_gateway_url.mjs`: prints the AgentRun data-link base URL for
  the deployed gateway endpoint.
- `scripts/render_runtime.mjs`: renders the runtime template and, for cloud
  apply, can inject selected secret env values plus ACR Personal pull auth into
  a temporary YAML file that is not committed.
- `scripts/preflight.sh`: local/cloud readiness checks.
- `scripts/smoke_deepseek_api.mjs`: DeepSeek `/chat/completions` credential and
  API smoke test.
- `scripts/smoke_deepseek_responses_adapter.mjs`: local Responses API adapter
  smoke test.
- `scripts/smoke_appserver_stdio.mjs`: local protocol smoke test for
  `codex app-server --listen stdio://`.
- `scripts/smoke_gateway.mjs`: HTTP smoke test for a running gateway.
- `scripts/smoke_gateway_turn.mjs`: end-to-end Codex turn smoke through the
  gateway and DeepSeek backend.
- `scripts/smoke_gateway_stream.mjs`: SSE streaming smoke test for a running
  gateway.
- `scripts/check_no_secrets.sh`: simple secret-pattern scan for deployment
  files.

## Local preflight

```bash
deploy/agentrun/scripts/preflight.sh
```

Use strict mode before cloud deployment:

```bash
deploy/agentrun/scripts/preflight.sh --strict
```

The current machine must have the real AgentRun CLI installed. A system
`/usr/bin/ar` archive tool is not sufficient, even though its binary name is
`ar`.

## DeepSeek backend

The container defaults to DeepSeek:

```bash
CODEX_MODEL_PROVIDER=deepseek
CODEX_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
CODEX_DEEPSEEK_RESPONSES_BASE_URL=http://127.0.0.1:9000/internal/deepseek/v1
DEEPSEEK_API_KEY_ENV=DEEPSEEK_API_KEY
CODEX_PROVIDER_WIRE_API=responses
DEEPSEEK_RESPONSES_ADAPTER=true
DEEPSEEK_THINKING=disabled
CODEX_SESSION_HOME_ROOT=/home/codex/.codex-sessions
```

Inject `DEEPSEEK_API_KEY` through AgentRun credential management or runtime
environment variables. Do not bake it into the image or YAML.

Use `deepseek-v4-flash` as the default low-friction backend and override
`CODEX_MODEL=deepseek-v4-pro` when a higher-reasoning deployment is required.

Important compatibility gate: Codex custom providers currently use the
Responses wire API, while the official DeepSeek OpenAI-compatible endpoint is
`/chat/completions`. The gateway therefore includes a loopback-only
Responses-to-DeepSeek adapter at `/internal/deepseek/v1/responses`; keep
`CODEX_DEEPSEEK_RESPONSES_BASE_URL` pointed at that adapter unless replacing it
with a separately verified adapter service.

Validate DeepSeek credentials separately:

```bash
DEEPSEEK_API_KEY="<runtime-secret>" \
node deploy/agentrun/scripts/smoke_deepseek_api.mjs

DEEPSEEK_API_KEY="<runtime-secret>" \
DEEPSEEK_RESPONSES_ADAPTER_URL="http://127.0.0.1:9000/internal/deepseek/v1" \
node deploy/agentrun/scripts/smoke_deepseek_responses_adapter.mjs
```

## Build image locally

Set a concrete ACR image name:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
```

Build:

```bash
deploy/agentrun/scripts/deploy.sh build
```

The wrapper builds `linux/amd64` and disables BuildKit provenance/SBOM
attestations by default:

```bash
docker build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f deploy/agentrun/Dockerfile \
  -t "$AGENTRUN_IMAGE" \
  .
```

That shape pushed cleanly to ACR Personal Edition. A default BuildKit export can
produce an OCI index plus attestation manifests that ACR Personal may accept
slowly or fail to finalize.

Run locally:

```bash
docker run --rm \
  -p 9000:9000 \
  -e CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
  -e DEEPSEEK_API_KEY="<dev-only-deepseek-key>" \
  -e ALLOW_UNAUTHENTICATED=false \
  "$AGENTRUN_IMAGE"
```

Smoke test a running gateway:

```bash
GATEWAY_URL="http://127.0.0.1:9000" \
CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
node deploy/agentrun/scripts/smoke_gateway.mjs

GATEWAY_URL="http://127.0.0.1:9000" \
CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
node deploy/agentrun/scripts/smoke_gateway_stream.mjs

GATEWAY_URL="http://127.0.0.1:9000" \
CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
node deploy/agentrun/scripts/smoke_gateway_turn.mjs
```

For a host-local gateway test without Docker, start through `entrypoint.sh` and
use a temporary `CODEX_HOME`. Running `node gateway/server.mjs` directly will
not generate the DeepSeek provider config and can make Codex fall back to the
default OpenAI provider:

```bash
TMP_GATEWAY_ROOT=$(mktemp -d /tmp/ai4ss-agentrun-gateway.XXXXXX)
set -a
source deploy/agentrun/.generated/secrets.env
set +a
PORT=9025 \
HOST=127.0.0.1 \
CODEX_HOME="$TMP_GATEWAY_ROOT/codex-home" \
CODEX_SESSION_HOME_ROOT="$TMP_GATEWAY_ROOT/sessions" \
CODEX_WORKSPACE_DIR="$PWD" \
deploy/agentrun/entrypoint.sh node deploy/agentrun/gateway/server.mjs
```

Push:

```bash
docker push "$AGENTRUN_IMAGE"
```

## Deploy with AgentRun CLI

Install and configure the AgentRun CLI first:

```bash
curl -fsSL https://raw.githubusercontent.com/Serverless-Devs/agentrun-cli/main/scripts/install.sh | sh
agentrun --version

agentrun config set access_key_id <ACCESS_KEY_ID>
agentrun config set access_key_secret <ACCESS_KEY_SECRET>
agentrun config set account_id <ALIYUN_ACCOUNT_ID>
agentrun config set region cn-hangzhou
```

On this machine the existing Aliyun `default` profile is an AK profile. To avoid
copying AK/SK into shell history or `~/.agentrun/config.json`, run AgentRun
commands through the profile-env helper:

```bash
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile default \
  --region cn-hangzhou \
  -- agentrun rt list
```

Set `AGENTRUN_IMAGE`, then generate/render/apply through the wrapper:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile default \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh render
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile default \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh apply
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile default \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh status
```

The AgentRun docs use `ar` as the short command. On this macOS machine, the
installer created `agentrun` but did not create `ar`; `/usr/bin/ar` is the system
archive tool. The wrapper detects `agentrun` first and only uses `ar` when it is
actually AgentRun CLI.

The AgentRun CLI injects default `cpu`, `memory`, `port`, and a `default`
endpoint when they are omitted. This template keeps to the official minimal
schema so `agentrun rt render` remains the source of truth for generated fields.

## ACR image push

ACR Personal Edition is the default path for this deployment. Use an image like:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<personal-namespace>/ai4ss-skills-codex-harness:<tag>"
```

Prepare the Personal Edition registry in the Alibaba Cloud console:

1. Open Container Registry ACR and enter the Personal Edition instance in
   `cn-hangzhou`.
2. Set the Registry login password if it has not been set.
3. Create a namespace, for example `ai4ss-skills`.
4. Create a private repository named `ai4ss-skills-codex-harness`.
5. Use the namespace and repository in `AGENTRUN_IMAGE`.

Then log in and push without putting the password in shell history:

```bash
export ACR_USERNAME="<registry-login-name>"
export ACR_PASSWORD="<registry-login-password>"
deploy/agentrun/scripts/deploy.sh registry-preflight --mode local-push
deploy/agentrun/scripts/deploy.sh acr-login
deploy/agentrun/scripts/deploy.sh build
deploy/agentrun/scripts/deploy.sh push
```

For AgentRun/FC cloud-side pulls, ACR Personal private repositories must be
rendered as `container.imageRegistryType: CUSTOM` with
`container.registryConfig.auth`. Plain `imageRegistryType: ACR` uses the
cloud-side RAM/service-role ACR path and was observed to fail against ACR
Personal private images with `AUTHENTICATION_FAILED` / `user jurisdiction
error`.

Current verified ACR Personal path for this repo:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859"
```

The registry login password is stored in the local macOS Keychain under service
`aliyun-acr-personal-cn-hangzhou`, account `15201208603`; do not print it.
`render_runtime.mjs` can read that password from Keychain when
`ACR_USERNAME=15201208603` is set, so `ACR_PASSWORD` does not need to live in a
local env file.
`docker push` completed for the current verified image
`registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859`
with manifest digest:

```text
sha256:005bba8b4b3c90b61f6b1289faf15529343306e4a52d3163b228a75b83adda00
```

Check registry prerequisites before building or invoking AgentRun cloud-build:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
deploy/agentrun/scripts/deploy.sh registry-preflight --mode local-push
```

`deploy.sh all` runs the local-push preflight automatically. `deploy.sh
cloud-build` runs the cloud-build preflight automatically. The check is
read-only: it does not create ACR instances, namespaces, repositories, or push
images.

Use `--mode cloud-build --strict` only if you want AgentRun's docker-image-
builder to build remotely; for ACR Personal Edition that requires
`DOCKER_IMAGE_BUILDER_USERNAME` and `DOCKER_IMAGE_BUILDER_PASSWORD` because the
builder still needs target registry push credentials.

If an ACR instance already exists, bootstrap the namespace/repository:

```bash
export ACR_INSTANCE_ID="cri-..."
deploy/agentrun/scripts/deploy.sh acr-bootstrap
deploy/agentrun/scripts/deploy.sh acr-bootstrap --yes
```

This helper is only for ACR Enterprise instances because the current
`aliyun cr create-namespace/create-repository` APIs require `--instance-id`.
The first command is a read-only check. The `--yes` form creates only the
missing namespace/repository inside that existing instance; it never creates an
ACR Personal or Enterprise instance.

For ACR Enterprise Edition, use an instance id and let the helper request the
official one-hour temporary login token:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
export ACR_INSTANCE_ID="cri-..."
node deploy/agentrun/scripts/acr_login.mjs --image "$AGENTRUN_IMAGE"
deploy/agentrun/scripts/deploy.sh build
deploy/agentrun/scripts/deploy.sh push
```

For ACR Personal Edition or an existing manually managed registry credential,
set the username/password through environment variables and do not write them
into commands:

```bash
export ACR_USERNAME="<registry-login-name>"
export ACR_PASSWORD="<registry-login-password>"
node deploy/agentrun/scripts/acr_login.mjs --image "$AGENTRUN_IMAGE"
```

If Docker is already authenticated, skip the login step:

```bash
SKIP_ACR_LOGIN=1 deploy/agentrun/scripts/deploy.sh all
```

Current local discovery: the Aliyun `chrome-aliyun` profile authenticates to
AgentRun in `cn-hangzhou` as account `1650944971821642`. The older `default`
profile authenticates as a different account and must not be used for this
deployment unless the registry/runtime ownership is moved.

First AgentRun apply may fail until the account's one-time AgentRun/FunctionAI
role authorization is completed. The console path is
<https://functionai.console.aliyun.com/cn-hangzhou/agent/>. Keep only the
FunctionAI/FC runtime roles selected unless the deployment actually needs
Flow/RDS/OSS helpers. The observed missing role was
`AliyunServiceRoleForAgentRun`.

AgentRun cloud-build builds and pushes to `spec.container.image`. The builder
receives Aliyun UID/AK/SK from the AgentRun profile, but target registry
username/password must come from `DOCKER_IMAGE_BUILDER_USERNAME` and
`DOCKER_IMAGE_BUILDER_PASSWORD`, or from literal `cloudBuild.registry` values
in a private runtime-build YAML. The committed template intentionally does not
store registry passwords.

The runtime templates default to `imageRegistryType: CUSTOM` with
`registryConfig.auth` placeholders because this deployment uses an ACR Personal
private repository. For ACR Enterprise, switch to the enterprise-supported path,
set `imageRegistryType`/`acrInstanceId` according to the current AgentRun docs,
and retest with `agentrun rt render`.

## Workspace and Session Persistence

The image is usable without a cloud filesystem: it ships an ai4ss-skills
workspace snapshot and seeds `/workspace` on startup if the directory is empty.
This makes first boot deterministic, but edits made inside the container are
ephemeral unless backed by a mount.

For persistent Codex sessions, use `runtime-nas.example.yaml` and mount NAS at
`/mnt/ai4ss-codex`; it sets `CODEX_SESSION_HOME_ROOT` to that mount.

For persistent workspace edits, also mount NAS at `/workspace`. The entrypoint
will seed an empty mounted workspace from the image snapshot and will not
overwrite it once `AGENTS.md` or `skills/` exists.

## Secrets

Do not commit secrets into this directory.

Runtime secrets should come from one of these mechanisms:

- Runtime environment variables injected at deploy time. Function Compute stores
  environment variables encrypted at rest and injects them during instance
  initialization.
- KMS or another runtime secret fetcher wired through `executionRoleArn`.
- AgentRun ModelService/model proxy credentials if the model path is moved out
  of this container.
- Alibaba Cloud / AgentRun local profile for deploy-time credentials.
- AgentRun credential management for inbound endpoint authentication.

`runtime.yaml` keeps secret values out of source. `deploy.sh apply` renders a
temporary YAML and injects `CODEX_GATEWAY_BEARER_TOKEN` plus `DEEPSEEK_API_KEY`
from the local environment by default. It also renders ACR Personal pull auth
from `ACR_USERNAME` plus either `ACR_PASSWORD` or the local macOS Keychain:

```bash
export ACR_USERNAME="15201208603"
export CODEX_GATEWAY_BEARER_TOKEN="<runtime-token>"
export DEEPSEEK_API_KEY="<runtime-deepseek-key>"
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh apply
```

The temp file is removed after `apply`. Do not run `agentrun rt render` against
that temporary file or commit exported YAML that includes secret env values.
Also avoid unfiltered `agentrun rt export` and
`aliyun agentrun list-agent-runtimes`; both can return runtime environment
variables. Use `agentrun rt status` or `--cli-query` filters for routine
diagnostics.

AgentRun marks an AgentRuntime without `credentialName` as anonymously
accessible at the platform level. Keep the gateway bearer token enabled anyway,
but production should also bind an AgentRun credential through the console path
`函数计算控制台 -> AgentRun -> Agent 运行时 -> 配置 -> 凭证 / 访问控制`.

The same inbound credential can be created with the Aliyun AgentRun CLI plugin:

```bash
deploy/agentrun/scripts/deploy.sh bootstrap-secrets
deploy/agentrun/scripts/deploy.sh credential-dry-run
deploy/agentrun/scripts/deploy.sh credential-create
```

Then uncomment/set:

```yaml
spec:
  credentialName: ai4ss-codex-harness-inbound
```

The gateway requires one of:

- `CODEX_GATEWAY_BEARER_TOKEN` set to a high-entropy token.
- `ALLOW_UNAUTHENTICATED=true` for local-only experiments.

The DeepSeek backend requires `DEEPSEEK_API_KEY` at runtime. For a fully
verified Codex model turn, the configured provider base URL must expose the
Responses API expected by Codex.

Each gateway session gets its own `CODEX_HOME` under
`CODEX_SESSION_HOME_ROOT`. The entrypoint writes the base managed Codex config
once, and the gateway copies it into each per-session home before spawning
`codex app-server`. This avoids concurrent child processes mutating the same
Codex state directory.

Production should not use unauthenticated mode.

## Required cloud validation

Before the deployment can be called complete, collect evidence for:

- `ar rt render` and `ar rt apply` success.
- Runtime reaches `READY`.
- Gateway `/readyz` is healthy through the AgentRun endpoint.
- App-server stdio smoke passes through the gateway.
- SSE stream preserves Codex notifications.
- Session idle cleanup works.
- Workspace persistence behavior is understood and documented.
- Secrets are injected without appearing in image layers, source, exported YAML,
  or logs.
- DeepSeek credential smoke passes, and a Codex turn is verified through the
  configured DeepSeek/adapter backend.
- Logs include session ids and do not expose private prompts or tokens.
- Cost and rollback commands are documented with observed values.

Once `GATEWAY_URL` is known:

```bash
set -a
source deploy/agentrun/.generated/secrets.env
set +a
export GATEWAY_URL="$(node deploy/agentrun/scripts/agentrun_gateway_url.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  --account-id 1650944971821642 \
  --runtime ai4ss-skills-codex-harness \
  --endpoint default)"
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh verify
```

Cloud smoke sends two auth layers when available:

- `X-API-Key: $AGENTRUN_RUNTIME_API_KEY` for the AgentRun platform credential.
- `Authorization: Bearer $CODEX_GATEWAY_BEARER_TOKEN` for the gateway itself.
- `X-AgentRun-Session-Id`-equivalent affinity via
  `x-agentrun-session-id` by default, generated once per smoke run. This header
  must be stable across `/sessions`, `/events`, and `/request` calls because
  the runtime uses `HEADER_FIELD` session affinity.

Both local values are generated by `deploy.sh bootstrap-secrets`.
