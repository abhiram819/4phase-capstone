from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import DATABASE_BACKEND
from app.db.collections import ensure_indexes
from app.db.mongo import close_mongo_client, get_db
from app.routes.devices import router as devices_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
	try:
		if DATABASE_BACKEND == "mongodb":
			ensure_indexes(get_db())
		yield
	finally:
		close_mongo_client()


app = FastAPI(title="NetPulse API", lifespan=lifespan)
app.include_router(devices_router)