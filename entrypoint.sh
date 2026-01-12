#!/bin/bash
set -e

echo "🔥 EmberBurn Industrial IoT Gateway Starting..."

# Clone repository if not already present
if [ ! -d "/app/code/.git" ]; then
    echo "📦 Cloning repository from ${REPO_URL}..."
    git clone --depth 1 --branch ${REPO_BRANCH} ${REPO_URL} /app/code
else
    echo "📦 Repository already cloned, pulling latest..."
    cd /app/code && git pull origin ${REPO_BRANCH}
fi

cd /app/code

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
else
    echo "⚠️  No requirements.txt found, installing common packages..."
    pip install --no-cache-dir opcua paho-mqtt influxdb-client prometheus-client
fi

echo "🚀 Starting EmberBurn..."
exec python main.py
