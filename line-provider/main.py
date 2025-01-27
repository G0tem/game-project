from fastapi import FastAPI
from api.routers import line_provider_router


app = FastAPI()


app.include_router(line_provider_router)
