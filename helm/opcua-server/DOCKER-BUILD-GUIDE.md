# EmberBurn Docker Build Guide

**Repository:** https://github.com/fireball-industries/Small-Application (renamed to EmberBurn)

## Step 1: Add Dockerfile to Python Repository

Create `Dockerfile` in the root of https://github.com/fireball-industries/Small-Application:

```dockerfile
# EmberBurn - Multi-Protocol Industrial IoT Gateway
# Fireball Industries - "Where Data Meets Fire"

FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/fireball-industries/Small-Application"
LABEL org.opencontainers.image.description="EmberBurn Industrial IoT Gateway - OPC UA, MQTT, Modbus, and 15+ protocols"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintainer="Patrick Ryan <patrick@fireballindustries.com>"

# Set working directory
WORKDIR /app

# Install system dependencies for OPC UA and Modbus
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite and logs
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash emberburn && \
    chown -R emberburn:emberburn /app

# Switch to non-root user
USER emberburn

# Expose ports
EXPOSE 4840  # OPC UA Server
EXPOSE 5000  # REST API + Web UI
EXPOSE 8000  # Prometheus metrics
EXPOSE 5020  # Modbus TCP (optional)
EXPOSE 9001  # WebSocket (optional)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 4840)); s.close()" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UPDATE_INTERVAL=2.0 \
    LOG_LEVEL=INFO

# Run the application
CMD ["python", "main.py"]
```

## Step 2: Add .dockerignore

Create `.dockerignore` in the root:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
ENV/
.git
.gitignore
.vscode/
.idea/
*.md
!README.md
.DS_Store
data/*.db
data/*.log
```

## Step 3: GitHub Actions Workflow (Already Configured! ✅)

The repository already includes a **multi-architecture GitHub Actions workflow** that automatically builds for AMD64 and ARM64!

**File**: `.github/workflows/docker-publish.yml`

**Features**:
- ✅ Multi-architecture builds (AMD64 + ARM64)
- ✅ QEMU emulation for cross-platform builds
- ✅ Build caching for faster builds
- ✅ SBOM (Software Bill of Materials) generation
- ✅ Build attestation and provenance
- ✅ Automatic tagging (latest, semver, branch, SHA)
- ✅ Pull request validation

**Platforms Supported**:
- `linux/amd64` - Traditional x86-64 servers, Intel/AMD processors
- `linux/arm64` - ARM64/aarch64 (Raspberry Pi 4+, AWS Graviton, Apple Silicon, NVIDIA Jetson)

**Automatic Triggers**:
- Push to `main` or `master` branch → Build and push `latest`
- Create tag `v*` → Build and push versioned release
- Pull request → Build only (validation, no push)
- Manual workflow dispatch → On-demand builds

The workflow is **production-ready** and requires no additional configuration!

## Step 4: Manual Build Options

```yaml
name: Build and Push EmberBurn Docker Image

on:
  push:
    branches:
      - main
      - master
    tags:
      - 'v*'
  pull_request:
    branches:
      - main
      - master
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: fireball-industries/emberburn

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

## Step 4: Manual Build & Push (Alternative)

If you prefer to build and push manually:

```powershell
# Clone the Python repo
cd C:\Users\Admin\Documents\GitHub
git clone https://github.com/fireball-industries/Small-Application.git emberburn
cd emberburn

# Login to GitHub Container Registry
$env:CR_PAT = "your_github_personal_access_token"
echo $env:CR_PAT | docker login ghcr.io -u fireball-industries --password-stdin

# Build the image (multi-platform)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/fireball-industries/emberburn:latest \
  -t ghcr.io/fireball-industries/emberburn:1.0.0 \
  --push .

# Or build for single platform (faster for testing)
docker build -t ghcr.io/fireball-industries/emberburn:latest .
docker push ghcr.io/fireball-industries/emberburn:latest
```

## Step 5: Update Helm Chart Image Reference

The Helm chart is already configured to use the correct image:

```yaml
# charts/emberburn/values.yaml (already set correctly)
emberburn:
  image:
    repository: ghcr.io/fireball-industries/emberburn  # ✅ Correct!
    tag: "1.0.0"
    pullPolicy: IfNotPresent
```

## Step 6: Verify Image

```bash
# Pull and test the image
docker pull ghcr.io/fireball-industries/emberburn:latest
docker run -p 4840:4840 -p 5000:5000 -p 8000:8000 \
  ghcr.io/fireball-industries/emberburn:latest

# Test OPC UA endpoint
curl http://localhost:4840

# Test Web UI
curl http://localhost:5000

# Test Prometheus metrics
curl http://localhost:8000/metrics
```

## Step 7: Deploy to K3s

```bash
# Install EmberBurn chart
helm install emberburn ./charts/emberburn \
  --namespace emberburn \
  --create-namespace

# Check deployment
kubectl get pods -n emberburn
kubectl logs -n emberburn -l app.kubernetes.io/name=emberburn

# Access Web UI (via LoadBalancer or Ingress)
kubectl get svc -n emberburn
```

---

## Troubleshooting

### Image Pull Error

If you see `ImagePullBackOff`:

1. **Make the GitHub Package public:**
   - Go to: https://github.com/orgs/fireball-industries/packages
   - Find `emberburn` package
   - Settings → Change visibility → Public

2. **Or add imagePullSecrets:**
   ```bash
   kubectl create secret docker-registry ghcr-secret \
     --docker-server=ghcr.io \
     --docker-username=fireball-industries \
     --docker-password=<your-github-token> \
     --namespace=emberburn
   
   # Update values.yaml:
   pod:
     imagePullSecrets:
       - name: ghcr-secret
   ```

### Application Not Starting

Check logs:
```bash
kubectl logs -n emberburn -l app.kubernetes.io/name=emberburn --tail=100
```

Common issues:
- Missing `main.py` in repo root
- Missing dependencies in `requirements.txt`
- Incorrect Python version

### Port Conflicts

If ports are already in use:
```yaml
# values.yaml
emberburn:
  ports:
    opcua: 4841      # Changed from 4840
    webui: 5001      # Changed from 5000
    prometheus: 8001 # Changed from 8000
```

---

## File Checklist for Python Repository

Add these files to https://github.com/fireball-industries/Small-Application:

- [ ] `Dockerfile` (see Step 1)
- [ ] `.dockerignore` (see Step 2)
- [ ] `.github/workflows/docker-publish.yml` (see Step 3)
- [ ] `requirements.txt` (should already exist)
- [ ] `main.py` (should already exist - entry point)
- [ ] `README.md` (update with EmberBurn branding)

Once pushed, GitHub Actions will automatically build and publish the Docker image!

---

**Fireball Industries - We Play With Fire So You Don't Have To™**
