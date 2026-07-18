#!/usr/bin/env bash
set -euo pipefail

: "${CODEX_WORKSPACE_DIR:=/workspace}"
: "${CODEX_HOME:=${HOME}/.codex}"
: "${CODEX_CONFIG_MANAGED:=true}"
: "${CODEX_WORKSPACE_SEED:=true}"
: "${WORKSPACE_SNAPSHOT_DIR:=/opt/ai4ss-codex-harness/workspace-snapshot}"
: "${CODEX_MODEL_PROVIDER:=deepseek}"
: "${CODEX_MODEL:=deepseek-v4-flash}"
: "${DEEPSEEK_BASE_URL:=https://api.deepseek.com}"
: "${PORT:=9000}"
: "${CODEX_DEEPSEEK_RESPONSES_BASE_URL:=http://127.0.0.1:${PORT}/internal/deepseek/v1}"
: "${DEEPSEEK_API_KEY_ENV:=DEEPSEEK_API_KEY}"
: "${CODEX_PROVIDER_WIRE_API:=responses}"
: "${CODEX_MCP_ENABLED:=true}"
: "${CODEX_MCP_ALIYUN_WEBSEARCH_ENABLED:=true}"
: "${CODEX_MCP_BRAVE_ENABLED:=false}"
: "${CODEX_MCP_PERPLEXITY_ENABLED:=false}"
: "${CODEX_MCP_TAVILY_ENABLED:=false}"
: "${CODEX_MCP_X_DOCS_ENABLED:=true}"
: "${CODEX_MCP_XAPI_ENABLED:=false}"
: "${ALIYUN_WEBSEARCH_MCP_URL:=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp}"

export CODEX_HOME

if [[ -n "${BRAVE_SEARCH_API_KEY:-}" && -z "${BRAVE_API_KEY:-}" ]]; then
  export BRAVE_API_KEY="$BRAVE_SEARCH_API_KEY"
fi

if [[ -n "${BAILIAN_API_KEY:-}" && -z "${DASHSCOPE_API_KEY:-}" ]]; then
  export DASHSCOPE_API_KEY="$BAILIAN_API_KEY"
fi

mkdir -p "$CODEX_HOME"
CONFIG_FILE="${CODEX_HOME}/config.toml"
mcp_enabled_names=()

if [[ "$CODEX_WORKSPACE_DIR" == *$'\n'* ]]; then
  printf 'CODEX_WORKSPACE_DIR must not contain newlines\n' >&2
  exit 64
fi

seed_workspace_if_needed() {
  case "$CODEX_WORKSPACE_SEED" in
    true|1|yes)
      ;;
    *)
      return 0
      ;;
  esac

  if [[ ! -d "$WORKSPACE_SNAPSHOT_DIR" ]]; then
    return 0
  fi

  mkdir -p "$CODEX_WORKSPACE_DIR"
  if [[ -e "$CODEX_WORKSPACE_DIR/AGENTS.md" || -d "$CODEX_WORKSPACE_DIR/skills" ]]; then
    return 0
  fi

  cp -a "$WORKSPACE_SNAPSHOT_DIR"/. "$CODEX_WORKSPACE_DIR"/
}

toml_escape() {
  local value=$1
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  printf '%s' "$value"
}

toml_array() {
  local first=1 item
  printf '['
  for item in "$@"; do
    if [[ "$first" -eq 0 ]]; then
      printf ', '
    fi
    printf '"%s"' "$(toml_escape "$item")"
    first=0
  done
  printf ']'
}

write_project_trust() {
  local escaped_workspace
  escaped_workspace=$(toml_escape "$CODEX_WORKSPACE_DIR")
  printf '[projects."%s"]\n' "$escaped_workspace"
  printf 'trust_level = "trusted"\n'
}

write_model_config() {
  local escaped_model escaped_provider
  escaped_model=$(toml_escape "$CODEX_MODEL")
  escaped_provider=$(toml_escape "$CODEX_MODEL_PROVIDER")
  printf 'model = "%s"\n' "$escaped_model"
  printf 'model_provider = "%s"\n' "$escaped_provider"

  if [[ "$CODEX_MODEL_PROVIDER" == "deepseek" ]]; then
    local provider_base_url escaped_base_url escaped_env_key escaped_wire_api
    provider_base_url="${CODEX_DEEPSEEK_RESPONSES_BASE_URL:-$DEEPSEEK_BASE_URL}"
    escaped_base_url=$(toml_escape "$provider_base_url")
    escaped_env_key=$(toml_escape "$DEEPSEEK_API_KEY_ENV")
    escaped_wire_api=$(toml_escape "$CODEX_PROVIDER_WIRE_API")

    printf '\n[model_providers.deepseek]\n'
    printf 'name = "DeepSeek"\n'
    printf 'base_url = "%s"\n' "$escaped_base_url"
    printf 'env_key = "%s"\n' "$escaped_env_key"
    printf 'wire_api = "%s"\n' "$escaped_wire_api"
  fi
}

