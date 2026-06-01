# Changelog

All notable changes to EmberBurn Industrial IoT Gateway will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.8] - 2026-04-27 — App Store Deployment Flow Alignment

Align the chart end-to-end with `APP_STORE_DEPLOYMENT_FLOW.md`. The chart was
already mostly conformant (Service named `{{ .Release.Name }}`, the Big Four
`embernet.ai/*` labels on pod template + Service, FQDN proxy pattern, no
subdomain). This release closes the remaining gaps.

### Fixed
- **values.yaml:** `embernet.appIcon` default was a bare filename
  (`fireball.png`), which produced an invalid `embernet.ai/app-icon` annotation
  — the doc requires a full URL. Changed default to `""` so the
  `service-webui.yaml` URL fallback (the GitHub avatar) is rendered.
- **values.yaml:** `network.hostNetwork` default reverted to `false` per
  `AUDIT_HELM_CHARTS.md` §5 (Multi-Instance Compatibility). `hostNetwork: true`
  turns every containerPort into a host port and collides on the second
  instance on the same node, breaking App Store multi-instance deployment.
- **NOTES.txt §10:** Was reading `embernet.guiType` while `_helpers.tpl`
  `storeLabels` reads `gui.type`/`gui.port`. Realigned NOTES.txt to read the
  same values that drive the discovery labels.

### Changed
- **NOTES.txt §1:** Lead with the App Store proxy path
  (`/api/proxy?target=http://{release}.{ns}.svc.cluster.local:{port}`) and
  demote the ingress/NodePort/port-forward variants to "Direct access (advanced)".
  Matches the doc's stance: App Store apps need no URL, ingress, or DNS record.
- **NOTES.txt §10:** Now prints the full FQDN proxy target so operators can
  verify the URL the dashboard's iframe will load.
- **values.yaml:** Added comment clarifying that `embernet.guiType` is kept for
  backward compat but `gui.type`/`gui.port` are the canonical inputs to the
  store-discovery labels.

## [4.1.7] - 2026-04-24 — App Store Deployment Alignment

### Changed
- **_helpers.tpl:** Standardized `app.kubernetes.io/name` to use chart name identity.
- **_helpers.tpl:** Updated `embernet.ai/app-name` to use "EmberBurn" branding and made it configurable via `.Values.embernet.appName`.
- **service-webui.yaml:** Made `embernet.ai/app-icon` annotation dynamic via `.Values.embernet.appIcon`.

## [4.1.5] - 2026-04-24 — Dashboard Routing Fix

### Fixed
- **service-webui.yaml:** Updated `flux.embernet.ai/service-name` annotation to default to `{{ .Release.Name }}` instead of `{{ .Chart.Name }}`. This resolves the 404 "Service Not Found" error in EmberNET Dashboard V4.0.7 by ensuring the proxy URL targets the actual Kubernetes service name.

---

## [4.1.2] - 2026-04-21 — Documentation & Template Alignment

### Fixed
- **NOTES.txt:** Updated all service name references from `{{ fullname }}` to `{{ .Release.Name }}` to match the actual service templates (service-webui, service-opcua, service-prometheus)
- **RELEASE_CHECKLIST.md:** Corrected stale `hostNetwork: true` guidance → `hostNetwork: false` (dashboard proxy requires ClusterIP networking)
- **RELEASE_CHECKLIST.md:** Updated service naming description to reference `{{ .Release.Name }}` directly instead of fullname helper

---

## [4.1.0] - 2026-04-17 — Dashboard Alignment & Multi-Instance Support

### ⚠️ BREAKING — Selector Label Change
- **`app` label changed:** `{{ fullname }}` → `{{ .Chart.Name }}` in `_helpers.tpl`
  - All instances now share `app: emberburn` for grouping
  - `app.kubernetes.io/instance` distinguishes individual releases
  - **Existing deployments must be deleted and reinstalled** (`helm uninstall` + `helm install`) — Kubernetes does not allow updating immutable `matchLabels` selectors in-place

