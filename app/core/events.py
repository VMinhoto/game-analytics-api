from datetime import datetime

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict,dataclass,field

from collections import defaultdict

from typing import Any, Callable, Coroutine


import redis.asyncio as redis



logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event definitions
# ---------------------------------------------------------------------------

@dataclass(frozen = True)
class Event:
    """Base class for all domain events"""

    event_type: str
    timestamp: str = field(default_factory = lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return  json.dumps(self.to_dict())
    

@dataclass(frozen = True)
class SnapshotCreatedEvent(Event):
    """Event Fired when a snapshot is created"""

    event_type: str = "snapshot.created"
    player_id: int = 0
    player_name: str = ""
    total_resources: int = 0
    continent: int = 0

@dataclass(frozen = True)
class AnomalyDetectedEvent(Event):
    """ Fired when an anomaly is detected"""

    event_type: str = "anomaly.detected"
    player_id: int = 0
    player_name: str = ""
    z_score: float = 0.0
    reason: str = ""


# ---------------------------------------------------------------------------
# Abstract event bus interface
# ---------------------------------------------------------------------------

# Type alias for event handler functions.
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]

class AbstractEventBus(ABC):
    """Contract for event implementation"""

    @abstractmethod
    async def publish(self, event:Event) -> None:
        """Publish an event to all subscribers"""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type"""


# ---------------------------------------------------------------------------
# In-memory implementation (Observer pattern)
# ---------------------------------------------------------------------------

class InMemoryEventBus(AbstractEventBus):
    """
    Simple in-process event bus.
 
    Handlers are async functions registered per event type.
    When an event is published, all matching handlers are called.
 
    Observer pattern — the bus is the subject, handlers
    are observers.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    async def publish(self, event: Event):
        handlers = self._handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Event Handler failed for %s", event.event_type
                )



    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

# ---------------------------------------------------------------------------
# Redis implementation (for cross-process / cross-service messaging)
# ---------------------------------------------------------------------------

class ReddisEventBus(AbstractEventBus):
    """
    Redis pub/sub backed event bus.
 
    Publishes events as JSON to Redis channels.  In production,
    separate worker processes subscribe to these channels and
    react independently — true decoupling across services.
 
    Falls back gracefully if Redis is unavailable.
    """
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._local_bus = InMemoryEventBus()

    async def publish(self, event):
        await self._local_bus.publish(event)

        try:
            await self._redis.publish(
                f"events: {event.event_type}",
                event.to_json(),
            )
        except redis.ConnectionError:
            logger.warning(
                "Reddis unavailable - event %s published locally only",
                event.event_type
            )
    
    def subscribe(self, event_type: str, handler: EventHandler):
        self._local_bus.subscribe(event_type,handler)
