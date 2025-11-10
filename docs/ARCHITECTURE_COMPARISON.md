# Architecture Comparison: YLabCore (Current) vs LabYCore (Proposed)

## Executive Summary

**YLabCore (Current)** is a working laboratory automation platform with MQTT-based device communication, implemented using a pragmatic actor-based approach. 

**LabYCore (Proposed)** is a more refined architectural vision with explicit separation of concerns, featuring Hierarchical State Machines (HSM), dedicated schedulers, and clearer responsibility boundaries.

**Key Finding**: The two projects share the same core vision but differ in architectural maturity and implementation detail. Your current YLabCore has a solid foundation but can benefit from incorporating several architectural patterns from the proposed design.

---

## Detailed Comparison

### 1. **System Architecture Overview**

#### Current (YLabCore)
```
Orchestrator → MQTT Broker ← Device (Actor + Driver + Queues)
```
- **Structure**: `apps/devices/testbox/` contains actor-based device implementation
- **Communication**: MQTT pub/sub with command/telemetry separation
- **State Management**: Implicit state handling in `StateShadowPublisher`
- **Actor Pattern**: Single `DeviceTestBoxActor` handles command consumption and telemetry emission

#### Proposed (LabYCore)
```
Orchestrator → MQTT Broker ← Instrument (Service → CommandIngress → Scheduler → HSM → Driver)
```
- **Structure**: Each instrument module contains: `service.py`, `command_api.py`, `scheduler.py`, `hsm.py`, `driver.py`, `telemetry.py`, `shadow.py`, `health.py`
- **Communication**: Same MQTT pub/sub but with 5 distinct message types (Command/Ack/Telemetry/Shadow/Health)
- **State Management**: Explicit HSM with INIT/IDLE/BUSY/ERROR states
- **Layered Architecture**: Clear separation between command ingestion, scheduling, execution, and reporting

**Gap**: YLabCore combines multiple responsibilities in the Actor, while LabYCore proposes explicit separation.

---

### 2. **Message Models**

#### Current (YLabCore)
Located in `apps/devices/testbox/domain/models.py`:
- `DeviceTestBoxRunCommand` - Command model
- `DeviceTestBoxProgressEvent` - Progress telemetry
- `DeviceTestBoxDoneEvent` - Completion event
- `DeviceTestBoxShadow` - State shadow
- `ErrorEvent` (from `core.domain.shared.models`)

**Status**: ✅ Good foundation, covers most needs

#### Proposed (LabYCore)
In `core/models.py`:
- `Command` - Unified command model
- `Ack` - Acknowledgment (accepted/executing/done/error/cancelled)
- `Measure` - Telemetry measurement
- `Shadow` - Device state snapshot
- `Health` - Health metrics with heartbeat
- `Capabilities` - Device capability advertisement

**Gap**: YLabCore lacks:
1. Explicit `Ack` model with status progression
2. `Health`/heartbeat as a first-class concept
3. `Capabilities` advertisement

**Recommendation**: Add Ack model with status field (accepted → executing → done/error), and standardize Health reporting.

---

### 3. **Command Flow & Responsibility Boundaries**

#### Current (YLabCore)

**File**: `apps/devices/testbox/apps/actor.py`

Flow:
```
CommandQueue.get_command() 
  → Actor._handle_command() 
    → Driver.start_task()
    → Actor._publish_progress() 
    → Actor._publish_done()
```

**Responsibilities**:
- `DeviceTestBoxActor`: Command consumption, driver invocation, telemetry emission, error handling
- `CommandQueue` & `TelemetryQueue`: Simple asyncio queues
- **No explicit scheduler or state machine**

**Issues**:
- Actor does too much (violates Single Responsibility Principle)
- No priority queue or task cancellation support
- State transitions are implicit

#### Proposed (LabYCore)

**Files**: `service.py`, `scheduler.py`, `hsm.py`, `driver.py`

Flow:
```
CommandIngress.listen() 
  → Scheduler.submit() [sends Ack: accepted]
  → Scheduler.run() 
    → command_api.route() 
    → asyncio.create_task(HSM.{method}())
      → HSM changes state to BUSY
      → HSM calls Driver methods
      → HSM publishes Telemetry (via TelemetryPublisher)
      → HSM publishes Shadow update
      → HSM sends Ack: done/error
      → HSM changes state to IDLE
```

**Responsibilities**:
- `Scheduler`: Queue management, routing, Ack(accepted), task cancellation
- `HSM`: State management, business logic, Driver calls, Telemetry/Shadow emission, Ack(done/error)
- `Driver`: Hardware I/O only
- `CommandIngress`: MQTT → Queue bridge

