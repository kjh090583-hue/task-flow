from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import config, db
from .routes import auth, tasks


@asynccontextmanager
async def lifespan(_: FastAPI):
    config.session_secret()  # SESSION_SECRET 이 없으면 시작할 때 실패한다. (D-038)
    db.init_db()
    yield


app = FastAPI(title="Task Flow API", lifespan=lifespan)
app.include_router(tasks.router)
app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
