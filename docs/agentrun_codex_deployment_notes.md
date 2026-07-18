# AgentRun deployment notes for Codex app-server

Last researched: 2026-07-06.

This note records the AgentRun documentation, deployment path, and CLI commands
needed for a Codex app-server hosting spike on Alibaba Cloud.

## Working conclusion

AgentRun is the Alibaba Cloud managed runtime line that best matches the
"managed agent runtime in the cloud" requirement. For our custom Codex
app-server, the most relevant path is AgentRun high-code / Agent Runtime with a
custom container image, managed with the AgentRun CLI (`ar`).

Use this split:

- `ar` / `agentrun`: primary control plane for AgentRun resources, especially
  `AgentRuntime` YAML, cloud build, runtime status, export, and delete.
- `s`: Serverless Devs path for official quick-start templates.
- `aliyun`: generic Alibaba Cloud CLI for credentials, supporting cloud
  resources, raw OpenAPI discovery, AgentRun credential APIs, and other Alibaba
  Cloud products. Do not assume `aliyun` replaces `ar` for Runtime YAML
  deployment; current AgentRun docs make `ar` the targeted declarative CLI.

For Codex specifically, do not expose `codex app-server` directly on the public
internet. Codex's app-server protocol supports `stdio`, WebSocket, Unix socket,
and `off`; OpenAI's docs mark WebSocket transport as experimental and
unsupported, and warn against direct public exposure. The safer shape is:

```text
external HTTPS/API auth
  -> our small gateway
  -> per-session local codex app-server over stdio or Unix socket
  -> model/tool/workspace backends
```

The model backend decision for this deployment is DeepSeek. The container writes
a managed Codex config with `model_provider = "deepseek"` and default model
`deepseek-v4-flash`; use `CODEX_MODEL=deepseek-v4-pro` for a higher-reasoning
runtime. Codex custom provider docs show `wire_api = "responses"`, while
DeepSeek's official OpenAI-compatible API is `/chat/completions`. Direct Codex
to DeepSeek was tested and failed on `https://api.deepseek.com/v1/responses`
with 404, so this deployment includes a loopback-only Responses-to-DeepSeek
adapter in `gateway/server.mjs`.

## Official documents map

AgentRun product and deployment:

- AgentRun overview:
  <https://help.aliyun.com/zh/functioncompute/what-is-agentrun>
- High-code Agent creation:
  <https://help.aliyun.com/zh/functioncompute/create-agent-by-code-high-code>
- AgentRun CLI official guide:
  <https://help.aliyun.com/zh/functioncompute/use-the-agentrun-cli-to-manage-agentrun-in-terminals-and-ci-pipelines>
- AgentRun CLI repository and manual:
  <https://github.com/Serverless-Devs/agentrun-cli>
- AgentRun HTTP data-link access:
  <https://help.aliyun.com/zh/functioncompute/access-agenrun-http-api>
- AgentRun custom domains:
  <https://help.aliyun.com/zh/functioncompute/custom-domains-agentrun>
- AgentRun PrivateLink / intranet access:
  <https://help.aliyun.com/zh/functioncompute/fc/access-agenrun-resources-through-privatelink-intranet>
- AgentRun service endpoints:
  <https://help.aliyun.com/zh/functioncompute/fc/developer-reference/api-agentrun-2025-09-10-endpoint>
- AgentRun OpenAPI product page:
  <https://api.aliyun.com/product/AgentRun>
- RAM authorization for AgentRun:
  <https://help.aliyun.com/zh/functioncompute/fc/authorize-ram-users-to-use-agentrun>

Alibaba Cloud CLI and Serverless Devs:

- Alibaba Cloud CLI credential configuration:
  <https://help.aliyun.com/zh/cli/configure-credentials/>
- Alibaba Cloud CLI command structure:
  <https://help.aliyun.com/zh/cli/understanding-command-structure>
- Alibaba Cloud CLI command-line options:
  <https://help.aliyun.com/zh/cli/command-line-options>
- Alibaba Cloud CLI plugin management:
  <https://help.aliyun.com/zh/cli/managing-and-using-cli-plugins>
- Alibaba Cloud CLI help:
  <https://help.aliyun.com/zh/cli/use-the-help-command>
- Alibaba Cloud CLI supported products:
  <https://help.aliyun.com/zh/cli/cloud-products-supporting-cli>
- Serverless Devs install:
  <https://help.aliyun.com/zh/functioncompute/fc/developer-reference/install-serverless-devs-and-docker>