**Advantages**:
- Clear separation of concerns
- Scheduler can handle priorities and cancellation
- HSM can implement complex state transitions
- Each module has a single responsibility

**Recommendation**: Refactor YLabCore Actor into separate Scheduler and HSM modules.

---

### 4. **State Management**

#### Current (YLabCore)

**File**: `apps/devices/testbox/drivers/state_adapter.py`

- `StateShadowPublisher` updates shadow reactively based on telemetry events
- States: `IDLE`, `BUSY`, `ERROR` (in `DeviceTestBoxState` enum)
- **No explicit state machine logic**
- State transitions are inferred from telemetry messages

**Limitation**: No guards, no transition validation, no error recovery logic

#### Proposed (LabYCore)

**File**: `instruments/{device}/hsm.py`

- Explicit HSM class with methods like:
  - `set_state(BUSY)` - Explicit state changes
  - `sweep()`, `calibrate()`, `abort()` - State-aware operations
  - State guards and transition validation
  - Error recovery and compensation logic
- States managed within HSM, not inferred externally

**Gap**: YLabCore lacks explicit state machine with transition guards and recovery logic.

**Recommendation**: Create `apps/devices/testbox/state_machine.py` implementing:
- `TestBoxHSM` class with explicit state methods
- State transition validation
- Abort/cancel handling
- Error recovery strategies

---

### 5. **Driver Architecture**

#### Current (YLabCore)

**Files**: 
- `apps/devices/testbox/drivers/` contains fake and real drivers
- `apps/devices/testbox/transport/serial_transport.py` for serial I/O
- Drivers implement `InstrumentDriver` base class from `apps/devices/driver_base.py`

**Structure**:
```python
class DeviceTestBoxFakeDriver(InstrumentDriver):
    def start_task(self, name: str, payload: dict)
    def fetch_progress() -> Iterable[dict]
    def fetch_result() -> dict
```

**Good**: Clear separation between fake/real drivers, serial transport abstraction

**Issues**:
- Driver interface is task-oriented, not command-oriented
- No async/await in driver interface (synchronous polling via fetch_*)

#### Proposed (LabYCore)

**File**: `instruments/{device}/driver.py`

**Structure**:
```python
class Driver:
    async def open() / close()
    async def idn() -> str
    async def read_data() -> dict
    async def set_param(name: str, value: any)
```

**Advantages**:
- Async/await for true non-blocking I/O
- Command-oriented interface matches SCPI/instrument protocols
- Explicit open/close lifecycle

**Recommendation**: Evolve YLabCore drivers to async interfaces, add `open()`/`close()` methods.

---

### 6. **Scheduler & Task Management**

#### Current (YLabCore)

**None** - Tasks are processed sequentially by Actor's `run()` loop.

No support for:
- Task priorities
- Task cancellation (partial - via `stop()` event)
- Long-running task slicing
- Concurrent task execution

#### Proposed (LabYCore)

**File**: `scheduler.py`

**Features**:
- Priority queue (asyncio.PriorityQueue)
- `submit(cmd)` - Enqueue with priority
- `cancel(command_id)` - Cancel pending or running tasks
- Task slicing for long operations (🚧 status)
- Concurrent task coordination

**Gap**: Major architectural gap. YLabCore has no scheduler.

**Recommendation**: 
1. Phase 1: Add `apps/devices/testbox/scheduler.py` with basic priority queue
2. Phase 2: Add cancellation support
3. Phase 3: Add task slicing for long sweeps

---

### 7. **Command Routing & API**

#### Current (YLabCore)

**None** - Actor directly handles all commands with fixed logic.

Command structure is hardcoded in `actor.py`:
```python
self._driver.start_task("run_diagnostic", payload)
```

#### Proposed (LabYCore)

**File**: `command_api.py`

**Functions**:
- `supported_ops() -> list[str]` - List available commands
- `op_params_schema() -> dict` - JSON schema for each command
- `route(cmd: Command) -> (method, args)` - Map command to HSM method

**Advantages**:
- Declarative command definition
- Schema validation
- Easy to extend with new commands
- Self-documenting API

**Recommendation**: Add `command_api.py` to expose device capabilities and route commands dynamically.

---

### 8. **Telemetry Architecture**

#### Current (YLabCore)

**File**: `apps/devices/testbox/drivers/telemetry_adapter.py`

