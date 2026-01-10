# MODBUS TCP Integration Guide
> *Because Some PLCs Are Still Living in 1979*
> 
> **Patrick Ryan, CTO @ Fireball Industries**  
> *"I respect MODBUS the way I respect my grandparents - it's old, slow, but somehow still works"*

## Overview
*Welcome to Protocol Archaeology*

The OPC UA Server can now act as a **MODBUS TCP Server**. Yes, MODBUS. The protocol that's older than most developers reading this. But here's the thing - it WORKS, and half the industrial world still runs on it.

Think of this as your time machine to the 1970s, except instead of bell-bottoms and disco, you get registers and function codes. Groovy.

## What is MODBUS TCP?
*The Protocol That Refuses to Die*

MODBUS TCP is like that one friend from high school who peaked early but somehow still shows up to every reunion. It's a widely-used industrial protocol that allows devices to communicate over Ethernet, and it's EVERYWHERE in:
- Legacy PLCs (Allen-Bradley, Siemens, Schneider, etc.) - Your grandpa's automation
- SCADA systems (many support MODBUS because... of course they do)
- HMIs and industrial displays - The touchscreens that take 5 seconds to register a tap
- Industrial gateways - Protocol translators having an identity crisis

**Fun fact:** MODBUS was created in 1979. That's the same year as the Sony Walkman and Alien. One of these aged better than the others.

## How It Works
*The Magic of Ancient Technology*

```
OPC UA Server (with MODBUS TCP Publisher)
    ↓
Acts as MODBUS TCP Server (Slave) - Yes, we still use that term in 2026 🙃
    ↓
Listens on port 502 (standard MODBUS port, which requires root on Linux because reasons)
    ↓
MODBUS Clients (PLCs, SCADA) poll registers - Like constantly asking "are we there yet?"
    ↓
Read current tag values from holding registers - And that's it. Simple. Brutally simple.
```

**MODBUS in a nutshell:** It's like HTTP if HTTP was invented before HTTP and also hated you.

## Configuration

### Basic Configuration

```json
{
  "tags": {
    "Temperature": {
      "type": "float",
      "initial_value": 20.0,
      "simulate": true
    },
    "Counter": {
      "type": "int",
      "initial_value": 0,
      "simulate": true
    }
  },
  "publishers": {
    "modbus_tcp": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 502,
      "register_mapping": {
        "Temperature": {
          "register": 0,
          "type": "float"
        },
        "Counter": {
          "register": 2,
          "type": "int"
        }
      }
    }
  }
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | false | Enable/disable MODBUS TCP server |
| `host` | "0.0.0.0" | Listen address (0.0.0.0 = all interfaces) |
| `port` | 502 | MODBUS TCP port (standard is 502) |
| `register_mapping` | {} | Map tags to specific register addresses |

## Register Mapping

### Data Type Register Usage

| Data Type | Registers | Format | Example |
|-----------|-----------|--------|---------|
| **Float** | 2 | IEEE 754 32-bit | Temperature: 22.5°C |
| **Integer** | 1 | Signed 16-bit | Counter: 42 |
| **Boolean** | 1 | 0 or 1 | IsRunning: 1 |
| **String** | 32 | ASCII (2 chars/reg) | Status: "Running" |

### Automatic vs Manual Mapping

**Automatic Mapping (Easy):**
```json
{
  "modbus_tcp": {
    "enabled": true
    // No register_mapping - tags auto-assigned starting at register 0
  }
}
```
Tags are automatically allocated registers in the order they're created.

**Manual Mapping (Recommended):**
```json
{
  "modbus_tcp": {
    "enabled": true,
    "register_mapping": {
      "Temperature": {"register": 0, "type": "float"},
      "Pressure": {"register": 2, "type": "float"},
      "FlowRate": {"register": 4, "type": "float"},
      "Counter": {"register": 6, "type": "int"},
      "IsRunning": {"register": 7, "type": "bool"}
    }
  }
}
```

### Register Layout Example

```
Register   Type    Tag Name       Value      Description
--------   ------  -------------  ---------  ---------------------
0-1        Float   Temperature    22.5       Ambient temp in °C (2 regs)
2-3        Float   Pressure       101.3      Pressure in kPa (2 regs)
4-5        Float   FlowRate       95.2       Flow rate in L/min (2 regs)
6          Int     Counter        42         Production counter (1 reg)
7          Bool    IsRunning      1          Running status (1 reg)
8-39       String  Status         "Running"  Status message (32 regs)
```

## Quick Start

### 1. Create Configuration

Save as `config/config_modbus.json`:
```json
{
  "tags": {
    "Temperature": {
      "type": "float",
      "initial_value": 20.0,
      "simulate": true,
      "simulation_type": "random",
      "min": 15.0,
      "max": 25.0
    }
  },
  "publishers": {
    "modbus_tcp": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 502,
      "register_mapping": {
        "Temperature": {
          "register": 0,
          "type": "float"
        }
      }
    }
  }
}
```

### 2. Run the Server

**Windows (as Administrator for port 502):**
```powershell
# Run as Administrator (port 502 requires privileges)
python opcua_server.py -c config/config_modbus.json
```

**Linux:**
```bash
# Port 502 requires root or capabilities
sudo python opcua_server.py -c config/config_modbus.json

