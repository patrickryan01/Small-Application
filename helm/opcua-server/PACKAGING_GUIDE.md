# EmberBurn - Rancher App Store Packaging Guide

**Internal Documentation for Fireball Industries DevOps Team**

---

## Overview

This document outlines the process for packaging and deploying EmberBurn to the Rancher App Store for multi-tenant client access.

---

## Directory Structure

The Helm chart is located at:
```
c:\Users\Admin\Documents\GitHub\Small-Application\helm\opcua-server\
```

This directory contains the complete Rancher-ready Helm chart with:

### Chart Files
- **Chart.yaml** - Chart metadata with Rancher annotations
- **values.yaml** - Default configuration values
- **questions.yaml** - Rancher UI form configuration
- **.helmignore** - Files to exclude from packaging

### Documentation
- **README.md** - General chart documentation
- **app-readme.md** - Rancher catalog tile description (what users see in app store)
- **RANCHER_APP_STORE_GUIDE.md** - Complete deployment guide for clients
- **QUICKSTART.md** - Fast deployment reference
- **MULTI_TENANT_NOTES.md** - Multi-tenancy architecture details

### Templates
Located in `templates/` directory:

#### Core Resources
- **namespace.yaml** - Namespace creation
- **serviceaccount.yaml** - Service account for pod
- **role.yaml** - Namespace-scoped permissions
- **rolebinding.yaml** - Bind role to service account
- **deployment.yaml** - EmberBurn pod deployment
- **configmap-tags.yaml** - Tag configuration
- **configmap-publishers.yaml** - Publisher configuration
- **pvc.yaml** - Persistent storage claim

#### Services
- **service-opcua.yaml** - OPC UA server service (ClusterIP)
- **service-webui.yaml** - Web UI service (LoadBalancer)
- **service-prometheus.yaml** - Prometheus metrics service (ClusterIP)

#### Optional Resources
- **ingress.yaml** - Ingress for domain-based access
- **hpa.yaml** - Horizontal Pod Autoscaler
- **servicemonitor.yaml** - Prometheus ServiceMonitor
- **networkpolicy.yaml** - Network traffic restrictions
- **pod-disruption-budget.yaml** - High availability settings

#### Helpers
- **_helpers.tpl** - Template functions
- **NOTES.txt** - Post-deployment instructions shown to users

---

## Rancher App Store Annotations

The `Chart.yaml` includes critical Rancher-specific annotations:

```yaml
annotations:
  # Certification and branding
  catalog.cattle.io/certified: "fireball"
  catalog.cattle.io/release-name: "emberburn"
  catalog.cattle.io/display-name: "EmberBurn - Multi-Protocol IoT Gateway"
  
  # Resource and compatibility
  catalog.cattle.io/provides-gvr: "apps/v1/Deployment"
  catalog.cattle.io/namespace: "emberburn"
  catalog.cattle.io/os: "linux"
  catalog.cattle.io/kube-version: ">=1.25.0"
  catalog.cattle.io/rancher-version: ">=2.6.0"
  
  # Auto-install behavior
  catalog.cattle.io/auto-install: "emberburn=match"
  
  # UI presentation
  catalog.cattle.io/categories: "Forge Industrial,IoT Gateway,SCADA,OPC UA,Monitoring"
  catalog.cattle.io/featured: "true"
  catalog.cattle.io/hidden: "false"
  
  # Custom metadata
  fireball.industries/project-type: "industrial-iot-gateway"
  fireball.industries/protocols: "15"
  fireball.industries/web-ui: "true"
  fireball.industries/branding: "emberburn"
```

**Key annotations**:
- `catalog.cattle.io/certified: "fireball"` - Shows "Fireball Certified" badge
- `catalog.cattle.io/categories` - Controls which categories the app appears in
- `catalog.cattle.io/featured: "true"` - Displays in featured apps section
- `catalog.cattle.io/kube-version` - Minimum Kubernetes version
- `catalog.cattle.io/rancher-version` - Minimum Rancher version

---

## RBAC & Permissions

EmberBurn includes proper RBAC configuration for secure multi-tenant operation:

