from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uuid
import time
import httpx

app = FastAPI()


class Bet(BaseModel):
    id: str
    event_id: str
    amount: float
    status: str = "pending"


bets: List[Bet] = []

LINE_PROVIDER_URL = "http://line-provider:8080"


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
    bets.append(bet)
    return bet


@app.post("/update_bet_status")
async def update_bet_status(event_id: str, state: str):
    for bet in bets:
        if bet.event_id == event_id:
            if state == "FINISHED_WIN":
                bet.status = "win"

            elif state == "FINISHED_LOSE":
                bet.status = "lose"

    return {"message": "Bet status updated"}


@app.get("/bets")
async def get_bets():
    return bets
