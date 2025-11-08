# TestBox Drivers 适配器指南

`drivers/` 目录负责连接设备侧与系统侧，包含 MQTT 适配器与虚拟/真实驱动的实现。

## 文件结构

- `__init__.py`：导出 Fake/Real 驱动，并引用通用 `InstrumentDriver` 基类。
- `command_adapter.py`：订阅 `cmd/run_diagnostic`，解析 JSON 并转成 `DeviceTestBoxRunCommand` 入队。
- `telemetry_adapter.py`：消费遥测队列，发布进度、完成、传感器和错误消息到相应主题。
- `state_adapter.py`：基于遥测构建状态影子并作为保留消息发布到 `state/shadow`。

## 驱动实现

- `DeviceTestBoxFakeDriver`：默认模拟驱动，通过随机阶段生成进度和结果。
- `DeviceTestBoxRealDriver`：真实仪器的占位实现，后续将通过串口 transport 与解析层完成。

## 扩展约定

- 新增协议（HTTP、gRPC 等）时，可在本目录创建新的适配器文件，并于 `main.py` 装配。
- 实现真实驱动需继承 `InstrumentDriver`，提供 `start_task/abort/fetch_progress/fetch_result` 等接口。
- MQTT 适配器的启动/停止必须在 `run_mqtt_async` 中显式调用，避免残留订阅或后台任务。
