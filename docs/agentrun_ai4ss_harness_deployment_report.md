# AgentRun ai4ss-skills harness deployment report

Last updated: 2026-07-06.

## Goal

Deploy and verify the full Codex ai4ss-skills harness on Alibaba Cloud AgentRun:
custom Codex app-server behind a secure gateway, production container image,
AgentRun Runtime YAML, secret injection, session/workspace persistence,
streaming, observability, automated deployment, smoke/regression harness, cost
notes, rollback, reusable documentation, and verification evidence.

## Current state

Completed in this repo:

- Researched AgentRun deployment docs and command surfaces in
  `docs/agentrun_codex_deployment_notes.md`.
- Added deployable scaffold under `deploy/agentrun/`.
- Added a no-dependency Node gateway around `codex app-server --listen
  stdio://`.
- Added container entrypoint that marks `CODEX_WORKSPACE_DIR` as a trusted
  Codex project so repo-local `.codex` config/hooks/policies can load in the
  mounted ai4ss-skills workspace.
- Added AgentRun `runtime.yaml` and `runtime-build.yaml` templates.
- Added Dockerfile based on the official Codex standalone installer.
- Added local preflight and smoke-test scripts.
- Set DeepSeek as the default backend target through managed Codex config:
  `CODEX_MODEL_PROVIDER=deepseek`, `CODEX_MODEL=deepseek-v4-flash`.
- Added loopback-only Responses-to-DeepSeek adapter at
  `/internal/deepseek/v1/responses`, because Codex custom providers use the
  Responses wire API while DeepSeek exposes `/chat/completions`.
- Added per-session `CODEX_HOME` directories under
  `/home/codex/.codex-sessions` to avoid concurrent app-server children
  mutating one shared Codex state directory.
- Added DeepSeek API smoke script for validating `DEEPSEEK_API_KEY` and
  `/chat/completions` separately from Codex app-server transport.
- Added `with_aliyun_profile_env.mjs` so AgentRun CLI commands can run from an
  existing Aliyun AK profile without copying AK/SK into commands or source.
- Added `acr_login.mjs` for ACR Enterprise temporary-token login and
  personal/manual registry login through environment variables.
- Added `bootstrap_secrets.mjs` and `deploy.sh bootstrap-secrets` for ignored,
  mode-0600 local deployment secret generation.
- Added `create_inbound_credential.mjs` to create or dry-run an AgentRun
  API-key credential for platform endpoint access without printing the key.
- Added `render_runtime.mjs` so `render` stays secret-free while `apply` can use
  a temporary runtime YAML with `CODEX_GATEWAY_BEARER_TOKEN` and
  `DEEPSEEK_API_KEY` injected from local environment variables.
- Added `agentrun_gateway_url.mjs` and `deploy.sh gateway-url` to derive the
  AgentRun data-link base URL for smoke tests.
- Updated gateway smoke scripts to send both gateway bearer auth and AgentRun
  `X-API-Key` platform auth when local generated secrets are available.

Local evidence collected:

- `codex --version`: `codex-cli 0.142.5`.
- `codex app-server --help` exposes `--listen stdio://`, `unix://`, `ws://`,
  `off`, schema generation, and WebSocket auth flags.
- `aliyun version`: `3.3.8`.
- Docker client: `29.6.0`.
- Node: `v26.3.1`.
- AgentRun CLI is installed at `/Users/siyaozheng/.local/bin/agentrun`; `ar` is
  now a symlink to the same binary.
- `agentrun --version`: `agentrun-cli, version 0.1.1`.
- `ar --version`: `agentrun-cli, version 0.1.1`.
- `node deploy/agentrun/scripts/smoke_appserver_stdio.mjs` succeeded and created
  thread `019f3557-8c70-74b0-9ef9-e94676f2025e`.
- Host gateway smoke on port `9017` succeeded and created thread
  `019f3557-caca-7fe0-9a91-9314f43f47b6`.
