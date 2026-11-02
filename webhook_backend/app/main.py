from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine

from app import models

from app.webhooks import router as webhook_router
from app.customer import router as customer_router
from app.auth import router as auth_router
from app.agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    yield

    engine.dispose()


app = FastAPI(
    title="Datastraw Customer Support API",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(webhook_router)
app.include_router(customer_router)
app.include_router(auth_router)
app.include_router(agent_router)


@app.get("/health")
def health_check():

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }