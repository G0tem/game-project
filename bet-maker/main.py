from fastapi import FastAPI
from api.routers import bet_maker_router
from database import redis_client


app = FastAPI()

app.include_router(bet_maker_router)


@app.on_event("startup")
async def startup():
    await redis_client.ping()  # Проверка подключения к Redis


@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()  # Закрытие соединения с Redis
