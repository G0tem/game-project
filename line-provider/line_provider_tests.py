import pytest
from fastapi.testclient import TestClient  # Используем TestClient из fastapi.testclient
from main import app  # Импортируем ваше FastAPI приложение
import time
import pytest_asyncio


# Фикстура для мокирования HTTP-запросов
@pytest.fixture
def mock_httpx_client(monkeypatch):
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            async def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code != 200:
                    raise Exception("HTTP error")

        # Мокируем ответы для разных URL
        if args[0] == "http://line_provider:8080/api/v1/events":
            return MockResponse(
                [{"event_id": "1", "deadline": time.time() + 1000, "state": 1}], 200
            )
        elif args[0] == "http://line-provider:8080/api/v1/event/1":
            return MockResponse(
                {"event_id": "1", "deadline": time.time() + 1000, "state": 1}, 200
            )
        elif args[0] == "http://line-provider:8080/api/v1/event/2":
            return MockResponse(
                {"event_id": "2", "deadline": time.time() - 1000, "state": 1}, 200
            )
        elif args[0] == "http://line-provider:8080/api/v1/event/3":
            return MockResponse(
                {"event_id": "3", "deadline": time.time() + 1000, "state": 2}, 200
            )
        elif args[0] == "http://line-provider:8080/api/v1/event/4":
            return MockResponse(
                {"event_id": "4", "deadline": time.time() + 1000, "state": 3}, 200
            )
        else:
            return MockResponse(None, 404)

    async def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            async def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code != 200:
                    raise Exception("HTTP error")

        # Мокируем ответы для POST-запросов
        if args[0] == "http://line-provider:8080/api/v1/bet":
            return MockResponse(
                {"id": "123", "event_id": "1", "amount": 100.0, "status": "pending"},
                200,
            )
        else:
            return MockResponse(None, 404)

    # Мокируем AsyncClient из httpx
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)


# Фикстура для создания тестового клиента
@pytest.fixture
def async_client():
    # Используем TestClient для тестирования FastAPI приложения
    with TestClient(app) as client:
        yield client


# Тест для получения списка событий
@pytest.mark.asyncio
async def test_get_events(mock_httpx_client, async_client):
    response = async_client.get(
        "/api/v1/events"
    )  # Убрали await, так как TestClient синхронный
    assert response.status_code == 200
    assert len(response.json()) > 0


# Тест для создания ставки
@pytest.mark.asyncio
async def test_place_bet(mock_httpx_client, async_client):
    response = async_client.post("/api/v1/bet", json={"event_id": "1", "amount": 100.0})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["event_id"] == "1"
    assert response.json()["amount"] == 100.0
    assert response.json()["status"] == "pending"


# Тест для создания ставки с истекшим сроком
@pytest.mark.asyncio
async def test_place_bet_expired_event(mock_httpx_client, async_client):
    response = async_client.post("/api/v1/bet", json={"event_id": "2", "amount": 100.0})
    assert response.status_code == 400
    assert response.json()["detail"] == "Betting deadline has passed"


# Тест для получения списка ставок
@pytest.mark.asyncio
async def test_get_bets(mock_httpx_client, async_client):
    # Создаем ставки
    async_client.post("/api/v1/bet", json={"event_id": "3", "amount": 100.0})
    async_client.post("/api/v1/bet", json={"event_id": "4", "amount": 200.0})

    # Получаем список ставок
    response = async_client.get("/api/v1/bets")
    assert response.status_code == 200
    bets = response.json()
    assert len(bets) == 2

    # Проверяем, что статусы ставок обновлены
    for bet in bets:
        if bet["event_id"] == "3":
            assert bet["status"] == "win"
        elif bet["event_id"] == "4":
            assert bet["status"] == "lose"
