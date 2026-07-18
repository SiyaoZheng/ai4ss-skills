#!/usr/bin/env bash
set -uo pipefail

STRICT=0
for arg in "$@"; do
  if [[ "$arg" == "--strict" ]]; then
    STRICT=1
  fi
done

SECRETS_FILE=${AGENTRUN_SECRETS_FILE:-deploy/agentrun/.generated/secrets.env}
if [[ -f "$SECRETS_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
  set +a
fi

FAILURES=0
WARNINGS=0

ok() {
  printf 'ok: %s\n' "$1"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf 'warn: %s\n' "$1"
}

fail() {
  FAILURES=$((FAILURES + 1))
  printf 'fail: %s\n' "$1"
}

need_command() {
  local cmd=$1
  local label=${2:-$cmd}
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$label found at $(command -v "$cmd")"
  else
    fail "$label missing"
  fi
}

check_optional_command() {
  local cmd=$1
  local label=${2:-$cmd}
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$label found at $(command -v "$cmd")"
  else
    warn "$label missing"
  fi
}

printf 'ai4ss-skills AgentRun deployment preflight\n'
printf 'strict=%s\n' "$STRICT"

need_command codex "Codex CLI"
need_command node "Node.js"
need_command docker "Docker CLI"
need_command aliyun "Alibaba Cloud CLI"
check_optional_command s "Serverless Devs CLI"

AGENTRUN_CLI=""
if command -v agentrun >/dev/null 2>&1; then
  AGENTRUN_CLI=$(command -v agentrun)
  ok "AgentRun CLI found as agentrun at $AGENTRUN_CLI"
elif command -v ar >/dev/null 2>&1; then
  if ar --version 2>&1 | grep -qi 'agentrun'; then
    AGENTRUN_CLI=$(command -v ar)
    ok "AgentRun CLI found as ar at $AGENTRUN_CLI"
  else
    warn "binary named ar exists at $(command -v ar), but it is not AgentRun CLI"
  fi
fi

if [[ -z "$AGENTRUN_CLI" ]]; then
  fail "AgentRun CLI missing; install from https://github.com/Serverless-Devs/agentrun-cli"
fi

if command -v codex >/dev/null 2>&1; then
  codex --version 2>/dev/null | sed 's/^/info: codex version /' || warn "could not read codex version"
fi

if command -v aliyun >/dev/null 2>&1; then
  aliyun version 2>/dev/null | sed 's/^/info: aliyun version /' || warn "could not read aliyun version"
fi

if command -v docker >/dev/null 2>&1; then
  docker version --format 'info: docker client {{.Client.Version}}' 2>/dev/null \
    || warn "Docker daemon/version check failed"
fi

for var in AGENTRUN_ACCESS_KEY_ID AGENTRUN_ACCESS_KEY_SECRET AGENTRUN_ACCOUNT_ID AGENTRUN_REGION; do
  if [[ -n "${!var:-}" ]]; then
    ok "$var is set"
  else
    warn "$var is not set; a local AgentRun profile may still provide it"
  fi
done

if [[ ! -f "$HOME/.agentrun/config.json" && -z "${AGENTRUN_ACCESS_KEY_ID:-}" ]]; then
  warn "AgentRun config is absent; run commands through deploy/agentrun/scripts/with_aliyun_profile_env.mjs --profile default --region cn-hangzhou -- <command>"
fi

MODEL_PROVIDER=${CODEX_MODEL_PROVIDER:-deepseek}
MODEL_NAME=${CODEX_MODEL:-deepseek-v4-flash}
DEEPSEEK_RUNTIME_BASE_URL=${CODEX_DEEPSEEK_RESPONSES_BASE_URL:-http://127.0.0.1:${PORT:-9000}/internal/deepseek/v1}
DEEPSEEK_WIRE_API=${CODEX_PROVIDER_WIRE_API:-responses}

printf 'info: Codex model provider target %s model %s\n' "$MODEL_PROVIDER" "$MODEL_NAME"

if [[ "$MODEL_PROVIDER" == "deepseek" ]]; then
  if [[ -n "${DEEPSEEK_API_KEY:-}" ]]; then
    ok "DEEPSEEK_API_KEY is set"
  else
    warn "DEEPSEEK_API_KEY is not set; runtime env injection, KMS, or an AgentRun model proxy must provide it"
  fi

  if [[ "$DEEPSEEK_WIRE_API" == "responses" && "$DEEPSEEK_RUNTIME_BASE_URL" == "https://api.deepseek.com" ]]; then
    warn "Codex custom providers use Responses wire_api; DeepSeek official API is chat-completions compatible, so a full Codex turn needs a verified Responses adapter or runtime support"
  elif [[ "$DEEPSEEK_RUNTIME_BASE_URL" == http://127.0.0.1:*"/internal/deepseek/v1" ]]; then
    ok "Codex DeepSeek provider points at the internal Responses adapter"
  fi
fi

if [[ -n "${CODEX_GATEWAY_BEARER_TOKEN:-}" ]]; then
  ok "CODEX_GATEWAY_BEARER_TOKEN is set"
else
  warn "CODEX_GATEWAY_BEARER_TOKEN is not set; deploy.sh apply injects it from env by default"
fi

for file in \
  deploy/agentrun/Dockerfile \
  deploy/agentrun/entrypoint.sh \
  deploy/agentrun/gateway/server.mjs \
  deploy/agentrun/runtime.yaml \
  deploy/agentrun/runtime-build.yaml \
  deploy/agentrun/runtime-nas.example.yaml \
  deploy/agentrun/scripts/check_no_secrets.sh \
  deploy/agentrun/scripts/deploy.sh \
  deploy/agentrun/scripts/acr_bootstrap.mjs \
  deploy/agentrun/scripts/acr_login.mjs \
  deploy/agentrun/scripts/agentrun_gateway_url.mjs \
  deploy/agentrun/scripts/bootstrap_secrets.mjs \
  deploy/agentrun/scripts/create_inbound_credential.mjs \
  deploy/agentrun/scripts/registry_preflight.mjs \
  deploy/agentrun/scripts/render_runtime.mjs \
  deploy/agentrun/scripts/with_aliyun_profile_env.mjs \
  deploy/agentrun/scripts/smoke_deepseek_api.mjs \
  deploy/agentrun/scripts/smoke_deepseek_responses_adapter.mjs \
  deploy/agentrun/scripts/smoke_appserver_stdio.mjs \
  deploy/agentrun/scripts/smoke_gateway.mjs \
  deploy/agentrun/scripts/smoke_gateway_turn.mjs \
  deploy/agentrun/scripts/smoke_gateway_stream.mjs; do
  if [[ -f "$file" ]]; then
    ok "$file exists"
  else
    fail "$file missing"
  fi
done

if grep -q '<namespace>' deploy/agentrun/runtime.yaml; then
  warn "runtime.yaml still contains image placeholder <namespace>"
fi

if grep -q '<tag>' deploy/agentrun/runtime.yaml; then
  warn "runtime.yaml still contains image placeholder <tag>"
fi

printf 'summary: failures=%s warnings=%s\n' "$FAILURES" "$WARNINGS"

if [[ "$STRICT" -eq 1 && "$FAILURES" -gt 0 ]]; then
  exit 1
fi

exit 0
