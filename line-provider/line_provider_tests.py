import time
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_simple_workflow(anyio_backend):
    test_id = "test_id"

    test_event = {
        "event_id": test_id,
        "coefficient": "1.0",
        "deadline": int(time.time()) + 600,
        "state": 1,
    }

    client = TestClient(app)  # Создаем TestClient

    # Создаем событие
    create_response = client.put("/api/v1/event", json=test_event)
    assert create_response.status_code == 200

    # Получаем событие
    response = client.get(f"/api/v1/event/{test_id}")
    assert response.status_code == 200
    assert response.json() == test_event

    # Обновляем событие
    updated_event = test_event.copy()
    updated_event["state"] = 2

    update_response = client.put(
        "/api/v1/event", json={"event_id": test_id, "state": 2}
    )
    assert update_response.status_code == 200

    # Проверяем обновленное событие
    response = client.get(f"/api/v1/event/{test_id}")
    assert response.status_code == 200
    assert response.json() == updated_event
