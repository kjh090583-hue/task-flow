from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .routes import tasks


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Task Flow API", lifespan=lifespan)
app.include_router(tasks.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
