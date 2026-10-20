import sqlite3

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import StatusUpdate, Task, TaskCreate

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


@router.patch("/{task_id}/status", response_model=Task)
def update_status(task_id: int, body: StatusUpdate):
    try:
        task = db.update_status(task_id, body.status)
    except sqlite3.Error:
        raise _storage_error()
    if task is None:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskCreate):
    try:
        task = db.update_task(task_id, body.title, body.description)
    except sqlite3.Error:
        raise _storage_error()
    if task is None:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int):
    try:
        deleted = db.delete_task(task_id)
    except sqlite3.Error:
        raise _storage_error()
    if not deleted:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
