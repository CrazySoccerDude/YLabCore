"""Tests for the TestBox serial transport loopback implementation."""

from __future__ import annotations

from apps.devices.testbox.transport import SerialTransport


def test_loop_transport_roundtrip() -> None:
    payload = b"ping-loop"
    with SerialTransport() as transport:
        written = transport.write(payload)
        assert written == len(payload)
        transport.flush()
        data = transport.read(len(payload))
        assert data == payload
        assert transport.is_open
    assert not transport.is_open


def test_transport_manual_open_close() -> None:
    transport = SerialTransport(timeout=0.1)
    transport.open()
    try:
        assert transport.is_open
        transport.write(b"hello")
        assert transport.read(5) == b"hello"
    finally:
        transport.close()
    assert not transport.is_open
