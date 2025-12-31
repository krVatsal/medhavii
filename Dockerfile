# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG INSTALL_OLLAMA=false

# ---------------------------------------------------------------------------
# Frontend build (Next.js)
# ---------------------------------------------------------------------------
FROM node:${NODE_VERSION}-bookworm AS frontend-build
WORKDIR /app/servers/nextjs

COPY servers/nextjs/package.json servers/nextjs/package-lock.json ./
RUN npm set registry https://registry.npmjs.org \
    && npm set fetch-retries 5 \
    && npm set fetch-retry-mintimeout 20000 \
    && npm set fetch-retry-maxtimeout 120000 \
    && npm ci --legacy-peer-deps --no-audit --progress=false

COPY servers/nextjs/ ./
RUN npm run build \
    && ls -la .next-build \
    && npm prune --production

# ---------------------------------------------------------------------------
# Backend build (FastAPI dependencies)
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS backend-build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/servers/fastapi

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libpq-dev \
    libcairo2 \
    pkg-config \
    libpango1.0-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY servers/fastapi/ /app/servers/fastapi/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Runtime image
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm
ARG NODE_VERSION
ARG PYTHON_VERSION

LABEL org.opencontainers.image.source="https://github.com/krVatsal/medhavii"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DATA_DIRECTORY=/app_data \
    TEMP_DIRECTORY=/tmp/presenton \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    NODE_ENV=production \
    PORT=80

ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies including LaTeX for Manim
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    ca-certificates \
    fontconfig \
    chromium \
    libreoffice \
    ffmpeg \
    dumb-init \
    git \
    texlive-full \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for Manim and MCP
RUN pip install --no-cache-dir manim mcp

# Clone the manim-mcp-server repository
RUN git clone https://github.com/abhiemj/manim-mcp-server.git /opt/manim-mcp-server
WORKDIR /opt/manim-mcp-server
RUN pip install --no-cache-dir .
WORKDIR /app

# Install ollama only when requested (can be slow/unreliable in CI)
RUN if [ "$INSTALL_OLLAMA" = "true" ]; then \
            echo "Installing Ollama..." && \
            curl -m 60 -fsSL https://ollama.com/install.sh | sh || echo "Ollama install skipped/failed"; \
        else \
            echo "Skipping Ollama install (INSTALL_OLLAMA=false)"; \
        fi

# Copy Python dependencies from builder
COPY --from=backend-build /usr/local/lib/python${PYTHON_VERSION} /usr/local/lib/python${PYTHON_VERSION}
COPY --from=backend-build /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy application code
COPY start.js LICENSE NOTICE ./
COPY servers/fastapi/ /app/servers/fastapi/

# Copy built frontend artifacts
COPY --from=frontend-build /app/servers/nextjs/.next-build /app/servers/nextjs/.next-build
COPY --from=frontend-build /app/servers/nextjs/node_modules /app/servers/nextjs/node_modules
COPY --from=frontend-build /app/servers/nextjs/package.json /app/servers/nextjs/package-lock.json /app/servers/nextjs/
COPY servers/nextjs/public /app/servers/nextjs/public
COPY servers/nextjs/next.config.mjs servers/nextjs/tsconfig.json servers/nextjs/tailwind.config.ts servers/nextjs/postcss.config.mjs /app/servers/nextjs/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Persist runtime data
VOLUME ["/app_data"]

EXPOSE 80

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "/app/start.js"]