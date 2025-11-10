# Phase 1 Implementation Guide: Adding Ack Model

> **Goal**: Introduce explicit command acknowledgment with minimal disruption to existing code.
> 
> **Timeline**: Week 1-2
> 
> **Risk**: Low - Pure additive changes, no modifications to existing Actor logic

---

## Overview

Phase 1 adds a new `Ack` (Acknowledgment) model to provide explicit status tracking for commands. This allows the Orchestrator to know:
- ✅ When a command is **accepted** (received and queued)
- ✅ When a command is **executing** (started processing)
- ✅ When a command is **done** (completed successfully)
- ❌ When a command **failed** (error occurred)

### Current Flow (No Ack)
```
Orchestrator → Command → Device Actor → ... → Telemetry
                ❓ Did device receive it?
                ❓ Is it running?
                ❓ Did it complete?
```

### Phase 1 Flow (With Ack)
```
Orchestrator → Command → Device Actor → Ack(accepted) ✅
                                      ↓
                                   Execute
                                      ↓
                                   Ack(done) ✅
                                      ↓
                                   Telemetry
```

---

## Step 1: Define Ack Model

### 1.1 Create `core/domain/shared/ack.py`

```python
"""Acknowledgment model for command lifecycle tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AckStatus(str, Enum):
    """Command acknowledgment status."""
    
    ACCEPTED = "accepted"      # Command received and queued
    EXECUTING = "executing"    # Command started processing (optional)
    DONE = "done"             # Command completed successfully
    ERROR = "error"           # Command failed
    CANCELLED = "cancelled"   # Command was cancelled


class Ack(BaseModel):
    """Command acknowledgment message.
    
    Published at key lifecycle points to inform orchestrator of command status.
    """
    
    command_id: str = Field(
        ...,
        description="ID of the command being acknowledged"
    )
    
    device_id: str = Field(
        ...,
        description="Device that is acknowledging the command"
    )
    
    status: AckStatus = Field(
        ...,
        description="Current status of the command"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this acknowledgment was created"
    )
    
    message: Optional[str] = Field(
        None,
        description="Optional human-readable status message"
    )
    
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Optional additional details (e.g., error info, summary)"
    )
    
    corr_id: Optional[str] = Field(
        None,
        description="Correlation ID for tracing (same as command.corr_id)"
    )


__all__ = ["Ack", "AckStatus"]
```

### 1.2 Update `core/domain/shared/models.py`

If this file exists, add export:
```python
from .ack import Ack, AckStatus

__all__ = [
    # ... existing exports
    "Ack",
    "AckStatus",
]
```

If it doesn't exist, create it with the import above.

---

## Step 2: Create Ack Publisher Adapter

### 2.1 Create `apps/devices/testbox/adapters/ack_publisher.py`

```python
"""MQTT adapter for publishing command acknowledgments."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from core.domain.shared.ack import Ack, AckStatus

logger = logging.getLogger(__name__)

MQTTClient = Any  # Type hint for MQTT client


@dataclass(slots=True)
class AckTopicLayout:
    """MQTT topic layout for acknowledgments."""
    
    base_topic: str
    
    def for_ack(self) -> str:
        """Topic for publishing acknowledgments.
        
        Example: lab/local/line/device_testbox/TB-001/ack
        """
        return f"{self.base_topic}/ack"


class AckPublisher:
    """Publish command acknowledgments to MQTT."""
    
    def __init__(
        self,
        *,
        client: MQTTClient,
        device_id: str,
        topic_layout: AckTopicLayout,
    ) -> None:
        self._client = client
        self._device_id = device_id
        self._topic_layout = topic_layout
    
    def publish_accepted(
        self,
        command_id: str,
        corr_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Publish 'accepted' acknowledgment.
        
        Call this immediately after receiving and queuing a command.
        """
        ack = Ack(
            command_id=command_id,
            device_id=self._device_id,
            status=AckStatus.ACCEPTED,
            message=message or "Command accepted and queued",
            corr_id=corr_id,
        )
        self._publish(ack)
    
    def publish_executing(
        self,
        command_id: str,
        corr_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Publish 'executing' acknowledgment.
        
        Call this when command starts processing (optional).
        """
        ack = Ack(
            command_id=command_id,
            device_id=self._device_id,
            status=AckStatus.EXECUTING,
            message=message or "Command executing",
            corr_id=corr_id,
        )
        self._publish(ack)
    
    def publish_done(
        self,
        command_id: str,
        corr_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Publish 'done' acknowledgment.
        
        Call this when command completes successfully.
        """
        ack = Ack(
            command_id=command_id,
            device_id=self._device_id,
            status=AckStatus.DONE,
            message=message or "Command completed successfully",
            details=details,
            corr_id=corr_id,
        )
        self._publish(ack)
    
    def publish_error(
        self,
        command_id: str,
        corr_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Publish 'error' acknowledgment.
        
        Call this when command fails.
        """
        ack = Ack(
            command_id=command_id,
            device_id=self._device_id,
            status=AckStatus.ERROR,
            message=message or "Command failed",
            details=details,
            corr_id=corr_id,
        )
        self._publish(ack)
    
    def publish_cancelled(
        self,
        command_id: str,
        corr_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Publish 'cancelled' acknowledgment.
        
        Call this when command is cancelled.
        """
        ack = Ack(
            command_id=command_id,
            device_id=self._device_id,
            status=AckStatus.CANCELLED,
            message=message or "Command cancelled",
            corr_id=corr_id,
        )
        self._publish(ack)
    
    def _publish(self, ack: Ack) -> None:
        """Internal: Publish acknowledgment to MQTT."""
        topic = self._topic_layout.for_ack()
        payload = ack.model_dump_json()
        
        logger.debug(
            "Publishing Ack [%s] for command %s to %s",
            ack.status.value,
            ack.command_id,
            topic,
        )
        
        self._client.publish(topic, payload, qos=1, retain=False)


__all__ = [
    "AckPublisher",
    "AckTopicLayout",
]
```

