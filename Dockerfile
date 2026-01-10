# Dockerfile for OPC UA Multi-Protocol Server
# Because containerizing 15 protocols is totally normal behavior
# 
# Author: Patrick Ryan, Fireball Industries
# "I containerized it so you don't have to"

FROM python:3.11-slim

LABEL maintainer="Patrick Ryan <patrick@fireballindustries.com>"
LABEL description="OPC UA Server with 15 protocols because we have issues"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
# (Yes, we need build tools for some of these Python packages)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# (This is where we find out which packages don't play nice with ARM64)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data /app/config /app/logs

# Expose ports
# 4840 - OPC UA Server (the main event)
# 5000 - REST API / Web UI (the pretty dashboard)
# 8000 - Prometheus metrics (for the monitoring nerds)
EXPOSE 4840 5000 8000

# Health check
# (Because K8s will restart us if we're dead)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost',4840)); s.close()" || exit 1

# Environment variables with sensible defaults
ENV UPDATE_INTERVAL=2.0 \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Run as non-root user (security best practice)
RUN useradd -m -u 1000 opcua && \
    chown -R opcua:opcua /app
USER opcua

# Default command
# (Override with ConfigMap if you want different configs)
CMD ["python", "opcua_server.py", "-c", "config/config_transformations_demo.json", "-l", "${LOG_LEVEL}"]