- Serverless Devs commands:
  <https://help.aliyun.com/zh/functioncompute/serverless-devs-commands>
- Function Compute environment variables:
  <https://help.aliyun.com/zh/functioncompute/fc/user-guide/environment-variables>
- Function AI encrypted shared/service variables:
  <https://help.aliyun.com/zh/functioncompute/management-variables>

Codex:

- Codex app-server:
  <https://developers.openai.com/codex/app-server>
- Codex remote connections:
  <https://developers.openai.com/codex/remote-connections>
- Codex custom model providers:
  <https://developers.openai.com/codex/config-advanced>
- Codex config reference:
  <https://developers.openai.com/codex/config-reference>
- Alibaba Cloud Model Studio Codex:
  <https://help.aliyun.com/zh/model-studio/codex>

DeepSeek:

- DeepSeek API docs:
  <https://api-docs.deepseek.com/>
- DeepSeek chat completions:
  <https://api-docs.deepseek.com/api/create-chat-completion>
- DeepSeek tool calls:
  <https://api-docs.deepseek.com/guides/tool_calls>
- DeepSeek thinking mode tool calls:
  <https://api-docs.deepseek.com/guides/thinking_mode>

Protocol bridge references:

- CC Switch Codex DeepSeek routing guide:
  <https://github.com/farion1231/cc-switch/blob/main/docs/guides/codex-deepseek-routing-guide-en.md>
- Moon Bridge:
  <https://github.com/ZhiYi-R/moon-bridge>

## Codex Responses to DeepSeek Chat bridge notes

The external bridge tutorials point to the same shape we now use: Codex keeps
`wire_api = "responses"` and talks to a local/loopback route; the route rewrites
`/v1/responses` requests into upstream `/chat/completions`, then converts Chat
JSON/SSE back into Responses JSON/SSE. Writing DeepSeek's Chat base URL directly
into Codex is not sufficient because request bodies, stream event names, tool
calls, and response item shapes differ.

DeepSeek official tool-call docs use Chat Completions `tools` plus assistant
`message.tool_calls`, followed by application-side execution and a `role:"tool"`
message with the matching `tool_call_id`. Strict tool mode is beta-only and
requires `base_url="https://api.deepseek.com/beta"` plus stricter JSON schema
rules, so the gateway intentionally strips `strict` from forwarded tool
definitions unless `DEEPSEEK_TOOL_STRICT=true` is set.

The gateway now handles:

- Responses function tools and namespace-wrapped function tools, flattened into
  DeepSeek Chat function tools with a reversible name map.
- DeepSeek streamed `delta.tool_calls` converted back into
  `response.output_item.added`,
  `response.function_call_arguments.delta`,
  `response.function_call_arguments.done`, and
  `response.output_item.done` events.
- Function-call output items from follow-up Responses requests converted into
  Chat `role:"tool"` messages.

The gateway does not yet claim full DeepSeek thinking-mode tool support. If we
enable `DEEPSEEK_THINKING=enabled`, follow-up requests must preserve
DeepSeek-specific `reasoning_content` for turns that include tool calls, or
DeepSeek can reject later requests. Keep production at
`DEEPSEEK_THINKING=disabled` until that replay path is implemented.

For cloud MCP servers, prefer Codex's native Streamable HTTP MCP configuration
over a stdio proxy. Current Codex MCP docs support `[mcp_servers.<name>]` with
`url`, `bearer_token_env_var`, `startup_timeout_sec`, and `tool_timeout_sec`.
The AgentRun entrypoint therefore configures `aliyun-websearch` and `x-docs`
as native HTTP MCP servers, not via `mcp-remote`. This avoids stdio proxy
startup timeouts and prevents proxy logs from printing authorization headers.

## Product model

AgentRun exposes several resource types:

- Agent Runtime: managed runtime for custom agent code. This is the key
  candidate for hosting our Codex app-server gateway.
- Sandbox: managed isolated execution environment, including code interpreter
  and browser-use style workloads.
- Model service / model proxy: managed model access path.
- Tool, skill, Super Agent: higher-level AgentRun abstractions.
- MCP and function-call protocols: AgentRun can bridge tool integration patterns,
  but this is not a replacement for our Codex app-server protocol.

AgentRun Runtime is built on Function Compute's serverless substrate. Relevant
capabilities from the docs include scale-to-zero, session affinity, idle timeout,
runtime configuration, environment variables, credentials, VPC, execution role,
health checks, logs, metrics, and OpenAI-compatible invocation paths.

Supported public regions listed for AgentRun service endpoints:

- `cn-beijing`
- `cn-hangzhou`
- `cn-shanghai`
- `cn-shenzhen`
- `ap-southeast-1`

Start with `cn-hangzhou` unless ACR, OSS, NAS, or network placement forces a
different region.

## Recommended Codex app-server spike

1. Build a container image for `codex-appserver`.

   Include Node.js, the Codex CLI/app-server binary, `git`, `rg`, Python, and
   any project-specific runtime dependencies. Do not bake secrets into the image.

2. Implement a small HTTP gateway as the container entrypoint.

   The gateway should expose authenticated HTTPS-friendly routes and start
   `codex app-server` per session over `stdio` or a Unix socket. Avoid exposing
   `codex app-server --listen ws://0.0.0.0:...` directly.

3. Push the image to Alibaba Cloud Container Registry.

   Example image name:

   ```text
   registry.cn-hangzhou.aliyuncs.com/<namespace>/codex-appserver:<tag>
   ```

4. Deploy it as an AgentRun `AgentRuntime` using `ar rt apply`.

5. Invoke through AgentRun's runtime endpoint or a custom domain.

   The data-link docs show the general OpenAI-compatible path:

   ```text
   https://<uid>.agentrun-data.<region>.aliyuncs.com/agent-runtimes/<runtime-name>/endpoints/<endpoint-name>/invocations/openai/v1/chat/completions
   ```

   For our gateway, the final route depends on the HTTP routes implemented by
   the gateway. The docs explicitly say the path after `invocations/` depends on
   the Agent Server implementation.

6. Verify operational behavior.

   Required spike checks:

   - Can a runtime instance keep a per-session child `codex app-server` process?
   - Does streaming survive AgentRun's data-link / custom-domain layer?
   - What are the practical idle-timeout and concurrent-session limits?
   - Where do workspace files live, and what persists across session affinity,
     instance recycle, and scale-to-zero?
   - Can we attach OSS/NAS or another workspace store cleanly?
   - How are credentials injected without writing secrets into source, image
     layers, logs, exported YAML, or command history?

## Prerequisites

Alibaba Cloud resources:

- Alibaba Cloud account and selected region.
- RAM user or role with `AliyunAgentRunFullAccess`.
- If using Super Agent commands, the service role
  `AliyunAgentRunSuperAgentRole`.
- ACR namespace/repository for the custom image.
- Optional OSS/NAS for workspace persistence.
- Optional VPC / PrivateLink if traffic must stay private.
- Optional ICP-ready domain and certificate if using custom domain in China.

Local tools:

- AgentRun CLI: `ar` or `agentrun`.
- Alibaba Cloud CLI: `aliyun`.
- Serverless Devs: `s`, only for template-based deployments or FC workflows.
- Docker or equivalent image build tooling if not using AgentRun cloud build.

Credential rule: use environment variables, local profiles, or AgentRun
credential management. Never commit AccessKey ID/secret, exported secret fields,
or real API keys.

## AgentRun CLI commands

Install:

```bash
curl -fsSL https://raw.githubusercontent.com/Serverless-Devs/agentrun-cli/main/scripts/install.sh | sh
ar --version
agentrun --version
```

Alternative install:

```bash
pip install agentrun-cli
```

Configure default profile:

```bash
ar config set access_key_id <ACCESS_KEY_ID>
ar config set access_key_secret <ACCESS_KEY_SECRET>
ar config set account_id <ALIYUN_ACCOUNT_ID>
ar config set region cn-hangzhou
ar config list
```

Configure a named profile:

```bash
ar config set access_key_id <ACCESS_KEY_ID> --profile staging
ar config set access_key_secret <ACCESS_KEY_SECRET> --profile staging
ar config set account_id <ALIYUN_ACCOUNT_ID> --profile staging
ar config set region cn-shanghai --profile staging
ar --profile staging rt list
```

Environment variables recognized by the CLI include:

```bash
export AGENTRUN_ACCESS_KEY_ID=<ACCESS_KEY_ID>
export AGENTRUN_ACCESS_KEY_SECRET=<ACCESS_KEY_SECRET>
export AGENTRUN_ACCOUNT_ID=<ALIYUN_ACCOUNT_ID>
export AGENTRUN_REGION=cn-hangzhou
```

The AgentRun CLI manual also documents aliases from Alibaba Cloud and FC env
names such as `ALIBABA_CLOUD_ACCESS_KEY_ID`,
`ALIBABA_CLOUD_ACCESS_KEY_SECRET`, `FC_ACCOUNT_ID`, and `FC_REGION`.

Current local state on 2026-07-06:

- `agentrun --version` and `ar --version` both report `agentrun-cli, version
  0.1.1`.
- The existing Aliyun `default` profile is an AK profile. `aliyun sts
  GetCallerIdentity --profile default --region cn-hangzhou` succeeds and
  returns account `1355772881925444`.
- `agentrun rt list` succeeds when run through
  `deploy/agentrun/scripts/with_aliyun_profile_env.mjs --profile default
  --region cn-hangzhou -- ...` and currently returns `[]`.
- `~/.agentrun/config.json` is absent, so use the helper or explicitly configure
  AgentRun CLI before deployment.

Safe AgentRun env wrapper:

```bash
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile default \
  --region cn-hangzhou \
  -- agentrun rt list
```

Runtime YAML from an existing image:

```yaml
apiVersion: agentrun/v1
kind: AgentRuntime
metadata:
  name: codex-appserver
spec:
  cpu: 2
  memory: 4096
  port: 9000
  enableSessionIsolation: true
  sessionIdleTimeoutSeconds: 900
  # credentialName: ai4ss-codex-harness-secrets
  protocol:
    type: HTTP
  healthCheck:
    httpGetUrl: /readyz
  env:
    CODEX_MODEL_PROVIDER: deepseek
    CODEX_MODEL: deepseek-v4-flash
    DEEPSEEK_BASE_URL: https://api.deepseek.com
    CODEX_DEEPSEEK_RESPONSES_BASE_URL: http://127.0.0.1:9000/internal/deepseek/v1
    DEEPSEEK_API_KEY_ENV: DEEPSEEK_API_KEY
    CODEX_PROVIDER_WIRE_API: responses
    DEEPSEEK_RESPONSES_ADAPTER: "true"
    DEEPSEEK_THINKING: disabled
    CODEX_SESSION_HOME_ROOT: /home/codex/.codex-sessions
  container:
    image: registry.cn-hangzhou.aliyuncs.com/<namespace>/codex-appserver:<tag>
```

`spec.credentialName` is an AgentRun inbound access credential for protecting
the platform endpoint. It is not the same thing as injecting arbitrary
application environment secrets into the container.

The container still needs `CODEX_GATEWAY_BEARER_TOKEN` and `DEEPSEEK_API_KEY`.
Current deployment scripts keep source YAML secret-free and inject those values
from local environment variables into a temporary YAML only for `apply`. For a
harder production posture, replace that with KMS fetch at startup or route model
traffic through an AgentRun ModelService/model proxy credential.

Workspace and persistence:

- The Docker image now carries an ai4ss-skills workspace snapshot at
  `/opt/ai4ss-codex-harness/workspace-snapshot`.
- `entrypoint.sh` seeds `CODEX_WORKSPACE_DIR` only when the target workspace is
  empty, so a fresh container has `/workspace` populated even without a mount.
- `runtime-nas.example.yaml` mounts NAS at `/mnt/ai4ss-codex` and persists
  `CODEX_SESSION_HOME_ROOT` there.
- To persist mutable workspace edits, mount NAS at `/workspace`; the same
  seed-on-empty logic initializes the mounted directory once and then leaves it
  alone.

Image registry gate:

```bash
export AGENTRUN_IMAGE=registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>
deploy/agentrun/scripts/deploy.sh registry-preflight --mode local-push
```

For Adrian's deployment, use ACR Personal Edition rather than Enterprise:

1. In the ACR console, open/create the Personal Edition instance in
   `cn-hangzhou`.
2. Set the Registry login password.
3. Create a namespace, for example `ai4ss-skills`.
4. Create a private repository named `ai4ss-skills-codex-harness`.
5. Export `ACR_USERNAME`; either export `ACR_PASSWORD` or store it in macOS
   Keychain under service `aliyun-acr-personal-cn-hangzhou`, then run:

```bash
deploy/agentrun/scripts/deploy.sh acr-login
deploy/agentrun/scripts/deploy.sh build
deploy/agentrun/scripts/deploy.sh push
```

For AgentRun/FC cloud-side pulls from an ACR Personal private repository, render
the runtime as `container.imageRegistryType: CUSTOM` with
`container.registryConfig.auth`. The AgentRun YAML field is `auth`; the OpenAPI
field produced by `agentrun rt render` is `authConfig`. The plain
`imageRegistryType: ACR` path was observed to fail with
`AUTHENTICATION_FAILED` / `user jurisdiction error` even after RAM/service-role
authorization was present.

Verified ACR Personal state on 2026-07-06:

