#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
DEPLOY_DIR="$ROOT_DIR/deploy/agentrun"
GENERATED_DIR="$DEPLOY_DIR/.generated"
SECRETS_FILE=${AGENTRUN_SECRETS_FILE:-"$GENERATED_DIR/secrets.env"}
RUNTIME_TEMPLATE=${AGENTRUN_RUNTIME_TEMPLATE:-"$DEPLOY_DIR/runtime.yaml"}
RUNTIME_FILE=${AGENTRUN_RUNTIME_FILE:-"$GENERATED_DIR/runtime.yaml"}
RUNTIME_NAME=${AGENTRUN_RUNTIME_NAME:-ai4ss-skills-codex-harness}
APPLY_TIMEOUT=${AGENTRUN_APPLY_TIMEOUT:-20m}
STATUS_TIMEOUT=${AGENTRUN_STATUS_TIMEOUT:-10m}
DELETE_TIMEOUT=${AGENTRUN_DELETE_TIMEOUT:-10m}
REQUIRED_APPLY_SECRET_ENV_KEYS=${AGENTRUN_REQUIRED_APPLY_SECRET_ENV_KEYS:-CODEX_GATEWAY_BEARER_TOKEN,DEEPSEEK_API_KEY}
OPTIONAL_APPLY_SECRET_ENV_KEYS=${AGENTRUN_OPTIONAL_APPLY_SECRET_ENV_KEYS:-DASHSCOPE_API_KEY,BAILIAN_API_KEY,ALIYUN_WEBSEARCH_MCP_URL,BRAVE_SEARCH_API_KEY,PERPLEXITY_API_KEY,TAVILY_API_KEY,CONTEXT7_API_KEY,HONCHO_MCP_URL,HONCHO_AUTH_HEADER,HONCHO_USER_NAME,HONCHO_WORKSPACE_ID,HONCHO_ASSISTANT_NAME,EVERME_MCP_URL,EVEROS_BASE_URL,EVERME_AGENT_ID,EVERME_LOCAL_APP_ID,EVERME_LOCAL_PROJECT_ID,EVERME_LOCAL_USER_ID,HEADROOM_PROXY_URL,HTTPS_PROXY,ALL_PROXY,NODE_USE_ENV_PROXY}
APPLY_SECRET_ENV_KEYS_OVERRIDE=${AGENTRUN_APPLY_SECRET_ENV_KEYS:-}
IMAGE=${AGENTRUN_IMAGE:-}

