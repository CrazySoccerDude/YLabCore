# TestBox 模块总览

TestBox 是 YLabCore 的虚拟诊断仪器实现，用于验证 device-centric 架构、MQTT 总线以及串口传输的整合。该包聚合了 Actor、驱动、领域模型、协议解析、Schema 与 Transport，既可作为本地演示，也可迁移到真实设备。

## 模块速览

| 子目录 | 作用 | 文档 |
| --- | --- | --- |
| `apps/` | Actor 循环、命令/遥测队列、CLI 入口 | `apps/APPS_OVERVIEW.md` |
| `domain/` | Pydantic 命令/事件/状态模型 | `domain/DOMAIN_MODELS.md` |
| `drivers/` | MQTT 命令/遥测/状态适配器与 Fake/Real 驱动 | `drivers/DRIVERS_GUIDE.md` |
| `parsers/` | 协议封装与解析（SCPI 占位） | `parsers/PARSERS_NOTES.md` |
| `schemas/` | JSON Schema 契约定义 | `schemas/SCHEMA_REFERENCE.md` |
| `transport/` | 串口传输封装，默认支持 `loop://` | `transport/TRANSPORT_GUIDE.md` |

## 运行方式

- Demo 模式（同步输出一次诊断）：
  ```bash
  uv run python -m apps.devices.testbox.apps.main
  ```
- MQTT 模式（订阅命令、发布遥测与状态影子）：
  ```bash
  uv run python -m apps.devices.testbox.apps.main --mode mqtt --config configs/devices.yaml
  ```

## 配置要点

- `configs/devices.yaml` 提供示例配置，其中 `transport.url` 默认为 `loop://`，可直接用于回环调试。
- 如需挂载真实串口，将 `url` 修改为实际端口（例如 `"COM3"`），并根据仪器参数调整 `baudrate`、`timeout` 等。

## 测试覆盖

- `tests/devices/testbox/` 目录涵盖 Actor、MQTT 适配器与串口 Transport 的单元测试。
- 运行 `uv run pytest` 确认组合流程与回环串口行为稳定。
