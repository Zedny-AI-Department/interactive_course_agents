from fastapi import FastAPI

from src.routes import data_processing_router


app = FastAPI()
app.include_router(data_processing_router)