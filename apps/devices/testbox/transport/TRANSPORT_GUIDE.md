# TestBox Transport 开发指南

`transport/` 目录对接物理通信链路，当前提供串口实现，并默认使用 pyserial 的 `loop://` 回环以便离线调试。

## 文件结构

- `serial_transport.py`：`SerialTransport` 封装，负责串口的打开/关闭、读写、flush/reset 等操作，支持上下文管理器与 `write_line()` 带换行写法。
- `__init__.py`：导出 `SerialTransport` 供驱动或配置直接引用。

## 核心特性

- **loop:// 支持**：默认回环模式无需额外驱动，可在测试或 CI 中快速验证链路。
- **可配置化**：接受 `url`、`baudrate`、`timeout`、`write_timeout`，以及 `bytesize/parity/stopbits/xonxoff/rtscts/dsrdtr` 等高级串口参数，可通过配置文件注入。
- **安全防护**：在读写前确认串口已打开，异常将转换为 `RuntimeError`，便于 Actor 捕获并上报。

## 扩展思路

- 连接真实 COM 口时，将 `url` 修改为 `"COM3"` 等实际端口即可。
- 若需对接 TCP、VISA 等其他传输方式，可在本目录新增模块并保持与 `SerialTransport` 类似的接口，以便驱动层无感切换。
