FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/fireball-industries/Small-Application"
LABEL org.opencontainers.image.description="EmberBurn Industrial IoT Gateway"
LABEL maintainer="patrick@fireball-industries.com"

WORKDIR /app

# Install git and build dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc g++ \
    libxml2-dev libxslt-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 emberburn && \
    mkdir -p /app/data && \
    chown -R emberburn:emberburn /app

USER emberburn

EXPOSE 4840 5000 8000

ENV PYTHONUNBUFFERED=1 \
    UPDATE_INTERVAL=2.0 \
    LOG_LEVEL=INFO \
    REPO_URL=https://github.com/fireball-industries/Small-Application.git \
    REPO_BRANCH=main

# Entrypoint script that clones code and runs it
COPY --chown=emberburn:emberburn entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
