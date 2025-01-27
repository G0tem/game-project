import pytest
from fastapi import HTTPException
from repositories import BetMakerRepository
from schemas import Bet
import fakeredis.aioredis as fakeredis
import time
import httpx
from unittest.mock import AsyncMock


@pytest.fixture
async def mock_redis():
    redis = fakeredis.FakeRedis()
    await redis.flushall()
    yield redis
    await redis.close()


@pytest.fixture
def mock_httpx_client(monkeypatch):
    async def mock_get(url, *args, **kwargs):
        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self.json_data = json_data

            def json(self):
                return self.json_data

        if url == "http://line-provider:8080/api/v1/events":
            return MockResponse(
                200,
                [
                    {
                        "id": "1",
                        "name": "Event 1",
                        "deadline": time.time() + 3600,
                        "state": 1,
                    },  # Активное событие
                    {
                        "id": "2",
                        "name": "Event 2",
                        "deadline": time.time() - 3600,
                        "state": 1,
                    },  # Прошедшее событие
                ],
            )
        elif url.startswith("http://line-provider:8080/api/v1/event/"):
            event_id = url.split("/")[-1]
            if event_id == "1":
                return MockResponse(
                    200,
                    {
                        "id": "1",
                        "name": "Event 1",
                        "deadline": time.time() + 3600,
                        "state": 1,
                    },
                )
            else:
                return MockResponse(404, {"detail": "Event not found"})
        else:
            return MockResponse(500, {"detail": "Internal Server Error"})

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))


@pytest.mark.asyncio
async def test_get_events(mock_httpx_client):
    events = await BetMakerRepository.get_events()
    assert len(events) == 1
    assert events[0]["id"] == "1"


@pytest.mark.asyncio
async def test_place_bet(mock_httpx_client, mock_redis):
    BetMakerRepository.redis_client = mock_redis

    # Успешная ставка
    bet = await BetMakerRepository.place_bet("1", 100.0)
    assert isinstance(bet, Bet)
    assert bet.event_id == "1"
    assert bet.amount == 100.0
    assert bet.status == "pending"

    # Ставка на несуществующее событие
    with pytest.raises(HTTPException) as exc_info:
        await BetMakerRepository.place_bet("999", 100.0)
    assert exc_info.value.status_code == 404
