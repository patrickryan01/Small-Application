# Complete Protocol Architecture
> *Or: How I Learned to Stop Worrying and Love Industrial IoT*
> 
> **By Patrick Ryan, CTO @ Fireball Industries**  
> *"Making industrial automation slightly less painful since whenever I started this company"*

## System Overview (aka "What Fresh Hell Did We Build?")

Look, I'm not saying this OPC UA Server is over-engineered, but it supports **9 industrial protocols simultaneously**. That's right, NINE. Because apparently "just use OPC UA" wasn't enterprise-y enough for 2026.

Is it overkill? Absolutely. Will it save your bacon when some legacy PLC from 1997 insists on MODBUS? Also yes.

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│              OPC UA Server Core (Port 4840)                          │
│          Tag Simulation + Real-time Updates                          │
│                                                                      │
└─────────────────────────┬────────────────────────────────────────────┘
                          │
                          │  PublisherManager orchestrates all protocols
                          │
      ┌───────────────────┴───────────────────┐
      │                                       │
      ▼                                       ▼
┌─────────────┐                     ┌────────────────┐
│  INBOUND    │                     │   OUTBOUND     │
│  (Server)   │                     │   (Clients)    │
└─────────────┘                     └────────────────┘
      │                                       │
      │                                       │
      ├─► OPC UA Server                      ├─► OPC UA Client ⭐ NEW
      │   (Clients connect to us)             │   (We push to servers)
      │   Port: 4840                          │   → Ignition
      │                                       │   → Historians
      │                                       │   → Cloud platforms
      │                                       │
      ├─► MODBUS TCP Server                  ├─► MQTT Publisher
      │   (PLCs poll us)                      │   (We publish to broker)
      │   Port: 502                           │   → Cloud (AWS/Azure)
      │   Registers: 0-1000                   │   → Node-RED
      │                                       │   → IoT platforms
      │                                       │
      ├─► REST API Server                    ├─► Sparkplug B Publisher
      │   (HTTP clients query us)             │   (We publish to broker)
      │   Port: 5001                          │   → Ignition Edge (native)
      │   GET/POST endpoints                  │   → Cirrus Link
      │                                       │
      ├─► WebSocket Server                   ├─► Apache Kafka Producer
      │   (Browsers connect to us)            │   (We publish to topics)
      │   Port: 9001                          │   → Data lakes
      │   Real-time push                      │   → Stream processing
      │                                       │
      │                                       └─► AMQP Publisher
      │                                           (We publish to exchange)
      │                                           → RabbitMQ
      │                                           → Enterprise bus
      │
      └─► Total: 4 Server Modes               └─► Total: 5 Client Modes
