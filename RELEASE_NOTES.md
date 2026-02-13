# EmberBurn Release Notes

## v4.0.5 — 2026-02-13

### Fix: Docker tags only from tagged releases

- **Fixed** Docker metadata to stop generating a `main` branch tag that raced with the versioned tag build
- **Removed** `type=ref,event=branch` and `type=ref,event=pr` from workflow metadata — only semver tags are generated now
- **Changed** `latest` condition to explicitly require a `v*` tag ref instead of `is_default_branch`
- **Result**: Pushing a `v*` tag now produces only `X.Y.Z`, `X.Y`, and `latest` — no more phantom `main` image
- **Chart version**: `4.0.5`, appVersion: `4.0.5`
- Image tag: `ghcr.io/embernet-ai/emberburn:4.0.5`
- Helm chart: `https://embernet-ai.github.io/Emberburn/emberburn-4.0.5.tgz`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v4.0.5` tag

---

## v4.0.4 — 2026-02-12

### Cleanup: Remove broken releases, fix workflow triggers

- **Removed** old broken releases (v4.0.1, v4.0.2, v4.0.3) and their tgz files from the repo
- **Cleaned** index.yaml to only contain the current version
- **Docker workflow** now only triggers on `v*` tags and `workflow_dispatch` — no more branch pushes or release events causing racing builds
- **Note**: CodeQL "Push on main" and built-in "pages build and deployment" are GitHub repo settings — disable CodeQL in Settings > Code Security, and set Pages source to "GitHub Actions" in Settings > Pages
- **Chart version**: `4.0.4`, appVersion: `4.0.4`
- Image tag: `ghcr.io/embernet-ai/emberburn:4.0.4`
- Helm chart: `https://embernet-ai.github.io/Emberburn/emberburn-4.0.4.tgz`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v4.0.4` tag

---

## v4.0.3 — 2026-02-12

### Fix: Workflow triggers causing image overwrites

- **Root cause**: Docker build workflow triggered on `push to main`, `v* tags`, AND `release published` — causing 3 simultaneous builds that raced and overwrote the working `latest` manifest with a broken one
- **Fix**: Stripped workflow down to only trigger on `v*` tags and `workflow_dispatch`. No more branch push or release event builds.
- **Chart version**: `4.0.3`, appVersion: `4.0.3`
- Image tag: `ghcr.io/embernet-ai/emberburn:4.0.3`
- Helm chart: `https://embernet-ai.github.io/Emberburn/emberburn-4.0.3.tgz`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v4.0.3` tag

---

## v4.0.2 — 2026-02-12

### Fix: Image tag 4.0.1 never published — 403 on pull

- **Root cause**: Chart.yaml and values.yaml were bumped to `4.0.1` but no `v4.0.1` git tag was pushed, so no container image was built. GHCR returns 403 (not 404) for non-existent tags on public repos, making it look like an auth issue.
- **Fix**: Bumped all versions to `4.0.2`, will push `v4.0.2` git tag to trigger GitHub Actions multi-arch build
- **Chart version**: `4.0.2`, appVersion: `4.0.2`
- Image tag: `ghcr.io/embernet-ai/emberburn:4.0.2`
- Helm chart: `https://embernet-ai.github.io/Emberburn/emberburn-4.0.2.tgz`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v4.0.2` tag

---

## v4.0.0 — 2026-02-12

### Major Release: Complete Helm Chart + Container Image

- **Breaking**: Major version bump to signal production-ready release
- **Helm Chart**: Packaged tarball with proper index.yaml for Helm repository
- **Container Image**: Multi-arch (amd64/arm64) build with working GHCR permissions
- **Workflow**: Cleaned permissions - no attestation features causing private package defaults
- **Chart version**: `4.0.0`, appVersion: `4.0.0`
- Image tag: `ghcr.io/embernet-ai/emberburn:4.0.0`
- Helm chart: `https://embernet-ai.github.io/Emberburn/emberburn-4.0.0.tgz`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v4.0.0` tag

---

## v3.10.4 — 2026-02-12

### Fix: ImagePullBackOff / 403 Forbidden (Final Fix)

- **Root cause**: Workflow still had `id-token: write` and `attestations: write` permissions even though attestation step was disabled. GHCR treats packages with attestation permissions as "security-sensitive" and defaults them to **private** visibility on every new tag.
- **Fix**: Removed `id-token: write` and `attestations: write` permissions from workflow entirely. Only `contents: read` and `packages: write` remain.
- **Manual action still required**: Until GitHub fixes this behavior, new tags may still default to private. Set package visibility to Public at: `https://github.com/orgs/Embernet-ai/packages/container/emberburn/settings`
- Image tag: `ghcr.io/embernet-ai/emberburn:3.10.4`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.10.4` tag

---

## v3.10.3 — 2026-02-12 ⚠️ FAILED

### Updates

- Clean release to verify attestation fix from v3.10.2
- **Result**: Still got 403 Forbidden - attestation permissions caused private package visibility
- Image tag: `ghcr.io/embernet-ai/emberburn:3.10.3` (requires manual public toggle)
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.10.3` tag

