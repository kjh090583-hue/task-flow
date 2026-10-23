import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response
from pwdlib import PasswordHash

from . import config, db

# 비밀번호는 Argon2 권장 설정의 전용 해시로만 저장한다. (D-035)
_password_hash = PasswordHash.recommended()
_dummy_hash: str | None = None

NOT_LOGGED_IN = "로그인이 필요합니다"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:
        return False


def verify_against_dummy(password: str) -> None:
    # 없는 계정이어도 해시 비교와 비슷한 시간이 걸리게 해서, 계정이 있는지 응답 시간으로 알 수 없게 한다. (D-038)
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = _password_hash.hash("dummy-password")
    verify_password(password, _dummy_hash)


def _expires_at() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=config.SESSION_MINUTES)).isoformat(timespec="seconds")


def hash_token(token: str) -> str:
    # 쿠키의 토큰이 아니라 SESSION_SECRET 으로 HMAC 한 값을 저장한다. (D-038)
    return hmac.new(config.session_secret(), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _set_cookie(response: Response, token: str) -> None:
    # HttpOnly, SameSite=Lax, Max-Age 30분. Secure 는 로컬 http 에서 끈다. (D-034)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=token,
        max_age=config.SESSION_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(config.SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")


def start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    db.delete_expired_sessions()
    db.create_session(user_id, hash_token(token), _expires_at())
    _set_cookie(response, token)


def current_user(request: Request, response: Response) -> dict:
    """로그인한 사용자를 돌려준다. 로그인하지 않았으면 401. 요청이 올 때마다 30분을 다시 늘린다. (D-038)"""
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail=NOT_LOGGED_IN)
    try:
        user = db.get_session_user(hash_token(token))
        if user is None:
            raise HTTPException(status_code=401, detail=NOT_LOGGED_IN)
        db.extend_session(user["session_id"], _expires_at())
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="저장소 오류")
    _set_cookie(response, token)
    return user
