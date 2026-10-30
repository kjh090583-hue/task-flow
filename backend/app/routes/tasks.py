import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from .. import auth, briefing, command, db, suggest
from ..schemas import (
    Briefing,
    CommandRequest,
    CommandResult,
    StatusUpdate,
    SuggestRequest,
    Suggestion,
    Task,
    TaskCreate,
)

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
        return db.create_task(body.title, body.description, user["id"], body.priority, body.due_date)
    except sqlite3.Error:
        raise _storage_error()


@router.post("/suggest", response_model=Suggestion)
def suggest_task(body: SuggestRequest):
    # 제안만 돌려준다. DB 는 열지 않는다. (D-044)
    try:
        return suggest.suggest_task(body.title, body.description, date.today())
    except suggest.SuggestUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))
    except suggest.SuggestFailed:
        raise HTTPException(status_code=502, detail="제안 실패")


@router.post("/briefing", response_model=Briefing)
def briefing_today(user: dict = Depends(auth.current_user)):
    # 로그인한 사람의 완료 아닌 Task 로 브리핑만 돌려준다. DB 는 읽기만 한다. (D-046)
    try:
        tasks = db.list_tasks(user["id"])
    except sqlite3.Error:
        raise _storage_error()
    try:
        return briefing.make_briefing(tasks, date.today())
    except briefing.BriefingUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))
    except briefing.BriefingFailed:
        raise HTTPException(status_code=502, detail="브리핑 실패")


@router.post("/command", response_model=CommandResult)
def command_text(body: CommandRequest, user: dict = Depends(auth.current_user)):
    # 로그인한 사람의 완료 아닌 Task 와 한 문장으로 제안만 돌려준다. DB 는 읽기만 한다. (D-049)
    try:
        tasks = db.list_tasks(user["id"])
    except sqlite3.Error:
        raise _storage_error()
    try:
        return command.make_command(tasks, body.text, date.today())
    except briefing.BriefingUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))
    except briefing.BriefingFailed:
        raise HTTPException(status_code=502, detail="명령 실패")


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
    # priority · due_date 는 요청에 있는 것만 바꾼다. due_date 가 null 이면 마감일을 지운다. (D-041)
    sent = {key: getattr(body, key) for key in ("priority", "due_date") if key in body.model_fields_set}
    try:
        task = db.update_task(task_id, body.title, body.description, user["id"], sent)
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
