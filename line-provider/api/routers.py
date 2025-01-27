from fastapi import APIRouter, HTTPException, Path
from schemas import Event
from repositories import LineProviderRepository


line_provider_router = APIRouter(prefix="/api/v1", tags=["Event"])


BET_MAKER_CALLBACK_URL = "http://bet-maker:8000/update_bet_status"


@line_provider_router.put("/event")
async def create_event(event: Event):
    await LineProviderRepository.create_event(event)

    return {}


@line_provider_router.get("/event/{event_id}")
async def get_event(event_id: str = Path()):
    event_id = await LineProviderRepository.get_event_by_id(event_id)
    if event_id:
        return event_id
    else:
        raise HTTPException(status_code=404, detail="Event not found")


@line_provider_router.get("/events")
async def get_events():
    list_events = await LineProviderRepository.get_events()
    return list_events
