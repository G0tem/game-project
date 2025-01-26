from fastapi import FastAPI, Path, HTTPException, Query
import decimal
import enum
import time
from typing import Optional
from pydantic import BaseModel
import httpx


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


events: dict[str, Event] = {
    "1": Event(
        event_id="1",
        coefficient=1.2,
        deadline=int(time.time()) + 600,
        state=EventState.NEW,
    ),
    "2": Event(
        event_id="2",
        coefficient=1.15,
        deadline=int(time.time()) + 60,
        state=EventState.NEW,
    ),
    "3": Event(
        event_id="3",
        coefficient=1.67,
        deadline=int(time.time()) + 90,
        state=EventState.NEW,
    ),
}

app = FastAPI()

BET_MAKER_CALLBACK_URL = "http://bet-maker:8000/update_bet_status"


@app.put("/event")
async def create_event(event: Event):
    if event.event_id not in events:
        events[event.event_id] = event
        return {}

    for p_name, p_value in event.dict(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)

    # Если статус события изменился, отправляем callback в bet-maker
    if event.state in [EventState.FINISHED_WIN, EventState.FINISHED_LOSE]:
        await notify_bet_maker(event.event_id, event.state)

    return {}


async def notify_bet_maker(event_id: str, state: EventState):
    async with httpx.AsyncClient() as client:
        params = {
            "event_id": event_id,
            "state": state.name,
        }
        try:
            response = await client.post(BET_MAKER_CALLBACK_URL, params=params)
            if response.status_code != 200:
                print(f"Failed to notify bet-maker: {response.status_code}")
        except httpx.ConnectError as e:
            print(f"Connection error: {e}")


@app.get("/event/{event_id}")
async def get_event(event_id: str = Path()):
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@app.get("/events")
async def get_events():
    return list(e for e in events.values() if time.time() < e.deadline)
