# OPC UA Client Mode - Quick Start Guide
> *Finally! Bidirectional OPC UA Without Losing Your Mind*
> 
> **Patrick Ryan, Fireball Industries CTO**  
> *"I spent 3 days debugging this so you don't have to"*

## What is OPC UA Client Mode?
*Aka "The Part Where We Become the Client"*

Alright, gather 'round for some OPC UA philosophy. Instead of just being an OPC UA **server** (where everyone connects to YOU like you're running a data soup kitchen), your system can now flip the script and act as an OPC UA **client** to push data to other servers.

**Think of it as:**
- **Server Mode** (original): "Here's my data, peasants. Come get it!" *[sits on throne]*
- **Client Mode** (new): "You know what? I'll just... bring it to you. No worries." *[frantically pushes data]*

It's like the difference between hosting a party vs. actually showing up to one. Revolutionary, I know.

---

## Use Cases
*When You Actually Need This*

### 1. Push to Ignition
Push your OPC UA tags directly to Ignition's built-in OPC UA server for visualization in Perspective/Vision.

**Translation:** Make Ignition happy by speaking its native language (OPC UA, but as a client).

### 2. Write to Historians
Send data to OSIsoft PI, Canary, or other historians with OPC UA interfaces.

**Translation:** Log everything forever because compliance. Also because your boss said so.

### 3. Redundancy
Push the same data to multiple servers for failover and redundancy.

**Translation:** Trust no one. Not even your primary server.

### 4. Gateway Scenarios
Aggregate data from multiple sources and forward to a central server.

**Translation:** You're the middleman. The data broker. The protocol translator. Living the dream.

---

## Quick Setup

### Step 1: Basic Configuration

Create `config_push_to_ignition.json`:

```json
{
  "OPC_ENDPOINT": "opc.tcp://0.0.0.0:4840/freeopcua/server/",
  "tags": [
    {
      "name": "Temperature",
      "type": "float",
      "initial_value": 25.5,
      "min_value": 20.0,
      "max_value": 30.0,
      "change_rate": 0.5
    },
    {
      "name": "Pressure",
      "type": "float",
      "initial_value": 101.3,
      "min_value": 90.0,
      "max_value": 110.0,
      "change_rate": 0.3
    }
  ],
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [
        {
          "url": "opc.tcp://localhost:4841",
          "name": "Ignition Server",
          "namespace": 2,
          "base_node": "ns=2;s=Gateway/",
          "auto_create_nodes": true
        }
      ],
      "reconnect_interval": 5
    }
  }
}
```

### Step 2: Start Your Server

```bash
python opcua_server.py config_push_to_ignition.json
```

### Step 3: Verify in Ignition

1. Open Ignition Designer
2. Navigate to OPC Connections > OPC-UA > OPC Browser
3. Look for nodes under `Gateway/`
4. You should see `Temperature` and `Pressure` updating in real-time!

---

## Configuration Options Explained

### Basic Options

```json
{
  "url": "opc.tcp://server:4841",     // OPC UA server endpoint
  "name": "Friendly Name",             // Name for logging
  "namespace": 2,                      // Namespace index (usually 2)
  "base_node": "ns=2;s=Gateway/",     // Base path for nodes
  "auto_create_nodes": true            // Create nodes if missing
}
```

### With Authentication

```json
{
  "url": "opc.tcp://server:4841",
  "username": "admin",
  "password": "password",
  "namespace": 2,
  "base_node": "ns=2;s=Gateway/"
}
```

### With Explicit Node Mapping

```json
{
  "url": "opc.tcp://historian:4840",
  "auto_create_nodes": false,
  "node_mapping": {
    "Temperature": "ns=1;s=Plant/Reactor/Temp",
    "Pressure": "ns=1;s=Plant/Reactor/Press"
  }
}
```

### Multiple Servers (Redundancy)

```json
{
  "opcua_client": {
    "enabled": true,
    "servers": [
      {
        "url": "opc.tcp://primary:4841",
        "name": "Primary Server"
      },
      {
        "url": "opc.tcp://backup:4841",
        "name": "Backup Server"
      }
    ]
  }
}
```

