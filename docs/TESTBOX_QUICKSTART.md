# TestBox Quickstart Guide

This guide walks through running the TestBox device service in both demo and MQTT modes. It assumes the repository has already been set up via `uv sync`.

## 1. Prepare the Environment

1. **Install dependencies** (if not done yet):
   ```powershell
   uv sync
   ```
2. **Activate the uv-provided Python** (optional if using `uv run`).
3. **Copy and adjust configuration**:
   - Use `configs/devices.yaml` as a starting point.
   - Update `device_id`, `mqtt.host`, and `transport.url` as needed.

## 2. Run in Demo Mode

Demo mode runs a single diagnostic cycle, prints the telemetry, and exits.

```powershell
uv run python -m apps.devices.testbox.apps.main
```

You should see a sequence of `testbox.diagnostic_progress` messages followed by a `testbox.diagnostic_done` event.

## 3. Run in MQTT Mode

1. **Start an MQTT broker** (Mosquitto example):
   ```powershell
   mosquitto -v
   ```
   Or use Docker:
   ```powershell
   docker run --rm -p 1883:1883 eclipse-mosquitto
   ```
2. **Launch TestBox in MQTT mode** using your config file:
   ```powershell
   uv run python -m apps.devices.testbox.apps.main --mode mqtt --config configs/devices.yaml
   ```
3. **Send a command** from another shell (using `mosquitto_pub`):
   ```powershell
   mosquitto_pub -t lab/local/line/device_testbox/TB-001/cmd/run_diagnostic -m "{\"device_id\": \"TB-001\", \"corr_id\": \"manual-1\"}"
   ```
4. **Observe telemetry**:
   ```powershell
   mosquitto_sub -t lab/local/line/device_testbox/TB-001/#
   ```
   You should receive progress events, the final `diagnostic_done` event, and the `state/shadow` retained message.

## 4. Switching to a Real Serial Port

- Update `transport.url` in the config to the appropriate COM port (e.g., `"COM3"`) or Linux device (e.g., `"/dev/ttyUSB0"`).
- Adjust `baudrate` and timeouts to match the instrument specifications.
- Implement or configure `DeviceTestBoxRealDriver` to call into the transport and parsers.

## 5. Next Steps

- Implement real SCPI parsing in `parsers/scpi.py`.
- Extend `DeviceTestBoxRealDriver` for actual hardware integration.
- Add heartbeat/LWT handling in `apps/devices/testbox/apps/hb.py` for production readiness.
- Integrate with orchestrator or persistor apps to build end-to-end workflows.
```}