"""
Integration tests for API endpoints.

These test the full request lifecycle: HTTP → route → service →
repository → database → response.  They use an in-memory SQLite
database for speed.
"""

import pytest


class TestHealthEndpoint:

    async def test_health_returns_200(self, async_client):
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPlayerEndpoints:

    async def test_list_players_empty_db(self, async_client):
        response = await async_client.get("/api/v1/players")
        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_players_with_data(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players")
        data = response.json()

        assert data["total"] == 3  # 3 unique players
        assert data["page"] == 1
        assert len(data["items"]) == 3

    async def test_list_players_pagination(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players?size=2&page=1")
        data = response.json()

        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2

    async def test_list_players_filter_continent(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players?continent=55")
        data = response.json()

        assert data["total"] == 2
        assert all(p["continent"] == 55 for p in data["items"])

    async def test_list_players_filter_min_resources(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players?min_resources=10000")
        data = response.json()

        assert all(p["total_resources"] >= 10000 for p in data["items"])

    async def test_list_players_invalid_page(self, async_client):
        response = await async_client.get("/api/v1/players?page=-1")

        assert response.status_code == 422  # Pydantic validation error

    async def test_get_player_returns_latest_snapshot(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players/1")
        data = response.json()

        assert response.status_code == 200
        assert data["player_name"] == "Alice"
        # Should return the LATEST snapshot (wood=6000, not 5000).
        assert data["wood_nr"] == 6000
        assert data["total_resources"] == 15000

    async def test_get_player_not_found(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Player not found"

    async def test_player_history_returns_multiple_snapshots(
        self, async_client, seed_data
    ):
        response = await async_client.get("/api/v1/players/1/history")
        snapshots = response.json()

        assert response.status_code == 200
        # Alice has 2 snapshots.
        assert len(snapshots) == 2
        # Newest first.
        assert snapshots[0]["wood_nr"] == 6000
        assert snapshots[1]["wood_nr"] == 5000

    async def test_player_history_not_found(self, async_client, seed_data):
        response = await async_client.get("/api/v1/players/999/history")
        assert response.status_code == 404


class TestAnalyticsEndpoints:

    async def test_resource_stats(self, async_client, seed_data):
        response = await async_client.get("/api/v1/analytics/resources")
        data = response.json()

        assert response.status_code == 200
        assert data["total_players"] == 3
        assert data["max_total_resources"] > 0
        assert data["avg_wood"] > 0

    async def test_continent_breakdown(self, async_client, seed_data):
        response = await async_client.get("/api/v1/analytics/continents")
        continents = response.json()
        continent_ids = [c["continent"] for c in continents]

        assert len(continents) == 2  # continents 44 and 55
        assert response.status_code == 200
        assert 44 in continent_ids
        assert 55 in continent_ids

    async def test_anomalies_endpoint(self, async_client, seed_data):
        response = await async_client.get("/api/v1/analytics/anomalies")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_anomalies_custom_threshold(self, async_client, seed_data):
        response = await async_client.get(
            "/api/v1/analytics/anomalies?z_threshold=1.0"
        )

        assert response.status_code == 200

    async def test_anomalies_invalid_threshold(self, async_client):
        response = await async_client.get(
            "/api/v1/analytics/anomalies?z_threshold=0.5"
        )
        
        assert response.status_code == 422  # Below ge=1.0