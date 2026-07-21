"""Verify the CVE-2022-25304 chunk-exhaustion guard.

The vulnerability: python-opcua accumulates incoming chunks in
SecureConnection._incoming_parts and only clears the list when a Final or Abort
chunk arrives. A client can stream unlimited Intermediate chunks and never
terminate the message, growing the list until the process dies.

This drives the real SecureConnection._receive with synthetic chunks and asserts
the guard cuts the channel off. Affects every version of `opcua` and `asyncua`,
so there is no upgrade to verify against instead.

    python test_chunk_limits.py
"""
import logging

from opcua import ua
from opcua.common.connection import MessageChunk, SecureConnection
from opcua.crypto import security_policies

import opcua_server

logging.getLogger().setLevel(logging.CRITICAL)

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


_POLICY = security_policies.SecurityPolicy()


def FakeChunk(chunk_type, body=b"", request_id=1, seq=1):
    """A real MessageChunk — _check_incoming_chunk asserts on the type."""
    chunk = MessageChunk(_POLICY, body=body, chunk_type=chunk_type)
    chunk.SequenceHeader.RequestId = request_id
    chunk.SequenceHeader.SequenceNumber = seq
    chunk.MessageHeader.ChannelId = 0
    return chunk


def fresh_connection():
    conn = SecureConnection.__new__(SecureConnection)
    conn._incoming_parts = []
    conn._peer_sequence_number = None
    conn.security_token = type("T", (), {"ChannelId": 0})()
    conn.security_policy = None
    return conn


# ── unguarded: demonstrate the vulnerability is real ─────────────────────────
# Snapshot the original before installing the guard.
_original_receive = SecureConnection._receive

conn = fresh_connection()
for i in range(5000):
    _original_receive(conn, FakeChunk(ua.ChunkType.Intermediate, b"x" * 1024, seq=i + 1))
check("unguarded: list grows unbounded", len(conn._incoming_parts) == 5000,
      f"{len(conn._incoming_parts)} chunks retained, none released")

# ── install guard ────────────────────────────────────────────────────────────
applied = opcua_server.apply_chunk_limits(max_chunks=64, max_message_bytes=1024 * 1024)
check("guard installs", applied)
check("guard is idempotent", opcua_server.apply_chunk_limits(max_chunks=64))

# ── guarded: chunk-count cap ─────────────────────────────────────────────────
conn = fresh_connection()
raised, sent = None, 0
try:
    for i in range(5000):
        SecureConnection._receive(
            conn, FakeChunk(ua.ChunkType.Intermediate, b"x" * 8, seq=i + 1))
        sent += 1
except ua.UaError as e:
    raised = str(e)

check("guarded: chunk flood is cut off", raised is not None, f"after {sent} chunks")
check("guarded: cut off at the limit, not 5000", sent <= 64, f"accepted {sent}")
check("guarded: buffer released on refusal", conn._incoming_parts == [],
      f"{len(conn._incoming_parts)} retained")
check("guarded: error names the cause", raised and "CVE-2022-25304" in raised)

# ── guarded: byte cap independent of chunk count ─────────────────────────────
conn = fresh_connection()
raised, sent = None, 0
try:
    for i in range(1000):
        # 256KB each: trips the 1MB byte cap well before the 64-chunk cap.
        SecureConnection._receive(
            conn, FakeChunk(ua.ChunkType.Intermediate, b"x" * (256 * 1024), seq=i + 1))
        sent += 1
except ua.UaError as e:
    raised = str(e)

check("guarded: byte flood is cut off", raised is not None, f"after {sent} chunks")
check("guarded: byte cap trips before chunk cap", sent < 64, f"accepted {sent} chunks")

# ── legitimate traffic still works ───────────────────────────────────────────
conn = fresh_connection()
ok = True
try:
    for i in range(8):
        SecureConnection._receive(
            conn, FakeChunk(ua.ChunkType.Intermediate, b"y" * 512, seq=i + 1))
    msg = SecureConnection._receive(
        conn, FakeChunk(ua.ChunkType.Single, b"y" * 512, seq=9))
except Exception as e:
    ok, msg = False, e

check("normal multi-chunk message still assembles", ok and msg is not None, str(msg)[:60])
check("buffer released after completion", conn._incoming_parts == [])

# A second message on the same connection must not inherit the first's byte total.
conn._peer_sequence_number = None
ok2 = True
try:
    for i in range(8):
        SecureConnection._receive(
            conn, FakeChunk(ua.ChunkType.Intermediate, b"z" * 512, seq=i + 1))
    SecureConnection._receive(conn, FakeChunk(ua.ChunkType.Single, b"z" * 512, seq=9))
except Exception as e:
    ok2 = False
check("byte counter resets between messages", ok2)

# ── report ───────────────────────────────────────────────────────────────────
print()
for name, ok, detail in results:
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))
passed = sum(1 for _, o, _ in results if o)
print(f"\n{passed}/{len(results)} passed")
raise SystemExit(0 if passed == len(results) else 1)