- Local image build succeeded:
  `ai4ss-skills-codex-harness:local`
  (`sha256:49c78766faa0e317d3961dd9ed57738cb99f8267bc5d72071e5faab16fdaad34`,
  size `224090650` bytes).
- Container gateway smoke on port `9019` succeeded and created thread
  `019f355b-3ac0-78b3-a0d6-d41d2a45a61b`.
- A first container smoke exposed two runtime issues: `/workspace` was not
  trusted by Codex and `bubblewrap` was missing. The Dockerfile/entrypoint were
  updated, the image was rebuilt, and the second container smoke no longer
  emitted those warnings.
- `AGENTRUN_IMAGE=registry.cn-hangzhou.aliyuncs.com/ai4ss-skills-test/ai4ss-skills-codex-harness:local-test deploy/agentrun/scripts/deploy.sh render`
  succeeded locally with AgentRun CLI render.
- Secret scan passed with `deploy/agentrun/scripts/check_no_secrets.sh`.
- Direct DeepSeek API smoke succeeded against `/chat/completions` with model
  `deepseek-v4-flash`.
- Direct Codex provider call to DeepSeek without adapter failed as expected:
  Codex attempted `/v1/responses` and DeepSeek returned 404.
- Host gateway adapter smoke succeeded against
  `http://127.0.0.1:9020/internal/deepseek/v1`, returning `ok`.
- Host gateway real turn smoke succeeded through Codex app-server and DeepSeek,
  returning `ok`.
- Container gateway smoke succeeded on `http://127.0.0.1:9021`.
- Container adapter smoke succeeded from inside the container against
  `http://127.0.0.1:9000/internal/deepseek/v1`, returning `ok`.
- Container real turn smoke succeeded through Codex app-server and DeepSeek,
  returning `ok`.
- `node --check` passed for all deployment `.mjs` scripts and the gateway.
- `bash -n` passed for all deployment shell scripts and `entrypoint.sh`.
- `deploy/agentrun/scripts/check_no_secrets.sh` passed.
- `render_runtime.mjs` passed a dummy secret-injection test without printing
  secret values, and fails closed when a required injected secret is missing.
- `deploy/agentrun/scripts/preflight.sh` completed with zero failures. Warnings
  are expected until a concrete ACR image replaces placeholders and AgentRun env
  is supplied through the helper.
- `node deploy/agentrun/scripts/smoke_deepseek_api.mjs` passed again on
  2026-07-06 with `deepseek-v4-flash`.
- `CODEX_MODEL=deepseek-v4-flash node
  deploy/agentrun/scripts/smoke_appserver_stdio.mjs` passed again and created
  thread `019f3586-fbd2-7332-b8ba-289ae4ce0ce6`.
- `node deploy/agentrun/scripts/with_aliyun_profile_env.mjs --profile default
  --region cn-hangzhou -- agentrun rt list` succeeded and returned `[]`.
- Installed Aliyun CLI AgentRun plugin `aliyun-cli-agentrun` `0.5.0`.
- `aliyun agentrun list-credentials --profile default --region cn-hangzhou`
  succeeded and returned an empty credentials list.
- `deploy/agentrun/scripts/deploy.sh bootstrap-secrets` created
  `deploy/agentrun/.generated/secrets.env` with mode `0600`, containing
  `CODEX_GATEWAY_BEARER_TOKEN` and `AGENTRUN_RUNTIME_API_KEY`; it does not
  contain `DEEPSEEK_API_KEY`.
- `create_inbound_credential.mjs --dry-run` validated the API-key inbound
  credential request shape with service-enforced values
  `credentialAuthType=api_key`, `credentialSourceType=internal`, and
  `headerKey=X-API-Key`.
- `deploy/agentrun/scripts/deploy.sh credential-create` created and then
  idempotently updated AgentRun credential `ai4ss-codex-harness-inbound`.
- `runtime.yaml` and `runtime-build.yaml` now bind
  `credentialName: ai4ss-codex-harness-inbound`.
- `agentrun rt render` output includes
  `"credentialName": "ai4ss-codex-harness-inbound"`.
