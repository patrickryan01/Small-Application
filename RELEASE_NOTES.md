# EmberBurn Release Notes

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