---

## Step 3: Integrate Ack Publisher into Actor

### 3.1 Modify `apps/devices/testbox/apps/actor.py`

**Add import at top:**
```python
from ..adapters.ack_publisher import AckPublisher
```

**Update `DeviceTestBoxActor.__init__()`:**
```python
def __init__(
    self,
    *,
    device_id: str,
    driver: InstrumentDriver,
    command_queue: CommandQueue,
    telemetry_queue: TelemetryQueue,
    ack_publisher: AckPublisher,  # NEW
) -> None:
    self._device_id = device_id
    self._driver = driver
    self._command_queue = command_queue
    self._telemetry_queue = telemetry_queue
    self._ack_publisher = ack_publisher  # NEW
    self._stop_event = asyncio.Event()
```

**Update `_handle_command()` method:**
```python
async def _handle_command(self, command: DeviceTestBoxRunCommand) -> None:
    # Publish 'accepted' ack immediately
    self._ack_publisher.publish_accepted(
        command_id=command.corr_id,  # Using corr_id as command_id for now
        corr_id=command.corr_id,
        message="TestBox command accepted and queued",
    )
    
    payload = command.params.model_dump(exclude_none=True)
    try:
        # Optional: Publish 'executing' ack when starting
        self._ack_publisher.publish_executing(
            command_id=command.corr_id,
            corr_id=command.corr_id,
        )
        
        self._driver.start_task("run_diagnostic", payload)
        await self._publish_progress(command)
        await self._publish_done(command)
        
        # Publish 'done' ack on success
        self._ack_publisher.publish_done(
            command_id=command.corr_id,
            corr_id=command.corr_id,
            message="TestBox diagnostic completed",
            details={"operation": "run_diagnostic"},
        )
        
    except Exception as exc:  # noqa: BLE001
        # Publish 'error' ack on failure
        self._ack_publisher.publish_error(
            command_id=command.corr_id,
            corr_id=command.corr_id,
            message=f"TestBox diagnostic failed: {exc}",
            details={"error_type": type(exc).__name__},
        )
        
        # Still publish error event for telemetry
        await self._telemetry_queue.put_telemetry(
            ErrorEvent(
                device_id=command.device_id,
                corr_id=command.corr_id,
                code="testbox.actor.error",
                message=str(exc),
                severity="ERROR",
                details={"command": command.model_dump(exclude_none=True)},
            )
        )
```

### 3.2 Update `create_actor()` function

```python
def create_actor(config: Dict[str, Any] | None = None) -> DeviceTestBoxRuntime:
    """Construct the actor and its queues for the device."""
    
    cfg = config.copy() if config else {}
    device_id = cfg.get("device_id", "TESTBOX-001")
    
    # Existing components
    command_queue = CommandQueue()
    telemetry_queue = TelemetryQueue()
    driver = _build_driver(cfg)
    
    # NEW: Create AckPublisher (requires MQTT client)
    # Note: This assumes MQTT client is passed in config or created here
    mqtt_client = cfg.get("mqtt_client")  # Must be provided by caller
    if mqtt_client is None:
        raise ValueError("mqtt_client required in config for AckPublisher")
    
    from ..adapters.ack_publisher import AckPublisher, AckTopicLayout
    
    base_topic = cfg.get("mqtt", {}).get("base_topic", f"lab/local/line/device_testbox/{device_id}")
    ack_publisher = AckPublisher(
        client=mqtt_client,
        device_id=device_id,
        topic_layout=AckTopicLayout(base_topic=base_topic),
    )
    
    # Create actor with AckPublisher
    actor = DeviceTestBoxActor(
        device_id=device_id,
        driver=driver,
        command_queue=command_queue,
        telemetry_queue=telemetry_queue,
        ack_publisher=ack_publisher,  # NEW
    )
    
    # ... rest of function unchanged
```