- Runtime templates now set `container.imageRegistryType: CUSTOM` with
  `registryConfig.auth`; render output includes `"imageRegistryType": "CUSTOM"`
  and redacts `authConfig.password` before printing.
- Local gateway smoke on `http://127.0.0.1:9023` passed after adding optional
  `X-API-Key` platform-auth headers:
  - `smoke_gateway.mjs`: passed.
  - `smoke_gateway_stream.mjs`: passed.
  - `smoke_gateway_turn.mjs`: passed through DeepSeek and returned `ok`.
- Host-local smoke on `http://127.0.0.1:9025` passed when the gateway was
  started through `entrypoint.sh` with a temporary `CODEX_HOME`:
  `deepseek-adapter-smoke`, `smoke`, `stream-smoke`, and `turn-smoke` all
  returned `ok`.
- A direct `node deploy/agentrun/gateway/server.mjs` host-local start is not a
  valid full-turn smoke unless a DeepSeek Codex config already exists in
  `CODEX_HOME`; without entrypoint-managed config, Codex falls back to the
  default OpenAI provider and fails with OpenAI 401.
- Fixed cloud workspace initialization risk: the image now carries a workspace
  snapshot under `/opt/ai4ss-codex-harness/workspace-snapshot`, and
  `entrypoint.sh` seeds `CODEX_WORKSPACE_DIR` only when the target workspace is
  empty.
- `docker build -f deploy/agentrun/Dockerfile -t
  ai4ss-skills-codex-harness:workspace-test .` passed after adding the
  workspace snapshot. Build context was about 166 MB after `.dockerignore`.
- Container-level smoke without mounting the local repository passed on
  `http://127.0.0.1:9026`: `smoke`, `stream-smoke`, and `turn-smoke` returned
  `ok`; `docker exec` inside the container confirmed the loopback-only
  DeepSeek adapter returned `ok`.
- Added `runtime-nas.example.yaml` for NAS-backed persistence. The default
  example persists Codex session homes at `/mnt/ai4ss-codex/codex-sessions`;
  mounting NAS at `/workspace` persists mutable workspace edits and uses the
  same seed-on-empty behavior.
- `AGENTRUN_RUNTIME_TEMPLATE=deploy/agentrun/runtime-nas.example.yaml
  deploy.sh render` passed; AgentRun CLI rendered `nasConfig` with
  `mountDir=/mnt/ai4ss-codex`, `userId=1000`, and `groupId=1000`.
- `AGENTRUN_IMAGE=registry.cn-hangzhou.aliyuncs.com/ai4ss-skills-test/ai4ss-skills-codex-harness:local-test
  node deploy/agentrun/scripts/with_aliyun_profile_env.mjs --profile default
  --region cn-hangzhou -- deploy/agentrun/scripts/deploy.sh render` succeeded.
- `aliyun cr list-instance --profile default --region cn-hangzhou` succeeded
  and returned zero ACR Enterprise instances.
- `aliyun cr create-instance` is not a valid CLI command, and
  `get-instance-count` returns `0`.
- Attempts to use old/default-instance personal ACR API names such as
  `GetNamespaceList`, `CreateRepoNamespace`, `GetRepoNamespaceList`, and
  REST-style `/repos/namespaces` through the current CLI failed; current CLI
  exposes enterprise-style namespace/repository APIs requiring `InstanceId`.
- Local environment does not contain `ACR_USERNAME`, `ACR_PASSWORD`,
  `ACR_INSTANCE_ID`, `DOCKER_IMAGE_BUILDER_USERNAME`,
  `DOCKER_IMAGE_BUILDER_PASSWORD`, or `AGENTRUN_IMAGE`.
- `~/.docker/config.json` has no registry auth hosts, credential store, or
  credential helpers.
- Added `deploy/agentrun/scripts/registry_preflight.mjs` and wired it into
  `deploy.sh registry-preflight`, `deploy.sh cloud-build`, and `deploy.sh all`.
  The check is read-only and fails before image build/apply when no target
  registry auth path is available.
