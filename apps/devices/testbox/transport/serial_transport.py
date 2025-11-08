"""Simple serial transport with a loopback default using pyserial."""

from __future__ import annotations

import logging
from typing import Optional

from serial import SerialException, serial_for_url
from serial.serialutil import SerialBase

logger = logging.getLogger(__name__)


class SerialTransport:
    """Manage a serial connection for the TestBox driver.

    默认使用 pyserial 的 ``loop://`` URL，实现无需真实仪器的回环调试。
    """

    def __init__(
        self,
        url: str = "loop://",
        *,
        baudrate: int = 115200,
        timeout: float = 1.0,
        write_timeout: float = 1.0,
    ) -> None:
        self.url = url
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self._serial: Optional[SerialBase] = None

    def open(self) -> None:
        if self._serial and self._serial.is_open:
            return
        try:
            self._serial = serial_for_url(
                self.url,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            logger.info("Serial transport opened %s", self.url)
        except SerialException as exc:  # pragma: no cover - pass through
            raise RuntimeError(f"无法打开串口 {self.url}: {exc}") from exc

    def close(self) -> None:
        if self._serial is None:
            return
        logger.info("Serial transport closing %s", self.url)
        self._serial.close()
        self._serial = None

    def write(self, data: bytes) -> int:
        serial = self._ensure_open()
        return serial.write(data)

    def read(self, size: int = 1) -> bytes:
        serial = self._ensure_open()
        return serial.read(size)

    def readline(self) -> bytes:
        serial = self._ensure_open()
        return serial.readline()

    def flush(self) -> None:
        serial = self._ensure_open()
        serial.flush()

    def reset(self) -> None:
        serial = self._ensure_open()
        serial.reset_input_buffer()
        serial.reset_output_buffer()

    @property
    def is_open(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def _ensure_open(self) -> SerialBase:
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("串口未打开，请先调用 open() 或使用上下文管理器。")
        return self._serial

    def __enter__(self) -> "SerialTransport":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


__all__ = ["SerialTransport"]
