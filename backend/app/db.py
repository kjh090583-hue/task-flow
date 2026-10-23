import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("TASKFLOW_DB", Path(__file__).resolve().parent.parent / "taskflow.db"))

# 이전용 계정. 기존 Task 의 주인이고, 이 이메일로 처음 가입하는 사람이 인수한다. (D-037)
MIGRATED_EMAIL = "migrated@test.com"

# 허용 상태 목록은 여기 한 곳에서만 정의한다. (D-003)
STATUSES = ("TODO", "IN_PROGRESS", "DONE")


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # 연결마다 켜야 외래 키를 검사한다. (D-038)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    # 표는 alembic 이 만든다. 마이그레이션하지 않은 DB 면 시작할 때 실패해서 조용히 어긋나지 않게 한다. (D-031, D-036)
    with _connect() as conn:
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        has_owner = "tasks" in tables and any(
            col["name"] == "owner_id" for col in conn.execute("PRAGMA table_info(tasks)")
        )
    if not {"tasks", "users", "sessions"} <= tables or not has_owner:
        raise RuntimeError(
            "DB 가 아직 마이그레이션되지 않았습니다. backend 폴더에서 `uv run alembic upgrade head` 를 실행하세요."
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Task 는 모두 owner_id(로그인한 사용자)로 한정한다. 남의 Task 는 없는 것과 같다. (D-033)


def list_tasks(owner_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE owner_id = ? ORDER BY id", (owner_id,)).fetchall()
    return [dict(row) for row in rows]


def create_task(title: str, description: str, owner_id: int) -> dict:
    now = _now()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, status, created_at, updated_at, owner_id) "
            "VALUES (?, ?, 'TODO', ?, ?, ?)",
            (title, description, now, now, owner_id),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def update_status(task_id: int, status: str, owner_id: int) -> dict | None:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
            (status, _now(), task_id, owner_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


def update_task(task_id: int, title: str, description: str, owner_id: int) -> dict | None:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET title = ?, description = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
            (title, description, _now(), task_id, owner_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


def delete_task(task_id: int, owner_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ? AND owner_id = ?", (task_id, owner_id))
    return cursor.rowcount > 0


# ---- 사용자 · 세션 (D-036, D-038)


def get_user_by_email(email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def create_user(email: str, password_hash: str) -> dict:
    # 이미 있는 이메일이면 sqlite3.IntegrityError 가 난다.
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, _now()),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def claim_user(user_id: int, password_hash: str) -> bool:
    # 비밀번호가 아직 없는 계정에만 한 번 정해 줄 수 있다. 이미 정해졌으면 False.
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ? AND password_hash IS NULL",
            (password_hash, user_id),
        )
    return cursor.rowcount == 1


def create_session(user_id: int, token_hash: str, expires_at: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, token_hash, expires_at, _now()),
        )


def delete_expired_sessions() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (_now(),))


def get_session_user(token_hash: str) -> dict | None:
    # 만료된 세션이면 지우고 None 을 돌려준다.
    with _connect() as conn:
        row = conn.execute(
            "SELECT s.id AS session_id, s.expires_at, u.id, u.email "
            "FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] <= _now():
            conn.execute("DELETE FROM sessions WHERE id = ?", (row["session_id"],))
            return None
    return dict(row)


def extend_session(session_id: int, expires_at: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE sessions SET expires_at = ? WHERE id = ?", (expires_at, session_id))


def delete_session(session_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
