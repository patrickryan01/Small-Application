# Kubernetes Deployment Guide 🚀
> *"From 15 Protocols to 15 Pods (Just Kidding, It's Just One)"*
>
> **Patrick Ryan, Fireball Industries**  
> *"I Kubernetes-ified it so you can claim DevOps on your resume"*

## What You Get

A **production-ready Helm chart** that deploys your OPC UA server with all 15 protocols in K3s via Rancher UI Store.

Because manually deploying to Kubernetes is for people with too much free time.

## Prerequisites

- **K3s cluster** (or any Kubernetes 1.19+)
- **Rancher UI** (for that sweet GUI deployment)
- **Docker registry** (to store your container image)
- **kubectl** (for when the GUI betrays you)
- **helm** (for local testing before you YOLO it to prod)

## Quick Start (The "I Trust You" Edition)

### Step 1: Build the Docker Image

```bash
# Build the image
docker build -t your-registry.com/opcua-server:1.0.0 .

# Push to your registry
docker push your-registry.com/opcua-server:1.0.0
```

**Pro Tip:** Replace `your-registry.com` with your actual registry. Shocking, I know.

### Step 2: Package the Helm Chart

```bash
# Package the chart
helm package helm/opcua-server

# This creates: opcua-server-1.0.0.tgz
```

### Step 3: Deploy via Rancher UI

1. **Open Rancher** → Go to your cluster
2. **Apps & Marketplace** → Charts
3. **Import/Upload Helm Chart**
4. **Upload** `opcua-server-1.0.0.tgz`
5. **Configure** (or use defaults like a boss)
6. **Install** → Watch the magic happen ✨

### Step 4: Access Your Server

```bash
# Get the service endpoint
kubectl get svc opcua-server -n default

# Port forward for local access (if needed)
kubectl port-forward svc/opcua-server 4840:4840 5000:5000
```

Now browse to `http://localhost:5000` for the Web UI!

## Detailed Deployment Guide

### Build & Push Container Image

```bash
# Build for multi-architecture (ARM64 + AMD64)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry.com/opcua-server:1.0.0 \
  --push .

# Or just AMD64 if you're boring
docker build -t your-registry.com/opcua-server:1.0.0 .
docker push your-registry.com/opcua-server:1.0.0
```

### Test Locally with Helm

```bash
# Install from local chart
helm install opcua-server helm/opcua-server \
  --set image.repository=your-registry.com/opcua-server \
  --set image.tag=1.0.0 \
  --namespace default

# Check status
helm status opcua-server

# Watch pods come up
kubectl get pods -w

# Check logs
kubectl logs -f deployment/opcua-server
```

### Customize Configuration

Create a `values.yaml` override file:

```yaml
# my-values.yaml
image:
  repository: your-registry.com/opcua-server
  tag: 1.0.0

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 200m
    memory: 512Mi

persistence:
  enabled: true
  size: 20Gi

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: opcua.yourdomain.com
      paths:
        - path: /
          pathType: Prefix

config:
  tags: |
    {
      "Temperature": {
        "type": "float",
        "initial_value": 20.0,
        "simulate": true,
        "simulation_type": "random",
        "min": 15.0,
        "max": 25.0
      }
    }
```

Deploy with custom values:

```bash
helm install opcua-server helm/opcua-server -f my-values.yaml
```

## Rancher UI Deployment (The GUI Way)

### Adding to Rancher Catalog

**Option 1: Git Repository**

1. Create a GitHub repo with your chart
2. Rancher → **Cluster Tools** → **Repositories**
3. **Add Repository**
   - Name: `opcua-charts`
   - Target: Git repository containing Helm charts
   - Git Repo URL: `https://github.com/your-org/opcua-charts`
   - Git Branch: `main`

**Option 2: HTTP Helm Repository**

```bash
# Host your chart on a web server
helm repo index . --url https://charts.yourdomain.com
# Upload index.yaml and .tgz files to web server
```

Then in Rancher:
1. **Repositories** → **Add Repository**
2. Name: `opcua-charts`
3. Index URL: `https://charts.yourdomain.com/index.yaml`

### Installing from Rancher UI

1. **Apps & Marketplace** → **Charts**
2. Find `opcua-server` in catalog
3. Click **Install**
4. **Namespace:** Choose or create (e.g., `industrial-iot`)
5. **Customize Helm Values:**
   - Image repository & tag
   - Resource limits
   - Persistence settings
   - Ingress configuration
6. **Install** → Wait for deployment
7. **View** → Check pods, services, logs

## Multi-Tenancy Setup

For multi-tenant deployments (different configs per namespace):

```bash
# Deploy to tenant-specific namespaces
helm install opcua-tenant1 helm/opcua-server \
  --namespace tenant1 \
  --create-namespace \
  -f tenant1-values.yaml

helm install opcua-tenant2 helm/opcua-server \
  --namespace tenant2 \
  --create-namespace \
  -f tenant2-values.yaml
```

Each tenant gets:
- Isolated namespace
- Own ConfigMap with custom tags
- Separate persistent storage
- Independent resource limits

## Configuration Options

### Key Helm Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image | `your-registry/opcua-server` |
| `image.tag` | Image tag | `1.0.0` |
| `service.type` | Service type (ClusterIP/LoadBalancer) | `ClusterIP` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | Storage size | `10Gi` |
| `ingress.enabled` | Enable ingress | `false` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `1Gi` |

### Environment Variables

Set via Helm values:

```yaml
env:
  - name: UPDATE_INTERVAL
    value: "1.0"
  - name: LOG_LEVEL
    value: "DEBUG"
  - name: PYTHONUNBUFFERED
    value: "1"
```

### Persistent Storage

The chart creates two PVCs:
- **Data PVC** (`10Gi`): SQLite database, historical data
- **Logs PVC** (`1Gi`): Application logs