```

---

## Protocol Matrix
*The Scorecard of Our Protocol Addiction*

| # | Protocol | Type | Port | Direction | Use Case | Millennial Translation |
|---|----------|------|------|-----------|----------|----------------------|
| 1 | OPC UA Server | Server | 4840 | ← Inbound | SCADA systems connect | "Y'all can read my data" |
| 2 | **OPC UA Client** ⭐ | Client | N/A | → Outbound | Push to Ignition, historians | "I'm sliding into your DMs" |
| 3 | MQTT | Client | N/A | → Outbound | IoT/cloud brokers | "Publishing my thoughts online" |
| 4 | Sparkplug B | Client | N/A | → Outbound | Ignition Edge native | "Speaking Ignition's language" |
| 5 | Apache Kafka | Producer | N/A | → Outbound | Enterprise streaming | "Screaming into the void (at scale)" |
| 6 | AMQP | Publisher | N/A | → Outbound | RabbitMQ messaging | "Enterprise-grade texting" |
| 7 | WebSocket | Server | 9001 | ← Inbound | Real-time browsers | "Live streaming my data" |
| 8 | REST API | Server | 5001 | ← Inbound | HTTP GET/POST | "The API everyone understands" |
| 9 | MODBUS TCP | Server | 502 | ← Inbound | Legacy PLCs poll | "Talking to grandpa's PLC" |

---

## Data Flow Examples

### Example 1: Complete Multi-Protocol Setup

```
Tag Update: Temperature = 25.5°C
│
├─► OPC UA Server (Port 4840)
│   └─► UaExpert reads value
│
├─► OPC UA Client ⭐
│   ├─► Writes to Ignition server (ns=2;s=Gateway/Temperature)
│   ├─► Writes to Historian (ns=1;s=Plant/Temp)
│   └─► Writes to Cloud server (ns=1;s=Devices/Edge001/Temp)
│
├─► MQTT Publisher
│   └─► Publishes to industrial/opcua/Temperature
│       ├─► Node-RED subscribes
│       ├─► AWS IoT Core receives
│       └─► Azure IoT Hub receives
│
├─► Sparkplug B Publisher
│   └─► Publishes DDATA message
│       └─► Ignition MQTT Engine receives
│
├─► Apache Kafka Producer
│   └─► Publishes to industrial-data topic
│       ├─► Kafka Streams processes
│       └─► Data lake ingests
│
├─► AMQP Publisher
│   └─► Publishes to industrial.data exchange
│       └─► RabbitMQ routes to queues
│
├─► WebSocket Server (Port 9001)
│   └─► Broadcasts to connected browsers
│       └─► Dashboard updates in real-time
│
├─► REST API (Port 5001)
│   └─► Stores in memory
│       └─► GET /api/tags/Temperature returns value
│
└─► MODBUS TCP Server (Port 502)
    └─► Stores in registers 0-1 (float = 2 registers)
        └─► PLC polls holding registers
```

---

## Architecture Patterns

### Pattern 1: Ignition Integration

**Goal:** Complete Ignition ecosystem integration

```
Your Server
├─► OPC UA Client → Ignition OPC UA Server (write tags)
└─► Sparkplug B → Ignition MQTT Engine (SCADA protocol)

Ignition connects via:
├─► OPC UA Client → Your OPC UA Server (read tags)
└─► Designer → Your REST API (monitoring)
```

**Configuration:**
```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{
        "url": "opc.tcp://ignition:4841",
        "namespace": 2,
        "base_node": "ns=2;s=Gateway/"
      }]
    },
    "sparkplug_b": {
      "enabled": true,
      "broker": "ignition",
      "port": 1883,
      "group_id": "Sparkplug B Devices"
    }
  }
}
```

---

### Pattern 2: Historian Logging

**Goal:** Log to multiple historians for redundancy

```
Your Server
├─► OPC UA Client
│   ├─► Primary Historian (OSIsoft PI)
│   └─► Backup Historian (Canary)
└─► Kafka Producer → Enterprise data lake
```

**Configuration:**
```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [
        {
          "url": "opc.tcp://pi-server:4840",
          "name": "Primary PI",
          "node_mapping": {
            "Temperature": "ns=1;s=Plant.Area1.Temp"
          }
        },
        {
          "url": "opc.tcp://canary:4840",
          "name": "Backup Canary"
        }
      ]
    },
    "kafka": {
      "enabled": true,
      "topic": "historian-backup"
    }
  }
}
```

---

### Pattern 3: Edge-to-Cloud Gateway

**Goal:** Push from factory floor to cloud platforms

```
Factory Floor
│
└─► Your Server (Edge Gateway)
    ├─► OPC UA Client → Cloud OPC UA Server
    ├─► MQTT → AWS IoT Core
    ├─► Kafka → Cloud Kafka Cluster
    └─► WebSocket ← Cloud dashboard