---

## Step 4: Update Orchestrator to Subscribe to Acks

### 4.1 Modify `apps/orchestrator/testbox/workflow.py`

**Add Ack subscription in `__init__()`:**
```python
def __init__(self, mqtt_client, config_path=None):
    self.client = mqtt_client
    # ... existing code ...
    
    # Subscribe to acknowledgments
    ack_topic = f"{self.base_topic}/ack"
    self.client.message_callback_add(ack_topic, self._handle_ack)
    self.client.subscribe(ack_topic)
    
    logger.info(f"Subscribed to Acks at {ack_topic}")
```

**Add handler method:**
```python
def _handle_ack(self, client, userdata, msg):
    """Handle acknowledgment messages from device."""
    try:
        ack_data = json.loads(msg.payload.decode())
        status = ack_data.get("status")
        command_id = ack_data.get("command_id")
        message = ack_data.get("message", "")
        
        logger.info(
            f"Received Ack [{status}] for command {command_id}: {message}"
        )
        
        # TODO: Track command status in workflow state
        # For now, just log
        
    except Exception as e:
        logger.error(f"Error handling Ack: {e}")
```

---

## Step 5: Write Tests

### 5.1 Create `tests/devices/testbox/test_ack_publisher.py`

```python
"""Test AckPublisher adapter."""

import json
from unittest.mock import Mock

import pytest

from apps.devices.testbox.adapters.ack_publisher import (
    AckPublisher,
    AckTopicLayout,
)
from core.domain.shared.ack import AckStatus


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client."""
    client = Mock()
    client.publish = Mock()
    return client


@pytest.fixture
def ack_publisher(mock_mqtt_client):
    """Create AckPublisher instance."""
    return AckPublisher(
        client=mock_mqtt_client,
        device_id="TB-TEST",
        topic_layout=AckTopicLayout(base_topic="lab/test/device_testbox/TB-TEST"),
    )


def test_publish_accepted(ack_publisher, mock_mqtt_client):
    """Test publishing 'accepted' acknowledgment."""
    ack_publisher.publish_accepted(
        command_id="cmd-123",
        corr_id="corr-123",
        message="Custom message",
    )
    
    # Verify publish was called
    assert mock_mqtt_client.publish.call_count == 1
    
    # Extract call arguments
    topic, payload, qos, retain = mock_mqtt_client.publish.call_args[0]
    
    # Verify topic
    assert topic == "lab/test/device_testbox/TB-TEST/ack"
    
    # Verify payload
    ack_data = json.loads(payload)
    assert ack_data["command_id"] == "cmd-123"
    assert ack_data["device_id"] == "TB-TEST"
    assert ack_data["status"] == "accepted"
    assert ack_data["message"] == "Custom message"
    assert ack_data["corr_id"] == "corr-123"
    
    # Verify QoS
    assert qos == 1
    assert retain is False


def test_publish_done_with_details(ack_publisher, mock_mqtt_client):
    """Test publishing 'done' acknowledgment with details."""
    details = {"duration": 45.2, "points": 100}
    
    ack_publisher.publish_done(
        command_id="cmd-456",
        corr_id="corr-456",
        details=details,
    )
    
    # Extract payload
    _, payload, _, _ = mock_mqtt_client.publish.call_args[0]
    ack_data = json.loads(payload)
    
    assert ack_data["status"] == "done"
    assert ack_data["details"] == details


def test_publish_error(ack_publisher, mock_mqtt_client):
    """Test publishing 'error' acknowledgment."""
    ack_publisher.publish_error(
        command_id="cmd-789",
        corr_id="corr-789",
        message="Timeout occurred",
        details={"error_code": "TIMEOUT"},
    )
    
    _, payload, _, _ = mock_mqtt_client.publish.call_args[0]
    ack_data = json.loads(payload)
    
    assert ack_data["status"] == "error"
    assert ack_data["message"] == "Timeout occurred"
    assert ack_data["details"]["error_code"] == "TIMEOUT"
```

### 5.2 Create `tests/devices/testbox/test_actor_with_ack.py`

