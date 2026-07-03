from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.utils.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.settings = settings
    yield


app = FastAPI(
    title="SHL Assessment Recommender",
    version="0.1.0",
    description="A stateless, catalog-grounded recommender service for SHL assessments.",
    lifespan=lifespan,
)
app.include_router(router)
