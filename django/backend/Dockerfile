# ---------------------------------------------------------------------------
# Stage 1: builder – install build deps and compile wheels
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

ARG REQUIREMENTS=local.txt
COPY requirements/ /tmp/requirements/

RUN pip install --no-cache-dir --prefix=/wheels -r /tmp/requirements/${REQUIREMENTS}

# ---------------------------------------------------------------------------
# Stage 2: runner – lean runtime image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder
COPY --from=builder /wheels /usr/local

# Create non-root user
RUN groupadd -g 1000 django && \
    useradd -u 1000 -g django -m -s /bin/bash django

WORKDIR /app

# Copy application code
COPY . /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Own the app directory
RUN chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