```

**Configuration:**
```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{
        "url": "opc.tcp://cloud.company.com:4841",
        "username": "edge-device-001",
        "password": "${CLOUD_PASSWORD}"
      }]
    },
    "mqtt": {
      "enabled": true,
      "broker": "mqtt.cloud.com",
      "port": 8883,
      "use_tls": true
    }
  }
}
```

---

### Pattern 4: Legacy PLC Integration

**Goal:** Bridge modern and legacy systems

```
Modern Systems
├─► Your OPC UA Server ← SCADA reads via OPC UA
└─► Your REST API ← Web dashboard reads via HTTP

Legacy Systems
└─► Your MODBUS TCP Server ← Old PLC polls via MODBUS
```

**Configuration:**
```json
{
  "publishers": {
    "modbus_tcp": {
      "enabled": true,
      "port": 502,
      "register_mapping": {
        "Temperature": {"register": 0, "type": "float"}
      }
    },
    "rest_api": {
      "enabled": true,
      "port": 5001
    }
  }
}
```

---

### Pattern 5: Development/Testing Setup

**Goal:** Local testing with all protocols

```
Your Server (localhost)
├─► OPC UA Server (4840) ← UaExpert connects
├─► OPC UA Client → Test server (4841)
├─► MQTT → Local Mosquitto (1883)
├─► WebSocket (9001) ← Browser connects
├─► REST API (5001) ← Postman tests
└─► MODBUS TCP (502) ← QModMaster polls
```

**Configuration:**
```json
{
  "publishers": {
    "opcua_client": {"enabled": true},
    "mqtt": {"enabled": true},
    "websocket": {"enabled": true},
    "rest_api": {"enabled": true},
    "modbus_tcp": {"enabled": true}
  }
}
```

---

## Protocol Selection Guide

### When to Use OPC UA Client

✅ **Use when:**
- Pushing to Ignition's OPC UA server
- Writing to historians (PI, Canary)
- Edge-to-cloud OPC UA connectivity
- Data replication to multiple OPC UA servers
- Centralized OPC UA server aggregation

❌ **Don't use when:**
- Need publish/subscribe (use MQTT instead)
- Need high-throughput streaming (use Kafka)
- Target doesn't support OPC UA

---

### When to Use MQTT

✅ **Use when:**
- IoT cloud platforms (AWS IoT, Azure IoT)
- Node-RED workflows
- Lightweight messaging
- Publish/subscribe needed
- Mobile app connectivity

❌ **Don't use when:**
- Need guaranteed delivery (use AMQP)
- Need high throughput (use Kafka)
- Target expects OPC UA

---

### When to Use Sparkplug B

✅ **Use when:**
- **Ignition Edge** (primary use case)
- Need birth/death certificates
- Need store-and-forward
- SCADA-specific features needed

❌ **Don't use when:**
- Target doesn't support Sparkplug B
- Standard MQTT is sufficient

---

### When to Use Kafka

✅ **Use when:**
- High-throughput streaming
- Data lake ingestion
- Stream processing pipelines
- Enterprise microservices
- Event sourcing

❌ **Don't use when:**
- Simple messaging (use MQTT)
- Request/response needed (use REST)
- Low-volume data

---

### When to Use MODBUS TCP

✅ **Use when:**
- Legacy PLCs need to poll data
- SCADA systems expect MODBUS
- Industrial HMIs use MODBUS
- Vendor tools require MODBUS

❌ **Don't use when:**
- Modern protocols available
- Need event-driven (MODBUS is poll-based)

---

### When to Use REST API

✅ **Use when:**
- Web applications
- Mobile apps
- Simple HTTP clients
- Periodic polling acceptable
- No persistent connection needed

❌ **Don't use when:**
- Need real-time push (use WebSocket)
- High-frequency updates (overhead)

---

## Performance Comparison

| Protocol | Latency | Throughput | CPU Usage | Best For |
|----------|---------|------------|-----------|----------|
| OPC UA Server | 5-20ms | Medium | Low | SCADA clients |
| **OPC UA Client** | 10-50ms | Medium | Low | Push to servers |
| MQTT | 5-30ms | High | Low | IoT/cloud |
| Sparkplug B | 5-30ms | High | Low | Ignition Edge |
| Kafka | 10-100ms | Very High | Medium | Streaming |
| AMQP | 10-50ms | High | Medium | Enterprise |
| WebSocket | 5-20ms | Medium | Low | Web browsers |
| REST API | 20-100ms | Low | Low | HTTP clients |
| MODBUS TCP | 50-200ms | Low | Low | Legacy PLCs |

---

## Network Topology

### Single Server Deployment

```
                    ┌─────────────────────────────┐
                    │   Your OPC UA Server        │
                    │   (All protocols enabled)   │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
  ┌──────────┐              ┌──────────┐              ┌──────────┐
  │ Ignition │              │  Cloud   │              │  Legacy  │
  │  (OPC UA │              │  (MQTT)  │              │  PLC     │
  │  Client) │              │          │              │ (MODBUS) │
  └──────────┘              └──────────┘              └──────────┘
