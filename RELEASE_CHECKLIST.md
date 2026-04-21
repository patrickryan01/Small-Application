# EmberBurn Release Checklist

Use this checklist every time you cut a new version. Copy/paste the raw markdown into your commit message or PR description and check items off as you go.

---

## 1. Pre-Flight — Verify Before You Touch Anything

- [ ] **Working tree clean** — `git status` shows no uncommitted changes
- [ ] **On `main` branch** — `git branch --show-current` returns `main`
- [ ] **Pulled latest** — `git pull embernet main` (org repo is source of truth)
- [ ] **Reviewed upstream** — No critical Python dependency updates needed for `requirements.txt`

---

## 2. GHCR Image Link Verification

> **Why this exists:** In v3.9.0 we discovered a 403 Forbidden on every image pull.
> The Dockerfile `org.opencontainers.image.source` label pointed to a repo name
> (`Small-Application`) that doesn't exist on the Embernet-ai org — the org repo is
> called `Emberburn`. GHCR uses this label to link packages to repos. Unlinked
> packages default to **private**, causing 403 even though the repo itself is public.

- [ ] **Dockerfile `image.source` label** matches the org repo exactly:
  ```
  LABEL org.opencontainers.image.source="https://github.com/Embernet-ai/Emberburn"
  ```
  If this says `Small-Application` or any other name → **STOP and fix it**.

- [ ] **GHCR package visibility is Public** — verify at:
  https://github.com/orgs/Embernet-ai/packages → `emberburn` → Package settings
  If the package doesn't exist yet (first release), you must set it to Public
  immediately after the first successful workflow run.

- [ ] **Workflow `IMAGE_NAME`** in `.github/workflows/docker-publish.yml` matches:
  ```yaml
  IMAGE_NAME: embernet-ai/emberburn
  ```

---

## 3. Version Bump (replace `X.Y.Z` with new version)

All four locations must have the **same** version string:

| File | Field(s) | Example |
|------|----------|---------|
| `helm/opcua-server/Chart.yaml` | `version`, `appVersion`, `catalog.cattle.io/upstream-version` | `4.0.9` |
| `helm/opcua-server/values.yaml` | `emberburn.image.tag` | `"4.0.9"` |

- [ ] `Chart.yaml` — `version: X.Y.Z`
- [ ] `Chart.yaml` — `appVersion: "X.Y.Z"`
- [ ] `Chart.yaml` — `catalog.cattle.io/upstream-version: "X.Y.Z"`
- [ ] `values.yaml` — `tag: "X.Y.Z"`

---

## 4. EmberNET Template Alignment

> **Added in v4.0.9:** Verify alignment with the canonical EmberNET Helm chart template.

### 4a. Store Labels (The Big Four)

Verify all four labels exist on **pod template** AND **Service (webui)** objects:

| Label | Pod Template | Service |
|-------|-------------|---------|
| `embernet.ai/store-app: "true"` | - [ ] Present | - [ ] Present |
| `embernet.ai/gui-type: "web"` | - [ ] Present | - [ ] Present |
| `embernet.ai/app-name: "emberburn"` | - [ ] Present | - [ ] Present |
| `embernet.ai/gui-port: "5000"` | - [ ] Present | - [ ] Present |

### 4b. Network Configuration

- [ ] `values.yaml` has `network.hostNetwork: false` (dashboard proxy requires ClusterIP networking)
- [ ] `deployment.yaml` has `hostNetwork` / `dnsPolicy` conditional block

### 4c. `_helpers.tpl`

- [ ] `emberburn.storeLabels` helper function exists
- [ ] Used in `deployment.yaml` pod template labels
- [ ] Used in `service-webui.yaml` labels

### 4d. Dashboard Integration

- [ ] Service name uses `{{ .Release.Name }}` directly (required for dashboard FQDN proxy routing)
- [ ] Service selector matches pod selector labels
- [ ] `gui-port` label value is a quoted number (`"5000"`)

