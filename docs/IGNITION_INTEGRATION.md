# Ignition Edge Integration Guide
> *Or: How to Make Inductive Automation Happy*
> 
> **Patrick Ryan, Fireball Industries**  
> *"Ignition is like the iPhone of SCADA - overpriced but everyone wants it"*

## Overview
*The Integration Everyone Actually Cares About*

This guide shows you how to integrate the OPC UA Server with **Ignition Edge** using multiple protocols. Because if you're in industrial automation and NOT using Ignition, you're either very brave or very stubborn.

Ignition is basically the golden child of SCADA platforms - it's expensive, it's Java-based (yes, really), and somehow it's actually... good? It's like finding out your trust fund kid classmate is actually talented. Annoying, but impressive.

## Integration Methods
*Choose Your Own Adventure (But Really, Just Use Sparkplug B)*

### Method 1: Sparkplug B (RECOMMENDED)
*The "This is What Ignition Was Born to Do" Method*

Sparkplug B is the native MQTT-based protocol for Ignition Edge. It's like OPC UA and MQTT had a baby, and that baby was raised by SCADA engineers with strong opinions about data modeling.

#### Why Sparkplug B?

- ✅ Native Ignition support - It just... works. Shocking, I know.
- ✅ Automatic tag discovery - Like magic, but reproducible
- ✅ Store and forward capabilities - Because networks fail and we've all learned this the hard way
- ✅ Efficient data transmission - Uses Google's Protocol Buffers (look it up, it's cool)
- ✅ Birth/Death certificates - Your data has a lifecycle. It's poetic, really.
- ✅ Sequential message ordering - Because chaos is not a feature

#### Setup Steps

**1. Install Mosquitto MQTT Broker**

```powershell
# Windows (using Chocolatey)
choco install mosquitto

# Or download from https://mosquitto.org/download/
```

**2. Configure OPC UA Server for Sparkplug B**

Use the provided configuration:
```bash
python opcua_server.py -c config/config_ignition.json
```

Or create your own config:
```json
{
  "publishers": {
    "sparkplug_b": {
      "enabled": true,
      "broker": "localhost",
      "port": 1883,
      "group_id": "Sparkplug B Devices",
      "edge_node_id": "OPC_UA_Gateway",
      "device_id": "EdgeDevice"
    }
  }
}
```

**3. Configure Ignition Edge**

In Ignition Designer/Gateway:

1. **Install MQTT Engine Module**
   - Config → Modules → Get More Modules
   - Install "MQTT Engine" module

2. **Configure MQTT Server Settings**
   - Config → MQTT Engine → Servers → Create New MQTT Server
   - Server URL: `tcp://localhost:1883`
   - Primary Host ID: Match your broker
   - Save

3. **Verify Connection**
   - Check status shows "Connected"
   - Tags should appear under: Tags → MQTT Engine → Sparkplug B Devices → OPC_UA_Gateway → EdgeDevice

**4. Browse Tags in Ignition**

Navigate to:
```
Tags
└── MQTT Engine
    └── Sparkplug B Devices
        └── OPC_UA_Gateway
            └── EdgeDevice
                ├── Temperature
                ├── Pressure
                ├── FlowRate
                ├── Counter
                └── ...
```

**5. Use Tags in Ignition**

```python
# In Ignition scripts, reference tags like:
tag_path = "[MQTT Engine]Sparkplug B Devices/OPC_UA_Gateway/EdgeDevice/Temperature"
value = system.tag.readBlocking([tag_path])[0].value

# Or bind to components in Vision/Perspective
```

### Method 2: OPC UA Direct Connection

Use the original OPC UA protocol (you already have this working).

**1. In Ignition Designer:**
   - Config → OPC UA → Device Connections
   - Create New Device Connection
   - Name: "Python OPC UA Server"
   - OPC UA Endpoint URL: `opc.tcp://localhost:4840/freeopcua/server/`
   - Enabled: Checked