- Added `deploy/agentrun/scripts/acr_bootstrap.mjs` and wired it into
  `deploy.sh acr-bootstrap` for existing ACR instances. It checks namespace and
  repository by parsing `AGENTRUN_IMAGE`; only `--yes` creates missing
  namespace/repository, and it never creates an ACR instance.
- AgentRun CLI source confirms `cloud-build` targets `spec.container.image`;
  target registry auth comes from `cloudBuild.registry` or
  `DOCKER_IMAGE_BUILDER_USERNAME` / `DOCKER_IMAGE_BUILDER_PASSWORD`. It does not
  create ACR instances, namespaces, or repositories.
- Alibaba Cloud CLI 3.3.8 help confirms `aliyun cr create-namespace` and
  `aliyun cr create-repository` are available, but both require
  `--instance-id`.
- Adrian confirmed there is no ACR Enterprise Edition instance. The deployment
  path is therefore ACR Personal Edition: use `imageRegistryType: CUSTOM` plus
  `registryConfig.auth` for AgentRun/FC cloud-side pulls, and use
  `ACR_USERNAME` plus Keychain/`ACR_PASSWORD` or an existing `docker login` for
  local build/push.
- ACR Personal Edition in `cn-hangzhou` is now configured with namespace
  `ai4ss-skills` and private repository `ai4ss-skills-codex-harness`.
- ACR fixed registry password was set through the console and stored only in
  macOS Keychain under service `aliyun-acr-personal-cn-hangzhou`, account
  `15201208603`.
- The current pushed image is
  `registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859`.
- Default BuildKit image export with attestation/manifest-list output stalled
  during ACR Personal push finalization. Rebuilding as a single `linux/amd64`
  Docker v2 manifest with `--provenance=false --sbom=false` pushed cleanly.
- The current pushed image manifest digest is
  `sha256:005bba8b4b3c90b61f6b1289faf15529343306e4a52d3163b228a75b83adda00`.
- Remote `docker manifest inspect` confirms media type
  `application/vnd.docker.distribution.manifest.v2+json` with 20 layers.
- `deploy.sh build` now defaults to `DOCKER_BUILD_PLATFORM=linux/amd64`,
  `DOCKER_BUILD_PROVENANCE=false`, and `DOCKER_BUILD_SBOM=false` for ACR
  Personal compatibility.
- AgentRun inbound credential `ai4ss-codex-harness-inbound` was created or
  updated with `X-API-Key` public config. AgentRun/FC service roles are now
  authorized in the target account.
- `deploy.sh all` reached AgentRun and updated the runtime and endpoint to the
  current image. `deploy.sh render` now redacts secret-shaped fields before
  printing AgentRun render output.

## Cloud deployment status

Deployed and verified on AgentRun.

Completed cloud gates:

- ACR Personal namespace/repository exists.
- Verified local image was pushed to ACR with a concrete immutable digest.
- Runtime YAML renders with the pushed image and DeepSeek/gateway environment.
- AgentRun platform inbound credential exists.
- `apply` command authenticates to AgentRun and updates the Runtime/Endpoint.
- Runtime status is `READY`.
- Endpoint `default` status is `READY`.
- Data-link smoke tests pass, including SSE and one real Codex turn through
  DeepSeek.

Still missing for production hardening:

- Workspace persistence mechanism is cloud-tested if NAS persistence is needed.
- Observability, cost measurement, and rollback rehearsal.

## Verification gates

Current cloud deployment evidence on 2026-07-06:

- Aliyun profile: `chrome-aliyun`, account `1650944971821642`, region
  `cn-hangzhou`.
- Runtime: `ai4ss-skills-codex-harness`, id
  `74897c1f-3a5b-4bd6-b1aa-7ef6cf970f6d`, status `READY`.
- Runtime image:
  `registry.cn-hangzhou.aliyuncs.com/ai4ss-skills/ai4ss-skills-codex-harness:20260706-151859`.
- Runtime version: `1`.
- Endpoint: `default`, id `62c40ce4-8bc4-442e-9058-9e454a5a82b9`,
  status `READY`.
