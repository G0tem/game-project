from pydantic import BaseModel


class Bet(BaseModel):
    id: str
    event_id: str
    amount: float
    status: str = "pending"
