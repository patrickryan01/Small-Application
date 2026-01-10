# OPC UA Client Mode - Implementation Summary
> *The "We Made OPC UA Fight Itself" Edition*
> 
> **Patrick Ryan, Fireball Industries**  
> *"I gave OPC UA an identity crisis and all I got was this bidirectional gateway"*

## ✅ Implementation Complete!
*No, Seriously, It Actually Works*

Your OPC UA Server now has **bidirectional capabilities**. It's like that friend who can't decide if they want to talk or listen, so they do both. Simultaneously. It's exhausting but impressive.

1. **OPC UA Server** (original) - Other clients connect to you (passive-aggressive mode)
2. **OPC UA Client** (NEW) - You aggressively push data to other servers (active-aggressive mode)

---

## What Was Added
*The Technical Stuff (For People Who Actually Read Documentation)*

### 1. New Publisher Class

**File:** `publishers.py`

**Class:** `OPCUAClientPublisher` (~350 lines of code I'll never get back)

**Features:**
- Connect to multiple OPC UA servers simultaneously - Because one server is never enough
- Auto-reconnect on disconnection (background thread) - Like your ex, but actually useful
- Node auto-creation (if enabled) - Creates nodes if they don't exist (magic!)
- Explicit node mapping support - For when you want full control (control freak mode: enabled)
- Username/password authentication - Basic security that everyone still uses
- Automatic type conversion (Python → OPC UA DataValue) - Type juggling at its finest
- Connection health monitoring - Keeping tabs on your connections
- Graceful error handling - Fails elegantly, like a Victorian lady fainting

**Key Methods:**
- `_connect_to_server()` - Establishes connection
- `_reconnect_loop()` - Background reconnection thread
- `_get_or_create_node()` - Node lookup/creation
- `publish()` - Write values to all connected servers

---

### 2. Configuration Files

#### `config/config_opcua_client.json`
Single server setup (Ignition)

```json
{
  "opcua_client": {
    "enabled": true,
    "servers": [{
      "url": "opc.tcp://localhost:4841",
      "name": "Ignition Server",
      "namespace": 2,
      "base_node": "ns=2;s=Gateway/",
      "auto_create_nodes": true
    }]
  }
}
```

#### `config/config_opcua_multi_server.json`
Multiple servers (primary, historian, backup)

```json
{
  "opcua_client": {
    "enabled": true,
    "servers": [
      {"url": "opc.tcp://ignition:4841", "name": "Ignition"},
      {"url": "opc.tcp://historian:4840", "name": "Historian"},
      {"url": "opc.tcp://backup:4842", "name": "Backup"}
    ]
  }
}
```

#### Updated `config/config_all_publishers.json`
Added `opcua_client` section

---

### 3. Documentation

#### `docs/OPCUA_CLIENT_INTEGRATION.md` (600+ lines)
Comprehensive guide covering:
- What is OPC UA Client Mode
- Key features and benefits
- Configuration reference
- Usage examples (Ignition, historians, cloud)
- Integration scenarios with diagrams
- Node addressing (automatic vs explicit)
- Testing procedures
- Troubleshooting guide
- Security best practices
- Performance considerations
- Common use cases

#### `docs/OPCUA_CLIENT_QUICKSTART.md` (400+ lines)
Quick start guide with:
- Step-by-step setup
- Real-world examples
- Configuration templates
- Testing procedures
- Troubleshooting tips

#### Updated Documentation:
- `docs/MULTI_PROTOCOL_SUMMARY.md` - Added OPC UA Client
- `docs/PROTOCOL_GUIDE.md` - Added section 2 (OPC UA Client)
- `README.md` - Updated protocol count to 9

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Your OPC UA Server                         │
│  (Tag Simulation + Multi-Protocol Publishing)               │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├─► OPC UA Server (port 4840) - Clients connect
                │
                └─► Publisher Manager
                    │
                    ├─► MQTT Publisher
                    ├─► Sparkplug B Publisher
                    ├─► Kafka Publisher
                    ├─► AMQP Publisher
                    ├─► WebSocket Publisher
                    ├─► MODBUS TCP Publisher
                    ├─► REST API Publisher
                    └─► OPC UA Client Publisher ⭐ NEW
                        │
                        ├─► Ignition OPC UA Server
                        ├─► Historian OPC UA Server
                        └─► Cloud OPC UA Server
```

### Data Flow

```
Tag Update (Temperature = 25.5)
    │
    ├─► PublisherManager.publish_to_all()
    │
    ├─► OPCUAClientPublisher.publish()
    │   │
    │   ├─► Server 1: Get/Create node → Write value
    │   ├─► Server 2: Get/Create node → Write value
    │   └─► Server 3: Get/Create node → Write value
    │
    └─► Other publishers (MQTT, Kafka, etc.)
```

### Node Addressing

**Method 1: Automatic (base_node + tag_name)**
```
base_node = "ns=2;s=Gateway/"
tag = "Temperature"
→ Result: "ns=2;s=Gateway/Temperature"
```

**Method 2: Explicit Mapping**
```json
{
  "node_mapping": {
    "Temperature": "ns=1;s=Plant/Reactor/Temp"
  }
}
```

---

## Usage Examples

### Example 1: Push to Ignition

**Command:**
```bash
python opcua_server.py config/config_opcua_client.json
```

**Result:**
- Your server runs on `opc.tcp://localhost:4840`
- Pushes data to Ignition at `opc.tcp://localhost:4841`
- Tags appear under `Gateway/` in Ignition Designer
- Auto-creates nodes if they don't exist

**Logs:**
```
INFO: Connected to OPC UA server: Ignition Server (opc.tcp://localhost:4841)
DEBUG: Wrote Temperature=25.5 to Ignition Server
DEBUG: Wrote Pressure=101.3 to Ignition Server
```

---

### Example 2: Multiple Servers (Redundancy)

**Configuration:**
```json
{
  "opcua_client": {
    "enabled": true,
    "servers": [
      {"url": "opc.tcp://primary:4841"},
      {"url": "opc.tcp://backup:4842"}
    ]
  }
}
```

**Result:**
- Same data written to both servers
- If primary fails, backup continues receiving data
- Auto-reconnect to primary when it comes back

---

### Example 3: Historian with Explicit Mapping

**Configuration:**
```json
{
  "opcua_client": {
    "enabled": true,
    "servers": [{
      "url": "opc.tcp://historian:4840",
      "username": "pi-interface",
      "password": "secure-pass",
      "auto_create_nodes": false,
      "node_mapping": {
        "Temperature": "ns=1;s=Plant.Area1.Temp",
        "Pressure": "ns=1;s=Plant.Area1.Press"
      }
    }]
  }
}
```

**Result:**
- Data written to predefined historian nodes
- No auto-creation (historian structure is fixed)
- Requires authentication

---

## Integration Points

### With Ignition

**Scenario:** Push data to Ignition's OPC UA server

**Setup:**
1. Enable Ignition's OPC UA server (Config → OPC-UA → Server Settings)
2. Configure anonymous access or create user
3. Use `namespace: 2` and `base_node: "ns=2;s=Gateway/"`
4. Start your server with `config_opcua_client.json`

**Access in Ignition:**
- Designer: OPC Browser → `Gateway/Temperature`
- Tag Path: `[default]Gateway/Temperature`
- Perspective: Bind to OPC tag

---

### With Historians (PI, Canary)

**Scenario:** Log to historian via OPC UA interface

**Setup:**
1. Enable historian's OPC UA interface
2. Create tags in historian structure
3. Use `node_mapping` for explicit paths
4. Disable `auto_create_nodes`
5. Use authentication

**Example:**
```json
{
  "node_mapping": {
    "Temperature": "ns=1;s=Plant/Area1/Reactor/Temperature"
  }
}
```

---

### With Cloud Platforms

**Scenario:** Edge-to-cloud data push

**Setup:**
1. Get cloud OPC UA endpoint URL
2. Get device credentials (username/password)
3. Configure namespace and base path
4. Enable TLS (future enhancement)

**Example:**
```json
{
  "url": "opc.tcp://opcua.cloud.com:4841",
  "username": "device-001",
  "password": "cloud-token-12345"
}
```

---

## Configuration Reference

### Server Object

```json
{
  "url": "opc.tcp://server:4841",    // Required: OPC UA endpoint
  "name": "Server Name",              // Optional: Friendly name
  "username": "admin",                // Optional: Username
  "password": "password",             // Optional: Password
  "namespace": 2,                     // Optional: Namespace index (default: 2)
  "base_node": "ns=2;s=Gateway/",    // Optional: Base node path
  "auto_create_nodes": true,          // Optional: Create nodes (default: false)
  "node_mapping": {                   // Optional: Explicit mappings
    "TagName": "ns=1;s=Path/To/Node"
  }
}
```

### Global Options

```json
{
  "opcua_client": {
    "enabled": true,                  // Enable/disable publisher
    "servers": [...],                 // Array of server objects
    "reconnect_interval": 5           // Seconds between reconnect attempts
  }
}
```

---

## Type Conversions

| Python Type | OPC UA Variant Type |
|-------------|---------------------|
| `bool` | Boolean |
| `int` | Int32 |
| `float` | Double |
| `str` | String |
| Other | String (converted) |

---

## Error Handling

### Connection Errors

**Error:** `Failed to connect to Server`

**Handling:**
- Logged as ERROR
- Server marked as disconnected
- Auto-reconnect thread attempts reconnection every N seconds

---

### Write Errors

**Error:** `BadNotWritable`, `BadNodeIdUnknown`

**Handling:**
- Logged as ERROR
- Other servers continue to receive data
- If error persists, server marked as disconnected

---

### Authentication Errors

**Error:** `BadUserAccessDenied`

**Handling:**
- Logged as ERROR
- Connection attempt fails
- Auto-reconnect continues trying

---

## Testing

### Unit Test (Connection)

```python
from publishers import OPCUAClientPublisher
import logging

config = {
    "enabled": True,
    "servers": [{
        "url": "opc.tcp://localhost:4841",
        "namespace": 2,
        "base_node": "ns=2;s=Test/"
    }],
    "reconnect_interval": 5
}

logger = logging.getLogger()
publisher = OPCUAClientPublisher(config, logger)
publisher.start()

# Publish test data
publisher.publish("Temperature", 25.5)
publisher.publish("Pressure", 101.3)

publisher.stop()
```

### Integration Test (with UaExpert)

1. Start your server with OPC UA Client enabled
2. Start UaExpert
3. Connect to the remote server (e.g., Ignition)
4. Browse to the base_node path
5. Monitor values - should update in real-time

---

## Performance

### Connection Performance

- **Initial connection:** ~100-500ms
- **Reconnection:** ~100-500ms
- **Background thread:** Check every 5 seconds (configurable)

### Write Performance

- **Single server:** ~5-50ms per tag
- **Multiple servers:** Sequential (server1, then server2, etc.)
- **Example:** 3 servers × 10ms = 30ms total per tag update

### Optimization Tips

1. Use `node_mapping` for production (faster lookups)
2. Disable `auto_create_nodes` in production
3. Increase `reconnect_interval` for stable networks
4. Limit number of servers for low-latency requirements

---

## Security

### Authentication

**Always use authentication for production:**
```json
{
  "username": "gateway-user",
  "password": "secure-password"
}
```

### Network Security

- Use VPN for remote connections
- Whitelist IP addresses
- Use firewalls to restrict access
- TLS/certificate support (future)

### Credential Management

**Use environment variables:**
```python
import os
config['servers'][0]['password'] = os.getenv('OPCUA_PASSWORD')
```

---

## Limitations

### Current Limitations

1. **No TLS support** - Coming in future version
2. **No certificate-based auth** - Coming in future version
3. **Sequential writes** - Could be parallelized for performance
4. **No timestamp support** - Writes use server timestamps
5. **No historical data** - Only current values

### Future Enhancements

1. X.509 certificate support
2. TLS encryption
3. Batch writes (write multiple nodes in one call)
4. Historical data writing
5. Method calls on remote servers
6. Subscription mode (bidirectional)

---

## Troubleshooting

### Issue: Cannot connect

**Check:**
- Server URL format: `opc.tcp://server:4841`
- Remote server is running
- Firewall allows port 4841
- Network connectivity: `telnet server 4841`

### Issue: Authentication failed

**Check:**
- Username/password correct
- User exists on remote server
- User has write permissions
- Try anonymous first (remove credentials)

### Issue: Cannot create nodes

**Check:**
- `auto_create_nodes: true`
- User has create permissions
- Namespace index is correct
- Check remote server logs

### Issue: Connection drops

**Check:**
- Network stability
- Server timeout settings
- Increase `reconnect_interval`
- Check remote server logs

---

## Summary

### What You Get

✅ Push data to other OPC UA servers  
✅ Multiple server support  
✅ Auto-reconnect on failure  
✅ Node auto-creation  
✅ Explicit node mapping  
✅ Authentication support  
✅ Automatic type conversion  
✅ Connection health monitoring  

### Use Cases

✅ Ignition Edge integration  
✅ Historian logging  
✅ Cloud platforms  
✅ Data replication  
✅ Gateway scenarios  

### Protocols Now Supported

1. OPC UA Server
2. **OPC UA Client** ⭐ NEW
3. MQTT
4. Sparkplug B
5. Apache Kafka
6. AMQP/RabbitMQ
7. WebSocket
8. REST API
9. MODBUS TCP

**Total: 9 industrial protocols!**

---

## Next Steps

1. **Test locally:** Use `config_opcua_client.json`
2. **Try Ignition:** Push to Ignition's OPC UA server
3. **Add historian:** Configure historian integration
4. **Go multi-server:** Set up redundancy
5. **Combine protocols:** Use OPC UA + MQTT + Kafka together

For more details, see:
- [OPCUA_CLIENT_INTEGRATION.md](OPCUA_CLIENT_INTEGRATION.md) - Complete guide
- [OPCUA_CLIENT_QUICKSTART.md](OPCUA_CLIENT_QUICKSTART.md) - Quick start

---

**You now have a complete bidirectional OPC UA gateway with multi-protocol support! 🚀**
