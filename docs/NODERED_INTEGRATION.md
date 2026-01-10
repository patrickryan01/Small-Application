# Node-RED Integration Guide
> *Low-Code for People Who Actually Code*
> 
> **Patrick Ryan @ Fireball Industries**  
> *"Node-RED: Because sometimes you want to prototype faster than your coffee can brew"*

## Overview
*Visual Programming for the Rest of Us*

Node-RED is perfect for prototyping, IoT integrations, and that weird one-off project your boss wants "by tomorrow." It's like Scratch for adults who know what an API is. This OPC UA Server can feed data to Node-RED using multiple protocols, because of course it can.

Think of Node-RED as industrial automation's answer to "can we make this work without writing actual code?" (Spoiler: yes, but you'll probably write JavaScript anyway)

## Integration Methods
*Pick Your Poison*

### Method 1: MQTT (RECOMMENDED)
*The "It Just Works™" Approach*

MQTT provides the best balance of simplicity and performance for Node-RED. It's like choosing vanilla ice cream - boring, reliable, and nobody's going to complain.

#### Setup Steps

**1. Install Node-RED** (if not already installed)

```bash
# Install Node.js first (https://nodejs.org/)
# Then install Node-RED globally
npm install -g --unsafe-perm node-red

# Start Node-RED
node-red

# Access at http://localhost:1880
```

**2. Start OPC UA Server with MQTT**

```bash
python opcua_server.py -c config/config_nodered.json
```

**3. Configure MQTT Node in Node-RED**

1. Drag an **MQTT In** node to the flow
2. Double-click to configure
3. Server: `localhost:1883`
4. Topic: `nodered/opcua/#` (subscribe to all tags)
5. QoS: 0 or 1
6. Output: auto-detect (JSON object)

**4. Example Flow - Display All Tags**

```
[MQTT In] → [Debug]
```

Configure MQTT In:
- Topic: `nodered/opcua/#`
- Output: a parsed JSON object

You'll see messages like:
```json
{
  "tag": "Temperature",
  "value": 22.5,
  "timestamp": 1736476800.123
}
```

**5. Example Flow - Temperature Dashboard**

```
[MQTT In: nodered/opcua/Temperature] → [Function: Extract Value] → [Gauge]
```

Function node code:
```javascript
msg.payload = msg.payload.value;
return msg;
```

#### Complete Example Flow (Import this!)

```json
[
  {
    "id": "mqtt_in",
    "type": "mqtt in",
    "name": "OPC UA Tags",
    "topic": "nodered/opcua/#",
    "qos": "0",
    "broker": "mqtt_broker",
    "x": 140,
    "y": 100
  },
  {
    "id": "mqtt_broker",
    "type": "mqtt-broker",
    "name": "Local Mosquitto",
    "broker": "localhost",
    "port": "1883"
  },
  {
    "id": "parse_temp",
    "type": "switch",
    "name": "Route by Tag",
    "property": "payload.tag",
    "rules": [
      {"t": "eq", "v": "Temperature", "vt": "str"},
      {"t": "eq", "v": "Pressure", "vt": "str"},
      {"t": "eq", "v": "Counter", "vt": "str"}
    ],
    "x": 340,
    "y": 100
  },
  {
    "id": "debug",
    "type": "debug",
    "name": "All Tags",
    "x": 540,
    "y": 100
  }
]
```

### Method 2: REST API (HTTP Request)

Use HTTP requests to poll tag values.

**1. HTTP Request Node Setup**

```
[Inject: Every 2s] → [HTTP Request] → [JSON Parse] → [Debug]
```

HTTP Request configuration:
- Method: GET
- URL: `http://localhost:5000/api/tags/Temperature`
- Return: a UTF-8 string

**2. Example Flow - Get All Tags**

```javascript
// Inject node (repeat every 2 seconds)
// ↓
// HTTP Request
{
  "method": "GET",
  "url": "http://localhost:5000/api/tags"
}
// ↓
// Function node
var tags = msg.payload.tags;
var temp = tags.Temperature.value;
var pressure = tags.Pressure.value;

msg.payload = {
  "temperature": temp,
  "pressure": pressure
};
return msg;
// ↓
// Debug / Dashboard
```

### Method 3: WebSocket (Real-Time)

For low-latency, real-time updates.

**1. Start OPC UA Server with WebSocket**

```bash
python opcua_server.py -c config/config_nodered.json
```

**2. WebSocket In Node Setup**

```
[WebSocket In] → [JSON Parse] → [Debug]
```

WebSocket configuration:
- Type: Connect to
- URL: `ws://localhost:9001`

**3. Example Flow**

