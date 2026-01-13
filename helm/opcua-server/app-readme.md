# EmberBurn - Multi-Protocol Industrial IoT Gateway

**"Where Data Meets Fire"** - Fireball Industries

Deploy EmberBurn for industrial-grade IoT data collection, protocol translation, and edge computing with 15+ protocol support and a beautiful web interface.

## 🔥 What is EmberBurn?

EmberBurn is a production-ready industrial IoT gateway that bridges legacy industrial equipment with modern cloud and analytics platforms. Built by Fireball Industries for multi-tenant Kubernetes environments.

## ✨ Key Features

- **🔌 15+ Protocols**: OPC UA Server, MQTT Publisher/Subscriber, Sparkplug B, Kafka, AMQP, WebSocket, REST API, GraphQL, Modbus TCP, InfluxDB, Prometheus, Node-RED integration, OPC UA Client, and more
- **🎨 Beautiful Web UI**: Flask-based dashboard with real-time tag monitoring, configuration, alarms, and protocol management
- **🏢 Multi-Tenant Ready**: Full namespace isolation with independent configurations, resource quotas, and persistent storage
- **💾 Data Persistence**: SQLite database with automatic backups, configurable retention, and audit logging
- **📊 Monitoring & Metrics**: Built-in Prometheus metrics, Grafana dashboards, and ServiceMonitor support
- **⚙️ Data Transformation**: Real-time unit conversions, scaling, computed tags, and custom transformations
- **🚨 Alarms & Notifications**: Threshold-based alarms with email and Slack notifications
- **🔒 Production Security**: Non-root containers, network policies, RBAC, and security contexts
- **📈 Autoscaling**: Horizontal Pod Autoscaler support for dynamic workload management

## 🚀 Self-Service Deployment

1. **Choose Resources**: Select small/medium/large preset or customize CPU/memory
2. **Configure Storage**: Enable persistent storage for data retention (10Gi default)
3. **Enable Protocols**: Turn on MQTT, InfluxDB, Sparkplug B, or other integrations as needed
4. **Deploy**: One-click deployment to your namespace
5. **Access**: Web UI automatically available via LoadBalancer or Ingress

## 🔌 Ports & Services

| Port | Service | Access |
|------|---------|--------|
| **4840** | OPC UA Server | OPC UA clients (UaExpert, Ignition, etc.) |
| **5000** | Web UI + REST API | Browser, API clients |
| **8000** | Prometheus Metrics | Prometheus scraper |

## 🏗️ Multi-Tenant Architecture

Each EmberBurn deployment includes:

✅ **Isolated Namespace** - Full RBAC and network isolation  
✅ **Dedicated Storage** - Independent PersistentVolumeClaim (10Gi+ configurable)  
✅ **Resource Limits** - CPU/memory quotas prevent noisy neighbors  
✅ **Service Accounts** - Namespace-scoped permissions  
✅ **ConfigMaps** - Separate tag and publisher configurations  
✅ **LoadBalancer** - External access without port conflicts  

**Perfect for**:
- Multi-site deployments (one instance per facility)
- Multi-environment setups (dev/staging/production)
- SaaS providers (one instance per customer)
- Protocol-specific gateways (MQTT vs InfluxDB vs Sparkplug)

## 📚 Quick Access After Deployment

**Web UI**: Dashboard, tag monitoring, configuration, alarms  
**REST API**: `/api/tags`, `/api/publishers`, `/api/alarms`  
**OPC UA**: `opc.tcp://<external-ip>:4840/freeopcua/server/`  
**Metrics**: `http://<external-ip>:8000/metrics`  

## 🎯 Common Use Cases

- **Protocol Translation**: OPC UA ↔ MQTT ↔ InfluxDB ↔ Sparkplug B
- **Edge Data Collection**: Manufacturing, oil & gas, building automation
- **IoT Gateway**: Connect legacy PLCs to cloud platforms
- **SCADA Integration**: Real-time data to Ignition, Grafana, or custom dashboards
- **Data Transformation**: Unit conversions, scaling, aggregation at the edge

## 🛡️ Security & Permissions

EmberBurn runs with enterprise security:

- **Non-root**: Runs as user/group 1000:1000
- **Dropped Capabilities**: All Linux capabilities removed
- **Network Policies**: Optional traffic restriction
- **RBAC**: Namespace-scoped service account
- **PVC Permissions**: FSGroup 1000 for write access to `/app/data`

**Required permissions**: Project Member role (minimum) with namespace creation rights

## 📖 Documentation

- **Deployment Guide**: See `RANCHER_APP_STORE_GUIDE.md` for complete multi-tenant setup
- **Multi-Tenant Notes**: See `MULTI_TENANT_NOTES.md` for architecture details
- **Quick Start**: See `QUICKSTART.md` for fast deployment
- **GitHub**: Full source code and documentation

## 💡 Support

This chart is maintained by Fireball Industries and included with your subscription.

- **Documentation**: Built into Web UI
- **Support**: support@fireball-industries.com
- **Updates**: Automatic via Rancher app catalog
- **Fleet Fallback**: Available if self-service deployment fails

---

**EmberBurn v1.0.0** - Production-ready industrial IoT gateway for Kubernetes  
*Fireball Industries* - https://fireballz.ai/emberburn