---

## v3.10.2 — 2026-02-12

### Fix: ImagePullBackOff / 403 Forbidden on GHCR (Again)

- **Root cause**: `actions/attest-build-provenance@v1` with `push-to-registry: true` creates a **separate SHA-tagged manifest** before the semver-tagged manifest. GHCR links the SHA manifest as a distinct image with private permissions, causing 403 when K8s tries to pull the semver tag that resolves to the SHA digest.
- **Fix**: Disabled attestation step in workflow. Attestations are useful for supply chain security but break GHCR image pulls.
- **Evidence**: Two manifests in GHCR for same digest - one with `sha256-...` tag (0 downloads, private), one with `3.10.2`/`latest` tags (1 download, works after manual public toggle).
- Image tag: `ghcr.io/embernet-ai/emberburn:3.10.2`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.10.2` tag

---

## v3.10.1 — 2026-02-12

### Fix: ImagePullBackOff / 403 Forbidden on GHCR

- **Root cause**: `docker-publish.yml` metadata-action included `type=sha`, generating SHA-digest tags (e.g., `sha-02870d...`). When workflow was triggered by branch push instead of semver tag, only SHA/branch tags were pushed — no `3.10.0` version tag existed in GHCR, causing 403 on pull.
- **Fix**: Removed `type=sha` from `docker/metadata-action` tag rules. Only semver, branch, PR, and `latest` tags are now generated.
- Image tag: `ghcr.io/embernet-ai/emberburn:3.10.1`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.10.1` tag

---

## v3.10.0 — 2026-02-11

### UI Fixes

- **Fixed**: Navbar logo showed broken Embernet image inside dashboard iframe. Replaced with `emberburn-chart-icon.png` — EmberBurn now uses its own branding, not the Embernet parent logo.
- **Fixed**: Dashboard showed "Loading tag data..." when 0 tags are running. Now shows "No tags configured".
- **Fixed**: Publishers, Alarms, and Config pages stuck on infinite loading spinner when accessed through the Embernet Dashboard iframe proxy.
  - **Root cause**: `api.js` used absolute path `/api` for fetch calls. The proxy URL rewriter in `publishers.py` only rewrites `text/html` responses — `api.js` is served as `application/javascript` so its paths were never rewritten. All API calls hit the dashboard host instead of routing through the proxy.
  - **Fix**: Changed `API_BASE` from `/api` (absolute) to `api` (relative). Browser resolves relative URLs against current page URL, which already includes the proxy prefix.
- Image tag: `ghcr.io/embernet-ai/emberburn:3.10.0`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.10.0` tag

---

## v3.9.0 — 2026-02-11

### Fix: GHCR 403 Forbidden (Image Pull Failure)

- **Root cause**: Dockerfile `org.opencontainers.image.source` label pointed to `Embernet-ai/Small-Application` (non-existent). GHCR uses this label to link packages to repositories — unlinked packages default to **private**, causing 403 on pull.
- **Fix**: Corrected label to `https://github.com/Embernet-ai/Emberburn` (the actual org repo name).
- **Action required**: GHCR package visibility must be set to **Public** via org package settings after first successful build.
- Image tag: `ghcr.io/embernet-ai/emberburn:3.9.0`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.9.0` tag

---

## v3.5.8 — 2026-02-10

### Feature: Proxy-Aware Static Asset Loading

- **Problem**: When loaded inside the Embernet Dashboard iframe via `/api/proxy`, CSS/JS/images failed to load because absolute paths (`/static/web/...`) resolved against the dashboard domain.
- **Fix**: Added `after_request` middleware in `publishers.py` that detects reverse proxy (`X-Forwarded-For` header) and rewrites all `href`/`src`/`fetch()` paths to route through `/api/proxy?target=http://PodIP:5000/...`.
- Direct access (no proxy) is unaffected — rewriting only activates when proxied.

---

## v3.5.7 — 2026-02-10

### Critical Fix: Server Killing Itself on Startup

- **Root cause**: Shutdown logic (`stop_all()`, `server.stop()`) was inside `_setup_transformation_callback()` instead of `shutdown()`. Called during init → Flask and OPC UA died immediately after starting.
- **Fix**: Moved all stop/shutdown code into `shutdown()` method where it belongs.
- Flask (5000) and OPC UA (4840) now stay alive after initialization.
- Added Troubleshooting section to `NETWORKING_GUIDE.md`.

---

## v3.5.6 — 2026-02-10

### Hotfix: "Launch UI" Proxies to Wrong Port

- **Root cause**: Dashboard picks the **first** `containerPort` for "Launch UI" reverse proxy. `opcua` (4840) was listed before `webui` (5000), so the dashboard proxied to OPC UA binary protocol → `connection refused`.
- **Fix**: Reordered ports in `deployment.yaml` — `webui` (5000) is now **first**.
- Added `CAUTION` block + multi-port example to `NETWORKING_GUIDE.md` Section 2d.