```
[WebSocket In: ws://localhost:9001] → [Function: Route] → [Gauge/Chart]
```

Function node:
```javascript
// WebSocket receives JSON strings
var data = JSON.parse(msg.payload);

if (data.tag === "Temperature") {
    msg.payload = data.value;
    return msg;
}
```

## Complete Node-RED Dashboard Example

Install dashboard nodes:
```bash
cd ~/.node-red
npm install node-red-dashboard
# Restart Node-RED
```

### Example Dashboard Flow

```json
[
  {
    "id": "mqtt_all_tags",
    "type": "mqtt in",
    "name": "All OPC UA Tags",
    "topic": "nodered/opcua/#",
    "qos": "0",
    "broker": "local_broker",
    "x": 130,
    "y": 100
  },
  {
    "id": "route_by_tag",
    "type": "switch",
    "name": "Route Tags",
    "property": "payload.tag",
    "rules": [
      {"t": "eq", "v": "Temperature"},
      {"t": "eq", "v": "Pressure"},
      {"t": "eq", "v": "FlowRate"},
      {"t": "eq", "v": "Counter"}
    ],
    "x": 330,
    "y": 100
  },
  {
    "id": "temp_gauge",
    "type": "ui_gauge",
    "name": "Temperature",
    "group": "dashboard_group",
    "min": 0,
    "max": 50,
    "x": 530,
    "y": 80
  },
  {
    "id": "pressure_gauge",
    "type": "ui_gauge",
    "name": "Pressure",
    "group": "dashboard_group",
    "min": 90,
    "max": 110,
    "x": 530,
    "y": 120
  },
  {
    "id": "flow_chart",
    "type": "ui_chart",
    "name": "Flow Rate",
    "group": "dashboard_group",
    "x": 530,
    "y": 160
  },
  {
    "id": "counter_text",
    "type": "ui_text",
    "name": "Counter",
    "group": "dashboard_group",
    "x": 530,
    "y": 200
  },
  {
    "id": "extract_value",
    "type": "function",
    "name": "Extract Value",
    "func": "msg.payload = msg.payload.value; return msg;",
    "x": 430,
    "y": 140
  }
]
```

Access dashboard at: `http://localhost:1880/ui`

## Advanced Use Cases

### Use Case 1: Data Logger to Database

```
[MQTT In] → [Function: Format] → [SQLite/MongoDB Node]
```

Function node:
```javascript
msg.payload = {
    tag: msg.payload.tag,
    value: msg.payload.value,
    timestamp: new Date(msg.payload.timestamp * 1000)
};
return msg;
```

### Use Case 2: Alerts and Notifications

```
[MQTT In: Temperature] → [Switch: > 30°C] → [Email/Telegram/SMS Node]
```

Switch node:
- Property: `payload.value`
- Rule: `> 30`

### Use Case 3: Cloud Integration

```
[MQTT In] → [Function: Transform] → [AWS IoT/Azure IoT Node]
```

### Use Case 4: Multi-Protocol Bridge

Bridge MQTT to another protocol:

```
[MQTT In: nodered/opcua/#] 
    → [Function: Transform]
    → [MQTT Out: cloud/devices/sensor1]
```

This re-publishes OPC UA data to a cloud MQTT broker.

### Use Case 5: Tag History and Analytics

```
[MQTT In: Temperature] 
    → [InfluxDB Out]
    → [Grafana Dashboard]
```

## Configuration Examples

### MQTT Configuration in Node-RED

**Simple Local Broker:**
```javascript
{
  "broker": "localhost",
  "port": 1883,
  "clientid": "node-red-client",
  "username": "",
  "password": ""
}
```

**Cloud MQTT Broker:**
```javascript
{
  "broker": "mqtt.example.com",
  "port": 8883,
  "tls": true,
  "username": "your-username",
  "password": "your-password"
}
```

### REST API Polling

**Poll Every 2 Seconds:**
```
[Inject: interval 2s]
    ↓
[HTTP Request: GET /api/tags]
    ↓
[Function: Process]
    ↓
[Dashboard Widgets]
```

**Selective Tag Polling:**
```javascript
// Function node to poll multiple specific tags
var tags = ["Temperature", "Pressure", "Counter"];
var results = [];

for (var i = 0; i < tags.length; i++) {
    var url = "http://localhost:5000/api/tags/" + tags[i];
    // Use HTTP Request node with msg.url
}
```

## Protocol Comparison for Node-RED

| Protocol | Latency | CPU Usage | Best For |
|----------|---------|-----------|----------|
| MQTT | Low (~10ms) | Low | Real-time dashboards |
| WebSocket | Very Low (~5ms) | Medium | High-frequency updates |
| REST API | Medium (~50ms) | Low | Periodic polling |
| OPC UA | Low (~10ms) | Medium | Legacy integration |