### Service Account
Created in `templates/serviceaccount.yaml`:
- Namespace-scoped
- Used by EmberBurn pods
- Can be customized via `pod.serviceAccount.name`

### Role
Created in `templates/role.yaml`:
- **Read** access to: ConfigMaps, Secrets, Services, PVCs, Pods, Events
- Namespace-scoped (no cluster-wide permissions)
- Enables service discovery and configuration management

### RoleBinding
Created in `templates/rolebinding.yaml`:
- Binds Role to ServiceAccount
- Namespace-scoped

**Control via values.yaml**:
```yaml
rbac:
  create: true  # Set to false to skip RBAC creation
```

### Storage Permissions

PVC write permissions are handled via security contexts:

**Deployment security context** (pod-level):
```yaml
securityContext:
  fsGroup: 1000  # Ensures PVC files owned by group 1000
```

**Container security context**:
```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false  # EmberBurn writes to /app/data
  capabilities:
    drop:
      - ALL
```

**Mount path with write access**:
```yaml
volumeMounts:
  - name: data
    mountPath: /app/data  # Full read/write for EmberBurn
```

Files written:
- `/app/data/emberburn.db` - SQLite database
- `/app/data/logs/` - Application logs
- `/app/data/backups/` - Configuration backups

---

## Questions.yaml - Rancher UI Configuration

The `questions.yaml` file generates the Rancher deployment wizard with organized sections:

### Question Groups
- **Namespace Settings** - Namespace name and creation
- **Security** - RBAC configuration
- **EmberBurn Settings** - Version, update interval, log level
- **Resources** - CPU/memory presets
- **Storage** - Persistent volume configuration
- **Service & Networking** - Service types, ports, ingress
- **Protocols** - MQTT, InfluxDB, Sparkplug B, etc.
- **Monitoring & Data** - Metrics, persistence, alarms
- **Advanced** - Autoscaling, node selectors, network policies
- **High Availability** - Pod disruption budget

### Conditional Questions
Uses `show_subquestion_if` and `show_if` for dynamic forms:

```yaml
- variable: persistence.enabled
  label: Enable Persistent Storage
  type: boolean
  default: true
  show_subquestion_if: true
  subquestions:
    - variable: persistence.size
      label: Storage Size
      type: string
      default: "10Gi"
```

### Input Validation
- **Required fields**: `required: true`
- **Enums**: `type: enum` with `options` list
- **Integer ranges**: `min` and `max` properties
- **Storage classes**: `type: storageclass` (auto-populates from cluster)
- **Secrets**: `type: secret` (auto-populates from namespace)
- **Hostnames**: `type: hostname`

---

## Packaging for Rancher App Store

### Step 1: Validate Chart

```bash
cd c:\Users\Admin\Documents\GitHub\Small-Application\helm\opcua-server

# Lint the chart
helm lint .

# Template test (dry-run)
helm template emberburn . --debug

# Test installation (local)
helm install emberburn-test . --namespace test-emberburn --create-namespace --dry-run
```

### Step 2: Package Chart

```bash
# Package the chart
helm package .

# Output: emberburn-1.0.0.tgz
```

### Step 3: Generate Chart Index

```bash
# Create index.yaml for chart repository
helm repo index . --url https://fireball-industries.github.io/helm-charts/charts/emberburn
```

### Step 4: Commit to Helm Repository

The packaged chart should be committed to:
```
C:\Users\Admin\Documents\GitHub\Helm-Charts\charts\emberburn\
```

Repository structure:
```
Helm-Charts/
├── charts/
│   └── emberburn/
│       ├── emberburn-1.0.0.tgz
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── questions.yaml
│       ├── templates/
│       └── ...
└── index.yaml
```

### Step 5: Add to Rancher Catalog

#### Option A: GitHub Pages (Recommended)
1. Push `Helm-Charts` repository to GitHub
2. Enable GitHub Pages on the repository
3. Rancher catalog URL: `https://fireball-industries.github.io/helm-charts`

#### Option B: Direct Rancher Cluster
1. In Rancher UI: **Apps & Marketplace** → **Chart Repositories** → **Create**
2. **Name**: `fireball-industries`
3. **Index URL**: `https://fireball-industries.github.io/helm-charts/index.yaml`
4. **Scope**: Select clusters/projects
5. Click **Create**

