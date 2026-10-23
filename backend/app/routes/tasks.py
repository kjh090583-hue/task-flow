import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from .. import auth, db
from ..schemas import StatusUpdate, Task, TaskCreate

# 모든 Task 요청은 로그인이 필요하다. 로그인하지 않았으면 401. (D-033)
router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(auth.current_user)])


def _storage_error() -> HTTPException:
    return HTTPException(status_code=500, detail="저장소 오류")


@router.get("", response_model=list[Task])
def list_tasks(user: dict = Depends(auth.current_user)):
    try:
        return db.list_tasks(user["id"])
    except sqlite3.Error:
        raise _storage_error()


@router.post("", response_model=Task, status_code=201)
def create_task(body: TaskCreate, user: dict = Depends(auth.current_user)):
    try:
        return db.create_task(body.title, body.description, user["id"])
    except sqlite3.Error:
        raise _storage_error()


@router.patch("/{task_id}/status", response_model=Task)
def update_status(task_id: int, body: StatusUpdate, user: dict = Depends(auth.current_user)):
    try:
        task = db.update_status(task_id, body.status, user["id"])
    except sqlite3.Error:
        raise _storage_error()
    if task is None:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskCreate, user: dict = Depends(auth.current_user)):
    try:
        task = db.update_task(task_id, body.title, body.description, user["id"])
    except sqlite3.Error:
        raise _storage_error()
    if task is None:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user: dict = Depends(auth.current_user)):
    try:
        deleted = db.delete_task(task_id, user["id"])
    except sqlite3.Error:
        raise _storage_error()
    if not deleted:
        raise HTTPException(status_code=404, detail="대상 카드가 없습니다")
