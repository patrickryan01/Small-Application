# EmberBurn Release Checklist

Use this checklist every time you cut a new version. Copy/paste the raw markdown into your commit message or PR description and check items off as you go.

---

## 1. Pre-Flight — Verify Before You Touch Anything

- [ ] **Working tree clean** — `git status` shows no uncommitted changes
- [ ] **On `main` branch** — `git branch --show-current` returns `main`
- [ ] **Pulled latest** — `git pull embernet main` (org repo is source of truth)

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
| `helm/opcua-server/Chart.yaml` | `version`, `appVersion`, `catalog.cattle.io/upstream-version` | `3.9.0` |
| `helm/opcua-server/values.yaml` | `emberburn.image.tag` | `"3.9.0"` |

- [ ] `Chart.yaml` — `version: X.Y.Z`
- [ ] `Chart.yaml` — `appVersion: "X.Y.Z"`
- [ ] `Chart.yaml` — `catalog.cattle.io/upstream-version: "X.Y.Z"`
- [ ] `values.yaml` — `tag: "X.Y.Z"`

---

## 4. Quality Gates

All must pass before committing:

- [ ] **Helm lint** — `helm lint helm/opcua-server` → `0 chart(s) failed`
- [ ] **Docker build** (optional, CI handles multi-arch) — `docker build -t emberburn:X.Y.Z .`

---

## 5. Helm Chart Packaging

- [ ] **Delete old `.tgz`** — `Remove-Item emberburn-*.tgz`
- [ ] **Package** — `helm package helm/opcua-server` (run from repo root)
- [ ] **Regenerate index** — `helm repo index . --url https://embernet-ai.github.io/Emberburn/`
- [ ] **Verify `index.yaml`** — `version:` and `urls:` reference the new `.tgz`

---

## 6. Release Notes

- [ ] Add entry to `RELEASE_NOTES.md` at the top with date and changes
- [ ] **KEEP ONLY PREVIOUS VERSIONS** — Remove the current version entry from `RELEASE_NOTES.md` before committing (release notes document history, not the current release)

---

## 7. Commit, Tag, Push

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

## 8. Post-Push Verification

- [ ] **GitHub Actions** — check the Actions tab on `Embernet-ai/Emberburn`,
      workflow should trigger on the `vX.Y.Z` tag and build multi-arch images
- [ ] **Image pull** — `docker pull ghcr.io/embernet-ai/emberburn:X.Y.Z` succeeds (no 403)
- [ ] **GitHub Release** — create one on `Embernet-ai/Emberburn` for tag `vX.Y.Z` if desired
- [ ] **Helm chart** — `helm repo update` shows the new version in your Rancher catalog

---

## Quick Reference — Git Remotes

| Remote | URL | Purpose |
|--------|-----|---------|
| `embernet` | `https://github.com/Embernet-ai/Emberburn.git` | Org repo — CI runs here |
| `origin` | `https://github.com/patrickryan01/Small-Application.git` | Personal fork |

---

*EmberBurn — Where Data Meets Fire 🔥*
