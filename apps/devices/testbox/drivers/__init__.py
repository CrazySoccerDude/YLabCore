"""Device TestBox drivers for fake and real backends."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from random import Random
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional

from ...driver_base import InstrumentDriver
from ..parsers.scpi import build_command, parse_response
from ..transport import SerialTransport

logger = logging.getLogger(__name__)


class DeviceTestBoxFakeDriver(InstrumentDriver):
    """Virtual diagnostic driver that simulates staged execution."""

    def __init__(
        self,
        *,
        default_duration_s: float = 60.0,
        stages: List[str] | None = None,
        seed: int = 7,
    ) -> None:
        self.default_duration_s = max(1.0, float(default_duration_s))
        self._stages = stages or [
            "power_on_self_test",
            "sensor_calibration",
            "thermal_stabilization",
            "diagnostic_sequence",
            "report_generation",
        ]
        self._rng = Random(seed)
        self._busy = False
        self._last_started: datetime | None = None
        self._last_progress: list[dict[str, Any]] = []
        self._last_result: dict[str, Any] | None = None

    def identify(self) -> Mapping[str, Any]:
        return {
            "model": "FAKE-TESTBOX",
            "vendor": "InstruHub",
            "firmware": "sim-1.0",
        }

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        if name != "run_diagnostic":
            raise ValueError(f"unsupported task: {name}")
        self._run_diagnostic(dict(params))

    def _run_diagnostic(self, params: Dict[str, Any]) -> None:
        if self._busy:
            raise RuntimeError("diagnostic already in progress")
        self._busy = True
        self._last_started = datetime.now(timezone.utc)
        duration = float(params.get("duration_s") or self.default_duration_s)
        profile = params.get("profile") or "default"
        self._last_progress = []
        total = len(self._stages)
        for idx, stage in enumerate(self._stages, start=1):
            jitter = self._rng.uniform(-0.1, 0.1) * duration / total
            elapsed = max(0.0, (duration / total) * idx + jitter)
            self._last_progress.append(
                {
                    "stage": stage,
                    "progress": min(1.0, idx / total),
                    "elapsed_s": round(elapsed, 3),
                    "message": f"{stage} completed",
                }
            )
        self._last_result = {
            "duration_s": round(duration, 3),
            "profile": profile,
            "passed": True,
            "summary": "All diagnostics completed without anomalies.",
        }
        self._busy = False

    def abort(self) -> None:
        if self._busy:
            self._busy = False
            self._last_progress = []
            self._last_result = {
                "duration_s": 0.0,
                "profile": None,
                "passed": False,
                "summary": "Diagnostic aborted by operator.",
            }

    def is_busy(self) -> bool:
        return self._busy

    def last_started_at(self) -> datetime | None:
        return self._last_started

    def fetch_progress(self) -> List[dict[str, Any]]:
        return list(self._last_progress)

    def fetch_result(self) -> dict[str, Any] | None:
        return dict(self._last_result) if self._last_result is not None else None


class DeviceTestBoxRealDriver(InstrumentDriver):
    """Serial-backed driver that speaks a SCPI-like protocol.

    该实现聚焦基础读写：
    - 使用 `SerialTransport` 打开串口并发送 `TESTBOX:RUN` 指令；
    - 调用 `_poll()` 解析串口响应，记录进度与结果；
    - 响应格式采用 ``TYPE:key=value`` 键值对约定，利用 `parse_response` 解析。
    """

    def __init__(
        self,
        transport: Optional[SerialTransport] = None,
        *,
        command_builder: Callable[..., str] = build_command,
        response_parser: Callable[[str], Mapping[str, Any]] = parse_response,
    ) -> None:
        self._transport = transport or SerialTransport()
        self._command_builder = command_builder
        self._response_parser = response_parser
        self._busy = False
        self._last_started: datetime | None = None
        self._progress: list[dict[str, Any]] = []
        self._result: dict[str, Any] | None = None

    def identify(self) -> Mapping[str, Any]:
        return {
            "model": "REAL-TESTBOX",
            "transport": self._transport.url,
        }

    def start_task(self, name: str, params: Mapping[str, Any]) -> None:
        if name != "run_diagnostic":
            raise ValueError(f"unsupported task: {name}")
        if self._busy:
            raise RuntimeError("diagnostic already in progress")

        payload = dict(params or {})
        self._transport.open()
        try:
            self._transport.reset()
        except RuntimeError:
            # 兼容无法 reset 的某些 URL
            logger.debug("Transport reset skipped for %s", self._transport.url)

        command = self._command_builder(
            "TESTBOX:RUN",
            self._render_duration(payload.get("duration_s")),
            payload.get("profile"),
        )
        logger.info("Issuing diagnostic command: %s", command.strip())
        self._transport.write(command.encode("utf-8"))
        self._transport.flush()

        self._busy = True
        self._last_started = datetime.now(timezone.utc)
        self._progress.clear()
        self._result = None

    def abort(self) -> None:
        if not self._busy:
            return
        try:
            command = self._command_builder("TESTBOX:ABORT")
            self._transport.write(command.encode("utf-8"))
            self._transport.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send abort command: %s", exc)
        finally:
            self._busy = False

    def is_busy(self) -> bool:
        return self._busy

    def last_started_at(self) -> datetime | None:
        return self._last_started

    def fetch_progress(self) -> List[dict[str, Any]]:
        self._poll()
        return list(self._progress)

    def fetch_result(self) -> dict[str, Any] | None:
        self._poll()
        return dict(self._result) if self._result is not None else None

    def _poll(self, limit: int | None = None) -> None:
        if not self._transport.is_open:
            return
        count = 0
        while True:
            line = self._transport.readline()
            if not line:
                break
            payload = line.decode("utf-8", "ignore").strip()
            if not payload:
                continue
            try:
                record = dict(self._response_parser(payload))
            except Exception as exc:  # noqa: BLE001
                logger.debug("Ignoring unparsable response %s: %s", payload, exc)
                continue
            self._ingest_record(record)
            if limit is not None:
                count += 1
                if count >= limit:
                    break

    def _ingest_record(self, record: MutableMapping[str, Any]) -> None:
        kind = str(record.pop("kind", record.pop("type", ""))).lower()
        if not kind:
            # 无分类数据，按照原始 payload 记录
            self._progress.append({"raw": dict(record)})
            return

        if kind in {"progress", "prog"}:
            entry = {
                "progress": float(record.get("progress", record.get("pct", 0.0))),
                "stage": str(record.get("stage", record.get("phase", "unknown"))),
                "elapsed_s": _try_float(record.get("elapsed_s")),
                "message": record.get("message"),
                "raw": dict(record),
            }
            self._progress.append(entry)
            return

        if kind in {"done", "result", "complete"}:
            passed = _normalize_passed(record.get("result") or record.get("status"))
            self._result = {
                "result": "PASS" if passed else "FAIL",
                "duration_s": _try_float(record.get("duration") or record.get("duration_s")),
                "summary": record.get("summary"),
                "raw": dict(record),
            }
            self._busy = False
            return

        if kind in {"error", "fail", "fault"}:
            self._result = {
                "result": "FAIL",
                "duration_s": _try_float(record.get("duration") or record.get("duration_s")),
                "summary": record.get("message") or record.get("summary"),
                "raw": dict(record),
            }
            self._busy = False
            return

        # 未知类型，记录原始信息以便调试
        self._progress.append({"kind": kind, "raw": dict(record)})

    @staticmethod
    def _render_duration(value: Any) -> Any:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return value


def _normalize_passed(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    lowered = str(value).strip().lower()
    if lowered in {"pass", "passed", "ok", "success"}:
        return True
    if lowered in {"fail", "failed", "error"}:
        return False
    return True


def _try_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "DeviceTestBoxFakeDriver",
    "DeviceTestBoxRealDriver",
]