#### Option C: Git Repository
1. In Rancher UI: **Apps & Marketplace** → **Chart Repositories** → **Create**
2. **Name**: `fireball-industries`
3. **Git Repo URL**: `https://github.com/fireball-industries/Helm-Charts`
4. **Git Branch**: `main`
5. Click **Create**

---

## Multi-Tenant Configuration

### Namespace Isolation

Each client deployment gets isolated namespace:

```yaml
namespace:
  name: emberburn  # Clients customize this (e.g., "client-a-emberburn")
  create: true
  labels:
    app: emberburn
    managed-by: fireball-industries
    podstore-type: industrial-iot
```

**Rancher enforces**:
- RBAC per namespace
- Resource quotas per namespace
- Network policies per namespace

### Resource Quotas

Set at namespace level (not in chart):

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: emberburn-quota
  namespace: client-a-emberburn
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    persistentvolumeclaims: "5"
```

### Network Policies

Optional per deployment via `networkPolicy.enabled=true`:

```yaml
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 5000
  
  egress:
    - {}  # Allow all egress
```

---

## Version Management

### Version Bump Process

1. **Update Chart.yaml**:
   ```yaml
   version: 1.1.0  # Chart version
   appVersion: "1.1.0"  # Application version
   ```

2. **Update Documentation**:
   - Update `RANCHER_APP_STORE_GUIDE.md` with new features
   - Update `NOTES.txt` if deployment changes
   - Update `README.md` with new capabilities

3. **Tag Git Commit**:
   ```bash
   git tag -a v1.1.0 -m "EmberBurn v1.1.0 - New features"
   git push origin v1.1.0
   ```

4. **Package New Version**:
   ```bash
   helm package .
   helm repo index . --merge index.yaml --url https://fireball-industries.github.io/helm-charts
   ```

5. **Clients Upgrade**:
   - Rancher auto-detects new version
   - Clients see "Upgrade Available" in Apps UI
   - One-click upgrade with option to review changes

---

## Testing Multi-Tenant Deployment

### Test Scenario 1: Basic Deployment

```bash
helm install emberburn-basic ./opcua-server \
  --namespace tenant-a \
  --create-namespace \
  --set namespace.name=tenant-a \
  --set persistence.size=5Gi \
  --set emberburn.resources.preset=small
```

### Test Scenario 2: Full-Featured Deployment

```bash
helm install emberburn-full ./opcua-server \
  --namespace tenant-b \
  --create-namespace \
  --set namespace.name=tenant-b \
  --set persistence.size=20Gi \
  --set emberburn.resources.preset=large \
  --set config.publishers.mqtt.enabled=true \
  --set config.publishers.mqtt.broker=mosquitto.default.svc.cluster.local \
  --set config.publishers.influxdb.enabled=true \
  --set config.publishers.influxdb.url=http://influxdb:8086 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=emberburn-b.example.com
```

### Test Scenario 3: Multi-Instance (Same Cluster)

```bash
# Production instance
helm install emberburn-prod ./opcua-server \
  --namespace prod-iot \
  --create-namespace \
  --set namespace.name=prod-iot

# Development instance
helm install emberburn-dev ./opcua-server \
  --namespace dev-iot \
  --create-namespace \
  --set namespace.name=dev-iot \
  --set emberburn.resources.preset=small

# Staging instance
helm install emberburn-staging ./opcua-server \
  --namespace staging-iot \
  --create-namespace \
  --set namespace.name=staging-iot
```

### Verify Isolation

```bash
# Check namespaces are isolated
kubectl get all -n prod-iot
kubectl get all -n dev-iot
kubectl get all -n staging-iot

# Verify PVCs are separate
kubectl get pvc -n prod-iot
kubectl get pvc -n dev-iot

# Check services don't conflict
kubectl get svc --all-namespaces | grep emberburn