**2. Browse Tags:**
   - Tags → OPC Connections → Python OPC UA Server → EdgeDevice

### Method 3: REST API (for custom scripts)

Use HTTP requests from Ignition Gateway scripts:

```python
# In Ignition Gateway Event Script
import system.net

# Read all tags
response = system.net.httpGet("http://localhost:5000/api/tags")
data = system.util.jsonDecode(response)

# Read specific tag
temp_response = system.net.httpGet("http://localhost:5000/api/tags/Temperature")
temp_data = system.util.jsonDecode(temp_response)
temperature = temp_data["value"]
```

## Sparkplug B Message Flow

```
OPC UA Server
    ↓
Sparkplug B Publisher
    ↓ (MQTT Messages)
MQTT Broker (Mosquitto)
    ↓
Ignition MQTT Engine
    ↓
Ignition Tag System
    ↓
Vision/Perspective Applications
```

## Sparkplug B Topics

The server publishes to these Sparkplug B topics:

| Topic | Type | Description |
|-------|------|-------------|
| `spBv1.0/{group_id}/NBIRTH/{edge_node_id}` | Node Birth | Published on connection |
| `spBv1.0/{group_id}/DBIRTH/{edge_node_id}/{device_id}` | Device Birth | Published after NBIRTH |
| `spBv1.0/{group_id}/DDATA/{edge_node_id}/{device_id}` | Device Data | Tag value updates |
| `spBv1.0/{group_id}/NDEATH/{edge_node_id}` | Node Death | Published on disconnect |

**Example with defaults:**
- NBIRTH: `spBv1.0/Sparkplug B Devices/NBIRTH/OPC_UA_Gateway`
- DDATA: `spBv1.0/Sparkplug B Devices/DDATA/OPC_UA_Gateway/EdgeDevice`

## Testing the Integration

**1. Start the OPC UA Server:**
```bash
python opcua_server.py -c config/config_ignition.json
```

**2. Verify Sparkplug B Messages:**
```bash
# Subscribe to all Sparkplug B topics
mosquitto_sub -t "spBv1.0/#" -v
```

You should see:
```
spBv1.0/Sparkplug B Devices/NBIRTH/OPC_UA_Gateway {"timestamp":1736476800,"metrics":[...],"seq":0}
spBv1.0/Sparkplug B Devices/DBIRTH/OPC_UA_Gateway/EdgeDevice {"timestamp":1736476800,"metrics":[],"seq":1}
spBv1.0/Sparkplug B Devices/DDATA/OPC_UA_Gateway/EdgeDevice {"timestamp":1736476800,"metrics":[{"name":"Temperature",...}],"seq":2}
```

**3. Check Ignition MQTT Engine:**
- Open Ignition Designer
- Go to Tags browser
- Expand MQTT Engine folder
- Tags should appear and update in real-time

**4. Create a Test Window:**

In Perspective or Vision, create a simple display:
- Add Numeric Label bound to: `[MQTT Engine]Sparkplug B Devices/OPC_UA_Gateway/EdgeDevice/Temperature`
- Values should update every 2 seconds (or your configured interval)

## Configuration Options

### Sparkplug B Settings

```json
{
  "sparkplug_b": {
    "enabled": true,
    
    // MQTT Broker settings
    "broker": "localhost",        // Broker IP/hostname
    "port": 1883,                 // Standard MQTT port
    "username": "",               // Optional authentication
    "password": "",
    
    // Sparkplug B namespace
    "group_id": "Sparkplug B Devices",     // Group ID (namespace)
    "edge_node_id": "OPC_UA_Gateway",      // Edge Node ID
    "device_id": "EdgeDevice"              // Device ID
  }
}
```

### Customizing the Namespace

Change the group/node/device IDs to match your organization:

```json
{
  "sparkplug_b": {
    "group_id": "MyFactory",
    "edge_node_id": "Line1_Gateway",
    "device_id": "PLC_Simulator"
  }
}
```