## Sample Flows

### 1. Simple Monitor

```javascript
[
    {
        "id": "mqtt_in_1",
        "type": "mqtt in",
        "name": "Temperature",
        "topic": "nodered/opcua/Temperature",
        "broker": "local_broker"
    },
    {
        "id": "function_1",
        "type": "function",
        "name": "Extract",
        "func": "return {payload: msg.payload.value};"
    },
    {
        "id": "debug_1",
        "type": "debug",
        "name": "Show Value"
    }
]
```

### 2. Alert System

```javascript
[
    {
        "id": "mqtt_in_2",
        "type": "mqtt in",
        "topic": "nodered/opcua/Temperature"
    },
    {
        "id": "switch_1",
        "type": "switch",
        "name": "Check Threshold",
        "property": "payload.value",
        "rules": [
            {"t": "gt", "v": "30"}
        ]
    },
    {
        "id": "email_1",
        "type": "e-mail",
        "name": "Send Alert",
        "to": "admin@example.com"
    }
]
```

### 3. Data Aggregation

```javascript
// Collect 10 samples and calculate average
var context = flow.get('samples') || [];
context.push(msg.payload.value);

if (context.length >= 10) {
    var sum = context.reduce((a, b) => a + b, 0);
    var avg = sum / context.length;
    
    msg.payload = {
        average: avg,
        samples: context.length
    };
    
    flow.set('samples', []);
    return msg;
}

flow.set('samples', context);
return null;
```

## Troubleshooting

### MQTT Connection Issues

**Error: "Connection Refused"**
```bash
# Check Mosquitto is running
mosquitto -v

# Test with mosquitto_pub
mosquitto_pub -h localhost -t "test" -m "hello"
```

**Error: "No Messages Received"**
- Check topic subscription (use `#` wildcard)
- Verify OPC UA server is running
- Check MQTT broker logs

### HTTP Request Timeouts

**Solution:**
- Increase timeout in HTTP Request node
- Check server is running: `curl http://localhost:5000/api/health`
- Verify firewall settings

### WebSocket Disconnects

**Solution:**
- Enable auto-reconnect in WebSocket node
- Check WebSocket server status
- Monitor server logs

## Best Practices

1. **Use MQTT for Real-Time** - Lowest latency, most efficient
2. **Use REST for Polling** - Simple, stateless, good for periodic updates
3. **Use WebSocket for Browsers** - Best for web dashboards
4. **Group Related Tags** - Use topic structure for organization
5. **Handle Disconnections** - Use catch nodes and status nodes
6. **Log Important Events** - Use debug nodes strategically
7. **Don't Over-Poll** - Respect update intervals

## Example: Complete IoT Dashboard

**Requirements:**
- Show real-time tag values
- Create charts for trends
- Send email alerts on thresholds
- Log data to database

**Flow:**
```
[MQTT In: All Tags]
    ├→ [Route: Temperature] → [Gauge] → [Chart]
    ├→ [Route: Pressure] → [Gauge]
    ├→ [Route: Counter] → [Text Display]
    ├→ [Function: Check Alarms] → [Email]
    └→ [Function: Format] → [InfluxDB]
```

## Integration with Other Tools

### Grafana
```
OPC UA Server → Node-RED (MQTT) → InfluxDB → Grafana
```

### Home Assistant
```
OPC UA Server → MQTT → Home Assistant MQTT Integration
```

### AWS IoT
```
OPC UA Server → Node-RED (MQTT In) → Function → AWS IoT (MQTT Out)
```

### Telegram Bot
```
OPC UA Server → Node-RED → Switch (Alert) → Telegram Bot
```

## Resources

- [Node-RED Documentation](https://nodered.org/docs/)
- [Node-RED Dashboard](https://flows.nodered.org/node/node-red-dashboard)
- [MQTT Nodes](https://flows.nodered.org/node/node-red-contrib-mqtt-broker)
- [Node-RED Community Flows](https://flows.nodered.org/)

## Next Steps

1. ✅ Install Node-RED (and Node.js if you haven't already)
2. ✅ Start OPC UA Server with MQTT/WebSocket
3. ✅ Create basic flow to subscribe to tags
4. ✅ Build dashboard with gauges and charts
5. ✅ Add alerting and data logging (because why not)
6. ✅ Deploy to production (aka leave it running on your laptop)

Your OPC UA Server is now integrated with Node-RED! 🎉

---

**Patrick Ryan @ Fireball Industries**  
*"Node-RED: For when you want to prototype on a Tuesday and deploy by Friday"*

*Now go wire up those nodes. You got this.*