- Data-link URL:
  `https://1650944971821642.agentrun-data.cn-hangzhou.aliyuncs.com/agent-runtimes/ai4ss-skills-codex-harness/endpoints/default/invocations`.
- `deploy/agentrun/scripts/deploy.sh verify` passed when run through
  `with_aliyun_profile_env.mjs --profile chrome-aliyun --region cn-hangzhou`.
- Cloud smoke covered `/readyz`, session create/delete, initialize,
  `thread/start`, SSE delivery, and one real Codex turn through the DeepSeek
  adapter. The turn smoke returned `ok`.

Important deployment findings:

- ACR Personal private images must be rendered as
  `container.imageRegistryType: CUSTOM` with `container.registryConfig.auth`.
  Plain `imageRegistryType: ACR` reached FC image optimization but failed with
  `AUTHENTICATION_FAILED` / `user jurisdiction error`.
- The AgentRun declarative YAML field is `registryConfig.auth`, while the
  OpenAPI/SDK field is `registryConfig.authConfig`. `agentrun rt render`
  confirms the mapping.
- Runtime clients must send a stable `x-agentrun-session-id` header from the
  first `/sessions` request onward because the runtime uses `HEADER_FIELD`
  session affinity. Without it, follow-up `/request` calls can hit a different
  instance and return `session not found`.
- Avoid unfiltered `agentrun rt export` and
  `aliyun agentrun list-agent-runtimes`; they can print runtime environment
  variables. Use `agentrun rt status` or filtered `--cli-query` diagnostics.

The goal is not complete until all gates below have direct evidence:

| Gate | Evidence needed | Current status |
|---|---|---|
| Local app-server protocol | `node deploy/agentrun/scripts/smoke_appserver_stdio.mjs` succeeds | passed locally |
| Local gateway | gateway process starts and `smoke_gateway.mjs` succeeds | passed locally |
| Image build | `docker build -f deploy/agentrun/Dockerfile ...` succeeds | passed locally with workspace snapshot |
| Container gateway | built image starts and `smoke_gateway.mjs` succeeds against container | passed locally without host workspace mount |
| DeepSeek API credential | `node deploy/agentrun/scripts/smoke_deepseek_api.mjs` succeeds with injected `DEEPSEEK_API_KEY` | passed locally |
| Responses adapter | `smoke_deepseek_responses_adapter.mjs` succeeds | passed host + container |
| Codex through DeepSeek | one real Codex turn succeeds using DeepSeek adapter | passed host + container |
| Image push | image exists in selected ACR repo | passed: ACR Personal image `20260706-151859` pushed with manifest digest `sha256:005bba8b4b3c90b61f6b1289faf15529343306e4a52d3163b228a75b83adda00` |
| AgentRun API auth | `agentrun rt list` succeeds in target region | passed with `chrome-aliyun` account `1650944971821642` |
| Runtime render | `ar rt render -f deploy/agentrun/runtime.yaml` succeeds | passed via helper |
| ACR discovery | selected registry/repo is available | passed: ACR Personal namespace/repo exists in `cn-hangzhou` |
| Registry preflight | `deploy.sh registry-preflight --mode local-push` finds a push auth path | passed with ACR Personal credentials and one expected warning for no Enterprise instance |
| ACR bootstrap | namespace/repository exists inside selected ACR instance | not applicable for ACR Personal Edition |
| Platform credential | AgentRun inbound credential exists and is bound in YAML | passed |
| Runtime deploy | `ar rt apply ...` succeeds | passed after rendering `CUSTOM` registry auth |
| Runtime ready | `ar rt status ai4ss-skills-codex-harness --wait` reaches ready | passed |
| Runtime version | published version exists for endpoint routing | passed: version `1` |
| Endpoint ready | public AgentRun endpoint exists and routes to version | passed: endpoint `default` READY |
| Streaming | SSE or compatible stream observed through AgentRun endpoint | passed |
| Session lifecycle | create, use, idle-cleanup, delete verified | create/use/delete passed; idle timeout not yet waited for full 900s |
| Workspace persistence | workspace snapshot plus optional NAS mount semantics documented and image-tested | partially passed; NAS YAML renders, cloud NAS not yet live-tested |
| Secrets | no secrets in repo, image layers, exported YAML, or logs | repo scan passed; generated/runtime cloud env contains expected secrets; avoid unfiltered export/list output |
| Observability | logs include session ids and useful failure signals | pending |
| Cost | idle/runtime/sandbox cost measured or estimated from billing docs | pending |
| Rollback | delete or previous image rollback tested | pending |