---

## 5. Quality Gates

All must pass before committing:

- [ ] **Helm lint** — `helm lint helm/opcua-server` → `0 chart(s) failed`
- [ ] **Helm template** — `helm template test-release helm/opcua-server` renders without errors
- [ ] **Docker build** (optional, CI handles multi-arch) — `docker build -t emberburn:X.Y.Z .`

---

## 6. Helm Chart Packaging (Automated)

> **As of v4.0.9:** The `release.yml` GitHub Actions workflow automatically
> runs `helm package` and `helm repo index` whenever `helm/**` files change
> on `main`. You no longer need to manually package or update `index.yaml`.
> The pipeline chain is: `release.yml` → commits `.tgz` + `index.yaml` → triggers `pages.yml` → deploys to GitHub Pages → Rancher picks up the update.

Manual fallback (only if CI is broken):

- [ ] **Delete old `.tgz`** — `Remove-Item emberburn-*.tgz`
- [ ] **Package** — `helm package helm/opcua-server` (run from repo root)
- [ ] **Regenerate index** — `helm repo index . --url https://embernet-ai.github.io/Emberburn/`
- [ ] **Verify `index.yaml`** — `version:` and `urls:` reference the new `.tgz`

---

## 7. Release Notes

- [ ] Add entry to `RELEASE_NOTES.md` at the top with date and changes
- [ ] **KEEP ONLY PREVIOUS VERSIONS** — Remove the current version entry from `RELEASE_NOTES.md` before committing (release notes document history, not the current release)

---

## 8. Commit, Tag, Push

Order matters — push to the **org remote first** so the CI workflow runs there:

```powershell
git add .
git commit -m "vX.Y.Z: <short description>"
git tag vX.Y.Z
git push embernet main --tags    # ← org repo, triggers CI
git push origin main --tags      # ← personal fork, keeps in sync
```

- [ ] Committed
- [ ] Tagged `vX.Y.Z`
- [ ] Pushed to **`embernet`** remote (Embernet-ai/Emberburn)
- [ ] Pushed to **`origin`** remote (personal fork)

---

## 9. Post-Push Verification

- [ ] **GitHub Actions (Docker)** — check Actions tab, `docker-publish.yml` triggered on `vX.Y.Z` tag
- [ ] **GitHub Actions (Pages)** — check Actions tab, `pages.yml` triggered on `index.yaml` change
- [ ] **Image pull** — `docker pull ghcr.io/embernet-ai/emberburn:X.Y.Z` succeeds (no 403)
- [ ] **GitHub Release** — create one on `Embernet-ai/Emberburn` for tag `vX.Y.Z` if desired
- [ ] **Helm chart** — `helm repo update` shows new version in Rancher catalog

### Post-Deploy Dashboard Verification

- [ ] **App appears in dashboard** — EmberBurn card visible in "Deployed Apps"
- [ ] **"OPEN" button works** — Opens Flask web UI in iframe
- [ ] **Web UI loads** — All pages (Dashboard, Tags, Publishers, Alarms, Config, Tag Generator) load
- [ ] **API endpoints work** — `/api/tags`, `/api/publishers` return data through proxy
- [ ] **OPC UA working** — Port 4840 accessible from other pods
- [ ] **Prometheus metrics** — Port 8000 `/metrics` endpoint returning data

---

## Quick Reference — Git Remotes

| Remote | URL | Purpose |
|--------|-----|---------|
| `embernet` | `https://github.com/Embernet-ai/Emberburn.git` | Org repo — CI runs here |
| `origin` | `https://github.com/patrickryan01/Small-Application.git` | Personal fork |

---

## Quick Reference — Sidecar Proxy

**EmberBurn does NOT need the sidecar proxy.**
Server-rendered Flask app with relative URL paths. Proxy-aware middleware handles URL rewriting natively (since v3.5.8).

---

*EmberBurn — Where Data Meets Fire 🔥*
