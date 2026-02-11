# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-editable

# Copy source and install project
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
