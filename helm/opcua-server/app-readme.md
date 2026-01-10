# OPC UA Multi-Protocol Server

Deploy an OPC UA server with 15 industrial protocols for IoT and SCADA integration.

## Features

- **15 Protocols**: OPC UA, MQTT, Sparkplug B, Kafka, AMQP, WebSocket, REST API, GraphQL, MODBUS TCP, InfluxDB, Alarms, Prometheus, SQLite, Data Transformation
- **Web UI**: Beautiful Flask-based dashboard
- **Multi-Tenant Ready**: Deploy per namespace with isolated configs
- **Persistent Storage**: SQLite database with automatic backups
- **Monitoring**: Prometheus metrics and Grafana integration
- **Transformations**: Real-time unit conversions and computed tags

## Quick Start

1. **Configure**: Set your image registry and tag configuration
2. **Deploy**: Install to your namespace
3. **Access**: Connect via OPC UA (port 4840) or Web UI (port 5000)

## Ports

- **4840**: OPC UA Server
- **5000**: REST API + Web UI
- **8000**: Prometheus Metrics

## Multi-Tenancy

Each deployment gets:
- Isolated namespace
- Independent configuration
- Separate persistent storage
- Dedicated resource limits

Perfect for multi-tenant K3s environments!

## Documentation

Full documentation at: [GitHub Repository](https://github.com/your-org/opcua-server)