- Region: `cn-hangzhou`.
- Namespace: `ai4ss-skills`.
- Repository: `ai4ss-skills-codex-harness`.
- Image:
  `registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859`.
- Manifest digest:
  `sha256:005bba8b4b3c90b61f6b1289faf15529343306e4a52d3163b228a75b83adda00`.

BuildKit's default export can produce OCI index / attestation metadata that is
not a good fit for this ACR Personal push path. Use the deploy wrapper defaults
or the equivalent explicit build:

```bash
docker build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f deploy/agentrun/Dockerfile \
  -t "$AGENTRUN_IMAGE" \
  .
```

If an ACR instance exists, namespace/repository bootstrap can be done through
the current `aliyun cr` plugin:

```bash
export ACR_INSTANCE_ID=cri-...
deploy/agentrun/scripts/deploy.sh acr-bootstrap
deploy/agentrun/scripts/deploy.sh acr-bootstrap --yes
```

The underlying CLI calls are `aliyun cr create-namespace --instance-id ...` and
`aliyun cr create-repository --instance-id ...`; both require an existing
Enterprise instance id. They do not apply to ACR Personal Edition and do not
create the ACR Personal/Enterprise instance itself.

AgentRun `cloud-build` invokes docker-image-builder against
`spec.container.image`. The builder receives the active AgentRun profile's
Aliyun UID/AK/SK, but target registry username/password are separate: provide
`DOCKER_IMAGE_BUILDER_USERNAME` and `DOCKER_IMAGE_BUILDER_PASSWORD`, or keep a
private runtime-build YAML with literal `cloudBuild.registry` credentials. The
committed `runtime-build.yaml` remains secret-free.

Deploy and check status:

```bash
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

Use explicit profile/output for CI:

```bash
ar --profile prod --output json rt apply -f deploy/agentrun/runtime.yaml
ar --profile prod --output json rt status codex-appserver --wait
ar --profile prod --output quiet rt get codex-appserver
```

Important syntax rule from the docs: global flags go before the command group:

```bash
ar --profile staging rt list
```

Do not write:

```bash
ar rt list --profile staging
```

Export and delete:

```bash
ar rt export codex-appserver -f deploy/agentrun/runtime.exported.yaml
ar rt delete codex-appserver --yes
```

Do not commit exported YAML until it has been checked for sensitive fields. Avoid
`--include-secrets` unless there is a controlled, temporary reason.

Cloud build YAML:

```yaml
apiVersion: agentrun/v1
kind: AgentRuntime
metadata:
  name: codex-appserver
spec:
  container:
    image: registry.cn-hangzhou.aliyuncs.com/<namespace>/codex-appserver:<tag>
    cloudBuild:
      dir: .
      setupScript: scripts/setup-agentrun-image.sh
      baseContainerConfig:
        image: serverless-registry.cn-hangzhou.cr.aliyuncs.com/functionai/docker-image-builder-worker:20260514-111141-2d80effe
```

Build and deploy:

```bash
ar rt apply -f deploy/agentrun/runtime-build.yaml
```

Build only:

```bash
ar rt cloud-build -f deploy/agentrun/runtime-build.yaml
```

Super Agent quick checks:

```bash
ar sa run --prompt "You are a deployment smoke-test assistant."
ar sa chat <super-agent-name>
ar sa invoke <super-agent-name> -m "Return OK only." --text-only
ar sa apply -f deploy/agentrun/superagent.yaml
ar sa render -f deploy/agentrun/superagent.yaml
ar sa delete <super-agent-name>
```

Runtime invocation shape:

```bash
curl "https://<uid>.agentrun-data.cn-hangzhou.aliyuncs.com/agent-runtimes/codex-appserver/endpoints/default/invocations/openai/v1/chat/completions" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <AGENTRUN_RUNTIME_API_KEY>" \
  -d '{
    "messages": [{"role": "user", "content": "Return OK only."}],
    "stream": true
  }'
