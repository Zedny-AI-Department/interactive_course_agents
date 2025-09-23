from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.routes import data_processing_router, task_router, image_processing_router
from src.services.redis_service import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_service.connect()
    yield
    # Shutdown
    await redis_service.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(data_processing_router)
app.include_router(task_router)
app.include_router(image_processing_router)
