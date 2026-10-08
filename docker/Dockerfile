# Phase 13 - Containerized Development
# Multi-stage secure Dockerfile

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Create a non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY backend/app ./app
# Ensure database directory is writable by non-root user
RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data
ENV DATABASE_URL="sqlite:////app/data/waste_management.db"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck (Native Python standard library, removing need for curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/bins', timeout=3)" || exit 1

# Run the application securely
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-max-requests", "1000"]
