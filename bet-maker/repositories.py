import httpx
from fastapi import HTTPException
import time
import uuid
from database import redis_client
from schemas import Bet


LINE_PROVIDER_URL = "http://line-provider:8080/api/v1"


class BetMakerRepository:

    @staticmethod
    async def get_events() -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LINE_PROVIDER_URL}/events")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch events")
            events = response.json()
            current_time = time.time()
            return [event for event in events if event["deadline"] > current_time]

    @staticmethod
    async def place_bet(event_id: str, amount: float) -> Bet:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LINE_PROVIDER_URL}/event/{event_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Event not found")
            event = response.json()
            if event["deadline"] < time.time():
                raise HTTPException(
                    status_code=400, detail="Betting deadline has passed"
                )

        bet = Bet(id=str(uuid.uuid4()), event_id=event_id, amount=amount)
        await redis_client.hset(
            f"bet:{bet.id}",
            mapping={
                "event_id": bet.event_id,
                "amount": bet.amount,
                "status": bet.status,
            },
        )
        return bet

    @staticmethod
    async def update_bet_status(event_id: str, state: str) -> dict:
        async for key in redis_client.scan_iter("bet:*"):
            bet_data = await redis_client.hgetall(key)
            if bet_data[b"event_id"].decode() == event_id:
                await redis_client.hset(key, "status", state.lower())
        return {"message": "Bet status updated"}

    @staticmethod
    async def get_bets() -> list[Bet]:
        bets = []
        async for key in redis_client.scan_iter("bet:*"):
            bet_data = await redis_client.hgetall(key)
            bets.append(
                {
                    "id": key.decode().split(":")[1],
                    "event_id": bet_data[b"event_id"].decode(),
                    "amount": float(bet_data[b"amount"]),
                    "status": bet_data[b"status"].decode(),
                }
            )
        return bets
