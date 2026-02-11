FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /app
ENV UV_HTTP_TIMEOUT=120 \
    UV_HTTP_CONNECT_TIMEOUT=30 \
    UV_HTTP_RETRIES=10

# Install dependencies first (better layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-editable

# Copy source and install project
COPY README.md ./
COPY src/ ./src/
RUN uv sync --locked --no-editable


FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS runtime

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy app
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/src/ /app/src/

EXPOSE 8000

CMD ["waktusolat-mcp-http"]