load_env_file() {
  local file=$1
  if [[ ! -f "$file" ]]; then
    return 0
  fi
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

load_env_file "$SECRETS_FILE"

usage() {
  cat <<'USAGE'
Usage: deploy/agentrun/scripts/deploy.sh <command>

Commands:
  preflight    Run local readiness checks.
  bootstrap-secrets
               Generate local ignored deployment secrets.
  render-file  Generate .generated/runtime.yaml from AGENTRUN_IMAGE.
  acr-login    Log in to ACR without printing credentials.
  acr-bootstrap
               Check/create namespace and repository inside an existing ACR instance.
  credential-dry-run
               Validate AgentRun inbound API-key credential request shape.
  credential-create
               Create AgentRun inbound API-key credential from AGENTRUN_RUNTIME_API_KEY.
  registry-preflight
               Check image registry, local push auth, and cloud-build registry auth prerequisites.
  build        Build the local Docker image tagged as AGENTRUN_IMAGE.
               Defaults: DOCKER_BUILD_PLATFORM=linux/amd64,
               DOCKER_BUILD_PROVENANCE=false, DOCKER_BUILD_SBOM=false.
  push         Push AGENTRUN_IMAGE.
  render       Run AgentRun CLI render against generated runtime YAML.
  cloud-build  Run AgentRun cloud build from runtime-build.yaml.
  apply        Run AgentRun CLI apply against generated runtime YAML.
  status       Wait for the AgentRun Runtime to become ready.
  gateway-url  Print AgentRun data-link base URL for the default endpoint.
  deepseek-smoke
               Verify DeepSeek /chat/completions connectivity when a key exists.
  deepseek-adapter-smoke
               Verify the local Responses-to-DeepSeek adapter.
  deepseek-tool-call-adapter-smoke
               Verify Responses function/tool-call streaming conversion with a fake DeepSeek upstream.
  smoke        Run gateway smoke against GATEWAY_URL.
  turn-smoke   Run a real Codex turn through the gateway and DeepSeek backend.
  tool-read-smoke
               Run a real Codex turn that must read a workspace skill file.
  pdf-smoke    Run a real Codex turn that must create a LaTeX article PDF.
  stream-smoke Run SSE gateway smoke against GATEWAY_URL.
  verify       status, smoke, stream-smoke, turn-smoke.
  delete       Delete the AgentRun Runtime.
  all          preflight, render-file, registry-preflight, build, acr-login unless skipped, push, render, apply, status.

Required for cloud commands:
  AGENTRUN_IMAGE=registry.<region>.aliyuncs.com/<namespace>/ai4ss-skills-codex-harness:<tag>
  AGENTRUN_ACCESS_KEY_ID / AGENTRUN_ACCESS_KEY_SECRET / AGENTRUN_ACCOUNT_ID / AGENTRUN_REGION
  or run through scripts/with_aliyun_profile_env.mjs.

Required for acr-login:
  Enterprise ACR: ACR_INSTANCE_ID plus Aliyun profile/env.
  Personal/manual ACR: ACR_USERNAME and ACR_PASSWORD.
  Set SKIP_ACR_LOGIN=1 when Docker is already authenticated or the image
  registry does not need login.

Required for acr-bootstrap:
  ACR_INSTANCE_ID and AGENTRUN_IMAGE.
  Pass --yes to create missing namespace/repository.

Required for credential-create / credential-dry-run:
  AGENTRUN_RUNTIME_API_KEY=...
  Run bootstrap-secrets first to create deploy/agentrun/.generated/secrets.env.

Required for smoke commands:
  GATEWAY_URL=https://...
  CODEX_GATEWAY_BEARER_TOKEN=...

Required for real DeepSeek/model-turn validation:
  DEEPSEEK_API_KEY=...

Required for apply unless AGENTRUN_APPLY_SECRET_ENV_KEYS is overridden:
  CODEX_GATEWAY_BEARER_TOKEN=...
  DEEPSEEK_API_KEY=...

Optional MCP env injected when present:
  DASHSCOPE_API_KEY or BAILIAN_API_KEY for Aliyun WebSearch, CONTEXT7_API_KEY,
  BRAVE_SEARCH_API_KEY, PERPLEXITY_API_KEY, TAVILY_API_KEY when explicitly enabled,
  HONCHO_MCP_URL/HONCHO_AUTH_HEADER, EVERME_MCP_URL, proxy env.
USAGE
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

find_agentrun() {
  if command -v agentrun >/dev/null 2>&1; then
    command -v agentrun
    return 0
  fi
  if command -v ar >/dev/null 2>&1 && ar --version 2>&1 | grep -qi 'agentrun'; then
    command -v ar
    return 0
  fi
  return 1
}

require_image() {
  [[ -n "$IMAGE" ]] || die "AGENTRUN_IMAGE is required"
  [[ "$IMAGE" != *"<namespace>"* ]] || die "AGENTRUN_IMAGE still contains <namespace>"
  [[ "$IMAGE" != *"<tag>"* ]] || die "AGENTRUN_IMAGE still contains <tag>"
}

render_runtime_file() {
  require_image
  node "$DEPLOY_DIR/scripts/render_runtime.mjs" \
    --template "$RUNTIME_TEMPLATE" \
    --out "$RUNTIME_FILE" \
    --image "$IMAGE"
  printf 'generated %s\n' "$RUNTIME_FILE"
}

append_csv_key() {
  local key=$1
  key=${key//[[:space:]]/}
  if [[ -z "$key" ]]; then
    return 0
  fi
  if [[ -z "${COMPUTED_SECRET_ENV_KEYS:-}" ]]; then
    COMPUTED_SECRET_ENV_KEYS=$key
  else
    COMPUTED_SECRET_ENV_KEYS="${COMPUTED_SECRET_ENV_KEYS},${key}"
  fi
}

computed_apply_secret_env_keys() {
  if [[ -n "$APPLY_SECRET_ENV_KEYS_OVERRIDE" ]]; then
    printf '%s\n' "$APPLY_SECRET_ENV_KEYS_OVERRIDE"
    return 0
  fi

  COMPUTED_SECRET_ENV_KEYS=""
  local key
  local required_keys=()
  local optional_keys=()
  IFS=',' read -r -a required_keys <<< "$REQUIRED_APPLY_SECRET_ENV_KEYS"
  IFS=',' read -r -a optional_keys <<< "$OPTIONAL_APPLY_SECRET_ENV_KEYS"

  for key in "${required_keys[@]}"; do
    append_csv_key "$key"
  done

  for key in "${optional_keys[@]}"; do
    key=${key//[[:space:]]/}
    if [[ -n "$key" && -v "$key" ]]; then
      local value=${!key}
      if [[ -n "$value" ]]; then
        append_csv_key "$key"
      fi
    fi
  done

  printf '%s\n' "$COMPUTED_SECRET_ENV_KEYS"
}

render_apply_runtime_file() {
  require_image
  local apply_file
  local secret_env_keys
  apply_file=$(mktemp "${TMPDIR:-/tmp}/agentrun-runtime.XXXXXX.yaml")
  secret_env_keys=$(computed_apply_secret_env_keys)
  node "$DEPLOY_DIR/scripts/render_runtime.mjs" \
    --template "$RUNTIME_TEMPLATE" \
    --out "$apply_file" \
    --image "$IMAGE" \
    --include-secret-env "$secret_env_keys"
  printf '%s\n' "$apply_file"
}

cmd=${1:-}
case "$cmd" in
  preflight)
    "$DEPLOY_DIR/scripts/preflight.sh"
    ;;
  bootstrap-secrets)
    node "$DEPLOY_DIR/scripts/bootstrap_secrets.mjs"
    ;;
  render-file)
    render_runtime_file
    ;;
  acr-login)
    require_image
    node "$DEPLOY_DIR/scripts/acr_login.mjs" --image "$IMAGE"
    ;;
  acr-bootstrap)
    require_image
    shift || true
    node "$DEPLOY_DIR/scripts/acr_bootstrap.mjs" --image "$IMAGE" "$@"
    ;;
  credential-dry-run)
    shift || true
    node "$DEPLOY_DIR/scripts/create_inbound_credential.mjs" --dry-run "$@"
    ;;
  credential-create)
    shift || true
    node "$DEPLOY_DIR/scripts/create_inbound_credential.mjs" "$@"
    ;;
  registry-preflight)
    require_image
    shift || true
    node "$DEPLOY_DIR/scripts/registry_preflight.mjs" --image "$IMAGE" "$@"
    ;;
  build)
    require_image
    docker build \
      --platform "${DOCKER_BUILD_PLATFORM:-linux/amd64}" \
      --provenance="${DOCKER_BUILD_PROVENANCE:-false}" \
      --sbom="${DOCKER_BUILD_SBOM:-false}" \
      -f "$DEPLOY_DIR/Dockerfile" \
      -t "$IMAGE" \
      "$ROOT_DIR"
    ;;
  push)
    require_image
    docker push "$IMAGE"
    ;;
  render)
    render_runtime_file
    AGENTRUN_CMD=$(find_agentrun) || die "AgentRun CLI missing; install agentrun-cli"
    "$AGENTRUN_CMD" rt render -f "$RUNTIME_FILE" | node "$DEPLOY_DIR/scripts/redact_agentrun_output.mjs"
    ;;
  cloud-build)
    require_image
    RUNTIME_TEMPLATE=${AGENTRUN_RUNTIME_BUILD_TEMPLATE:-"$DEPLOY_DIR/runtime-build.yaml"}
    node "$DEPLOY_DIR/scripts/registry_preflight.mjs" --mode cloud-build --strict --image "$IMAGE" --runtime-build "$RUNTIME_TEMPLATE"
    render_runtime_file
    AGENTRUN_CMD=$(find_agentrun) || die "AgentRun CLI missing; install agentrun-cli"
    "$AGENTRUN_CMD" rt cloud-build -f "$RUNTIME_FILE"
    ;;
  apply)
    AGENTRUN_CMD=$(find_agentrun) || die "AgentRun CLI missing; install agentrun-cli"
    APPLY_FILE=$(render_apply_runtime_file)
    trap 'rm -f "$APPLY_FILE"' EXIT
    "$AGENTRUN_CMD" rt apply -f "$APPLY_FILE" --timeout "$APPLY_TIMEOUT"
    ;;
  status)
    AGENTRUN_CMD=$(find_agentrun) || die "AgentRun CLI missing; install agentrun-cli"
    "$AGENTRUN_CMD" rt status "$RUNTIME_NAME" --wait --timeout "$STATUS_TIMEOUT"
    ;;
  gateway-url)
    node "$DEPLOY_DIR/scripts/agentrun_gateway_url.mjs"
    ;;
  deepseek-smoke)
    node "$DEPLOY_DIR/scripts/smoke_deepseek_api.mjs"
    ;;
  deepseek-adapter-smoke)
    node "$DEPLOY_DIR/scripts/smoke_deepseek_responses_adapter.mjs"
    ;;
  deepseek-tool-call-adapter-smoke)
    node "$DEPLOY_DIR/scripts/smoke_deepseek_tool_calls_adapter.mjs"
    ;;
  smoke)
    node "$DEPLOY_DIR/scripts/smoke_gateway.mjs"
    ;;
  turn-smoke)
    node "$DEPLOY_DIR/scripts/smoke_gateway_turn.mjs"
    ;;
  tool-read-smoke)
    node "$DEPLOY_DIR/scripts/smoke_gateway_tool_read.mjs"
    ;;
  pdf-smoke)
    node "$DEPLOY_DIR/scripts/smoke_research_pdf.mjs"
    ;;
  stream-smoke)
    node "$DEPLOY_DIR/scripts/smoke_gateway_stream.mjs"
    ;;
  verify)
    "$0" status
    "$0" smoke
    "$0" stream-smoke
    "$0" turn-smoke
    ;;
  delete)
    AGENTRUN_CMD=$(find_agentrun) || die "AgentRun CLI missing; install agentrun-cli"
    "$AGENTRUN_CMD" rt delete "$RUNTIME_NAME" --yes --timeout "$DELETE_TIMEOUT"
    ;;
  all)
    "$0" preflight
    "$0" render-file
    "$0" registry-preflight --mode local-push
    "$0" build
    if [[ "${SKIP_ACR_LOGIN:-0}" != "1" ]]; then
      "$0" acr-login
    fi
    "$0" push
    "$0" render
    "$0" apply
    "$0" status
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    usage >&2
    die "unknown command: $cmd"
    ;;
esac
