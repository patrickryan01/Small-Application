# EmberBurn - Multi-Protocol Industrial IoT Gateway

**"Where Data Meets Fire"** - Fireball Industries

EmberBurn is a Python-based industrial IoT gateway supporting OPC UA, MQTT, Modbus TCP, and 15+ industrial protocols with a beautiful Flask web UI.

## Quick Start

```bash
helm install emberburn ./emberburn \
  --namespace emberburn \
  --create-namespace
```

## What You Get

- 🔥 **OPC UA Server** - Port 4840
- 🌐 **Web UI + REST API** - Port 5000
- 📊 **Prometheus Metrics** - Port 8000
- 🔌 **MQTT Client** - Publish to any broker
- 📡 **Modbus TCP** - Optional on port 5020
- 💾 **SQLite Persistence** - Data stored in PVC
- 🎯 **Data Transformation** - Built-in processing
- 🚨 **Alarms & Events** - Threshold monitoring

## Configuration

### Basic Configuration

```yaml
emberburn:
  image:
    repository: ghcr.io/fireball-industries/emberburn
    tag: latest
  
  ports:
    opcua: 4840
    webui: 5000
    prometheus: 8000
```

### Connect to MQTT Broker

```yaml
config:
  publishers:
    mqtt:
      enabled: true
      broker: mosquitto-mqtt-pod
      port: 1883
      topic_prefix: "industrial/emberburn"
```

### Connect to InfluxDB

```yaml
config:
  publishers:
    influxdb:
      enabled: true
      url: "http://influxdb-pod:8086"
      org: "fireball-industries"
      bucket: "industrial"
```

### Define Custom Tags

```yaml
config:
  tags:
    Temperature:
      type: float
      simulate: true
      simulation_type: sine
      min: 15.0
      max: 30.0
      units: "°C"
    
    Pressure:
      type: float
      simulate: true
      simulation_type: random
      min: 95.0
      max: 105.0
```

## Services

| Service | Type | Port | Purpose |
|---------|------|------|---------|
| `emberburn-opcua` | ClusterIP | 4840 | OPC UA clients |
| `emberburn-webui` | LoadBalancer | 5000 | Web UI access |
| `emberburn-prometheus` | ClusterIP | 8000 | Metrics scraping |

## Accessing the Web UI

```bash
# Get LoadBalancer IP
kubectl get svc -n emberburn emberburn-webui

# Open browser to:
http://<EXTERNAL-IP>:5000
```

## Monitoring

Enable Prometheus ServiceMonitor:

```yaml
monitoring:
  serviceMonitor:
    enabled: true
    namespace: monitoring
```

## Persistence

Data and logs are stored in a PVC:

```yaml
persistence:
  enabled: true
  size: 5Gi
  storageClass: local-path  # K3s default
```

## Resource Presets

Choose preset or custom resources:

```yaml
emberburn:
  resources:
    preset: medium  # small, medium, large, custom
```

**Presets:**
- **Small:** 100m CPU, 256Mi RAM (dev/test)
- **Medium:** 250m CPU, 512Mi RAM (production)
- **Large:** 500m CPU, 1Gi RAM (heavy load)

## Network Policies

Isolate EmberBurn with NetworkPolicy:

```yaml
networkPolicy:
  enabled: true
  allowedNamespaces:
    - iot
    - databases
    - monitoring
```

## Building the Docker Image

See [DOCKER-BUILD-GUIDE.md](DOCKER-BUILD-GUIDE.md) for complete instructions.

**Quick build:**

1. Add Dockerfile to https://github.com/fireball-industries/Small-Application
2. Push to GitHub
3. GitHub Actions auto-builds to `ghcr.io/fireball-industries/emberburn:latest`

## Troubleshooting

### Image Pull Error

Make GitHub package public:
- Go to: https://github.com/orgs/fireball-industries/packages
- Settings → Change visibility → Public

### Check Logs

```bash
kubectl logs -n emberburn -l app.kubernetes.io/name=emberburn
```

### Test Endpoints

```bash
# OPC UA (from inside cluster)
kubectl run -it --rm opcua-test --image=nicolaka/netshoot -- \
  curl emberburn-opcua.emberburn.svc.cluster.local:4840

# Web UI
curl http://<EXTERNAL-IP>:5000

# Metrics
curl http://emberburn-prometheus.emberburn.svc.cluster.local:8000/metrics
```

## Example Deployment

**Scenario:** Connect EmberBurn to MQTT and InfluxDB for industrial data collection

```bash
# Install with MQTT and InfluxDB enabled
helm install emberburn ./emberburn \
  --namespace emberburn \
  --create-namespace \
  --set config.publishers.mqtt.enabled=true \
  --set config.publishers.mqtt.broker=mosquitto-mqtt-pod \
  --set config.publishers.influxdb.enabled=true \
  --set config.publishers.influxdb.url=http://influxdb-pod:8086
```

Access Web UI to configure tags and transformations!

## Integration Examples

### CODESYS PLC → EmberBurn (OPC UA)

```iecst
// CODESYS code to connect to EmberBurn OPC UA
VAR
    opcClient: UA_Client;
    temperature: REAL;
END_VAR

opcClient.Connect('opc.tcp://emberburn-opcua.emberburn.svc.cluster.local:4840');
temperature := opcClient.ReadVariable('Temperature');
```

### Node-RED → EmberBurn (REST API)

```json
{
  "method": "GET",
  "url": "http://emberburn-webui.emberburn.svc.cluster.local:5000/api/tags"
}
```

### Grafana Dashboard (Prometheus)

Add data source: `http://emberburn-prometheus.emberburn.svc.cluster.local:8000`

## Links

- **Python Repository:** https://github.com/fireball-industries/Small-Application
- **Helm Charts:** https://github.com/fireball-industries/helm-charts
- **Documentation:** https://fireballz.ai/docs/emberburn
- **Container Image:** ghcr.io/fireball-industries/emberburn

---

**Fireball Industries - We Play With Fire So You Don't Have To™**