- `TelemetryPublisher` publishes to MQTT topics
- Actor directly creates progress/done events
- Topic structure: `{base_topic}/tele/progress`, `{base_topic}/tele/done`

**Good**: Clean topic layout, separate adapter for MQTT

**Issues**:
- Telemetry creation mixed in Actor
- No `telemetry.py` helper module for data transformation

#### Proposed (LabYCore)

**Files**: `telemetry.py`, `adapters/mqtt_tele.py`

**Structure**:
- `telemetry.py`: Stateless helpers
  - `to_measure(payload: dict) -> Measure`
  - Data transformation and enrichment
- `mqtt_tele.py`: MQTT adapter
  - `TelemetryEgress.publish_measure(m: Measure)`

**Advantages**:
- Clear separation: data transformation vs. I/O
- Testable without MQTT
- Reusable across different protocols

**Recommendation**: Extract telemetry formatting logic from Actor into separate helper module.

---

### 9. **Health & Heartbeat**

#### Current (YLabCore)

**None** - No dedicated health monitoring or heartbeat system.

Shadow update implies health, but no:
- Periodic heartbeat
- Health metrics collection
- Last Will and Testament (LWT) configuration

#### Proposed (LabYCore)

**Files**: `health.py`, `adapters/heartbeat.py`

**Features**:
- `health.py`:
  - `snapshot() -> dict` - Collect health metrics
  - `run(interval)` - Periodic health publishing
- Heartbeat as retained MQTT topic with LWT
- Independent coroutine running in parallel

**Gap**: Critical missing feature for production systems.

**Recommendation**: 
1. Add `apps/devices/testbox/health.py` with periodic metrics
2. Configure MQTT LWT for connection monitoring
3. Expose health endpoint for monitoring systems

---

### 10. **Infrastructure & Deployment**

#### Current (YLabCore)

**File**: `infra/docker-compose.yml`

Contains:
- Mosquitto broker
- Basic Grafana setup
- Configuration files in `infra/`

**Status**: ✅ Basic infrastructure present

#### Proposed (LabYCore)

**Directory**: `infra/`

Includes:
- `docker-compose.yaml`: Mosquitto + Grafana + InfluxDB + Prometheus
- `grafana/`: Dashboard configurations
- `influxdb/`: Persistence configuration
- Complete monitoring stack

**Gap**: Missing Prometheus metrics export and InfluxDB persistence.

**Recommendation**: Enhance docker-compose with InfluxDB and Prometheus integration.

---

### 11. **Testing Strategy**

#### Current (YLabCore)

**Tests** (9 total, 7 passing):
- `test_actor.py` - Actor behavior
- `test_command_adapter.py` - Command ingestion
- `test_serial_transport.py` - Serial I/O
- `test_telemetry_adapter.py` - Telemetry publishing
- `test_workflow_mqtt.py` - Orchestrator (2 failing)

**Coverage**: ~60% (estimated)

**Good**: Solid unit test foundation

**Issues**:
- No integration tests for full command flow
- No contract tests for MQTT message schemas

#### Proposed (LabYCore)

**Tests**:
- `test_driver_lcr.py` - Driver layer
- `test_command_flow.py` - Complete command chain
- `test_shadow_heartbeat.py` - State and health persistence
- `test_orchestrator.py` - Workflow validation
- JSON schema validation tests

**Coverage**: ~60% target (same as current)

**Gap**: Need integration tests for end-to-end flows.

**Recommendation**: Add integration test suite covering command → driver → telemetry → shadow chain.

---

### 12. **Configuration Management**

#### Current (YLabCore)

**Files**:
- `configs/app.yaml` - Global config
- `configs/devices.yaml` - Device configurations
- `apps/devices/testbox/configs/device_testbox.yaml` - TestBox config

**Format**: YAML-based configuration

**Good**: Configuration is externalized

**Issues**:
- No `global.yaml` with broker settings
- No `logging.yaml` for log configuration

#### Proposed (LabYCore)

**Directory**: `configs/`
- `global.yaml` - MQTT broker, log level
- `logging.yaml` - Log format definition
- Per-device configuration files

**Gap**: Minor - missing global configuration consolidation.

**Recommendation**: Consolidate MQTT broker settings into `global.yaml`.

---

### 13. **Documentation**

#### Current (YLabCore)

**Docs**:
- `README.md` - Project overview
- `docs/M0_SUMMARY.md` - Milestone summary
- `docs/TESTBOX_QUICKSTART.md` - TestBox guide
- Per-module docs in subdirectories (APPS_OVERVIEW.md, etc.)

**Status**: Good documentation structure