```python
"""Test Actor with Ack integration."""

import asyncio

import pytest

from apps.devices.testbox.apps.actor import DeviceTestBoxActor
from apps.devices.testbox.apps.queues import CommandQueue, TelemetryQueue
from apps.devices.testbox.domain.models import (
    DeviceTestBoxRunCommand,
    DeviceTestBoxRunParams,
)
from apps.devices.testbox.drivers import DeviceTestBoxFakeDriver
from unittest.mock import Mock


@pytest.mark.asyncio
async def test_actor_emits_accepted_ack():
    """Test that actor emits 'accepted' ack when receiving command."""
    driver = DeviceTestBoxFakeDriver(default_duration_s=0.1, seed=42)
    command_queue = CommandQueue()
    telemetry_queue = TelemetryQueue()
    
    # Mock AckPublisher
    mock_ack_publisher = Mock()
    mock_ack_publisher.publish_accepted = Mock()
    mock_ack_publisher.publish_executing = Mock()
    mock_ack_publisher.publish_done = Mock()
    
    actor = DeviceTestBoxActor(
        device_id="TB-001",
        driver=driver,
        command_queue=command_queue,
        telemetry_queue=telemetry_queue,
        ack_publisher=mock_ack_publisher,
    )
    
    # Enqueue a command
    command = DeviceTestBoxRunCommand(
        corr_id="test-cmd",
        device_id="TB-001",
        params=DeviceTestBoxRunParams(profile="default", duration_s=0.1),
    )
    await command_queue.put_command(command)
    
    # Run actor for short time
    actor_task = asyncio.create_task(actor.run())
    await asyncio.sleep(0.2)
    actor.stop()
    await command_queue.join()
    await actor_task
    
    # Verify acks were published
    mock_ack_publisher.publish_accepted.assert_called_once()
    mock_ack_publisher.publish_done.assert_called_once()
    
    # Verify accepted ack has correct command_id
    call_kwargs = mock_ack_publisher.publish_accepted.call_args[1]
    assert call_kwargs["command_id"] == "test-cmd"
    assert call_kwargs["corr_id"] == "test-cmd"
```

---

## Step 6: Run and Verify

### 6.1 Run Unit Tests
```bash
uv run pytest tests/devices/testbox/test_ack_publisher.py -v
uv run pytest tests/devices/testbox/test_actor_with_ack.py -v
```

### 6.2 Manual MQTT Test

**Terminal 1: Start Mosquitto**
```bash
mosquitto -v
```

**Terminal 2: Subscribe to Acks**
```bash
mosquitto_sub -t 'lab/+/+/+/+/ack' -v
```

**Terminal 3: Run TestBox in MQTT mode**
```bash
uv run python -m apps.devices.testbox.apps.main --mode mqtt --config configs/devices.yaml
```

**Terminal 4: Publish a command**
```bash
mosquitto_pub -t 'lab/local/line/device_testbox/TB-001/cmd/run_diagnostic' \
  -m '{"corr_id": "test-123", "device_id": "TB-001", "params": {"profile": "default"}}'
```

**Expected in Terminal 2:**
```
lab/local/line/device_testbox/TB-001/ack {"command_id": "test-123", "status": "accepted", ...}
lab/local/line/device_testbox/TB-001/ack {"command_id": "test-123", "status": "executing", ...}
lab/local/line/device_testbox/TB-001/ack {"command_id": "test-123", "status": "done", ...}
```

---

## Success Criteria

Phase 1 is complete when:

- ✅ `Ack` model defined in `core/domain/shared/ack.py`
- ✅ `AckPublisher` adapter created and working
- ✅ Actor emits Acks at appropriate lifecycle points
- ✅ Orchestrator subscribes to Ack topic
- ✅ Unit tests pass for AckPublisher
- ✅ Integration test passes for Actor with Ack
- ✅ Manual MQTT test shows Acks published correctly
- ✅ All existing tests still pass (no regressions)
- ✅ Ack messages visible in MQTT logs

---

## Benefits Achieved

After Phase 1:
1. **Visibility**: Orchestrator can track command lifecycle
2. **Debugging**: Easier to diagnose stuck or lost commands
3. **Monitoring**: Can build dashboards showing command flow
4. **Foundation**: Ack infrastructure ready for Phase 2 (HSM)

---

## Next Steps

Once Phase 1 is complete and validated:
- Proceed to [Phase 2: Extract HSM](./PHASE2_IMPLEMENTATION_GUIDE.md) (to be created)
- Or pause and stabilize if needed

---

## Troubleshooting

### Issue: MQTT client not available in config
**Solution**: Update `main.py` to create MQTT client and pass to `create_actor()`

### Issue: Acks not visible in Mosquitto
**Solution**: Check topic pattern in subscription: `lab/+/+/+/+/ack`

### Issue: Tests fail with "mqtt_client required"
**Solution**: Mock MQTT client in test fixtures (see examples above)

---

**Questions?** Refer to [ARCHITECTURE_EVOLUTION.md](./ARCHITECTURE_EVOLUTION.md) for context.
