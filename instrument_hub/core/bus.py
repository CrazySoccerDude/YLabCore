from __future__ import annotations

from dataclasses import dataclass
import asyncio
import inspect
import logging
from threading import RLock
from typing import Any, Awaitable, Mapping, Protocol
from uuid import uuid4

from .executors import ExecutorRegistry
from .policy import DispatchMode, DispatchPolicy


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Event:
    topic: str
    payload: Any
    metadata: Mapping[str, Any] | None = None


class EventHandler(Protocol):
    def __call__(self, event: Event) -> Any | Awaitable[Any]: ...


class EventDispatchError(RuntimeError):
    def __init__(self, event: Event, errors: list[Exception]) -> None:
        super().__init__(f"Unhandled exception(s) during event dispatch for topic '{event.topic}'")
        self.event = event
        self.errors = errors


@dataclass(frozen=True, slots=True)
class _Subscriber:
    token: str
    callback: EventHandler
    policy: DispatchPolicy
    order: int


class _BaseEventBus:
    def __init__(self, *, executor_registry: ExecutorRegistry | None = None) -> None:
        self._lock = RLock()
        self._subscriptions_by_topic: dict[str, list[_Subscriber]] = {}
        self._topic_by_token: dict[str, str] = {}
        self._registry = executor_registry or ExecutorRegistry()
        self._sequence = 0

    def subscribe(
        self,
        topic: str,
        callback: EventHandler,
        *,
        policy: DispatchPolicy | None = None,
    ) -> str:
        token = uuid4().hex
        actual_policy = policy or DispatchPolicy.default()
        subscriber = _Subscriber(
            token=token,
            callback=callback,
            policy=actual_policy,
            order=self._sequence,
        )

        with self._lock:
            bucket = self._subscriptions_by_topic.setdefault(topic, [])
            if actual_policy.name:
                for existing in bucket:
                    if existing.policy.name == actual_policy.name:
                        raise ValueError(
                            f"Duplicate subscriber name '{actual_policy.name}' for topic '{topic}'"
                        )
            bucket.append(subscriber)
            self._topic_by_token[token] = topic
            self._sequence += 1

        return token

    def unsubscribe(self, token: str) -> bool:
        with self._lock:
            topic = self._topic_by_token.pop(token, None)
            if topic is None:
                return False

            subscribers = self._subscriptions_by_topic.get(topic)
            if not subscribers:
                return False

            for index, subscriber in enumerate(subscribers):
                if subscriber.token == token:
                    del subscribers[index]
                    break
            else:
                return False

            if not subscribers:
                self._subscriptions_by_topic.pop(topic, None)

        return True

    def shutdown(self, wait: bool = True) -> None:
        self._registry.shutdown(wait=wait)

    def _snapshot_subscribers(self, topic: str) -> tuple[_Subscriber, ...]:
        with self._lock:
            return tuple(self._subscriptions_by_topic.get(topic, ()))

    def _resolve_order(self, subscribers: tuple[_Subscriber, ...]) -> list[_Subscriber]:
        if len(subscribers) <= 1:
            return list(subscribers)

        name_to_subscriber: dict[str, _Subscriber] = {}
        for subscriber in subscribers:
            name = subscriber.policy.name
            if name:
                name_to_subscriber[name] = subscriber

        adjacency: dict[_Subscriber, set[_Subscriber]] = {subscriber: set() for subscriber in subscribers}
        indegree: dict[_Subscriber, int] = {subscriber: 0 for subscriber in subscribers}

        def _resolve_targets(labels: tuple[str, ...]) -> list[_Subscriber]:
            resolved: list[_Subscriber] = []
            for label in labels:
                target = name_to_subscriber.get(label)
                if target is not None:
                    resolved.append(target)
            return resolved

        for subscriber in subscribers:
            for target in _resolve_targets(subscriber.policy.run_before):
                if target is subscriber:
                    continue
                adjacency[subscriber].add(target)
                indegree[target] += 1
            for source in _resolve_targets(subscriber.policy.run_after):
                if source is subscriber:
                    continue
                if subscriber not in adjacency[source]:
                    adjacency[source].add(subscriber)
                    indegree[subscriber] += 1

        ready: list[tuple[int, int, _Subscriber]] = []
        for subscriber in subscribers:
            if indegree[subscriber] == 0:
                ready.append((subscriber.policy.priority, subscriber.order, subscriber))

        ready.sort()
        ordered: list[_Subscriber] = []

        while ready:
            priority, order, subscriber = ready.pop(0)
            ordered.append(subscriber)
            for target in adjacency[subscriber]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append((target.policy.priority, target.order, target))
                    ready.sort()

        if len(ordered) != len(subscribers):
            return sorted(subscribers, key=lambda sub: (sub.policy.priority, sub.order))

        return ordered


