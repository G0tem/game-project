from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import time
import httpx
from redis.asyncio import Redis

app = FastAPI()


redis_client = Redis(host="redis", port=6379, db=0)


class Bet(BaseModel):
    id: str
    event_id: str
    amount: float
    status: str = "pending"


LINE_PROVIDER_URL = "http://line-provider:8080"


@app.on_event("startup")
async def startup():
    await redis_client.ping()  # Проверка подключения к Redis


@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()  # Закрытие соединения с Redis


@app.get("/events")
async def get_events():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LINE_PROVIDER_URL}/events")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch events")
        events = response.json()
        current_time = time.time()
        return [event for event in events if event["deadline"] > current_time]


@app.post("/bet")
async def place_bet(event_id: str, amount: float):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LINE_PROVIDER_URL}/event/{event_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Event not found")
        event = response.json()
        if event["deadline"] < time.time():
            raise HTTPException(status_code=400, detail="Betting deadline has passed")

    bet = Bet(id=str(uuid.uuid4()), event_id=event_id, amount=amount)
    await redis_client.hset(
        f"bet:{bet.id}",
        mapping={"event_id": bet.event_id, "amount": bet.amount, "status": bet.status},
    )
    return bet


@app.post("/update_bet_status")
async def update_bet_status(event_id: str, state: str):
    async for key in redis_client.scan_iter("bet:*"):
        bet_data = await redis_client.hgetall(key)
        if bet_data[b"event_id"].decode() == event_id:
            await redis_client.hset(key, "status", state.lower())
    return {"message": "Bet status updated"}


@app.get("/bets")
async def get_bets():
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