write_mcp_server() {
  local name=$1 command=$2
  shift 2
  local args=("$@")
  printf '\n[mcp_servers.%s]\n' "$name"
  printf 'command = "%s"\n' "$(toml_escape "$command")"
  if [[ "${#args[@]}" -gt 0 ]]; then
    printf 'args = '
    toml_array "${args[@]}"
    printf '\n'
  fi
  mcp_enabled_names+=("$name")
}

write_http_mcp_server() {
  local name=$1 url=$2 bearer_env=${3:-}
  printf '\n[mcp_servers.%s]\n' "$name"
  printf 'url = "%s"\n' "$(toml_escape "$url")"
  if [[ -n "$bearer_env" ]]; then
    printf 'bearer_token_env_var = "%s"\n' "$(toml_escape "$bearer_env")"
  fi
  printf 'startup_timeout_sec = 30\n'
  printf 'tool_timeout_sec = 60\n'
  mcp_enabled_names+=("$name")
}

write_cloud_mcp_config() {
  case "$CODEX_MCP_ENABLED" in
    true|1|yes)
      ;;
    *)
      return 0
      ;;
  esac

  if [[ -n "${DASHSCOPE_API_KEY:-}" ]]; then
    case "$CODEX_MCP_ALIYUN_WEBSEARCH_ENABLED" in
      true|1|yes)
        write_http_mcp_server "aliyun-websearch" "$ALIYUN_WEBSEARCH_MCP_URL" "DASHSCOPE_API_KEY"
        ;;
    esac
  fi

  if [[ -n "${BRAVE_API_KEY:-}" ]]; then
    case "$CODEX_MCP_BRAVE_ENABLED" in
      true|1|yes)
        write_mcp_server "brave-search" "brave-search-mcp-server" "--transport" "stdio"
        ;;
    esac
  fi

  if [[ -n "${PERPLEXITY_API_KEY:-}" ]]; then
    case "$CODEX_MCP_PERPLEXITY_ENABLED" in
      true|1|yes)
        write_mcp_server "perplexity" "perplexity-mcp"
        ;;
    esac
  fi

  if [[ -n "${TAVILY_API_KEY:-}" ]]; then
    case "$CODEX_MCP_TAVILY_ENABLED" in
      true|1|yes)
        write_mcp_server "tavily" "tavily-mcp"
        ;;
    esac
  fi

  if [[ -n "${CONTEXT7_API_KEY:-}" ]]; then
    write_mcp_server "context7" "sh" "-lc" 'exec context7-mcp --api-key "$CONTEXT7_API_KEY"'
  fi

  case "$CODEX_MCP_X_DOCS_ENABLED" in
    true|1|yes)
      write_http_mcp_server "x-docs" "https://docs.x.com/mcp"
      ;;
  esac

  case "$CODEX_MCP_XAPI_ENABLED" in
    true|1|yes)
      write_mcp_server "xapi" "xurl" "mcp" "https://api.x.com/mcp"
      ;;
  esac

  if [[ -n "${HONCHO_MCP_URL:-}" ]]; then
    if [[ -n "${HONCHO_AUTH_HEADER:-}" ]]; then
      write_mcp_server "honcho" "sh" "-lc" 'exec mcp-remote "$HONCHO_MCP_URL" --header "Authorization:${HONCHO_AUTH_HEADER}"'
    else
      write_mcp_server "honcho" "sh" "-lc" 'exec mcp-remote "$HONCHO_MCP_URL"'
    fi
  fi

  if [[ -n "${EVERME_MCP_URL:-}" ]]; then
    write_mcp_server "everme" "sh" "-lc" 'exec mcp-remote "$EVERME_MCP_URL"'
  fi
}

export_enabled_mcp_names() {
  CODEX_MCP_ENABLED_NAMES=$(IFS=,; printf '%s' "${mcp_enabled_names[*]:-}")
  export CODEX_MCP_ENABLED_NAMES
}

write_managed_config() {
  local tmp_file
  tmp_file="${CONFIG_FILE}.tmp"
  mcp_enabled_names=()
  {
    printf '# Generated by ai4ss AgentRun Codex harness entrypoint.\n'
    printf '# Runtime secrets are read from environment variables, not written here.\n\n'
    write_model_config
    write_cloud_mcp_config
    printf '\n'
    write_project_trust
  } > "$tmp_file"
  mv "$tmp_file" "$CONFIG_FILE"
  export_enabled_mcp_names
}

append_project_trust_if_missing() {
  touch "$CONFIG_FILE"
  local escaped_workspace project_header
  escaped_workspace=$(toml_escape "$CODEX_WORKSPACE_DIR")
  project_header="[projects.\"${escaped_workspace}\"]"
  if ! grep -Fqx "$project_header" "$CONFIG_FILE"; then
    {
      printf '\n%s\n' "$project_header"
      printf 'trust_level = "trusted"\n'
    } >> "$CONFIG_FILE"
  fi
}

case "$CODEX_CONFIG_MANAGED" in
  true|1|yes)
    write_managed_config
    ;;
  *)
    append_project_trust_if_missing
    export_enabled_mcp_names
    ;;
esac

seed_workspace_if_needed

exec "$@"
