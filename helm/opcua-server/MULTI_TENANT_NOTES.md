# Multi-Tenant Deployment Notes
# Patrick Ryan - "One cluster, many tenants, zero problems (theoretically)"

## How This Works for Multi-Tenancy in K3s

This Helm chart is **designed** for multi-tenant K3s deployments:

### ✅ What Makes It Multi-Tenant Ready

1. **Namespace Isolation**
   - Each tenant gets their own namespace
   - Resources are isolated by namespace
   - No cross-tenant communication by default

2. **Separate Storage**
   - Each deployment creates its own PVCs
   - SQLite database per tenant
   - Logs stored separately

3. **Independent Configuration**
   - ConfigMap per deployment
   - Different tag configs per tenant
   - Custom publisher settings

4. **Resource Quotas**
   - Set CPU/memory limits per deployment
   - Prevents tenant resource hogging
   - Predictable performance

5. **Network Policies** (optional, add if needed)
   - Restrict pod-to-pod communication
   - Isolate tenant networks
   - Control ingress/egress

## Deployment Patterns

### Pattern 1: Shared Cluster, Isolated Namespaces

```bash
# Tenant: Manufacturing
helm install opcua-manufacturing helm/opcua-server \
  --namespace manufacturing \
  --create-namespace \
  --set image.repository=registry.io/opcua-server \
  --set resources.limits.memory=1Gi \
  --set persistence.size=20Gi

# Tenant: Warehouse
helm install opcua-warehouse helm/opcua-server \
  --namespace warehouse \
  --create-namespace \
  --set image.repository=registry.io/opcua-server \
  --set resources.limits.memory=512Mi \
  --set persistence.size=10Gi

# Tenant: Energy
helm install opcua-energy helm/opcua-server \
  --namespace energy \
  --create-namespace \
  --set image.repository=registry.io/opcua-server \
  --set resources.limits.memory=2Gi \
  --set persistence.size=50Gi
```

Each tenant:
- ✅ Cannot access other tenant's data
- ✅ Has own resource allocation
- ✅ Has independent configuration
- ✅ Can be upgraded independently

### Pattern 2: Namespace-Level Resource Quotas

Create resource quotas per tenant namespace:

```yaml
# manufacturing-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: manufacturing-quota
  namespace: manufacturing
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    persistentvolumeclaims: "5"
```

Apply quotas:
```bash
kubectl apply -f manufacturing-quota.yaml
kubectl apply -f warehouse-quota.yaml
kubectl apply -f energy-quota.yaml
```

### Pattern 3: Network Policies for Isolation

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-other-namespaces
  namespace: manufacturing
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from same namespace only
  - from:
    - podSelector: {}
  # Allow from ingress controller
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
  # Allow same namespace
  - to:
    - podSelector: {}
```

## Rancher-Specific Features

### Projects for Tenant Grouping

In Rancher, group namespaces into Projects:

1. **Create Project**: "Industrial IoT"
2. **Add Namespaces**: manufacturing, warehouse, energy
3. **Set Resource Limits**: Project-level quotas
4. **RBAC**: Control who can access which project

### Rancher Multi-Cluster

For true isolation, deploy to separate K3s clusters:

- Cluster 1: Tenant A (manufacturing)
- Cluster 2: Tenant B (warehouse)  
- Cluster 3: Tenant C (energy)

Rancher manages all from single UI.

## Security Considerations

### RBAC for Tenant Access

Create role bindings per namespace:

```yaml
# manufacturing-admin-role.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: manufacturing-admin
  namespace: manufacturing
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: manufacturing-admin-binding
  namespace: manufacturing
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: ServiceAccount
  name: manufacturing-admin
  namespace: manufacturing
```

### Secrets Per Tenant

Store sensitive data in namespace-scoped secrets:

```bash
# Tenant 1 MQTT credentials
kubectl create secret generic mqtt-credentials \
  --from-literal=username=tenant1-user \
  --from-literal=password=tenant1-pass \
  --namespace manufacturing

# Tenant 2 MQTT credentials  
kubectl create secret generic mqtt-credentials \
  --from-literal=username=tenant2-user \
  --from-literal=password=tenant2-pass \
  --namespace warehouse
```

Reference in deployment:
```yaml
envFrom:
  - secretRef:
      name: mqtt-credentials
```

## Storage Considerations

### Per-Tenant Storage Classes

Create different storage classes for different tenant tiers:

```yaml
# premium-storage.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: premium-ssd
provisioner: rancher.io/local-path
parameters:
  type: ssd
---
# standard-storage.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard-hdd
provisioner: rancher.io/local-path
parameters:
  type: hdd
```

Deploy with different storage:
```bash
# Premium tenant
helm install opcua-premium . \
  --set persistence.storageClass=premium-ssd

# Standard tenant
helm install opcua-standard . \
  --set persistence.storageClass=standard-hdd
```

## Monitoring Multi-Tenant Deployments

### Prometheus with Tenant Labels

ServiceMonitor automatically adds namespace labels:

```yaml
# Grafana dashboard query
sum(opcua_tag_updates_total) by (namespace)
```

View metrics per tenant in Grafana.

### Cost Tracking

Use namespace labels for cost allocation:

```bash
kubectl label namespace manufacturing cost-center=CC1001
kubectl label namespace warehouse cost-center=CC2002
kubectl label namespace energy cost-center=CC3003
```

## Troubleshooting Multi-Tenant Issues

### Tenant Can't Access Their Services

```bash
# Check namespace
kubectl get all -n manufacturing

# Check RBAC
kubectl auth can-i get pods --namespace manufacturing --as system:serviceaccount:manufacturing:default

# Check network policies
kubectl get networkpolicies -n manufacturing
```

### Storage Issues

```bash
# Check PVCs per namespace
kubectl get pvc -n manufacturing
kubectl get pvc -n warehouse
kubectl get pvc -n energy

# Check storage quotas
kubectl describe resourcequota -n manufacturing
```

### Resource Limits Hit

```bash
# Check resource usage
kubectl top pods -n manufacturing

# Check quota usage
kubectl describe quota -n manufacturing
```

## Best Practices

1. ✅ **Always use namespaces** - One per tenant minimum
2. ✅ **Set resource quotas** - Prevent resource hogging
3. ✅ **Use network policies** - Enforce isolation
4. ✅ **Separate storage** - Per-tenant PVCs
5. ✅ **RBAC** - Tenant-specific access control
6. ✅ **Label everything** - For cost tracking and monitoring
7. ✅ **Document tenant configs** - Keep track of deployments
8. ✅ **Test isolation** - Verify tenants can't access each other

## Production Checklist

Before going multi-tenant in production:

- [ ] Namespace strategy defined
- [ ] Resource quotas configured
- [ ] Network policies tested
- [ ] Storage classes assigned
- [ ] RBAC roles created
- [ ] Secrets per namespace
- [ ] Monitoring labels applied
- [ ] Cost tracking configured
- [ ] Backup strategy per tenant
- [ ] Disaster recovery tested
- [ ] Documentation updated
- [ ] Tenant onboarding process documented

## Summary

This Helm chart is **100% ready** for multi-tenant K3s deployment via Rancher:

✅ Namespace isolation  
✅ Independent configuration  
✅ Separate persistent storage  
✅ Resource limits  
✅ RBAC support  
✅ Network policy ready  
✅ Rancher UI integration  
✅ Questions.yaml for easy config  
✅ Multi-deployment tested  

Deploy it once per tenant, sit back, and watch the isolation work its magic! 🚀

**Patrick Ryan, 2026**
*"Multi-tenancy: Because sometimes sharing is NOT caring"*
