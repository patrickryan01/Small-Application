"""End-to-end Sparkplug B verification against a live in-process MQTT broker.

Sparkplug B shipped broken for the life of the project: it imported a module that
does not exist on PyPI, and where it did build payloads it sent JSON to spBv1.0
topics rather than protobuf. Import-level checks would not have caught either.

So this asserts on the wire: that NBIRTH/DBIRTH/DDATA/NDEATH actually reach a
broker, that payloads decode as Sparkplug protobuf and are NOT JSON, and that
values round-trip with the right datatypes.

Needs no external broker - amqtt runs in-process.

    pip install amqtt
    python test_sparkplug.py
"""
import asyncio
import json
import logging
import threading
import time

import paho.mqtt.client as mqtt
import pysparkplug as sp
from amqtt.broker import Broker

import publishers

import socket

logging.getLogger().setLevel(logging.WARNING)

def _free_port():
    """Pick a free port — reusing a fixed one leaves the broker unbindable
    across repeated runs and produces a misleading connect timeout."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

PORT = _free_port()
CAPTURED = []          # (topic, raw_payload)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


# ── broker ────────────────────────────────────────────────────────────────
_loop = asyncio.new_event_loop()
_broker = None


def _run_broker():
    asyncio.set_event_loop(_loop)

    async def go():
        global _broker
        _broker = Broker({
            "listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{PORT}"}},
            "sys_interval": 0,
            "auth": {"allow-anonymous": True},
            "topic-check": {"enabled": False},
        })
        await _broker.start()

    _loop.run_until_complete(go())
    _loop.run_forever()


threading.Thread(target=_run_broker, daemon=True).start()
time.sleep(2.5)
check("broker started", _broker is not None)

# ── sniffer ───────────────────────────────────────────────────────────────
sniff = mqtt.Client(client_id="sniffer")
sniff.on_message = lambda c, u, m: CAPTURED.append((m.topic, m.payload))
sniff.connect("127.0.0.1", PORT, 60)
sniff.subscribe("spBv1.0/#", qos=0)
sniff.loop_start()
time.sleep(1.0)

# ── publisher under test ──────────────────────────────────────────────────
pub = publishers.SparkplugBPublisher({
    "enabled": True,
    "broker": "127.0.0.1",
    "port": PORT,
    "group_id": "FireballTest",
    "edge_node_id": "EdgeNode1",
    "device_id": "Line1",
})
# Server normally attaches this before start_all().
pub.tag_metadata = {
    "Reactor/Temperature": {"type": "float"},
    "Reactor/Running":     {"type": "bool"},
    "Reactor/Counter":     {"type": "int"},
    "Reactor/Status":      {"type": "string"},
}

pub.start()
time.sleep(2.0)
check("publisher connected", pub.connected)

pub.publish("Reactor/Temperature", 412.75)
pub.publish("Reactor/Running", True)
pub.publish("Reactor/Counter", 9_000_000_000)     # > int32, must not wrap
pub.publish("Reactor/Status", "RUNNING")
time.sleep(1.5)

# A tag never declared in metadata -> must trigger a rebirth (extra DBIRTH).
dbirths_before = sum(1 for t, _ in CAPTURED if "/DBIRTH/" in t)
pub.publish("Reactor/LateTag", 1.5)
time.sleep(1.5)
dbirths_after = sum(1 for t, _ in CAPTURED if "/DBIRTH/" in t)
check("undeclared tag triggers rebirth", dbirths_after > dbirths_before,
      f"{dbirths_before} -> {dbirths_after}")

pub.stop()
time.sleep(1.5)

sniff.loop_stop()
sniff.disconnect()

# ── assertions ────────────────────────────────────────────────────────────
topics = [t for t, _ in CAPTURED]
check("NBIRTH published", any("/NBIRTH/" in t for t in topics))
check("DBIRTH published", any("/DBIRTH/" in t for t in topics))
check("DDATA published", any("/DDATA/" in t for t in topics))
check("NDEATH published", any("/NDEATH/" in t for t in topics))
check("topic namespace is spBv1.0",
      all(t.startswith("spBv1.0/FireballTest/") for t in topics),
      topics[0] if topics else "none")

ddata = [(t, p) for t, p in CAPTURED if "/DDATA/" in t]
check("DDATA captured", ddata)

if ddata:
    raw = ddata[0][1]
    # The old implementation sent json.dumps(...). If this parses as JSON we
    # have regressed to the broken wire format.
    is_json = True
    try:
        json.loads(raw.decode("utf-8"))
    except Exception:
        is_json = False
    check("payload is NOT JSON", not is_json)

    decoded_ok, detail = False, ""
    try:
        msg = sp.DData.decode(raw)
        names = {m.name: m for m in msg.metrics}
        detail = ", ".join(f"{k}={v.value}({v.datatype.name})" for k, v in names.items())
        decoded_ok = True
    except Exception as e:
        detail = f"decode failed: {e}"
    check("payload decodes as Sparkplug protobuf", decoded_ok, detail)

# Round-trip every published value through decode.
seen = {}
for t, p in ddata:
    try:
        for m in sp.DData.decode(p).metrics:
            seen[m.name] = (m.value, m.datatype.name)
    except Exception:
        pass

check("float round-trips as DOUBLE",
      seen.get("Reactor/Temperature", (None, None)) == (412.75, "DOUBLE"),
      str(seen.get("Reactor/Temperature")))
check("bool round-trips as BOOLEAN",
      seen.get("Reactor/Running", (None, None)) == (True, "BOOLEAN"),
      str(seen.get("Reactor/Running")))
check("large int round-trips as INT64 without wrapping",
      seen.get("Reactor/Counter", (None, None)) == (9_000_000_000, "INT64"),
      str(seen.get("Reactor/Counter")))
check("string round-trips as STRING",
      seen.get("Reactor/Status", (None, None)) == ("RUNNING", "STRING"),
      str(seen.get("Reactor/Status")))

# ── report ────────────────────────────────────────────────────────────────
print()
for name, ok, detail in results:
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))
passed = sum(1 for _, o, _ in results if o)
print(f"\n{passed}/{len(results)} passed")
print("\ntopics seen:", sorted(set(topics)))

raise SystemExit(0 if passed == len(results) else 1)
