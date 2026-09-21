FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.10.6 /uv /usr/local/bin/uv

WORKDIR /app

# Keep dependency installation cacheable while application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY artifacts/ ./artifacts/
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "what_s_price.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