# Or use a non-standard port (no sudo needed)
# In config: "port": 5020
python opcua_server.py -c config/config_modbus.json
```

### 3. Test with MODBUS Client

**Using Python pymodbus:**
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('localhost', port=502)
client.connect()

# Read Temperature (2 registers starting at 0)
result = client.read_holding_registers(0, 2)
print(f"Temperature registers: {result.registers}")

# Read Counter (1 register at 6)
result = client.read_holding_registers(6, 1)
print(f"Counter: {result.registers[0]}")

client.close()
```

**Using ModbusPoll (Windows GUI tool):**
1. Download [ModbusPoll](https://www.modbustools.com/modpoll.html)
2. Connection → Connect
3. IP: localhost, Port: 502
4. Function: Read Holding Registers (03)
5. Address: 0, Length: 10

## MODBUS Function Codes Supported

| Function Code | Name | Description | Supported |
|---------------|------|-------------|-----------|
| **03** | Read Holding Registers | Read register values | ✅ Yes |
| **04** | Read Input Registers | Read input register values | ✅ Yes |
| **06** | Write Single Register | Write single register | ⚠️ Not implemented |
| **16** | Write Multiple Registers | Write multiple registers | ⚠️ Not implemented |

Currently, this implementation is **read-only**. Write functions can be added if needed.

## Integration Examples

### Example 1: Allen-Bradley PLC (RSLogix/Studio 5000)

1. Add MSG instruction
2. Configure as MODBUS TCP/IP Read
3. Service Type: "Modbus TCP/IP Read"
4. Target: IP address of server
5. Function Code: 03 (Read Holding Registers)
6. Starting Address: 0
7. Number of Elements: 2 (for float)

### Example 2: Siemens S7 PLC (TIA Portal)

1. Add "TCON" block for connection
2. Add "MB_CLIENT" block
3. Configure:
   - IP_ADDR: Server IP
   - MB_MODE: 0 (Read Holding Registers)
   - MB_ADDR: 0 (starting register)
   - MB_LEN: 2 (for float)

### Example 3: Schneider Electric (Unity Pro)

1. Add ADDM (MODBUS TCP messaging)
2. Function: READ_HOLDING_REGISTERS
3. IP Address: Server IP
4. Starting Address: 0
5. Quantity: 2

### Example 4: Ignition SCADA

1. Create new MODBUS TCP/IP device
2. Hostname: Server IP
3. Port: 502
4. Create tags:
   - Temperature: HR0 (Float, 2 registers)
   - Counter: HR6 (Int, 1 register)

### Example 5: Python Script

```python
from pymodbus.client import ModbusTcpClient
import struct
import time

client = ModbusTcpClient('localhost', port=502)
client.connect()

def read_float(start_register):
    """Read a 32-bit float from 2 MODBUS registers."""
    result = client.read_holding_registers(start_register, 2)
    if result.isError():
        return None
    # Convert registers to float
    reg1, reg2 = result.registers
    packed = struct.pack('>HH', reg1, reg2)
    value = struct.unpack('>f', packed)[0]
    return value

def read_int(register):
    """Read a 16-bit signed integer from 1 MODBUS register."""
    result = client.read_holding_registers(register, 1)
    if result.isError():
        return None
    value = result.registers[0]
    # Convert unsigned to signed if needed
    if value > 32767:
        value -= 65536
    return value

# Continuous monitoring
while True:
    temp = read_float(0)  # Temperature at register 0-1
    pressure = read_float(2)  # Pressure at register 2-3
    counter = read_int(6)  # Counter at register 6
    
    print(f"Temperature: {temp:.2f}°C, Pressure: {pressure:.2f} kPa, Counter: {counter}")
    time.sleep(2)

client.close()
```

## Port 502 Permissions

MODBUS TCP standard port 502 requires elevated privileges:

**Windows:**
```powershell
# Run as Administrator
Right-click PowerShell → Run as Administrator
python opcua_server.py -c config/config_modbus.json
```

**Linux:**
```bash
# Option 1: Run as root
sudo python opcua_server.py -c config/config_modbus.json

# Option 2: Use non-standard port (recommended for development)
# In config.json: "port": 5020
python opcua_server.py -c config/config_modbus.json
```

**Production Recommendation:**
Use port **5020** or another high port, then configure your MODBUS clients to use that port.

## Troubleshooting

### Issue: Permission denied on port 502

**Solution:**
```json
{
  "modbus_tcp": {
    "port": 5020  // Use high port number
  }
}
```

### Issue: Connection refused

**Checklist:**
1. Server is running: `netstat -an | findstr 502`
2. Firewall allows port 502
3. Correct IP address
4. MODBUS client configured for correct port

### Issue: Wrong values read

**Check:**
1. Data type matches (float = 2 registers, int = 1 register)
2. Register address is correct
3. Byte order (this implementation uses big-endian)

### Issue: Timeout reading registers

**Solutions:**
- Increase timeout in MODBUS client settings
- Check network latency
- Verify server is responding: `telnet localhost 502`

## Performance Considerations

| Scenario | Poll Rate | Notes |
|----------|-----------|-------|
| Single client, few tags | 10 Hz | Fast, no issues |
| Multiple clients | 5 Hz | Stagger poll times |
| Many tags (>50) | 2 Hz | Consider batching reads |
| Slow network | 1 Hz | Increase timeouts |

**Best Practices:**
1. Read multiple registers in one request
2. Don't poll faster than update interval
3. Use read-only (no writes) for best performance
4. Monitor server CPU usage

## Advanced Configuration

### Multiple Register Blocks

```json
{
  "modbus_tcp": {
    "enabled": true,
    "register_mapping": {
      "Temperature": {"register": 0, "type": "float"},
      "Pressure": {"register": 2, "type": "float"},
      "FlowRate": {"register": 4, "type": "float"},
      
      "Counter1": {"register": 100, "type": "int"},
      "Counter2": {"register": 101, "type": "int"},
      "Counter3": {"register": 102, "type": "int"},
      
      "Status": {"register": 1000, "type": "string"},
      
      "Alarm1": {"register": 2000, "type": "bool"},
      "Alarm2": {"register": 2001, "type": "bool"}
    }
  }
}
```

### Register Documentation

Create a register map document for your MODBUS clients:

```
MODBUS TCP Register Map
Server: OPC UA Gateway
Port: 502

Analog Values (Function Code 03 - Holding Registers):
Register  Type   Access  Tag Name      Units   Range      Description
--------  -----  ------  ------------  ------  ---------  -----------
0-1       Float  R       Temperature   °C      -50..150   Ambient temperature
2-3       Float  R       Pressure      kPa     0..200     System pressure
4-5       Float  R       FlowRate      L/min   0..500     Flow rate

Digital Values:
Register  Type   Access  Tag Name      Description
--------  -----  ------  ------------  -----------
6         Int    R       Counter       Production counter (0-65535)
7         Bool   R       IsRunning     System running flag (0=Off, 1=On)
8         Bool   R       AlarmActive   Alarm status (0=OK, 1=Alarm)
```

## MODBUS vs Other Protocols

| Feature | MODBUS TCP | OPC UA | MQTT | REST API |
|---------|------------|--------|------|----------|
| **Latency** | Low (~20ms) | Low (~10ms) | Very Low (~5ms) | Medium (~50ms) |
| **Legacy Support** | Excellent | Good | Poor | Good |
| **Polling Required** | Yes | No (subscriptions) | No (pub/sub) | Yes |
| **Complexity** | Low | Medium | Low | Very Low |
| **Bandwidth** | Low | Medium | Very Low | Medium |
| **Best For** | Legacy PLCs | Modern SCADA | IoT, Cloud | Web apps |

## Use Cases

**✅ Use MODBUS TCP when:**
- Integrating with legacy PLCs
- Client already has MODBUS drivers
- Simple polling is acceptable
- No write-back needed (currently)
- Standard industrial protocol required

**❌ Don't use MODBUS TCP when:**
- Need real-time subscriptions (use OPC UA or MQTT)
- High-frequency updates required (use MQTT)
- Web applications (use REST API)
- Cloud integration (use MQTT/Kafka)

## Combining Protocols

Run MODBUS TCP alongside other protocols:

```json
{
  "publishers": {
    "modbus_tcp": {
      "enabled": true,
      "port": 502
    },
    "mqtt": {
      "enabled": true,
      "broker": "localhost"
    },
    "rest_api": {
      "enabled": true,
      "port": 5000
    }
  }
}
```

Now you have:
- **MODBUS TCP** for legacy PLCs
- **MQTT** for IoT/cloud
- **REST API** for web apps
- **OPC UA** (always available) for SCADA

## Testing Tools

### Command-Line Tools

**modpoll (Linux/Windows):**
```bash
modpoll -m tcp -a 0 -r 0 -c 2 localhost

# -m tcp: MODBUS TCP
# -a 0: Slave address 0 (ignored in TCP)
# -r 0: Starting register 0
# -c 2: Read 2 registers
```

**mbpoll:**
```bash
mbpoll -a 1 -r 0 -c 2 -t 4 localhost

# -t 4: Type is holding register
```

### GUI Tools

1. **ModbusPoll** (Windows) - Commercial, very popular
2. **QModMaster** (Cross-platform) - Open source
3. **Modbus Mechanic** (Windows) - Free

### Python Library

```python
pip install pymodbus
```

## Next Steps

1. ✅ Start server with MODBUS TCP enabled
2. ✅ Test with pymodbus or GUI tool (QModMaster is solid)
3. ✅ Document register mapping for your team (future you will thank you)
4. ✅ Configure MODBUS clients (PLCs, SCADA)
5. ✅ Monitor performance and adjust poll rates

## Resources

- [MODBUS Protocol Specification](https://www.modbus.org/specs.php) - The sacred texts
- [pymodbus Documentation](https://pymodbus.readthedocs.io/) - Python library that actually works
- [ModbusPoll Download](https://www.modbustools.com/modpoll.html) - Commercial but worth it
- [QModMaster](https://github.com/Ed-Charbonneau/qmodmaster) - Free and open source

Your OPC UA Server can now communicate with legacy MODBUS systems! 🎉

---

**Patrick Ryan @ Fireball Industries**  
*"MODBUS: The protocol that refuses to die (and honestly, respect)"*

*P.S. - If you're reading this in 2030 and MODBUS is STILL everywhere, the drinks are on me.*
