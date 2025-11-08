# TestBox Domain 模型说明

`domain/` 目录使用 Pydantic 定义命令、事件、状态等领域模型，是驱动、Actor 与适配器共享的数据契约。

## 文件结构

- `models.py`：包含所有模型定义与校验规则。
- `__init__.py`：导出常用模型，方便其他模块按需引用。

## 主要模型

- `DeviceTestBoxRunParams` / `DeviceTestBoxRunCommand`：描述诊断入口参数与命令元数据。
- `DeviceTestBoxProgressEvent` / `DeviceTestBoxDoneEvent`：描述诊断执行过程与最终结果。
- `DeviceTestBoxSensorSnapshot`：封装模拟的传感器读数列表。
- `DeviceTestBoxShadow` / `DeviceTestBoxState`：维护设备状态影子，用于 MQTT 保留消息。

## 约束与实践

- 所有命令/事件必须携带 `corr_id` 和 `device_id`，便于链路追踪。
- 通过 `model_validator` 保证阶段名称、传感器列表等关键字段不为空。
- 时间戳统一使用 `datetime.now(timezone.utc)`，避免时区差异。
- 调整字段后需同步更新 `schemas/` 下的 JSON Schema 并补充测试。
