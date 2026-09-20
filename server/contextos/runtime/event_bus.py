import asyncio
from typing import Callable, Set, Dict, Any, List
from contextos.models.event import EventEnvelope, EventType
import contextos.storage.db as db_mod

class EventBus:
    """
    In-process asynchronous event bus with automatic SQLite persistence.
    """

    def __init__(self):
        self._listeners: Set[Callable[[EventEnvelope], Any]] = set()

    def subscribe(self, callback: Callable[[EventEnvelope], Any]):
        self._listeners.add(callback)

    def unsubscribe(self, callback: Callable[[EventEnvelope], Any]):
        self._listeners.discard(callback)

    async def emit(self, event: EventEnvelope):
        # 1. Persist to SQLite
        db_mod.db.save_event(event)

        # 2. Dispatch to subscribers (e.g. WebSocket clients)
        tasks = []
        for listener in list(self._listeners):
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    tasks.append(asyncio.create_task(res))
            except Exception as e:
                print(f"[ContextOS EventBus Error] Dispatch failed: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(self, event: EventEnvelope):
        """Synchronous wrapper for emitting events."""
        db_mod.db.save_event(event)
        for listener in list(self._listeners):
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(res)
                        else:
                            loop.run_until_complete(res)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[ContextOS EventBus Error] Sync dispatch failed: {e}")

event_bus = EventBus()
