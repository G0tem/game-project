from fastapi import APIRouter
from repositories import BetMakerRepository


bet_maker_router = APIRouter(prefix="/api/v1", tags=["Bet"])


@bet_maker_router.get("/events")
async def get_events():
    return await BetMakerRepository.get_events()


@bet_maker_router.post("/bet")
async def place_bet(event_id: str, amount: float):
    return await BetMakerRepository.place_bet(event_id, amount)


@bet_maker_router.post("/update_bet_status")
async def update_bet_status(event_id: str, state: str):
    return await BetMakerRepository.update_bet_status(event_id, state)


@bet_maker_router.get("/bets")
async def get_bets():
    return await BetMakerRepository.get_bets()