# Verify RBAC isolation
kubectl auth can-i list pods -n prod-iot --as system:serviceaccount:dev-iot:emberburn
# Should return "no"
```

---

## Troubleshooting Rancher App Store Issues

### Chart Not Appearing in Catalog

**Check**:
1. Verify `index.yaml` is accessible at catalog URL
2. Confirm Chart.yaml has proper `apiVersion: v2`
3. Check Rancher catalog refresh (can take 5-10 minutes)
4. Review Rancher logs: **☰ → Cluster → System → Rancher → View Logs**

**Fix**:
```bash
# Force refresh catalog
# In Rancher UI: Apps & Marketplace → Chart Repositories → ⋮ → Refresh
```

### Questions Not Rendering

**Check**:
1. Validate `questions.yaml` syntax
2. Ensure `type` fields are valid Rancher types
3. Check for circular dependencies in `show_if` conditions

**Test locally**:
```bash
# Validate YAML syntax
yamllint questions.yaml

# Check for schema errors
helm template . --debug
```

### RBAC Permissions Errors

**Symptom**: Pod can't read ConfigMaps or access PVC

**Check**:
```bash
kubectl get role,rolebinding -n <namespace>
kubectl describe role emberburn -n <namespace>
kubectl auth can-i get configmaps --as system:serviceaccount:<namespace>:emberburn -n <namespace>
```

**Fix**: Verify `rbac.create=true` in deployment

### PVC Write Permission Denied

**Symptom**: Logs show "Permission denied" writing to `/app/data`

**Check**:
```bash
kubectl describe pvc -n <namespace>
kubectl get pod -n <namespace> -o yaml | grep -A 10 securityContext
```

**Fix**: Ensure `fsGroup: 1000` in deployment security context

### Service Not Accessible

**Symptom**: LoadBalancer pending or no external IP

**Check**:
```bash
kubectl get svc -n <namespace>
kubectl describe svc emberburn-webui -n <namespace>
```

**Fix**:
- Verify cluster supports LoadBalancer (MetalLB, cloud provider)
- Change to NodePort if LoadBalancer unavailable
- Check firewall rules

---

## Monitoring & Metrics

### Prometheus Integration

If Prometheus Operator installed:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: "30s"
    labels:
      release: prometheus  # Match your Prometheus release
```

EmberBurn exposes metrics at:
- `http://<pod-ip>:8000/metrics`

Metrics include:
- `emberburn_tag_value{tag="Temperature"}` - Current tag values
- `emberburn_tag_updates_total{tag="Temperature"}` - Update counter
- `emberburn_publisher_status{publisher="MQTT"}` - Publisher health
- `emberburn_alarms_active` - Active alarm count

### Grafana Dashboard

Pre-built dashboard available in:
```
config/grafana-dashboard.json
```

Import to Grafana:
1. **Dashboards → Import**
2. Upload `grafana-dashboard.json`
3. Select Prometheus data source
4. Dashboard shows:
   - Real-time tag values
   - Publisher statuses
   - Active alarms
   - System metrics (CPU/memory)

---

## Security Considerations

### Non-Root Execution

EmberBurn runs as user 1000 (non-root):

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  runAsNonRoot: true
```

**Benefits**:
- Prevents privilege escalation
- Limits blast radius of vulnerabilities
- Meets compliance requirements

### Dropped Capabilities

All Linux capabilities removed:

```yaml
capabilities:
  drop:
    - ALL
```

### Read-Only Root Filesystem

Disabled for EmberBurn (requires write to `/app/data`):

```yaml
readOnlyRootFilesystem: false
```

**Alternative**: Use tmpfs for writable areas:
```yaml
volumeMounts:
  - name: tmp
    mountPath: /tmp
  - name: data
    mountPath: /app/data

volumes:
  - name: tmp
    emptyDir: {}
  - name: data
    persistentVolumeClaim:
      claimName: emberburn-data
```

### Network Policies

Enable to restrict traffic:

```yaml
networkPolicy:
  enabled: true
