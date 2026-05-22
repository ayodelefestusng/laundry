# Builder stage
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install uv binary directly from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies (isolated virtualenv)
RUN uv sync --frozen --no-cache

# Copy source code
COPY . .

# Install build tools only if needed for compiling deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Runtime stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy only the built app + venv from builder
COPY --from=builder /app /app

# Expose port
EXPOSE 8000



CMD ["/app/.venv/bin/gunicorn", "myproject.wsgi:application", "-b", "0.0.0.0:8000"]
