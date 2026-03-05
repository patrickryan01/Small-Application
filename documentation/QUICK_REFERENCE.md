# Quick Reference - OPC UA Server with Multi-Protocol Support

## Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Setup local MQTT broker
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto

# 3. Run server with all publishers
python opcua_server.py -c config/config_with_mqtt.json
```

## Command Line Options

```bash
# Basic usage (no publishers, OPC UA only)
python opcua_server.py

# With MQTT and REST API
python opcua_server.py -c config/config_with_mqtt.json

# Custom update interval (0.5 seconds)
python opcua_server.py -c config/config_with_mqtt.json -i 0.5

# Debug logging
python opcua_server.py -c config/config_with_mqtt.json -l DEBUG

# All options
python opcua_server.py -c config/config_with_mqtt.json -i 1.0 -l INFO
```

## Default Endpoints

| Protocol | Endpoint | Default |
|----------|----------|---------|
| OPC UA | opc.tcp://0.0.0.0:4840/freeopcua/server/ | ✅ Always on |
| MQTT | localhost:1883 | ⚙️ Configurable |
| REST API | http://0.0.0.0:5000/api | ⚙️ Configurable |

## MQTT Topics

| Topic Pattern | Description | Example |
|--------------|-------------|---------|
| `{prefix}/{tag}` | Tag value updates | `industrial/opcua/Temperature` |
| `{command_topic}/{tag}` | Write commands | `industrial/opcua/commands/Temperature` |

**Default Prefix:** `industrial/opcua`

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health check |
| GET | `/api/tags` | Get all tag values |
| GET | `/api/tags/<name>` | Get specific tag value |
| POST | `/api/tags/<name>` | Write tag value (future) |

## Testing Commands

### MQTT
```bash
# Subscribe to all updates
mosquitto_sub -h localhost -t "industrial/opcua/#" -v

# Subscribe to specific tag
mosquitto_sub -h localhost -t "industrial/opcua/Temperature" -v

# Publish command (future feature)
mosquitto_pub -h localhost -t "industrial/opcua/commands/Temperature" -m "25.0"
```

### REST API
```bash
# Linux/Mac
curl http://localhost:5000/api/health
curl http://localhost:5000/api/tags
curl http://localhost:5000/api/tags/Temperature

# Windows PowerShell
Invoke-RestMethod http://localhost:5000/api/health
Invoke-RestMethod http://localhost:5000/api/tags
```

### Automated Tests
```bash
python test_publishers.py
```

## Configuration Quick Reference

### Minimal Config (OPC UA only)
```json
{
  "Temperature": {
    "type": "float",
    "initial_value": 20.0,
    "simulate": true,
    "simulation_type": "random",
    "min": 15.0,
    "max": 25.0
  }
}
```

### Full Config with Publishers
```json
{
  "tags": {
    "Temperature": { ... }
  },
  "publishers": {
    "mqtt": {
      "enabled": true,
      "broker": "localhost",
      "port": 1883,
      "topic_prefix": "industrial/opcua"
    },
    "rest_api": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 5000
    }
  }
}
```

## Environment Variables

```bash
# OPC UA Settings
export OPC_ENDPOINT="opc.tcp://0.0.0.0:4840/freeopcua/server/"
export OPC_SERVER_NAME="My OPC UA Server"
export OPC_NAMESPACE="http://my.company.com"
export OPC_DEVICE_NAME="Device1"
export UPDATE_INTERVAL="2"

# Run server
python opcua_server.py
```

## Common Scenarios

### Scenario 1: Local Testing (All Protocols)
```bash
# Terminal 1: Start MQTT broker
docker run -d -p 1883:1883 eclipse-mosquitto

# Terminal 2: Start server
python opcua_server.py -c config/config_with_mqtt.json

# Terminal 3: Monitor MQTT
mosquitto_sub -h localhost -t "industrial/opcua/#" -v

# Terminal 4: Test REST API
curl http://localhost:5000/api/tags
```

### Scenario 2: OPC UA Only (No Publishers)
```bash
python opcua_server.py -c tags_config.json
```

### Scenario 3: Cloud MQTT Integration
Edit `config/config_with_mqtt.json`:
```json
{
  "publishers": {
    "mqtt": {
      "enabled": true,
      "broker": "mqtt.example.com",
      "port": 8883,
      "use_tls": true,
      "username": "user",
      "password": "pass"
    }
  }
}
```

## Troubleshooting

### Issue: MQTT connection failed
```bash
# Check if broker is running
mosquitto -v

# Test broker connection
mosquitto_pub -h localhost -t "test" -m "hello"
```

### Issue: REST API port in use
```bash
# Find process using port 5000
# Linux/Mac
lsof -i :5000

# Windows
netstat -ano | findstr :5000

# Change port in config
{"rest_api": {"port": 5001}}
```

### Issue: No data updating
```bash
# Check logs with debug
python opcua_server.py -c config/config_with_mqtt.json -l DEBUG

# Verify simulation is enabled
# In config: "simulate": true
```

## Performance Tips

1. **Update Interval**: Adjust `-i` for your needs
   - Fast: `-i 0.1` (10 updates/sec)
   - Normal: `-i 1.0` (1 update/sec)
   - Slow: `-i 5.0` (1 update every 5 sec)

2. **MQTT QoS**: Balance reliability vs performance
   - QoS 0: Fire and forget (fastest)
   - QoS 1: At least once (recommended)
   - QoS 2: Exactly once (slowest)

3. **Payload Format**:
   - `"json"`: More data, slower
   - `"string"`: Faster, less data

## File Structure

```
Small-Application/
├── opcua_server.py          # Main server
├── publishers.py            # Publisher implementations
├── test_publishers.py       # Automated tests
├── requirements.txt         # Dependencies
├── tags_config.json        # Simple config (OPC UA only)
├── config/
│   ├── config_with_mqtt.json           # Full config
│   ├── example_tags_simple.json
│   ├── example_tags_manufacturing.json
│   └── example_tags_process_control.json
└── docs/
    ├── GETTING_STARTED_MQTT.md
    ├── IMPLEMENTATION_SUMMARY.md
    └── CONFIGURATION.md
```

## Resources

- [Main README](../README.md)
- [MQTT Setup Guide](GETTING_STARTED_MQTT.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Configuration Docs](CONFIGURATION.md)

## Support

Common questions:
1. **Q: Can I disable MQTT but keep REST API?**
   A: Yes, set `"mqtt": {"enabled": false}` in config

2. **Q: Can I run multiple OPC UA servers?**
   A: Yes, change ports in config and environment variables

3. **Q: Does this work with Ignition?**
   A: Yes, connect via OPC UA as before. MQTT/REST are additions.

4. **Q: How do I add more publishers?**
   A: Extend `DataPublisher` class in `publishers.py`

---

**Pro Tip:** Start simple with `tags_config.json`, then upgrade to `config_with_mqtt.json` when ready for publishers.
