#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$ROOT_DIR"

if rg -n --hidden \
  --glob 'deploy/agentrun/**' \
  --glob '!deploy/agentrun/.generated/**' \
  --glob 'docs/agentrun*.md' \
  -e 'sk-[A-Za-z0-9_-]{20,}' \
  -e 'LTAI[A-Za-z0-9]{16,}' \
  -e 'AKIA[A-Za-z0-9]{16}' \
  -e 'BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY' \
  -e 'CODEX_GATEWAY_BEARER_TOKEN=[A-Za-z0-9._~+/=-]{12,}' \
  .; then
  printf 'fail: possible secret found\n' >&2
  exit 1
fi

printf 'ok: no obvious secrets found in AgentRun deployment files\n'
