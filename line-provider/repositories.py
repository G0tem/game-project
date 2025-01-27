import httpx
from schemas import Event
import time

from schemas import EventState

BET_MAKER_CALLBACK_URL = "http://bet-maker:8000/update_bet_status"


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


class LineProviderRepository:
    @staticmethod
    async def notify_bet_maker(event_id: str, state: EventState) -> None:
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

    @staticmethod
    async def create_event(event: Event) -> dict:
        if event.event_id not in events:
            events[event.event_id] = event
            return {}

        for p_name, p_value in event.dict(exclude_unset=True).items():
            setattr(events[event.event_id], p_name, p_value)

        if event.state in [EventState.FINISHED_WIN, EventState.FINISHED_LOSE]:
            await LineProviderRepository.notify_bet_maker(event.event_id, event.state)

        return {}

    @staticmethod
    async def get_event_by_id(event_id: str) -> Event:
        if event_id in events:
            return events[event_id]

    @staticmethod
    async def get_events() -> list[Event]:
        return list(e for e in events.values() if time.time() < e.deadline)
