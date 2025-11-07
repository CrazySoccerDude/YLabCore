"""占位：ADM-X2001 LCR 仪器驱动实现。"""

from __future__ import annotations

from .lcr_base import LCRDriver


class ADMX2001Driver(LCRDriver):
    """TODO: 结合 transport 与 parser 完成具体协议。"""

    def identify(self) -> dict:
        raise NotImplementedError

    def start_sweep(self, params: dict) -> None:
        raise NotImplementedError

    def abort(self) -> None:
        raise NotImplementedError