```

For RAM-signed data-link access, AgentRun uses its own
`Agentrun-Authorization` header and `AGENTRUN4-HMAC-SHA256` signature scheme.
Do not assume the standard `Authorization` header or normal ACS3 body hashing is
accepted for this data-link path.

Exit codes to handle in CI:

- `0`: success.
- `1`: resource not found or failed state.
- `2`: argument error.
- `3`: authentication or permission error.
- `4`: server error or timeout.
- `5`: runtime or endpoint create/update/delete failed.
- `6`: polling exceeded timeout.
- `130`: interrupted.

## Serverless Devs path

Use this for Alibaba's AgentRun quick-start templates, not as the primary path
for a custom Codex app-server runtime unless the template shape fits.

Install:

```bash
npm install -g @serverless-devs/s
s --version
```

Initialize an AgentRun LangChain quick start:

```bash
s init agentrun-quick-start-langchain
cd agentrun-quick-start-langchain
uv venv
uv pip install -r requirements.txt
```

Set AgentRun environment variables:

```bash
export AGENTRUN_ACCESS_KEY_ID=<ACCESS_KEY_ID>
export AGENTRUN_ACCESS_KEY_SECRET=<ACCESS_KEY_SECRET>
export AGENTRUN_ACCOUNT_ID=<ALIYUN_ACCOUNT_ID>
export AGENTRUN_REGION=cn-hangzhou
```

Configure and deploy:

```bash
s config add
s deploy -a agentrun-deploy
```

Common Serverless Devs commands:

```bash
s init
s build
s deploy
s deploy -t s.yaml
s local invoke
s local start
```

## Alibaba Cloud CLI commands

The generic Alibaba Cloud CLI is still needed for account-level setup, profile
management, other Alibaba Cloud resources, and raw OpenAPI discovery.

Interactive profile setup:

```bash
aliyun configure --mode AK --profile agentrun
```

Non-interactive profile setup:

```bash
aliyun configure set \
  --profile agentrun \
  --mode AK \
  --access-key-id <ACCESS_KEY_ID> \
  --access-key-secret <ACCESS_KEY_SECRET> \
  --region cn-hangzhou
```

Inspect and switch profiles:

```bash
aliyun configure list
aliyun configure get --profile agentrun region
aliyun configure switch --profile agentrun
aliyun configure set --profile agentrun --region cn-hangzhou
```

One-shot profile use:

```bash
aliyun ecs describe-regions --profile agentrun
```

CLI profile priority from the docs:

1. `--profile` command-line argument.
2. `ALIBABA_CLOUD_PROFILE` environment variable.
3. Current active profile from `aliyun configure list`.

Enable plugin auto-install and update plugins:

```bash
aliyun configure set --auto-plugin-install true
export ALIBABA_CLOUD_CLI_PLUGIN_AUTO_INSTALL=true
aliyun plugin update
```

Help and product discovery:

```bash
aliyun --help
aliyun <product> --help
aliyun <product> <ApiName> --help
```

For AgentRun OpenAPI exploration, the OpenAPI product page identifies the
product as `AgentRun` and version `2025-09-10`. Use the CLI help / OpenAPI
portal to confirm exact parameters before scripting destructive calls:

```bash
aliyun AgentRun --help
aliyun AgentRun CreateAgentRuntime --help
aliyun AgentRun GetAgentRuntime --help
```

Service endpoint examples from the AgentRun endpoint document:

```text
cn-beijing:    agentrun.cn-beijing.aliyuncs.com
cn-hangzhou:   agentrun.cn-hangzhou.aliyuncs.com
cn-shanghai:   agentrun.cn-shanghai.aliyuncs.com
cn-shenzhen:   agentrun.cn-shenzhen.aliyuncs.com
ap-southeast-1: agentrun.ap-southeast-1.aliyuncs.com
```

VPC endpoints use the `agentrun-vpc.<region>.aliyuncs.com` shape.

Raw OpenAPI command template, only after confirming the CLI plugin parameters:

```bash
aliyun AgentRun <ApiName> \
  --profile agentrun \
  --region cn-hangzhou \
  --endpoint agentrun.cn-hangzhou.aliyuncs.com \
  <api-parameters>
