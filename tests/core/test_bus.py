from __future__ import annotations

import asyncio
import unittest

from instrument_hub.core.bus import AsyncEventBus, EventBus, EventDispatchError
from instrument_hub.core.policy import DispatchMode, DispatchPolicy


class EventBusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()

    def tearDown(self) -> None:
        self.bus.shutdown()

    def test_subscribe_and_publish(self) -> None:
        received: list[tuple[str, object]] = []

        def handler(event):
            received.append((event.topic, event.payload))

        self.bus.subscribe("foo.bar", handler)
        self.bus.publish("foo.bar", {"value": 42})

        self.assertEqual(received, [("foo.bar", {"value": 42})])

    def test_unsubscribe(self) -> None:
        called = False

        def handler(event):
            nonlocal called
            called = True

        token = self.bus.subscribe("topic", handler)
        self.assertTrue(self.bus.unsubscribe(token))
        self.assertFalse(self.bus.unsubscribe(token))  # 幂等

        self.bus.publish("topic", None)
        self.assertFalse(called)

    def test_multiple_handlers_order(self) -> None:
        results: list[str] = []

        def handler_one(event):
            results.append("one")

        def handler_two(event):
            results.append("two")

        self.bus.subscribe("topic", handler_one)
        self.bus.subscribe("topic", handler_two)
        self.bus.publish("topic", None)

        self.assertEqual(results, ["one", "two"])

    def test_priority_overrides_subscription_order(self) -> None:
        results: list[str] = []

        def handler_low(event):
            results.append("low")

        def handler_high(event):
            results.append("high")

        self.bus.subscribe("topic", handler_low)
        self.bus.subscribe(
            "topic",
            handler_high,
            policy=DispatchPolicy(priority=-10, name="high"),
        )

        self.bus.publish("topic", None)

        self.assertEqual(results, ["high", "low"])

    def test_background_handler_runs_in_executor(self) -> None:
        from threading import current_thread

        thread_names: list[str] = []

        def background_handler(event):
            thread_names.append(current_thread().name)

        self.bus.subscribe(
            "topic",
            background_handler,
            policy=DispatchPolicy(mode=DispatchMode.BACKGROUND, await_result=True, name="bg"),
        )

        self.bus.publish("topic", None)

        self.assertTrue(thread_names)
        self.assertTrue(any("ThreadPoolExecutor" in name for name in thread_names))

    def test_background_handler_fire_and_forget(self) -> None:
        from threading import Event as ThreadingEvent

        signal = ThreadingEvent()

        def background_handler(event):
            signal.set()

        self.bus.subscribe(
            "topic",
            background_handler,
            policy=DispatchPolicy(mode=DispatchMode.BACKGROUND, await_result=False, name="bg"),
        )

        self.bus.publish("topic", None)

        self.assertTrue(signal.wait(1.0))

    def test_publish_no_subscribers(self) -> None:
        # 不应抛出异常
        self.bus.publish("no.listeners", {"noop": True})

    def test_handler_exception_aggregated(self) -> None:
        called: list[str] = []

        def bad_handler(event):
            raise RuntimeError("boom")

        def good_handler(event):
            called.append("ok")

        self.bus.subscribe("topic", bad_handler)
        self.bus.subscribe("topic", good_handler)

        with self.assertRaises(EventDispatchError) as ctx:
            self.bus.publish("topic", None)

        self.assertEqual(called, ["ok"])
        self.assertEqual(len(ctx.exception.errors), 1)
        self.assertIsInstance(ctx.exception.errors[0], RuntimeError)
        self.assertEqual(ctx.exception.event.topic, "topic")


class AsyncEventBusTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.bus = AsyncEventBus()

    async def asyncTearDown(self) -> None:
        self.bus.shutdown()

    async def test_async_handler_receives_event(self) -> None:
        received: list[int] = []

        async def handler(event):
            await asyncio.sleep(0)
            received.append(event.payload)

        self.bus.subscribe(
            "topic",
            handler,
            policy=DispatchPolicy(mode=DispatchMode.ASYNC),
        )

        await self.bus.publish("topic", 42)

        self.assertEqual(received, [42])

    async def test_mixed_sync_async_order(self) -> None:
        order: list[str] = []

        def sync_handler(event):
            order.append("sync")

        async def async_handler(event):
            await asyncio.sleep(0)
            order.append("async")

        self.bus.subscribe(
            "topic",
            sync_handler,
            policy=DispatchPolicy(name="sync", priority=-1),
        )
        self.bus.subscribe(
            "topic",
            async_handler,
            policy=DispatchPolicy(mode=DispatchMode.ASYNC, name="async", priority=0),
        )

        await self.bus.publish("topic", None)

        self.assertEqual(order, ["sync", "async"])

    async def test_async_fire_and_forget(self) -> None:
        signal = asyncio.Event()

        async def async_handler(event):
            await asyncio.sleep(0)
            signal.set()

        self.bus.subscribe(
            "topic",
            async_handler,
            policy=DispatchPolicy(mode=DispatchMode.ASYNC, await_result=False),
        )

        await self.bus.publish("topic", None)

        await asyncio.wait_for(signal.wait(), timeout=1.0)

    async def test_background_handler_from_async_bus(self) -> None:
        from threading import Event as ThreadingEvent, current_thread

        signal = ThreadingEvent()
        thread_names: list[str] = []

        def background_handler(event):
            thread_names.append(current_thread().name)
            signal.set()

        self.bus.subscribe(
            "topic",
            background_handler,
            policy=DispatchPolicy(mode=DispatchMode.BACKGROUND, await_result=True),
        )

        await self.bus.publish("topic", None)

        self.assertTrue(signal.is_set())
        self.assertTrue(any("ThreadPoolExecutor" in name for name in thread_names))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