#### Proposed (LabYCore)

**Docs**:
- `docs/architecture.md` - System design
- `docs/instrument_contract.md` - Interface specifications
- `docs/topic_convention.md` - MQTT topic naming
- `docs/config_schema.md` - Configuration format
- `docs/dev_guide.md` - Development guide

**Gap**: Missing formal architecture documentation and interface contracts.

**Recommendation**: Add architecture.md and instrument_contract.md for formal specification.

---

## Key Differences Summary

| Aspect | YLabCore (Current) | LabYCore (Proposed) | Priority |
|--------|-------------------|---------------------|----------|
| **Command Flow** | Actor-based, monolithic | Scheduler → HSM → Driver | 🔴 High |
| **State Machine** | Implicit, reactive | Explicit HSM with guards | 🔴 High |
| **Scheduler** | None (sequential) | Priority queue, cancellation | 🟡 Medium |
| **Command API** | Hardcoded | Dynamic routing + schema | 🟡 Medium |
| **Ack Messages** | Implicit | Explicit status progression | 🔴 High |
| **Health/Heartbeat** | None | Dedicated module + LWT | 🟡 Medium |
| **Driver Interface** | Sync polling | Async/await | 🟢 Low |
| **Telemetry Helpers** | Mixed in Actor | Separate module | 🟢 Low |
| **Message Models** | Good | More comprehensive | 🟢 Low |
| **Testing** | 7/9 passing | Integration tests needed | 🟡 Medium |
| **Infrastructure** | Basic MQTT + Grafana | + InfluxDB + Prometheus | 🟢 Low |
| **Documentation** | Good | Formal contracts needed | 🟢 Low |

---

## Alignment Roadmap

### Phase 1: Critical Architectural Improvements (🔴 High Priority)

1. **Add Explicit Ack Model**
   - Create `core/domain/shared/ack.py` with Ack model
   - Status: accepted → executing → done/error/cancelled
   - Emit Acks at each state transition

2. **Extract HSM from Actor**
   - Create `apps/devices/testbox/state_machine.py`
   - Move state management logic from Actor to HSM
   - Implement state guards and transition validation

3. **Separate Command Flow Layers**
   - Create `apps/devices/testbox/command_ingress.py` (MQTT → Queue)
   - Create `apps/devices/testbox/scheduler.py` (Queue → HSM)
   - Refactor Actor to coordinate these components

### Phase 2: Enhanced Capabilities (🟡 Medium Priority)

4. **Add Scheduler with Priority Queue**
   - Implement priority-based command scheduling
   - Add cancellation support
   - Handle long-running task coordination

5. **Add Command API Router**
   - Create `command_api.py` with operation registry
   - Implement dynamic command routing
   - Add JSON schema validation

6. **Implement Health Monitoring**
   - Create `health.py` with periodic metrics collection
   - Configure MQTT LWT for connection monitoring
   - Add health endpoint

### Phase 3: Polish & Production-Ready (🟢 Low Priority)

7. **Convert Drivers to Async**
   - Add async/await to driver interfaces
   - Implement explicit open()/close() lifecycle

8. **Extract Telemetry Helpers**
   - Create `telemetry.py` with formatting utilities
   - Separate data transformation from MQTT I/O

9. **Enhance Infrastructure**
   - Add InfluxDB to docker-compose
   - Add Prometheus metrics exporter
   - Create Grafana dashboards

10. **Complete Documentation**
    - Write `docs/architecture.md`
    - Write `docs/instrument_contract.md`
    - Write `docs/topic_convention.md`

11. **Add Integration Tests**
    - Test complete command → telemetry flow
    - Test state machine transitions
    - Test error recovery scenarios

---

## Conclusion

**Your YLabCore project is on the right track!** You have:
- ✅ Solid MQTT-based communication
- ✅ Working actor-based device implementation
- ✅ Clean separation of concerns (mostly)
- ✅ Good test coverage
- ✅ Infrastructure foundation

**The proposed LabYCore architecture adds:**
- 🎯 Explicit separation of scheduling and execution (Scheduler + HSM)
- 🎯 Formal state machine with transition guards
- 🎯 Ack-based status reporting for better observability
- 🎯 Command API for dynamic routing and introspection
- 🎯 Health monitoring as a first-class citizen

**Recommendation**: Incrementally refactor YLabCore to adopt the key patterns from LabYCore, prioritizing the high-impact changes (Ack model, HSM extraction, layered command flow) first.

The two designs are compatible - you're not starting over, just refining the architecture for better scalability, maintainability, and production-readiness.