### Fixed
- **Service names:** All services now use `{{ .Release.Name }}` as the base instead of `{{ fullname }}`
  - WebUI service: `<release-name>` (was `<release-name>-emberburn`)
  - OPC UA service: `<release-name>-opcua` (was `<release-name>-emberburn-opcua`)
  - Prometheus service: `<release-name>-metrics` (was `<release-name>-emberburn-metrics`)
  - **This fixes dashboard FQDN proxy routing** — the "OPEN" button now resolves correctly
- **Ingress backend:** Updated to reference new webui service name
- **Deployment strategy:** Added `strategy.type: Recreate` to prevent scheduling deadlock when using `hostNetwork: true` with a RWO PersistentVolumeClaim

### Multi-Instance Deployment
Multiple Emberburn instances can now be deployed simultaneously:
```bash
helm install emberburn-plant-a helm/opcua-server -n plant-a --create-namespace
helm install emberburn-plant-b helm/opcua-server -n plant-b --create-namespace
```
Each instance gets unique services, PVCs, and ConfigMaps while sharing the `app: emberburn` identity label.

---

## [Unreleased]

### Added
- **Multi-Architecture Support** - Native ARM64/aarch64 Docker images
  - Automatic multi-arch builds via GitHub Actions (AMD64 + ARM64)
  - Support for Raspberry Pi 4/5 deployment
  - AWS Graviton instance support
  - Apple Silicon (M1/M2/M3) compatibility
  - NVIDIA Jetson support
  - ARM-based server support (Ampere Altra, etc.)
- Build scripts for multi-architecture Docker builds
  - `scripts/build-multi-arch.sh` (Linux/macOS)
  - `scripts/build-multi-arch.ps1` (Windows PowerShell)
- Comprehensive ARM64 deployment documentation
  - [docs/ARM64_DEPLOYMENT.md](docs/ARM64_DEPLOYMENT.md)
  - [docs/MULTI_ARCH_QUICK_REFERENCE.md](docs/MULTI_ARCH_QUICK_REFERENCE.md)
- Enhanced GitHub Actions CI/CD pipeline
  - QEMU setup for cross-platform builds
  - Build caching for faster builds
  - SBOM (Software Bill of Materials) generation
  - Build attestation and provenance
  - Enhanced metadata tagging (semver, branch, SHA)

### Changed
- Enhanced `.dockerignore` for smaller, optimized Docker images (~40% size reduction)
- Updated GitHub Actions workflow to build for multiple architectures
- Updated deployment documentation with ARM64 examples
- Improved build process with better caching

### Performance
- ARM64 images are ~3% smaller than AMD64 images
- AWS Graviton instances show ~10% better performance than equivalent x86 instances
- 20-40% cost savings when using AWS Graviton vs traditional x86 instances

### Documentation
- Updated README with multi-architecture feature announcement
- Updated KUBERNETES_DEPLOYMENT with ARM64 deployment instructions
- Updated DOCKER-BUILD-GUIDE with multi-arch build examples
- Added ARM64_IMPLEMENTATION_SUMMARY with complete technical details

## [1.0.0] - 2026-01-XX

### Added
- Initial release of EmberBurn Industrial IoT Gateway
- OPC UA Server with customizable tags
- Multi-protocol support (15 protocols)
  - MQTT, Sparkplug B, REST API, WebSocket
  - Kafka, AMQP, Modbus TCP, GraphQL
  - InfluxDB, Prometheus, SQLite
- Web-based configuration UI (Python Flask)
- Data transformation engine
- Alarm and notification system
- Kubernetes/Helm deployment support
- Docker containerization
- Comprehensive documentation

### Features
- Multiple simulation modes (random, sine, increment, static)
- Multi-protocol data publishing
- Tag discovery API
- Historical data persistence
- Metrics and monitoring
- RBAC and multi-tenancy support

---

## Version Numbering

- **Major** version: Breaking changes or major new features
- **Minor** version: New features, backwards compatible
- **Patch** version: Bug fixes, documentation updates

## Links

- [GitHub Repository](https://github.com/fireball-industries/Small-Application)
- [Documentation](https://fireballz.ai/emberburn)
- [Docker Images](https://ghcr.io/fireball-industries/emberburn)
