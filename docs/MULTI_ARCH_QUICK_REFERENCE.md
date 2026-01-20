# Multi-Architecture Build Quick Reference

## Quick Commands

### Pull and Run (Any Platform)
```bash
# Docker automatically selects the correct architecture
docker pull ghcr.io/fireball-industries/emberburn:latest
docker run -p 4840:4840 -p 5000:5000 -p 8000:8000 \
  ghcr.io/fireball-industries/emberburn:latest
```

### Build Multi-Arch (Linux/Mac)
```bash
# Using included script
bash scripts/build-multi-arch.sh --push --tag 1.0.0

# Manual buildx
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myregistry.com/emberburn:1.0.0 \
  --push .
```

### Build Multi-Arch (Windows PowerShell)
```powershell
# Using included script
.\scripts\build-multi-arch.ps1 -Push -Tag 1.0.0

# Manual buildx
docker buildx build --platform linux/amd64,linux/arm64 `
  -t myregistry.com/emberburn:1.0.0 `
  --push .
```

### Platform-Specific Builds
```bash
# ARM64 only
docker buildx build --platform linux/arm64 \
  -t myregistry.com/emberburn:arm64 --push .

# AMD64 only
docker buildx build --platform linux/amd64 \
  -t myregistry.com/emberburn:amd64 --push .
```

### Verify Architecture
```bash
# Check image architecture
docker image inspect ghcr.io/fireball-industries/emberburn:latest | grep Architecture

# Check manifest
docker buildx imagetools inspect ghcr.io/fireball-industries/emberburn:latest
```

## Kubernetes Deployment

### ARM64 Node Selector
```yaml
nodeSelector:
  kubernetes.io/arch: arm64
```

### Mixed Architecture Cluster
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/arch
          operator: In
          values:
          - arm64  # or amd64
```

## Supported Platforms

- ✅ **linux/amd64** - x86-64 (Intel/AMD)
- ✅ **linux/arm64** - ARM 64-bit (Raspberry Pi, AWS Graviton, Apple Silicon)

## Build Script Options

### Bash Script (`build-multi-arch.sh`)
```bash
--push              # Push to registry
--tag TAG           # Custom tag (default: latest)
--registry REG      # Registry URL (default: ghcr.io/fireball-industries)
--platforms PLAT    # Platforms (default: linux/amd64,linux/arm64)
--load              # Load to local Docker (single platform)
--dry-run           # Show commands without executing
```

### PowerShell Script (`build-multi-arch.ps1`)
```powershell
-Push              # Push to registry
-Tag TAG           # Custom tag (default: latest)
-Registry REG      # Registry URL (default: ghcr.io/fireball-industries)
-Platforms PLAT    # Platforms (default: linux/amd64,linux/arm64)
-Load              # Load to local Docker (single platform)
-DryRun            # Show commands without executing
```

## Common Use Cases

### Raspberry Pi Deployment
```bash
docker pull ghcr.io/fireball-industries/emberburn:latest
docker run -d --restart unless-stopped \
  -p 4840:4840 -p 5000:5000 -p 8000:8000 \
  -v /opt/emberburn/data:/app/data \
  ghcr.io/fireball-industries/emberburn:latest
```

### AWS Graviton (ECS Fargate)
```json
"runtimePlatform": {
  "cpuArchitecture": "ARM64",
  "operatingSystemFamily": "LINUX"
}
```

### K3s on ARM64
```bash
helm install emberburn ./helm/opcua-server \
  --set nodeSelector."kubernetes\.io/arch"=arm64
```

## Troubleshooting

### Exec Format Error
```bash
# Force specific platform
docker pull --platform linux/arm64 ghcr.io/fireball-industries/emberburn:latest
```

### Setup Multi-Arch Builder
```bash
# Linux/Mac
docker buildx create --name multi-arch --driver docker-container --bootstrap
docker buildx use multi-arch

# Enable QEMU
docker run --privileged --rm tonistiigi/binfmt --install all
```

### Check Available Builders
```bash
docker buildx ls
```

## GitHub Actions (Automatic)

Builds are **automatically triggered** on:
- ✅ Push to `main`/`master` → Build and push `latest`
- ✅ Create tag `v*` → Build and push versioned release
- ✅ Pull request → Build validation only

**No manual intervention needed!** Just push code and images are built for both architectures.

## Documentation

- Full Guide: [docs/ARM64_DEPLOYMENT.md](ARM64_DEPLOYMENT.md)
- Kubernetes: [../KUBERNETES_DEPLOYMENT.md](../KUBERNETES_DEPLOYMENT.md)
- Docker Build: [../helm/opcua-server/DOCKER-BUILD-GUIDE.md](../helm/opcua-server/DOCKER-BUILD-GUIDE.md)