```

Allows:
- Ingress from ingress controller to port 5000
- Ingress from any namespace to OPC UA port 4840
- All egress (for MQTT, InfluxDB, etc.)

Customize via `values.yaml` for tighter restrictions.

---

## Backup & Disaster Recovery

### Configuration Backup

Export Helm values:

```bash
helm get values emberburn -n <namespace> > emberburn-backup.yaml
```

### Data Backup

Backup PVC using Velero, Rancher Backup, or manual:

```bash
# Manual PVC backup
kubectl cp <namespace>/<pod-name>:/app/data ./emberburn-data-backup

# Restore
kubectl cp ./emberburn-data-backup <namespace>/<pod-name>:/app/data
```

### Full Disaster Recovery

1. **Save configuration**:
   ```bash
   helm get values emberburn -n prod-iot > prod-values.yaml
   kubectl get pvc emberburn-data -n prod-iot -o yaml > prod-pvc.yaml
   ```

2. **Recreate deployment**:
   ```bash
   helm install emberburn ./opcua-server -n prod-iot-new --create-namespace -f prod-values.yaml
   ```

3. **Restore data**:
   - Restore PVC from backup
   - Or copy data to new PVC

---

## Support & Maintenance

### Client Support Process

1. **Self-Service** (Primary):
   - Clients deploy via Rancher UI
   - Use `RANCHER_APP_STORE_GUIDE.md` for guidance
   - Troubleshoot via logs and metrics

2. **Fleet Fallback** (Secondary):
   - If Rancher app store deployment fails
   - Support team deploys via Fleet
   - Same configuration, different delivery method

3. **Direct Support** (Last Resort):
   - SSH/kubectl access by support team
   - Manual Helm deployment
   - Custom troubleshooting

### Update Strategy

**Minor Updates** (1.0.0 → 1.1.0):
- Bug fixes, new features
- Backward compatible
- Clients upgrade via Rancher UI

**Major Updates** (1.x → 2.0):
- Breaking changes
- May require data migration
- Release notes detail upgrade path

### Deprecation Policy

- **Notice Period**: 90 days before deprecating features
- **LTS Versions**: Support N-2 versions (e.g., support 1.0 when 1.2 is latest)
- **Security Updates**: Backport critical security fixes to LTS versions

---

## Appendix: File Checklist

Before packaging, verify all files present:

**Required**:
- [x] Chart.yaml (with Rancher annotations)
- [x] values.yaml (with rbac.create)
- [x] questions.yaml (complete UI form)
- [x] .helmignore
- [x] templates/_helpers.tpl
- [x] templates/namespace.yaml
- [x] templates/serviceaccount.yaml
- [x] templates/role.yaml
- [x] templates/rolebinding.yaml
- [x] templates/deployment.yaml
- [x] templates/configmap-tags.yaml
- [x] templates/configmap-publishers.yaml
- [x] templates/pvc.yaml
- [x] templates/service-*.yaml (3 services)
- [x] templates/NOTES.txt

**Optional but Recommended**:
- [x] README.md
- [x] app-readme.md (Rancher catalog description)
- [x] RANCHER_APP_STORE_GUIDE.md (client documentation)
- [x] templates/ingress.yaml
- [x] templates/hpa.yaml
- [x] templates/servicemonitor.yaml
- [x] templates/networkpolicy.yaml
- [x] templates/pod-disruption-budget.yaml

**Documentation**:
- [x] QUICKSTART.md
- [x] MULTI_TENANT_NOTES.md
- [x] This packaging guide

---

## Conclusion

EmberBurn is now packaged and ready for Rancher App Store deployment with:

✅ **Complete RBAC** - Namespace-scoped permissions  
✅ **Write Permissions** - PVC accessible via fsGroup 1000  
✅ **Multi-Tenant Support** - Full namespace isolation  
✅ **Self-Service UI** - Rancher questions.yaml form  
✅ **Documentation** - Comprehensive deployment guide  
✅ **Security Hardening** - Non-root, dropped capabilities  
✅ **Monitoring** - Prometheus metrics and Grafana dashboards  
✅ **High Availability** - HPA, PDB, autoscaling support  

Clients can now discover and deploy EmberBurn through Rancher's Apps & Marketplace with full self-service capability.

---

*EmberBurn v1.0.0 - Rancher App Store Packaging*  
*Fireball Industries DevOps Team*  
*Last Updated: 2026-01-13*
