FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# Copy only dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies using pip directly from pyproject.toml
RUN pip install --no-cache-dir -e .

# ── Runtime image ──────────────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:$PATH"

# psycopg2 runtime lib + PDF/Cairo support (xhtml2pdf/reportlab)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Copy project source
COPY . .

# Build-time environment variables (use dummy values for collectstatic)
ARG SECRET_KEY=build-time-dummy-key
ARG DATABASE_URI=sqlite:///db.sqlite3
ENV SECRET_KEY=${SECRET_KEY}
ENV DATABASE_URI=${DATABASE_URI}

# Create dummy SQLite database for collectstatic
RUN touch db.sqlite3

# Collect static files
RUN python manage.py collectstatic --no-input --clear

EXPOSE 8000

CMD ["gunicorn", "myproject.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120"]