---

## Real-World Examples

### Example 1: Ignition Integration

**Goal:** Push to Ignition for Perspective dashboards

```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{
        "url": "opc.tcp://ignition.local:4841",
        "namespace": 2,
        "base_node": "ns=2;s=EdgeGateway/",
        "auto_create_nodes": true
      }]
    }
  }
}
```

**Result:**
- Tags appear in Ignition Designer under `EdgeGateway/`
- Use in Perspective: `[default]EdgeGateway/Temperature`
- Bindings update in real-time

---

### Example 2: OSIsoft PI Historian

**Goal:** Log to PI via OPC UA interface

```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{
        "url": "opc.tcp://pi-server:4840",
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
}
```

**Result:**
- Data written to predefined PI tags
- No auto-creation (PI structure predefined)
- Historian captures all changes

---

### Example 3: Edge to Cloud

**Goal:** Push from edge device to cloud OPC UA server

```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{
        "url": "opc.tcp://cloud.company.com:4841",
        "username": "edge-device-001",
        "password": "cloud-token-12345",
        "namespace": 1,
        "base_node": "ns=1;s=Devices/EdgeDevice001/",
        "auto_create_nodes": true
      }]
    }
  }
}
```

**Result:**
- Secure connection to cloud
- Data available in cloud dashboards
- Auto-reconnect if connection drops

---

## Testing

### Test 1: Verify Connection

Check server logs:

```
INFO: Connected to OPC UA server: Ignition Server (opc.tcp://localhost:4841)
```

### Test 2: Verify Writes

Check server logs:

```
DEBUG: Wrote Temperature=25.5 to Ignition Server
DEBUG: Wrote Pressure=101.3 to Ignition Server
```

### Test 3: Check Remote Server

Use UaExpert to connect to the remote server and verify nodes are being updated.

---

## Troubleshooting

### Issue: "Failed to connect"

**Solutions:**
- Check URL format: `opc.tcp://server:4841`
- Verify remote server is running
- Check firewall (allow port 4841)
- Test with: `telnet server 4841`

### Issue: "BadUserAccessDenied"

**Solutions:**
- Verify username/password
- Check remote server user permissions
- Try anonymous first (remove username/password)

### Issue: "Cannot write to nodes"

**Solutions:**
- Enable `auto_create_nodes: true`
- Check remote server write permissions
- Verify node IDs in `node_mapping`

### Issue: "Connection drops frequently"

**Solutions:**
- Increase `reconnect_interval`
- Check network stability
- Verify server timeout settings

---

## Advanced: Combine with Other Publishers

You can run OPC UA Client alongside other publishers:

```json
{
  "publishers": {
    "opcua_client": {
      "enabled": true,
      "servers": [{"url": "opc.tcp://ignition:4841"}]
    },
    "mqtt": {
      "enabled": true,
      "broker": "mqtt.cloud.com",
      "topic_prefix": "plant/data"
    },
    "rest_api": {
      "enabled": true,
      "port": 5001
    }
  }
}
```

**Result:**
- Data goes to Ignition (OPC UA)
- Data goes to cloud (MQTT)
- Local monitoring (REST API)

---

## Performance

- **Connection**: ~100-500ms initial connection
- **Write latency**: ~5-50ms per write
- **Multiple servers**: Sequential writes (server1, then server2, etc.)
- **Reconnection**: Automatic every 5 seconds (configurable)

---

## Summary

**Before:** OPC UA Server only
```
[Your Server] ← Ignition connects to you
```

**After:** Bidirectional
```
[Your Server] ← Ignition reads from you
[Your Server] → You write to Ignition
```

**Best practices:**
1. Use `auto_create_nodes: true` during development
2. Switch to `node_mapping` in production
3. Always use authentication for remote servers
4. Test with UaExpert before deploying

For complete documentation, see [OPCUA_CLIENT_INTEGRATION.md](OPCUA_CLIENT_INTEGRATION.md)
