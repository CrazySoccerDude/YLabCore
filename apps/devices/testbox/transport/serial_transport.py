"""占位：串口传输实现。"""

from __future__ import annotations


class SerialTransport:
    """TODO: 管理串口打开、读写、重连与超时。"""

    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate

    def open(self) -> None:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def read(self, size: int = 1) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