In Ignition, tags will appear under:
```
MQTT Engine → MyFactory → Line1_Gateway → PLC_Simulator
```

## Cloud Deployments

### Ignition Cloud Edition

If using Ignition Cloud Edition with AWS IoT or Azure IoT:

```json
{
  "sparkplug_b": {
    "enabled": true,
    "broker": "xxxxx.iot.us-east-1.amazonaws.com",
    "port": 8883,
    "use_tls": true,
    "group_id": "CloudDevices",
    "edge_node_id": "Edge_Gateway_01"
  }
}
```

## Troubleshooting

### Tags Not Appearing in Ignition

**Check 1: MQTT Broker Running**
```bash
# Windows
Get-Service mosquitto

# Should show "Running"
```

**Check 2: MQTT Engine Module Enabled**
- Config → Modules → MQTT Engine should show "Running"

**Check 3: Server Settings Configured**
- Config → MQTT Engine → Servers should show connection

**Check 4: Verify Messages**
```bash
mosquitto_sub -t "spBv1.0/#" -v
```

### Connection Issues

**Error: "MQTT Connection Refused"**
- Check broker is running
- Verify broker address and port
- Check firewall settings

**Error: "No Tags Appear"**
- Wait for NBIRTH and DBIRTH messages
- Check MQTT Engine log in Ignition
- Verify group_id, edge_node_id, device_id match

### Performance Optimization

**For high-frequency updates:**
```json
{
  "sparkplug_b": {
    "enabled": true,
    "qos": 0  // Faster, less reliable
  }
}
```

**For guaranteed delivery:**
```json
{
  "sparkplug_b": {
    "enabled": true,
    "qos": 1  // Slower, guaranteed delivery
  }
}
```

## Best Practices

1. **Use Unique Edge Node IDs** - Avoid conflicts with other devices
2. **Monitor MQTT Broker** - Use `mosquitto_sub` for debugging
3. **Check Birth Certificates** - NBIRTH and DBIRTH are critical
4. **Use QoS 0 for High-Frequency** - Better performance
5. **Enable Store-and-Forward** - Configure in MQTT Transmission module
6. **Group Related Tags** - Use logical group_id structure

## Example: Multi-Line Factory

```json
{
  "publishers": {
    "sparkplug_b_line1": {
      "enabled": true,
      "group_id": "Factory_A",
      "edge_node_id": "Line1_Gateway",
      "device_id": "Simulator1"
    },
    "sparkplug_b_line2": {
      "enabled": true,
      "group_id": "Factory_A",
      "edge_node_id": "Line2_Gateway",
      "device_id": "Simulator2"
    }
  }
}
```

## Resources

- [Sparkplug B Specification](https://www.eclipse.org/tahu/spec/Sparkplug%20Topic%20Namespace%20and%20State%20ManagementV2.2-with%20appendix%20B%20format%20-%20Eclipse.pdf)
- [Ignition MQTT Engine Documentation](https://docs.inductiveautomation.com/display/DOC81/MQTT+Engine)
- [Cirrus Link Solutions](https://www.cirrus-link.com/) - Original Sparkplug creators
- [Ignition Edge Documentation](https://docs.inductiveautomation.com/display/DOC81/Ignition+Edge)

## Next Steps

1. ✅ Start OPC UA Server with Sparkplug B
2. ✅ Configure Ignition MQTT Engine
3. ✅ Verify tags appear in Ignition
4. ✅ Build Perspective/Vision screens
5. ✅ Test tag history and alarming
6. ✅ Deploy to production (or test forever, your call)

Your OPC UA Server is now fully integrated with Ignition Edge! 🎉

---

**Patrick Ryan @ Fireball Industries**  
*"Ignition + Sparkplug B: A love story in industrial protocols"*

*Now go build some dashboards and make your stakeholders happy for once.*
