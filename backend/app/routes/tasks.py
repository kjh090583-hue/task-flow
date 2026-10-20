import sqlite3

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import Task, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _storage_error() -> HTTPException:
    return HTTPException(status_code=500, detail="저장소 오류")


@router.get("", response_model=list[Task])
def list_tasks():
    try:
        return db.list_tasks()
    except sqlite3.Error:
        raise _storage_error()


@router.post("", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    try:
        return db.create_task(body.title, body.description)
    except sqlite3.Error:
        raise _storage_error()
