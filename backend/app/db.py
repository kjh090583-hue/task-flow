import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("TASKFLOW_DB", Path(__file__).resolve().parent.parent / "taskflow.db"))

# 이전용 계정. 기존 Task 의 주인이고, 로그인이 생기기 전까지 새 카드의 주인이기도 하다. (D-037)
MIGRATED_EMAIL = "migrated@test.com"

# 허용 상태 목록은 여기 한 곳에서만 정의한다. (D-003)
STATUSES = ("TODO", "IN_PROGRESS", "DONE")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


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
    with _connect() as conn:
        conn.execute(_SCHEMA)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_tasks() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def create_task(title: str, description: str) -> dict:
    now = _now()
    with _connect() as conn:
        has_owner = any(col["name"] == "owner_id" for col in conn.execute("PRAGMA table_info(tasks)"))
        if has_owner:
            # 임시: 로그인(단위 2 ~ 3)이 생기기 전까지 새 카드의 주인은 이전용 계정이다. (D-036, D-037)
            # owner_id 는 NOT NULL 이므로 주인 없이 만들 수 없다. 단위 3 에서 로그인한 사용자로 바꾼다.
            owner = conn.execute("SELECT id FROM users WHERE email = ?", (MIGRATED_EMAIL,)).fetchone()
            if owner is None:
                raise sqlite3.IntegrityError("이전용 계정이 없다")
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, status, created_at, updated_at, owner_id) "
                "VALUES (?, ?, 'TODO', ?, ?, ?)",
                (title, description, now, now, owner["id"]),
            )
        else:
            # 아직 마이그레이션하지 않은 DB: 이전과 같이 동작한다.
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, status, created_at, updated_at) "
                "VALUES (?, ?, 'TODO', ?, ?)",
                (title, description, now, now),
            )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def update_status(task_id: int, status: str) -> dict | None:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), task_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


def update_task(task_id: int, title: str, description: str) -> dict | None:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET title = ?, description = ?, updated_at = ? WHERE id = ?",
            (title, description, _now(), task_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


def delete_task(task_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
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