```

For first deployment, prefer `ar rt apply` over raw `aliyun AgentRun
CreateAgentRuntime`, because `ar` handles AgentRun YAML defaults, endpoint
reconciliation, cloud build, status polling, output modes, and export.

First-use role authorization:

- Official AgentRun docs say the console checks for missing SLR permissions on
  first use and guides creation of roles including `AliyunServiceRoleForFC` and
  `AliyunServiceRoleForAgentRun`.
- The observed `deploy.sh apply` failure after image push was:
  `EntityNotExist.Role` for
  `acs:ram::1355772881925444:role/aliyunserviceroleforagentrun`.
- The FunctionAI/AgentRun console opened a "角色授权" modal at
  <https://functionai.console.aliyun.com/cn-hangzhou/agent/>.
- Before submitting, reduce optional items when possible. For this runtime
  deployment, RDS, OSS, and Flow/CloudFlow options were unchecked; the remaining
  visible items were FunctionAI/FC runtime roles and policies.
- Because the final button changes cloud-account permissions, click "一键授权"
  only after explicit user confirmation.

ACR discovery and login:

```bash
aliyun cr list-instance --profile default --region cn-hangzhou
aliyun cr get-authorization-token --instance-id <cri-...> --profile default --region cn-hangzhou
```

Current local state: `aliyun cr list-instance --profile default --region
cn-hangzhou` returns no ACR Enterprise instances. The new ACR OpenAPI requires
`--instance-id` for namespace/repository operations. If using ACR Enterprise,
create/select the instance first and use the helper:

```bash
export ACR_INSTANCE_ID="cri-..."
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
node deploy/agentrun/scripts/acr_login.mjs --image "$AGENTRUN_IMAGE"
```

If using ACR Personal Edition, the official docs require a registry login name
and independent registry login password from the ACR console. Keep those in
environment variables or macOS Keychain:

```bash
export ACR_USERNAME="<registry-login-name>"
export ACR_PASSWORD="<registry-login-password>"
node deploy/agentrun/scripts/acr_login.mjs --image "$AGENTRUN_IMAGE"
```

The local verified path stores the password in Keychain, so only
`ACR_USERNAME=15201208603` is required for `render_runtime.mjs` on this Mac.

AgentRun platform credentials:

- AgentRuntime has a `credentialName` field. Alibaba Cloud governance docs state
  that an AgentRuntime without `CredentialName` is anonymously accessible at the
  platform level.
- For production, bind an AgentRun credential through
  `函数计算控制台 -> AgentRun -> Agent 运行时 -> 配置 -> 凭证 / 访问控制`.
- Our gateway still requires `CODEX_GATEWAY_BEARER_TOKEN`; platform
  `credentialName` and gateway bearer auth are complementary.
- `aliyun-cli-agentrun` plugin version `0.5.0` is installed locally. It exposes
  `aliyun agentrun list-credentials`, `create-credential`,
  `update-credential`, `delete-credential`, and `get-access-token`.
- Before credential creation, `aliyun agentrun list-credentials --profile
  default --region cn-hangzhou` succeeded and returned an empty list.
- On 2026-07-06, `deploy/agentrun/scripts/deploy.sh credential-create` created
  AgentRun credential `ai4ss-codex-harness-inbound` using API-key auth and
  `X-API-Key` as the header. Re-running the command updates the same
  credential.
- Valid API-key credential creation shape:

  ```bash
  aliyun agentrun create-credential \
    --profile default \
    --region cn-hangzhou \
    --credential-name ai4ss-codex-harness-inbound \
    --credential-auth-type api_key \
    --credential-source-type internal \
    --credential-secret "$AGENTRUN_RUNTIME_API_KEY" \
    --credential-public-config 'headerKey=X-API-Key prefix=' \
    --enabled true
  ```

  Use `--cli-dry-run` first. Do not print or commit
  `AGENTRUN_RUNTIME_API_KEY`.

Cloud gateway smoke should include two auth layers:

```bash
export GATEWAY_URL="$(deploy/agentrun/scripts/deploy.sh gateway-url)"
deploy/agentrun/scripts/deploy.sh smoke
deploy/agentrun/scripts/deploy.sh stream-smoke
deploy/agentrun/scripts/deploy.sh turn-smoke
```

The smoke scripts add `X-API-Key: $AGENTRUN_RUNTIME_API_KEY` for AgentRun and
`Authorization: Bearer $CODEX_GATEWAY_BEARER_TOKEN` for the gateway.

## Codex-specific runtime shape

Container process model:

```text
PID 1: codex-appserver-gateway
  - handles auth, HTTP routing, request validation, tracing, and rate limits
  - starts one or more local codex app-server children
  - speaks JSON-RPC over stdio or Unix socket to each child
```

Recommended Codex child command:

```bash
codex app-server --listen stdio://
```

Alternative local-only control socket:

```bash
codex app-server --listen unix:///tmp/codex-appserver.sock
```

Do not use this as a public listener:

```bash
codex app-server --listen ws://0.0.0.0:4500
```

If WebSocket is used for an internal, controlled path, use Codex WebSocket auth
flags and keep it behind network controls:

```bash
codex app-server \
  --listen ws://127.0.0.1:4500 \
  --ws-auth capability-token \
  --ws-token-file /run/secrets/codex-ws-token