class EventBus(_BaseEventBus):
    def publish(
        self,
        topic: str,
        payload: Any,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        subscribers = self._snapshot_subscribers(topic)

        if not subscribers:
            return

        event = Event(topic=topic, payload=payload, metadata=metadata)
        errors: list[Exception] = []

        for subscriber in self._resolve_order(subscribers):
            try:
                self._dispatch_to_handler(subscriber, event)
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(exc)
                LOGGER.exception(
                    "Event handler %r raised during dispatch of topic '%s'",
                    subscriber.callback,
                    topic,
                )

        if errors:
            raise EventDispatchError(event, errors)

    def _dispatch_to_handler(self, subscriber: _Subscriber, event: Event) -> None:
        policy = subscriber.policy
        if policy.mode is DispatchMode.SYNC:
            result = subscriber.callback(event)
            if inspect.isawaitable(result):
                self._await_sync_awaitable(result)
            return

        if policy.mode is DispatchMode.BACKGROUND:
            future = self._registry.get(policy.executor_name).submit(
                _invoke_handler,
                subscriber.callback,
                event,
            )
            if policy.await_result:
                future.result()
            else:
                future.add_done_callback(_log_future_exception)
            return

        if policy.mode is DispatchMode.ASYNC:
            self._dispatch_async(subscriber.callback, event, policy)
            return

        raise RuntimeError(f"Unsupported dispatch mode {policy.mode!r}")

    def _dispatch_async(
        self,
        handler: EventHandler,
        event: Event,
        policy: DispatchPolicy,
    ) -> None:
        result = handler(event)
        if not inspect.isawaitable(result):
            raise TypeError("Async dispatch requires awaitable handler result")

        if not policy.await_result:
            raise NotImplementedError("Async handlers currently require await_result=True")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_consume_awaitable(result))
            return

        raise RuntimeError(
            "Cannot synchronously await coroutine while an event loop is running; use AsyncEventBus instead"
        )

    @staticmethod
    def _await_sync_awaitable(awaitable: Awaitable[Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_consume_awaitable(awaitable))
            return
        raise RuntimeError(
            "Synchronous dispatch cannot await coroutine while event loop is running; use AsyncEventBus"
        )


class AsyncEventBus(_BaseEventBus):
    async def publish(
        self,
        topic: str,
        payload: Any,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        subscribers = self._snapshot_subscribers(topic)

        if not subscribers:
            return

        event = Event(topic=topic, payload=payload, metadata=metadata)
        errors: list[Exception] = []
        loop = asyncio.get_running_loop()
        background_refs: list[asyncio.Future[Any]] = []

        for subscriber in self._resolve_order(subscribers):
            policy = subscriber.policy
            try:
                if policy.mode is DispatchMode.SYNC:
                    result = subscriber.callback(event)
                    if inspect.isawaitable(result):
                        await result
                elif policy.mode is DispatchMode.BACKGROUND:
                    future = loop.run_in_executor(
                        self._registry.get(policy.executor_name),
                        _invoke_handler,
                        subscriber.callback,
                        event,
                    )
                    if policy.await_result:
                        await future
                    else:
                        future.add_done_callback(_log_asyncio_future_exception)
                        background_refs.append(future)
                elif policy.mode is DispatchMode.ASYNC:
                    result = subscriber.callback(event)
                    if not inspect.isawaitable(result):
                        raise TypeError("Async dispatch requires awaitable handler result")
                    if policy.await_result:
                        await result
                    else:
                        task = asyncio.ensure_future(result)
                        task.add_done_callback(_log_task_exception)
                        background_refs.append(task)
                else:  # pragma: no cover - defensive
                    raise RuntimeError(f"Unsupported dispatch mode {policy.mode!r}")
            except Exception as exc:
                errors.append(exc)
                LOGGER.exception(
                    "Event handler %r raised during async dispatch of topic '%s'",
                    subscriber.callback,
                    topic,
                )

        if errors:
            raise EventDispatchError(event, errors)


def _invoke_handler(handler: EventHandler, event: Event) -> None:
    handler(event)


def _log_future_exception(future) -> None:
    try:
        future.result()
    except Exception:  # pragma: no cover - logging side-effect
        LOGGER.exception("Background handler raised")


async def _consume_awaitable(awaitable: Awaitable[Any]) -> Any:
    return await awaitable


def _log_asyncio_future_exception(future: asyncio.Future[Any]) -> None:
    try:
        future.result()
    except Exception:  # pragma: no cover - logging side-effect
        LOGGER.exception("Background async handler raised")


def _log_task_exception(task: asyncio.Future[Any]) -> None:
    try:
        task.result()
    except Exception:  # pragma: no cover - logging side-effect
        LOGGER.exception("Async handler task raised")

