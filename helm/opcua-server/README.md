# OPC UA Multi-Protocol Server - Helm Chart

Production-ready Helm chart for deploying OPC UA server with 15 industrial protocols.

## Installation

### Via Rancher UI

1. Go to **Apps & Marketplace** → **Charts**
2. Upload this chart or add repository
3. Click **Install**
4. Fill in configuration form
5. Deploy!

### Via Helm CLI

```bash
helm install my-opcua-server . \
  --set image.repository=your-registry.com/opcua-server \
  --set image.tag=1.0.0 \
  --namespace your-namespace \
  --create-namespace
```

## Multi-Tenant Deployment

Deploy multiple isolated instances:

```bash
# Tenant 1
helm install opcua-tenant1 . \
  --namespace tenant1 \
  --create-namespace \
  --set multitenancy.enabled=true

# Tenant 2
helm install opcua-tenant2 . \
  --namespace tenant2 \
  --create-namespace \
  --set multitenancy.enabled=true
```

Each deployment gets:
- Isolated namespace
- Independent PVC for data
- Separate ConfigMap
- Dedicated resources

## Configuration

See `values.yaml` for all options or use Rancher UI forms.

### Key Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container registry | `your-registry.com/opcua-server` |
| `image.tag` | Image version | `1.0.0` |
| `persistence.enabled` | Enable storage | `true` |
| `persistence.size` | Storage size | `10Gi` |
| `ingress.enabled` | Enable web access | `false` |
| `resources.limits.memory` | Memory limit | `1Gi` |

### Example: Production Deployment

```yaml
image:
  repository: registry.company.com/opcua-server
  tag: 1.0.0

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

ingress:
  enabled: true
  hosts:
    - host: opcua-prod.company.com

mqtt:
  enabled: true
  broker: mqtt.company.com
  
influxdb:
  enabled: true
  url: https://influxdb.company.com
```

## Accessing Services

**Inside cluster:**
```
opcua-server:4840      # OPC UA
opcua-server:5000      # Web UI
opcua-server:8000      # Metrics
```

**External (with ingress):**
```
https://your-hostname.com  # Web UI
```

## Upgrading

```bash
helm upgrade my-opcua-server . -f custom-values.yaml
```

## Uninstalling

```bash
helm uninstall my-opcua-server
```

**Note:** This does NOT delete PVCs. Delete manually if needed:
```bash
kubectl delete pvc opcua-server-data opcua-server-logs
```

## Support

- Documentation: See `KUBERNETES_DEPLOYMENT.md`
- Issues: GitHub repository
- Author: Patrick Ryan, Fireball Industries
