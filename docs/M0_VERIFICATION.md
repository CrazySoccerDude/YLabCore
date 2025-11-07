# M0 验收指南

## 目标
验证 MQTT 总线基础功能，确保能够发布和订阅消息。

## 前置条件

### 1. 安装 Mosquitto

**Windows (Chocolatey):**
```powershell
choco install mosquitto
```

**或者从官网下载:**
https://mosquitto.org/download/

### 2. 安装 Python 依赖

```powershell
cd c:\PythonProject\6_YLabCore
uv sync
```

## 验收步骤

### 步骤 1: 启动 Mosquitto Broker

在第一个 PowerShell 终端中运行：

```powershell
mosquitto -v
```

**预期输出:**
```
1730851234: mosquitto version 2.x starting
1730851234: Using default config.
1730851234: Opening ipv4 listen socket on port 1883.
1730851234: mosquitto running
```

### 步骤 2: 启动订阅者（观察窗口）

在第二个 PowerShell 终端中运行：

```powershell
mosquitto_sub -t 'inst/#' -v
```

这个终端会保持等待，显示所有 `inst/` 开头的消息。

### 步骤 3: 运行 InstruHub

在第三个 PowerShell 终端中运行：

```powershell
cd c:\PythonProject\6_YLabCore
uv run python -m instrument_hub.app.main
```

**预期输出（主程序终端）:**
```
2025-11-06 14:20:00 [INFO] __main__: Starting InstruHub (M0 - Basic Environment)
2025-11-06 14:20:00 [INFO] instrument_hub.core.bus_mqtt: Connecting to MQTT broker at localhost:1883 as 'instruhub_main'
2025-11-06 14:20:00 [INFO] instrument_hub.core.bus_mqtt: Connected to MQTT broker successfully
2025-11-06 14:20:00 [INFO] __main__: Connected to MQTT broker successfully
2025-11-06 14:20:00 [INFO] __main__: Published hello message to inst/SYS/diag/hello
2025-11-06 14:20:01 [INFO] __main__: M0 verification complete - check terminal with: mosquitto_sub -t 'inst/#' -v
2025-11-06 14:20:01 [INFO] instrument_hub.core.bus_mqtt: Disconnected from MQTT broker
```

**预期输出（订阅者终端）:**
```
inst/SYS/diag/hello {"message": "InstruHub M0 initialized", "version": "0.1.0", "timestamp": 1730851234.567}
```

## ✅ 验收标准

- [x] Mosquitto 成功启动并监听 1883 端口
- [x] 订阅者终端能够收到 `inst/SYS/diag/hello` 消息
- [x] 消息载荷是有效的 JSON 格式
- [x] 消息包含 `message`、`version`、`timestamp` 三个字段
- [x] 程序正常退出，无错误日志

## 常见问题

### Q: Mosquitto 启动失败，提示端口被占用

**A:** 检查是否已有 Mosquitto 实例运行：

```powershell
Get-Process mosquitto -ErrorAction SilentlyContinue
```

如果有，停止它：

```powershell
Stop-Process -Name mosquitto
```

### Q: 订阅者没有收到消息

**A:** 检查：
1. Mosquitto 是否正常运行
2. 订阅的 topic 是否正确（`inst/#`）
3. 主程序是否报错连接失败

### Q: 主程序报错 "Failed to connect to MQTT broker"

**A:** 确认：
1. Mosquitto 已启动并监听 1883 端口
2. 防火墙未阻止 localhost:1883
3. 运行 `telnet localhost 1883` 测试连通性

## 下一步

M0 通过后，继续实现 M1：
- IOChannel (串口传输层)
- JSONL 事件日志
- 状态事件（link_up/down/retry）
