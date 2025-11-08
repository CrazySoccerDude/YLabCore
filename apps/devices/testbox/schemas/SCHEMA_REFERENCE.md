# TestBox JSON Schema 参考

`schemas/` 目录提供命令、事件、遥测与状态影子的 JSON Schema 定义，便于消费者验证消息契约。

## 现有文件

- `cmd.run_diagnostic.schema.json`：运行诊断命令的结构约束。
- `evt.diagnostic_progress.schema.json`：进度事件格式。
- `evt.diagnostic_done.schema.json`：完成事件格式。
- `tele.sensor_snapshot.schema.json`：传感器快照遥测格式。
- `state.shadow.schema.json`：状态影子结构。

## 使用建议

- 在消息总线或 API 网关侧加载 Schema，可提前拦截无效负载。
- 与 `domain/models.py` 的 Pydantic 定义保持一致；更新模型时需同步调整 Schema。
- 后续可在测试中调用 `model_json_schema()` 对比，防止契约漂移。
