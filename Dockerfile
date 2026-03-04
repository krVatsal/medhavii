# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG INSTALL_OLLAMA=false

# ---------------------------------------------------------------------------
# Frontend build
# ---------------------------------------------------------------------------
FROM node:${NODE_VERSION}-bookworm AS frontend-build
WORKDIR /app/servers/nextjs

COPY servers/nextjs/package*.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps --no-audit --progress=false

COPY servers/nextjs/ ./
RUN npm run build && \
    echo "Build completed. Checking .next folder:" && \
    ls -la .next/ && \
    echo "Checking .next/standalone:" && \
    ls -la .next/standalone/ || echo "WARNING: .next/standalone not found!" && \
    echo "Checking .next/static:" && \
    ls -la .next/static/ || echo "WARNING: .next/static not found!"

# ---------------------------------------------------------------------------
# Backend build
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS backend-build
WORKDIR /app/servers/fastapi

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    libcairo2 pkg-config libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY servers/fastapi/ ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel \
    && pip wheel --no-deps --wheel-dir /wheels .

# ---------------------------------------------------------------------------
# Runtime image
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm
ARG NODE_VERSION
ARG INSTALL_OLLAMA

ENV NODE_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    PORT=80

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx curl ca-certificates dumb-init git \
    chromium libreoffice ffmpeg \
    texlive-latex-extra texlive-fonts-recommended \
    texlive-fonts-extra texlive-xetex \
    build-essential pkg-config \
    libcairo2-dev libpango1.0-dev \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python deps (install BEFORE copying code for better caching)
COPY --from=backend-build /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install /wheels/* manim mcp

# Manim MCP server (clone only, no installation needed)
RUN git clone --depth=1 https://github.com/abhiemj/manim-mcp-server.git /opt/manim-mcp-server

# Ollama (optional)
RUN if [ "$INSTALL_OLLAMA" = "true" ]; then \
        curl -fsSL https://ollama.com/install.sh | sh || true; \
    fi

WORKDIR /app

# Static files (change rarely)
COPY start.js LICENSE NOTICE ./
COPY nginx.conf /etc/nginx/nginx.conf

# Frontend artifacts and dependencies (change less often)
# Standalone mode bundles only what's needed - much smaller!
COPY --from=frontend-build /app/servers/nextjs/.next/standalone ./
COPY --from=frontend-build /app/servers/nextjs/.next/static ./servers/nextjs/.next/static
COPY --from=frontend-build /app/servers/nextjs/public ./servers/nextjs/public

# Python code (COPY LAST - changes most frequently)
COPY servers/fastapi/ servers/fastapi/

VOLUME ["/app_data"]
EXPOSE 80

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "/app/start.js"]
