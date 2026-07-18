FROM node:20-bookworm-slim

ARG CODEX_INSTALLER_URL=https://chatgpt.com/codex/install.sh

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    bubblewrap \
    ca-certificates \
    curl \
    git \
    latexmk \
    poppler-utils \
    python3 \
    python3-pypdf \
    ripgrep \
    texlive-fonts-recommended \
    texlive-latex-base \
    texlive-latex-recommended \
    tini \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g \
    @brave/brave-search-mcp-server@2.0.85 \
    @perplexity-ai/mcp-server@0.9.0 \
    @upstash/context7-mcp@3.2.2 \
    @xdevplatform/xurl@1.2.2 \
    mcp-remote@0.1.38 \
    tavily-mcp@0.2.20 \
  && npm cache clean --force

RUN useradd --create-home --shell /bin/bash codex \
  && mkdir -p /workspace /opt/ai4ss-codex-harness/workspace-snapshot \
  && chown -R codex:codex /workspace /opt/ai4ss-codex-harness

USER codex
ENV PATH="/home/codex/.local/bin:/home/codex/.codex/bin:${PATH}"

RUN curl -fsSL "${CODEX_INSTALLER_URL}" | CODEX_NON_INTERACTIVE=1 sh \
  && codex --version

COPY --chown=codex:codex deploy/agentrun/gateway/server.mjs /opt/ai4ss-codex-harness/server.mjs
COPY --chown=codex:codex deploy/agentrun/entrypoint.sh /opt/ai4ss-codex-harness/entrypoint.sh

COPY --chown=codex:codex AGENTS.md DESIGN.md DESIGNPLAN.md LICENSE README.md WORKFLOW.md /opt/ai4ss-codex-harness/workspace-snapshot/
COPY --chown=codex:codex deploy /opt/ai4ss-codex-harness/workspace-snapshot/deploy
COPY --chown=codex:codex docs /opt/ai4ss-codex-harness/workspace-snapshot/docs
COPY --chown=codex:codex dsl /opt/ai4ss-codex-harness/workspace-snapshot/dsl
COPY --chown=codex:codex evals /opt/ai4ss-codex-harness/workspace-snapshot/evals
COPY --chown=codex:codex hooks /opt/ai4ss-codex-harness/workspace-snapshot/hooks
COPY --chown=codex:codex references /opt/ai4ss-codex-harness/workspace-snapshot/references
COPY --chown=codex:codex scripts /opt/ai4ss-codex-harness/workspace-snapshot/scripts
COPY --chown=codex:codex skills /opt/ai4ss-codex-harness/workspace-snapshot/skills

WORKDIR /workspace

ENV HOST=0.0.0.0
ENV PORT=9000
ENV CODEX_BIN=codex
ENV CODEX_HOME=/home/codex/.codex
ENV CODEX_SESSION_HOME_ROOT=/home/codex/.codex-sessions
ENV CODEX_WORKSPACE_DIR=/workspace
ENV CODEX_CONFIG_MANAGED=true
ENV CODEX_MCP_ENABLED=true
ENV CODEX_WORKSPACE_SEED=true
ENV WORKSPACE_SNAPSHOT_DIR=/opt/ai4ss-codex-harness/workspace-snapshot
ENV CODEX_MODEL_PROVIDER=deepseek
ENV CODEX_MODEL=deepseek-v4-flash
ENV DEEPSEEK_BASE_URL=https://api.deepseek.com
ENV CODEX_DEEPSEEK_RESPONSES_BASE_URL=http://127.0.0.1:9000/internal/deepseek/v1
ENV CODEX_PROVIDER_WIRE_API=responses
ENV DEEPSEEK_RESPONSES_ADAPTER=true
ENV DEEPSEEK_THINKING=disabled
ENV SESSION_IDLE_MS=900000
ENV MAX_SESSIONS=16
ENV SESSION_EVENT_BUFFER=200
ENV ALLOW_UNAUTHENTICATED=false

EXPOSE 9000

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/ai4ss-codex-harness/entrypoint.sh"]
CMD ["node", "/opt/ai4ss-codex-harness/server.mjs"]