## Next commands

Local checks:

```bash
deploy/agentrun/scripts/preflight.sh
node deploy/agentrun/scripts/smoke_deepseek_api.mjs
node deploy/agentrun/scripts/smoke_appserver_stdio.mjs
docker build -f deploy/agentrun/Dockerfile -t ai4ss-skills-codex-harness:local .
docker run --rm -p 9000:9000 \
  -e CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
  -e DEEPSEEK_API_KEY="<dev-only-deepseek-key>" \
  -e CODEX_WORKSPACE_DIR=/workspace \
  -v "$PWD:/workspace:ro" \
  ai4ss-skills-codex-harness:local
GATEWAY_URL=http://127.0.0.1:9000 \
CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
node deploy/agentrun/scripts/smoke_gateway.mjs
DEEPSEEK_RESPONSES_ADAPTER_URL=http://127.0.0.1:9000/internal/deepseek/v1 \
node deploy/agentrun/scripts/smoke_deepseek_responses_adapter.mjs
GATEWAY_URL=http://127.0.0.1:9000 \
CODEX_GATEWAY_BEARER_TOKEN="<dev-only-token>" \
node deploy/agentrun/scripts/smoke_gateway_turn.mjs
```

After installing AgentRun CLI and selecting an image:

```bash
export AGENTRUN_IMAGE="registry.cn-hangzhou.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>"
export ACR_USERNAME="15201208603"
export CODEX_GATEWAY_BEARER_TOKEN="<runtime-token>"
export DEEPSEEK_API_KEY="<runtime-deepseek-key>"

node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- agentrun rt list

node deploy/agentrun/scripts/acr_login.mjs --image "$AGENTRUN_IMAGE"
docker build -f deploy/agentrun/Dockerfile -t "$AGENTRUN_IMAGE" .
docker push "$AGENTRUN_IMAGE"

node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh render
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh apply
node deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  --profile chrome-aliyun \
  --region cn-hangzhou \
  -- deploy/agentrun/scripts/deploy.sh status

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

## Sources

- AgentRun CLI:
  <https://help.aliyun.com/zh/functioncompute/use-the-agentrun-cli-to-manage-agentrun-in-terminals-and-ci-pipelines>
- AgentRun runtime CLI manual:
  <https://github.com/Serverless-Devs/agentrun-cli/blob/main/docs/zh/runtime.md>
- AgentRun data-link access:
  <https://help.aliyun.com/zh/functioncompute/access-agenrun-http-api>
- Codex app-server:
  <https://developers.openai.com/codex/app-server>
- Codex CLI install:
  <https://developers.openai.com/codex/cli>
- Codex custom model providers:
  <https://developers.openai.com/codex/config-advanced>
- DeepSeek API docs:
  <https://api-docs.deepseek.com/>
- ACR temporary login token:
  <https://help.aliyun.com/zh/acr/developer-reference/api-cr-2018-12-01-getauthorizationtoken>
- AgentRuntime parameter reference:
  <https://help.aliyun.com/zh/functioncompute/fc/developer-reference/api-agentrun-2025-09-10-struct-agentruntime>
- AgentRun credential governance note:
  <https://help.aliyun.com/zh/cgc/user-guide/ai-governance-supported-check-items>
- Function Compute environment variables:
  <https://help.aliyun.com/zh/functioncompute/fc/user-guide/environment-variables>
- Function AI encrypted shared/service variables:
  <https://help.aliyun.com/zh/functioncompute/management-variables>
