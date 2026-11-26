from fastapi import FastAPI

from app.routes.devices import router as devices_router

app = FastAPI(title="NetPulse API")
app.include_router(devices_router)