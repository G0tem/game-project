from fastapi import APIRouter, Path
from schemas import Event
from repositories import LineProviderRepository


line_provider_router = APIRouter(prefix="/api/v1", tags=["Event"])


@line_provider_router.put("/event")
async def create_event(event: Event):
    await LineProviderRepository.create_event(event)

    return {"message": "Event created or updated successfully"}


@line_provider_router.get("/event/{event_id}")
async def get_event(event_id: str = Path()):
    return await LineProviderRepository.get_event_by_id(event_id)


@line_provider_router.get("/events")
async def get_events():
    return await LineProviderRepository.get_events()