---

## v3.5.5 — 2026-02-10

### Hotfix: CrashLoopBackOff

- **Root cause**: Liveness/readiness probes targeted OPC UA port `4840`, which is slow to bind during container startup (tag loading, protocol initialization). K8s killed the container before OPC UA finished starting.
- **Fix**: Probes now target Flask web UI port `5000` (starts instantly, reliable liveness indicator).
- Liveness: `initialDelaySeconds: 45`, `failureThreshold: 6` (more startup headroom).
- **All container ports unchanged**: `4840` (OPC UA), `5000` (WebUI), `8000` (Prometheus) — industrial protocol data still flows on all ports.

---

## v3.5.4 — 2026-02-10

### Hotfix

- **Fixed**: `embernet.io/app-icon` label used emoji `🔥` which is not a valid Kubernetes label value (must be alphanumeric, `-`, `_`, `.`). Changed to `"fire"`.
- **Fixed**: Added `release: types: [published]` trigger to `docker-publish.yml` so GitHub Releases created through the UI fire the container build workflow.
- Chart version: `3.5.4`, appVersion: `3.5.4`
- Image tag: `ghcr.io/embernet-ai/emberburn:3.5.4`

---

## v3.5.3 — 2026-02-10

### 🔥 Highlights

**Embernet UI Redesign** — Complete visual overhaul matching the Embernet Industrial Dashboard design language.  
**OPC UA Tag Generator** — New feature for creating, managing, importing, and exporting OPC UA tags.  
**Helm Chart Fixes** — Corrected index URL, added chart icon, cleaned stale packages.

---

### UI Redesign

- Replaced sidebar navigation with horizontal header (logo, nav links, dark mode toggle, company logo)
- Dark mode is now the default; light mode toggle via localStorage
- Migrated entire CSS from fire/orange theme to Embernet red palette (`--ember-red: #E31837`)
- Added Inter font (Google Fonts), responsive breakpoints at 768px
- Status footer with OPC UA connection indicator and version display
- All 6 page templates updated (`index`, `tags`, `alarms`, `publishers`, `config`, `tag-generator`)

### OPC UA Tag Generator

- **New page** at `/tag-generator` with stat cards, quick actions, and searchable tag table
- **Create tags** with full metadata: name, data type, initial value, units, category, simulation, alarm config
- **Delete tags** with confirmation dialog
- **Write values** to live tags via modal
- **Bulk import** from CSV or JSON files with preview table
- **Export** all tags as CSV or JSON
- **3 built-in templates** for rapid tag setup:
  - 3-Phase Motor (9 tags: current, voltage, power, RPM, temp, vibration, run status, fault, hours)
  - Tank Level (7 tags: level, flow in/out, temp, pressure, high/low alarms)
  - Conveyor (6 tags: speed, running, jam, items counted, motor temp, belt tension)

### Backend API

New REST endpoints in `publishers.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tags/create` | POST | Create a tag with type conversion and metadata |
| `/api/tags/<name>` | DELETE | Delete a tag from cache and metadata |
| `/api/tags/bulk` | POST | Bulk create with per-tag error reporting |
| `/api/tags/export` | GET | Export as JSON or CSV (`?format=csv`) |

### Helm Chart

- Added `embernet.io/app-icon` label to pod template
- Chart icon set to Embernet GitHub org avatar
- Added `emberburn-chart-icon.png` asset
- Fixed `index.yaml` URL to `https://embernet-ai.github.io/Emberburn/`
- Fixed `sources` in `Chart.yaml` to point to `Embernet-ai/Emberburn`
- Image tag pinned, pullPolicy set to `IfNotPresent`

### Container Image

- Built and tagged as `ghcr.io/embernet-ai/emberburn:3.5.3`
- Multi-arch build (amd64/arm64) via GitHub Actions on `v3.5.3` tag
- Base image: `python:3.11-slim`

### Artwork Assets

- `embernet-white.png` — Header logo (dark mode)
- `embernet.png` — Header logo (light mode)
- `fireball.png` — Company logo
- `favicon-32x32.png` — Browser tab icon
- `emberburn-chart-icon.png` — Helm chart catalog icon

---

### Bug Fixes (v3.5.1 → v3.5.4)

- **v3.5.1**: Added actual Embernet artwork assets (replaced empty placeholders)
- **v3.5.2**: Fixed GZIP invalid header caused by `index.yaml` pointing to wrong GitHub Pages domain
- **v3.5.3**: Fixed `index.yaml` URL to correct org repo (`Embernet-ai/Emberburn`), fixed `sources` in `Chart.yaml`
- **v3.5.4**: Fixed invalid K8s label (emoji not allowed), added `release` event trigger to GitHub Actions workflow

---

*EmberBurn — Where Data Meets Fire 🔥*  
*Fireball Industries × Embernet*
