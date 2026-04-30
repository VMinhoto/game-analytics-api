"""
Unit tests for the in-memory event bus.

Tests the Observer pattern implementation without any
external dependencies (no Redis needed).
"""

import pytest

from app.core.events import (
    AnomalyDetectedEvent,
    InMemoryEventBus,
    SnapshotCreatedEvent,
)


class TestInMemoryEventBus:

    @pytest.fixture
    def bus(self):
        return InMemoryEventBus()

    async def test_publish_calls_subscribed_handler(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("snapshot.created", handler)
        event = SnapshotCreatedEvent(player_id=1, player_name="Alice")


        await bus.publish(event)

        assert len(received) == 1
        assert received[0].player_name == "Alice"

    async def test_handler_only_receives_matching_events(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("anomaly.detected", handler)


        # Publish a different event type.
        await bus.publish(SnapshotCreatedEvent(player_id=1))
        assert len(received) == 0

        # Now publish matching type.
        await bus.publish(AnomalyDetectedEvent(player_id=1, z_score=3.5))
        assert len(received) == 1

    async def test_multiple_handlers_all_called(self, bus):
        results = {"a": False, "b": False}

        async def handler_a(event):
            results["a"] = True

        async def handler_b(event):
            results["b"] = True

        bus.subscribe("snapshot.created", handler_a)
        bus.subscribe("snapshot.created", handler_b)


        await bus.publish(SnapshotCreatedEvent())

        assert results["a"] is True
        assert results["b"] is True

    async def test_failing_handler_doesnt_break_others(self, bus):
        received = []

        async def bad_handler(event):
            raise ValueError("I'm broken")

        async def good_handler(event):
            received.append(event)

        bus.subscribe("snapshot.created", bad_handler)
        bus.subscribe("snapshot.created", good_handler)


        await bus.publish(SnapshotCreatedEvent())

        # Good handler still executed despite bad handler failing.
        assert len(received) == 1

    async def test_event_serialization(self):
        event = SnapshotCreatedEvent(
            player_id=5,
            player_name="Alice",
            total_resources=15000,
            continent=55,
        )
        data = event.to_dict()
        json_str = event.to_json()

        
        assert data["player_id"] == 5
        assert data["event_type"] == "snapshot.created"
        assert "timestamp" in data


        assert '"player_name": "Alice"' in json_str