```

### Distributed Deployment

```
Factory Floor                Edge Gateway              Cloud
     │                            │                      │
     ├─► PLC 1 ──┐                │                      │
     ├─► PLC 2 ──┼─► MODBUS ──────┤                      │
     └─► PLC 3 ──┘                │                      │
                                  │                      │
                          ┌───────┴────────┐             │
                          │  Your Server   │             │
                          │  (Multi-Proto) │             │
                          └───────┬────────┘             │
                                  │                      │
                                  ├─► OPC UA Client ─────┼─► Cloud OPC UA
                                  ├─► MQTT ──────────────┼─► AWS IoT
                                  └─► Kafka ─────────────┼─► Data Lake
                                  │                      │
                          Local Network                  │
                                  │                      │
                          Ignition Server                │
                              (Reads via OPC UA)         │
```

---

## Summary
*The Part Where We Pat Ourselves on the Back*

### What You Have Now

🎉 **9 Industrial Protocols:**
1. OPC UA Server (original) - The foundation
2. **OPC UA Client** ⭐ NEW - The plot twist
3. MQTT - The IoT darling
4. Sparkplug B - Ignition's BFF
5. Apache Kafka - The enterprise flex
6. AMQP/RabbitMQ - The reliable one
7. WebSocket - The real-time enabler
8. REST API - The people's champion
9. MODBUS TCP - The legacy legend

### Capabilities
*What This Thing Can Actually Do*

✅ Server mode (4 protocols) - Others connect to you (popular kid energy)  
✅ Client mode (5 protocols) - You push to others (aggressive networking)  
✅ Bidirectional OPC UA - Server + Client (identity crisis resolved)  
✅ Multi-cloud - AWS, Azure, Google (cloud-agnostic and proud)  
✅ Multi-SCADA - Ignition, Wonderware, etc. (doesn't play favorites)  
✅ Legacy support - MODBUS TCP (respecting the ancients)  
✅ Modern web - WebSocket + REST (keeping up with the times)  
✅ Enterprise - Kafka + RabbitMQ (resume fodder)  

### Use Cases Enabled
*The "Why Did We Build This?" Answer Sheet*

✅ Ignition Edge integration (complete) - The main event  
✅ Historian logging (PI, Canary) - For compliance and paranoia  
✅ Cloud platforms (AWS, Azure) - Buzzword compliance achieved  
✅ Legacy PLC bridging - Bringing grandpa's hardware to the party  
✅ Data lake ingestion - Lake of data, ocean of possibilities  
✅ Real-time dashboards - Making stakeholders happy since 2025  
✅ IoT gateway scenarios - Edge computing with extra steps  
✅ Enterprise data bus - Because "integration" sounds professional  

---

**You now have a complete industrial gateway capable of bridging any protocol to any other protocol! 🚀**

*Now go forth and integrate all the things. Or take a nap. Both are valid choices.*

**-Patrick Ryan, CTO @ Fireball Industries**  
*"Making industrial automation slightly less painful, one protocol at a time"*
