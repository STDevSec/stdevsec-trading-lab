# STDevsec Trading Lab API image.
FROM python:3.12-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Workspace manifests + sources needed to resolve the api package.
COPY pyproject.toml uv.lock* ./
COPY packages ./packages
COPY apps/api ./apps/api

RUN uv sync --no-dev

EXPOSE 8000
# Apply migrations (from apps/api where alembic.ini lives) then serve.
CMD ["sh", "-c", "cd apps/api && alembic upgrade head && cd /app && uvicorn stdevsec_api.main:app --host 0.0.0.0 --port 8000"]
