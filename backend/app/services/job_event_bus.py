"""
Job Event Bus - In-memory pub/sub for job status updates
"""
import asyncio
from typing import Dict, Set, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class JobEvent:
    """Job update event"""
    job_id: str
    db_alias: str
    status: str
    progress: float
    current_step: str
    timestamp: datetime
    results: Dict[str, Any] = None
    error_message: str = None


class JobEventBus:
    """
    In-memory event bus for job updates.
    Background tasks emit events, SSE endpoints subscribe to them.
    """
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, db_alias: str) -> asyncio.Queue:
        """Subscribe to job updates for a specific database"""
        queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            if db_alias not in self._subscribers:
                self._subscribers[db_alias] = set()
            self._subscribers[db_alias].add(queue)

        logger.info(f"New subscriber for {db_alias} (total: {len(self._subscribers[db_alias])})")
        return queue

    async def unsubscribe(self, db_alias: str, queue: asyncio.Queue):
        """Unsubscribe from job updates"""
        async with self._lock:
            if db_alias in self._subscribers:
                self._subscribers[db_alias].discard(queue)
                if not self._subscribers[db_alias]:
                    del self._subscribers[db_alias]
                logger.info(f"Subscriber removed for {db_alias} (remaining: {len(self._subscribers.get(db_alias, []))})")

    async def publish(self, event: JobEvent):
        """Publish a job update event to all subscribers"""
        db_alias = event.db_alias

        async with self._lock:
            subscribers = self._subscribers.get(db_alias, set()).copy()

        if subscribers:
            logger.debug(f"Publishing event for {db_alias} to {len(subscribers)} subscribers")

            for queue in subscribers:
                try:
                    # Non-blocking put, drop oldest if full
                    if queue.full():
                        try:
                            queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    queue.put_nowait(event)
                except Exception as e:
                    logger.error(f"Failed to publish to subscriber: {e}")

    def has_subscribers(self, db_alias: str) -> bool:
        """Check if there are any active subscribers for a database"""
        return db_alias in self._subscribers and len(self._subscribers[db_alias]) > 0


# Global event bus instance
job_event_bus = JobEventBus()
