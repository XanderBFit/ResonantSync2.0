# --- Frontend Build Stage ---
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Backend Dependencies Stage ---
FROM python:3.11-slim-bookworm AS backend-builder
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential python3-dev
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Final Runtime Stage ---
FROM python:3.11-slim-bookworm

# Security Hardening: Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Runtime deps and system upgrades
RUN apt-get update && apt-get install -y ffmpeg && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy backend deps
COPY --from=backend-builder /root/.local /home/appuser/.local

# Copy backend code (backend/static/ is excluded via .dockerignore)
COPY backend/ .

# Always copy fresh frontend build last - this is the authoritative static content
COPY --from=frontend-builder /app/frontend/dist ./static

# Ensure ownership and permissions
RUN chown -R appuser:appuser /app

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