Mounted at:
- `/app/data` - Database files
- `/app/logs` - Log files

## Networking & Services

### Service Ports

The deployment exposes 3 ports:

1. **4840** - OPC UA Server (TCP)
2. **5000** - REST API / Web UI (HTTP)
3. **8000** - Prometheus Metrics (HTTP)

### Accessing Services

**Inside the cluster:**
```
opcua-server.default.svc.cluster.local:4840  # OPC UA
opcua-server.default.svc.cluster.local:5000  # Web UI
opcua-server.default.svc.cluster.local:8000  # Metrics
```

**External access via LoadBalancer:**
```yaml
service:
  type: LoadBalancer
```

**External access via Ingress:**
```yaml
ingress:
  enabled: true
  hosts:
    - host: opcua.yourdomain.com
```

## Monitoring & Observability

### Prometheus Metrics

If you have Prometheus Operator installed:

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
```

This creates a ServiceMonitor that auto-discovers the metrics endpoint.

### Logs

View logs in Rancher UI or via kubectl:

```bash
# Rancher UI: Workload → Pods → View Logs

# kubectl
kubectl logs -f deployment/opcua-server
kubectl logs -f deployment/opcua-server --tail=100
```

### Health Checks

The deployment includes:
- **Liveness Probe:** TCP check on port 4840
- **Readiness Probe:** TCP check on port 4840

K8s will auto-restart unhealthy pods.

## Upgrades & Rollbacks

### Upgrade Deployment

```bash
# Upgrade to new version
helm upgrade opcua-server helm/opcua-server \
  --set image.tag=1.1.0

# Or via Rancher UI: Apps → opcua-server → Upgrade
```

### Rollback

```bash
# List releases
helm history opcua-server

# Rollback to previous version
helm rollback opcua-server 1

# Or via Rancher UI: Apps → opcua-server → Rollback
```

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl get pods

# Describe pod
kubectl describe pod opcua-server-xxxxx

# Check logs
kubectl logs opcua-server-xxxxx

# Common issues:
# 1. Image pull error → Check registry credentials
# 2. CrashLoopBackOff → Check logs for Python errors
# 3. ConfigMap missing → Check ConfigMap exists
```

### Service Not Reachable

```bash
# Check service
kubectl get svc opcua-server

# Check endpoints
kubectl get endpoints opcua-server

# Port forward for testing
kubectl port-forward svc/opcua-server 4840:4840

# Test connection
nc -zv localhost 4840
```

### Persistent Volume Issues

```bash
# Check PVCs
kubectl get pvc

# Describe PVC
kubectl describe pvc opcua-server-data

# Check storage class
kubectl get storageclass

# If pending: Check storage provisioner is installed
```

### Configuration Issues

```bash
# Check ConfigMap
kubectl get configmap opcua-server-config -o yaml

# Edit ConfigMap
kubectl edit configmap opcua-server-config

# Restart pod to pick up changes
kubectl rollout restart deployment/opcua-server
```

## Security Best Practices

### Network Policies

Restrict pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: opcua-server-netpol
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: opcua-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 1883  # MQTT
```

### Secrets Management

Store sensitive data in Secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: opcua-secrets
type: Opaque
stringData:
  mqtt-password: "your-mqtt-password"
  influxdb-token: "your-influxdb-token"
```

Reference in deployment:

```yaml
envFrom:
  - secretRef:
      name: opcua-secrets
```

### RBAC

The chart creates a ServiceAccount with minimal permissions.

For additional permissions, create a Role/RoleBinding.

## Performance Tuning

### Resource Limits

For production:

```yaml
resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Autoscaling

**Note:** OPC UA server state isn't easily replicated, so autoscaling is limited.

For high-availability, consider:
- Active/standby setup
- External state store (Redis, PostgreSQL)
- Shared persistent volume

## Production Checklist

Before deploying to production:

- [ ] Build multi-arch image (AMD64 + ARM64)
- [ ] Push to private registry
- [ ] Set resource limits and requests
- [ ] Enable persistent storage
- [ ] Configure ingress with TLS
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Test backup/restore procedures
- [ ] Document disaster recovery plan
- [ ] Set up alerts for pod failures
- [ ] Review security policies
- [ ] Test multi-tenancy isolation
- [ ] Load test with expected tag count

## Examples

### Minimal Deployment

```bash
helm install opcua-server helm/opcua-server \
  --set image.repository=myregistry/opcua-server \
  --set image.tag=1.0.0
```

### Production Deployment

```bash
helm install opcua-server helm/opcua-server \
  --namespace production \
  --create-namespace \
  -f production-values.yaml
```

Where `production-values.yaml`:

```yaml
image:
  repository: myregistry.azurecr.io/opcua-server
  tag: 1.0.0
  pullPolicy: Always

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

persistence:
  enabled: true
  size: 50Gi
  storageClass: premium-rwo

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: opcua-prod.company.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: opcua-tls
      hosts:
        - opcua-prod.company.com

serviceMonitor:
  enabled: true
  interval: 30s
```

## Summary

You now have:
- ✅ **Dockerfile** for containerization
- ✅ **Helm Chart** for Kubernetes deployment
- ✅ **Rancher UI** integration
- ✅ **Multi-tenancy** support
- ✅ **Production-ready** configuration
- ✅ **Monitoring** integration (Prometheus)
- ✅ **Persistent storage** for SQLite
- ✅ **Ingress** for external access

**Deploy to K3s:**
```bash
helm install opcua-server helm/opcua-server \
  --set image.repository=your-registry/opcua-server
```

**Or via Rancher UI:** Apps → Charts → opcua-server → Install

**Patrick Ryan, 2026**  
*"It's Kubernetes now. Your problem, not mine."* 😎
