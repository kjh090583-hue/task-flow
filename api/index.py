import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main import app as taskflow

# 화면(frontend/dist)과 API(/api)를 한 앱으로 묶는다. 붙인 앱의 lifespan 은 돌지 않아 여기서 이어 받는다. (D-051)
app = FastAPI(lifespan=taskflow.router.lifespan_context)
app.mount("/api", taskflow)
app.mount("/", StaticFiles(directory=ROOT / "frontend" / "dist", html=True))
