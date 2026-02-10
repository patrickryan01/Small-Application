# Embernet Networking & Helm Chart Integration Guide

> **How the Industrial Dashboard routes traffic, and how every other Helm chart must be structured to work with "Launch UI" from the dashboard.**

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [How the Dashboard Routes Traffic](#2-how-the-dashboard-routes-traffic)
3. [The Two Launch URL Strategies](#3-the-two-launch-url-strategies)
4. [Traefik Ingress (Our Reverse Proxy)](#4-traefik-ingress-our-reverse-proxy)
5. [OAuth2 Proxy — The Auth Gateway](#5-oauth2-proxy--the-auth-gateway)
6. [Helm Chart Requirements for "Launch UI"](#6-helm-chart-requirements-for-launch-ui)
7. [Namespace Ownership Errors — The Fix](#7-namespace-ownership-errors--the-fix)
8. [Multi-Instance Deployments](#8-multi-instance-deployments)
9. [Helm Chart Template Checklist](#9-helm-chart-template-checklist)
10. [Complete Example: Compliant Helm Chart](#10-complete-example-compliant-helm-chart)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        INTERNET                                      │
│                           │                                          │
│                     ┌─────▼─────┐                                    │
│                     │  Traefik  │  (K3s built-in IngressController)  │
│                     │  :443/80  │                                    │
│                     └─────┬─────┘                                    │
│                           │                                          │
│              ┌────────────▼────────────┐                             │
│              │ industrial.embernet.ai  │                             │
│              │    Ingress Rule         │                             │
│              └────────────┬────────────┘                             │
│                           │                                          │
│                   ┌───────▼───────┐                                  │
│                   │ OAuth2 Proxy  │   (Azure AD SSO gate)            │
│                   │   :4180       │                                  │
│                   └───────┬───────┘                                  │
│                           │ Authenticated                            │
│                   ┌───────▼───────┐                                  │
│                   │   Dashboard   │   (Go binary, :8080)             │
│                   │   embernet-   │                                  │
│                   │   dashboard   │                                  │
│                   └───┬───┬───┬───┘                                  │
│                       │   │   │                                      │
│          ┌────────────┘   │   └────────────┐                         │
│          ▼                ▼                 ▼                         │
│   /api/proxy?      K8s API             /static/                      │
│   target=<PodIP>   (nodes,pods,        (CSS, images,                 │
│                     events,shell)       templates)                    │
│          │                                                           │
│          ▼                                                           │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│   │  Node-RED    │  │  Ignition    │  │  Emberburn   │              │
│   │  10.42.x.x   │  │  10.42.x.x   │  │  10.42.x.x   │              │
│   │  :1880       │  │  :8088       │  │  :3000       │              │
│   └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **Traefik** is the only thing touching the internet. It terminates TLS.
- **OAuth2 Proxy** sits between Traefik and the dashboard. Every request must be authenticated via Azure AD before reaching the Go backend.
- **The Dashboard** serves its own HTML/CSS/JS and provides API endpoints. It also acts as a **reverse proxy** to reach pod GUIs inside the cluster.
- **App pods** (Node-RED, Emberburn, Ignition, etc.) live on the pod network (`10.42.0.0/16` in K3s). They are **never** directly exposed to the internet. The dashboard proxies to them.

---

## 2. How the Dashboard Routes Traffic

The Go backend (`main.go`) registers these network-relevant handlers:

| Route | Purpose |
|-------|---------|
| `/` | Serves the HTML view (operator/engineer/admin/global_command) |
| `/static/` | Static assets (CSS, images, JS) |
| `/api/proxy?target=http://<IP>:<PORT>` | **Reverse proxy** — forwards requests to internal pod IPs |
| `/api/shell` | WebSocket bridge for node shell access |
| `/api/shell/pod` | WebSocket bridge for container shell access |
| `/api/store/apps` | Lists available apps from Helm repos + builtins |
| `/api/store/deploy` | Deploys an app via HelmChart CRD |
| `/api/nodes` | Node metrics (CPU, RAM, pods, apps) |
| `/api/events/*` | Cluster events and activity timeline |
| `/api/storage/*` | Longhorn storage management |

### The Reverse Proxy (`/api/proxy`)

This is how **"Launch UI"** works. When a user clicks "Launch UI" on a deployed app card:

```
Browser → /api/proxy?target=http://10.42.1.15:1880 → Pod's web UI
```

The proxy handler in `internal/proxy/handlers.go`:

1. Parses the `target` query parameter
2. **SSRF protection** — only allows private IPs (`10.x`, `172.16-31.x`, `192.168.x`) and `.svc.cluster.local` DNS
3. Creates a `httputil.ReverseProxy` pointing to the target
4. Sets the `Host` header to match the target (critical for apps that inspect Host)
5. Streams the response back to the browser

**Security Model:** The proxy only allows traffic to **cluster-internal addresses**. You cannot proxy to `google.com` — the SSRF check blocks it.

---

## 3. The Two Launch URL Strategies

The dashboard generates launch URLs in `client.go` → `getAppsForNode()`. There are two strategies:

### Strategy A: Rancher K8s API Proxy (When `RANCHER_URL` is set)

```
https://rancher.yourdomain.com/k8s/clusters/local/api/v1/namespaces/<ns>/services/http:<svc>:<port>/proxy/
```

**How it works:** Rancher provides a built-in Kubernetes API proxy that can route to any Service in the cluster. This works through Rancher's auth, so the user must be authenticated with Rancher.

**Pros:** Uses Rancher's existing auth + TLS chain. Clean URLs.
**Cons:** Requires Rancher to be configured and reachable. Needs the pod to have a matching K8s Service.

### Strategy B: Dashboard Reverse Proxy (Default / Fallback)

```
/api/proxy?target=http://<PodIP>:<ContainerPort>
```

**How it works:** The dashboard itself proxies the request via Go's `httputil.ReverseProxy`. The browser never talks directly to the pod.

**Pros:** Works without Rancher. No extra config needed.
**Cons:** Requires the dashboard pod to have network access to the target pod (always true in K3s on the same cluster).

### Which Strategy Gets Used?

```go
if rancherURL != "" {
    // Strategy A: Rancher proxy
    launchURL = fmt.Sprintf("%s/k8s/clusters/local/api/v1/namespaces/%s/services/http:%s:%d/proxy/",
        rancherURL, pod.Namespace, svcName, guiPort)
} else if pod.Status.PodIP != "" {
    // Strategy B: Dashboard reverse proxy
    launchURL = fmt.Sprintf("/api/proxy?target=http://%s:%d", pod.Status.PodIP, guiPort)
}
```

**Currently `rancher.enabled: false` in values.yaml**, so all apps use **Strategy B** (dashboard reverse proxy via pod IP).

---

## 4. Traefik Ingress (Our Reverse Proxy)

K3s ships with Traefik as the default IngressController. Every app that wants external access **must** create an Ingress resource or go through the dashboard's proxy.

### For the Dashboard Itself

The dashboard's Ingress routes `industrial.embernet.ai` → OAuth2 Proxy → Dashboard:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dashboard
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: traefik
  tls:
    - hosts: ["industrial.embernet.ai"]
      secretName: industrial-embernet-ai-tls
  rules:
    - host: industrial.embernet.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: oauth2-proxy   # ← Auth gateway, NOT the dashboard directly
                port:
                  number: 4180
```

### For Other Apps — YOU DON'T NEED SEPARATE INGRESSES

**This is the critical point.** Apps deployed from the App Store do **NOT** need their own Ingress. The dashboard's `/api/proxy` reverse-proxies to their pod IPs directly. Their GUIs are accessed **through the dashboard**, not via separate public URLs.

**However**, if an app genuinely needs its own public URL (e.g., a webhook endpoint, or a API that external systems call), then yes — it needs its own Ingress with Traefik. See Section 6 for the template requirements.

---

## 5. OAuth2 Proxy — The Auth Gateway

All traffic to the dashboard passes through OAuth2 Proxy first. The flow:

```
User → industrial.embernet.ai → Traefik → OAuth2 Proxy → [Authenticated?]
                                                             │
                                                    NO ──→ Redirect to Azure AD login
                                                    YES ──→ Forward to Dashboard :8080
                                                             with X-Forwarded-Email,
                                                             X-Forwarded-Groups headers
```

OAuth2 Proxy injects identity headers that the dashboard reads for RBAC:
- `X-Forwarded-Email` → User identity
- `X-Forwarded-Groups` → Azure AD group GUIDs (matched against `azureAD.groups.*` in values.yaml)

**Other apps do NOT need their own OAuth2 Proxy.** They are accessed through the dashboard's authenticated session. The `/api/proxy` handler inherits the user's authenticated context.

---

## 6. Helm Chart Requirements for "Launch UI"

For an app to show a working "Launch UI" button in the dashboard, it needs:

### Requirement 1: A Kubernetes Service

The dashboard builds launch URLs using the pod's `app` label as the service name:

```go
svcName := pod.Labels["app"]
```

**Your Helm chart MUST create a Service with a name that matches the pod's `app` label.** If using `{{ include "chart.fullname" . }}` for both, this works automatically.

### Requirement 2: Exposed Container Port

The dashboard detects GUI capability by checking `pod.Spec.Containers[].Ports`:

```go
for _, container := range pod.Spec.Containers {
    for _, port := range container.Ports {
        if port.ContainerPort > 0 {
            hasGUI = true
            guiPort = port.ContainerPort
            break
        }
    }
}
```

**Your Deployment MUST declare `containerPort` in the pod spec.** If no port is declared, the app won't get a "Launch UI" button.

### Requirement 3: Store Labels

For the dashboard to identify and display the app correctly:

```yaml
metadata:
  labels:
    embernet.io/store-app: "true"       # Required: makes pod visible to operators
    embernet.io/app-name: "My App"      # Optional: display name (falls back to pod name)
    embernet.io/app-icon: "🔥"          # Optional: icon (URL or emoji)
    app: {{ include "chart.fullname" . }}  # Required: used for service lookup
```

### Requirement 4: Network Accessibility

The dashboard pod must be able to reach the app pod on the pod network. In K3s, this is **always true** for pods on the same cluster — no extra config needed. Just make sure:

- The app pod is **Running** (not CrashLoopBackOff)
- The container port is **listening** (the app is actually serving HTTP)
- The app doesn't require HTTPS internally (the proxy connects via plain HTTP to pod IPs)

### Requirement 5: No Hardcoded Namespaces in Charts

Charts that create their own Namespace resources cause the error in Section 7. **Never create Namespace resources in Helm templates.** Let the namespace be created externally or by `helm install --create-namespace`.

---

## 7. Namespace Ownership Errors — The Fix

### The Error

```
Error: INSTALLATION FAILED: Unable to continue with install: Namespace "emberburn" 
in namespace "" exists and cannot be imported into the current release: invalid 
ownership metadata; label validation error: missing key "app.kubernetes.io/managed-by": 
must be set to "Helm"; annotation validation error: missing key 
"meta.helm.sh/release-name": must be set to "emberburn"
```

### Why This Happens

This error occurs when:

1. A Helm chart includes a `Namespace` resource in its templates (e.g., `templates/namespace.yaml`)
2. The namespace **already exists** but was created **outside of Helm** (e.g., by `kubectl create ns`, by a previous install, or by K3s itself)
3. Helm 3.2+ requires **ownership labels** on any resource it manages. A pre-existing namespace doesn't have `app.kubernetes.io/managed-by: Helm`, so Helm refuses to adopt it.

### The Permanent Fix: NEVER Create Namespaces in Helm Charts

**Remove any `namespace.yaml` or namespace resource from your `templates/` directory.**

```bash
# If your chart has this file, DELETE IT:
rm charts/emberburn/templates/namespace.yaml
```

Instead, use `helm install --create-namespace`:

```bash
# Helm creates the namespace if it doesn't exist, and manages it properly
helm install emberburn ./charts/emberburn -n emberburn --create-namespace
```

### If the Namespace Already Exists and You're Stuck

**Option A: Adopt it (add Helm ownership labels to the existing namespace):**

```bash
kubectl label namespace emberburn \
  app.kubernetes.io/managed-by=Helm

kubectl annotate namespace emberburn \
  meta.helm.sh/release-name=emberburn \
  meta.helm.sh/release-namespace=emberburn
```

Then retry `helm install`.

**Option B: Delete and recreate (if safe):**

```bash
# ⚠️ THIS DELETES EVERYTHING IN THE NAMESPACE
kubectl delete namespace emberburn
helm install emberburn ./charts/emberburn -n emberburn --create-namespace
```

**Option C: Use `--no-hooks` if the namespace template has install hooks:**

```bash
helm install emberburn ./charts/emberburn -n emberburn --create-namespace --no-hooks
```

### Prevention: Chart Template Audit

Search ALL your Helm chart templates for namespace resources:

```bash
# Run this in every chart directory
grep -rn "kind: Namespace" templates/
```

If found, **delete that template file** and document that `--create-namespace` is required on install.

---

## 8. Multi-Instance Deployments

### Same Chart, Different Releases

```bash
helm install clientA-node1-emberburn ./charts/emberburn -n clientA --create-namespace
helm install clientA-node2-emberburn ./charts/emberburn -n clientA --create-namespace
```

**Helm uses the release name as a prefix for all resources:**

| Release Name | Deployment | Service | Ingress |
|---|---|---|---|
| `clientA-node1-emberburn` | `clientA-node1-emberburn` | `clientA-node1-emberburn` | `clientA-node1-emberburn` |
| `clientA-node2-emberburn` | `clientA-node2-emberburn` | `clientA-node2-emberburn` | `clientA-node2-emberburn` |

**This ONLY works if the chart templates use `{{ include "chart.fullname" . }}` for resource names — NOT hardcoded names.**

### Namespace Strategy

| Pattern | Use Case |
|---------|----------|
| One namespace per client | `helm install app ./chart -n client-a --create-namespace` |
| One namespace per app | `helm install app ./chart -n emberburn --create-namespace` |
| Shared namespace | `helm install client-a-app ./chart -n apps` |

**Recommended for Embernet:** One namespace per client, multiple releases in it. This isolates clients while allowing multi-instance apps per client.

### Ingress Hostname Conflicts

If multiple instances create Ingresses, each needs a **unique hostname**:

```bash
helm install instance1 ./chart -n test \
  --set ingress.host=instance1.embernet.ai

helm install instance2 ./chart -n test \
  --set ingress.host=instance2.embernet.ai
```

**But remember:** If the app is only accessed through the dashboard's "Launch UI" proxy, it doesn't need an Ingress at all. Skip it with `--set ingress.enabled=false`.

---

## 9. Helm Chart Template Checklist

Apply this to **every** Embernet Helm chart (Emberburn, Node-RED, Ignition, etc.):

### ✅ Required in `_helpers.tpl`

```yaml
{{- define "chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "chart.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 }}
{{ include "chart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: {{ include "chart.fullname" . }}
{{- end }}
```

### ✅ Required in `templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
        embernet.io/store-app: "true"
        embernet.io/app-name: {{ .Chart.Name | quote }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - name: http
              containerPort: {{ .Values.service.port }}
              protocol: TCP
```

### ✅ Required in `templates/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "chart.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "chart.selectorLabels" . | nindent 4 }}
```

### ✅ Optional: `templates/ingress.yaml` (Only If App Needs Its Own Public URL)

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "chart.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - {{ .Values.ingress.host | quote }}
      secretName: {{ include "chart.fullname" . }}-tls
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "chart.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```

### ❌ NEVER Include in Templates

```yaml
# ❌ DO NOT CREATE NAMESPACES IN HELM CHARTS
apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Release.Namespace }}

# ❌ DO NOT HARDCODE RESOURCE NAMES
metadata:
  name: emberburn-deployment    # WILL CONFLICT WITH MULTI-INSTANCE

# ❌ DO NOT HARDCODE NAMESPACES
metadata:
  namespace: emberburn          # USE {{ .Release.Namespace }}

# ❌ DO NOT HARDCODE SELECTORS
selector:
  matchLabels:
    app: emberburn              # USE {{ include "chart.selectorLabels" . }}
```

---

## 10. Complete Example: Compliant Helm Chart

Here's a minimal but complete chart structure that works with the Embernet Dashboard:

```
my-app-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   └── service.yaml
```

### `Chart.yaml`
```yaml
apiVersion: v2
name: my-app
description: My Industrial Application
type: application
version: 1.0.0
appVersion: "1.0.0"
```

### `values.yaml`
```yaml
replicaCount: 1

image:
  repository: ghcr.io/embernet-ai/my-app
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 3000

ingress:
  enabled: false
  host: ""

nameOverride: ""
fullnameOverride: ""
```

### Install Command
```bash
helm install my-app ./my-app-chart -n client-namespace --create-namespace
```

### Verify It Works with "Launch UI"
```bash
# 1. Check pod is running with correct labels
kubectl get pods -n client-namespace -l embernet.io/store-app=true --show-labels

# 2. Check service exists and matches
kubectl get svc -n client-namespace

# 3. Check pod has container ports declared
kubectl get pod <pod-name> -n client-namespace -o jsonpath='{.spec.containers[*].ports}'

# 4. Test proxy manually
curl -k https://industrial.embernet.ai/api/proxy?target=http://<POD_IP>:<PORT>
```

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Launch UI" button missing | Pod has no `containerPort` declared | Add `ports:` to Deployment spec |
| "Launch UI" shows blank iframe | App serves on different path (e.g., `/ui`) | Check app's base URL config. May need path rewriting in proxy. |
| "Failed to reach target" | Pod is not Running or port is wrong | `kubectl logs <pod>` + verify port |
| Namespace ownership error | Chart creates Namespace resource | Delete `templates/namespace.yaml`, use `--create-namespace` |
| App not visible in node card | Missing `embernet.io/store-app: "true"` label | Add label to pod template |
| App shows for Admins but not Operators | Operator role only sees `embernet.io/store-app` pods | Ensure label is set |
| Name conflict on multi-install | Hardcoded resource names in templates | Use `{{ include "chart.fullname" . }}` everywhere |
| Ingress hostname conflict | Two instances with same `host` value | Set unique `--set ingress.host=` per instance, or disable ingress |
| `gzip: Invalid header` in Rancher catalog | `index.yaml` URL missing `/charts/` | See RELEASE_CHECKLIST.md |
| App iframe blocked by CORS | Target app rejects non-Origin requests | App needs to allow dashboard origin or proxy rewrites Origin header |
| WebSocket (shell) disconnects | OAuth2 Proxy timeout | Increase `--upstream-timeout` in OAuth2 Proxy args |

---

## Quick Reference: Install Commands

```bash
# Dashboard (special — has OAuth2 Proxy, its own ingress, the whole stack)
helm upgrade --install dashboard ./charts/industrial-dashboard -n fireball-system --create-namespace

# Any other app (accessed through dashboard "Launch UI")
helm install <release-name> ./charts/<app-chart> -n <namespace> --create-namespace

# Multi-instance of same app
helm install client-a-nodered ./charts/nodered -n client-a --create-namespace
helm install client-b-nodered ./charts/nodered -n client-b --create-namespace

# If namespace ownership error — adopt it first
kubectl label namespace <ns> app.kubernetes.io/managed-by=Helm
kubectl annotate namespace <ns> meta.helm.sh/release-name=<release> meta.helm.sh/release-namespace=<ns>
```