```

Generate protocol schema pinned to the installed Codex version:

```bash
codex app-server generate-ts --out ./schemas
codex app-server generate-json-schema --out ./schemas
```

## Verified AgentRun deployment on 2026-07-06

- Runtime account/profile: `chrome-aliyun`, account `1650944971821642`, region
  `cn-hangzhou`.
- Runtime name/id: `ai4ss-skills-codex-harness` /
  `74897c1f-3a5b-4bd6-b1aa-7ef6cf970f6d`.
- Runtime status: `READY`.
- Runtime version: `1`.
- Endpoint name/id: `default` / `62c40ce4-8bc4-442e-9058-9e454a5a82b9`.
- Endpoint status: `READY`.
- Data-link URL:
  `https://1650944971821642.agentrun-data.cn-hangzhou.aliyuncs.com/agent-runtimes/ai4ss-skills-codex-harness/endpoints/default/invocations`.
- `deploy/agentrun/scripts/deploy.sh verify` passed through
  `with_aliyun_profile_env.mjs --profile chrome-aliyun --region cn-hangzhou`.
- Verified through AgentRun: `/readyz`, session create/delete, initialize,
  `thread/start`, SSE event delivery, and a real Codex turn through the
  DeepSeek adapter returning `ok`.
- Current verified image:
  `registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859`.
- `deploy.sh render` redacts secret-shaped fields before printing AgentRun
  render output.
- Smoke clients must send a stable `x-agentrun-session-id` header from the
  first `/sessions` request onward; otherwise follow-up calls can route to a
  different instance and return `session not found`.
- Do not use unfiltered `agentrun rt export` or
  `aliyun agentrun list-agent-runtimes` in logs or docs because they can include
  runtime environment variables.

## Remaining production checks before committing to AgentRun

- Runtime lifecycle: whether a long-lived child process per user session is
  tolerated under scale-to-zero and idle-timeout behavior.
- Streaming: data-link SSE is verified; still verify custom domains if used.
- Endpoint routing: data-link runtime endpoint serves gateway routes directly;
  still verify any fronting custom-domain path.
- Custom domain target type: the custom-domain docs currently emphasize Agent
  route targets. Confirm whether our Runtime endpoint is supported or whether
  we need a fronting layer.
- Workspace persistence: exact OSS/NAS/ephemeral disk semantics for session
  files, Git worktrees, diffs, and artifacts.
- Secret injection: current runtime env injection works; KMS/model-proxy based
  production secret handling is still open.
- Image pull auth: verified for ACR Personal private image through
  `CUSTOM + registryConfig.auth`.
- Observability: confirm logs include enough Codex session/thread correlation
  while not printing prompts, private files, or secrets.
- Cost model: measure idle billing, concurrent sessions, scale-up latency, and
  sandbox usage cost before production.

## First concrete deployment checklist

1. Create a minimal gateway that can spawn `codex app-server --listen stdio://`
   and run a one-turn smoke test.
2. Build and push `registry.cn-hangzhou.aliyuncs.com/<namespace>/codex-appserver:<tag>`.
3. Install and configure `ar` with a least-privilege RAM user.
4. Create `deploy/agentrun/runtime.yaml`.
5. Run:

   ```bash
   ar rt render -f deploy/agentrun/runtime.yaml
   ar rt apply -f deploy/agentrun/runtime.yaml
   ar rt status codex-appserver --wait
   ```

6. Invoke the runtime endpoint with a non-secret smoke-test prompt.
7. Check logs, streaming, process lifecycle, workspace persistence, and cost.
8. Only after the spike works, add custom domain / PrivateLink / CI deployment.

## Repo deployment package

The ai4ss-skills harness deployment scaffold now lives under
`deploy/agentrun/`:

- `deploy/agentrun/Dockerfile`
- `deploy/agentrun/gateway/server.mjs`
- `deploy/agentrun/runtime.yaml`
- `deploy/agentrun/runtime-build.yaml`
- `deploy/agentrun/scripts/preflight.sh`
- `deploy/agentrun/scripts/deploy.sh`
- `deploy/agentrun/scripts/acr_login.mjs`
- `deploy/agentrun/scripts/agentrun_gateway_url.mjs`
- `deploy/agentrun/scripts/bootstrap_secrets.mjs`
- `deploy/agentrun/scripts/create_inbound_credential.mjs`
- `deploy/agentrun/scripts/render_runtime.mjs`
- `deploy/agentrun/scripts/with_aliyun_profile_env.mjs`
- `deploy/agentrun/scripts/smoke_appserver_stdio.mjs`
- `deploy/agentrun/scripts/smoke_gateway.mjs`

The current deployment status and verification matrix are recorded in
`docs/agentrun_ai4ss_harness_deployment_report.md`.
