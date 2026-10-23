import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response

from .. import auth, db
from ..schemas import LoginRequest, RegisterRequest, User

router = APIRouter(prefix="/auth", tags=["auth"])

LOGIN_FAILED = "이메일 또는 비밀번호가 올바르지 않습니다"
ALREADY_REGISTERED = "이미 가입된 이메일입니다"


def _storage_error() -> HTTPException:
    return HTTPException(status_code=500, detail="저장소 오류")


@router.post("/register", response_model=User, status_code=201)
def register(body: RegisterRequest, response: Response):
    password_hash = auth.hash_password(body.password)
    try:
        existing = db.get_user_by_email(body.email)
        if existing is None:
            try:
                user = db.create_user(body.email, password_hash)
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=409, detail=ALREADY_REGISTERED)
        elif existing["email"] == db.MIGRATED_EMAIL and existing["password_hash"] is None:
            # 인수되지 않은 이전용 계정: 처음 가입하는 사람이 비밀번호를 정해 계정과 기존 Task 를 받는다. (D-037)
            if not db.claim_user(existing["id"], password_hash):
                raise HTTPException(status_code=409, detail=ALREADY_REGISTERED)
            user = existing
        else:
            raise HTTPException(status_code=409, detail=ALREADY_REGISTERED)
        auth.start_session(response, user["id"])
    except sqlite3.Error:
        raise _storage_error()
    return user


@router.post("/login", response_model=User)
def login(body: LoginRequest, response: Response):
    try:
        user = db.get_user_by_email(body.email)
        # 없는 이메일, 틀린 비밀번호, 인수되지 않은 이전용 계정을 같은 401 로 응답한다. (D-038)
        if user is None or user["password_hash"] is None:
            auth.verify_against_dummy(body.password)
            raise HTTPException(status_code=401, detail=LOGIN_FAILED)
        if not auth.verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail=LOGIN_FAILED)
        auth.start_session(response, user["id"])
    except sqlite3.Error:
        raise _storage_error()
    return user


@router.post("/logout", status_code=204)
def logout(response: Response, user: dict = Depends(auth.current_user)):
    try:
        db.delete_session(user["session_id"])
    except sqlite3.Error:
        raise _storage_error()
    auth.clear_cookie(response)


@router.get("/me", response_model=User)
def me(user: dict = Depends(auth.current_user)):
    return user
