import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("TASKFLOW_DB", Path(__file__).resolve().parent.parent / "taskflow.db"))

# 이전용 계정. 기존 Task 의 주인이고, 이 이메일로 처음 가입하는 사람이 인수한다. (D-037)
MIGRATED_EMAIL = "migrated@test.com"

# 허용 상태 목록은 여기 한 곳에서만 정의한다. (D-003)
STATUSES = ("TODO", "IN_PROGRESS", "DONE")

# 허용 우선순위 목록도 여기 한 곳에서만 정의한다. 기본값은 NORMAL 이다. (D-003, D-041)
PRIORITIES = ("LOW", "NORMAL", "HIGH")


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
        task_columns = (
            {col["name"] for col in conn.execute("PRAGMA table_info(tasks)")} if "tasks" in tables else set()
        )
    # owner_id(D-036)와 priority · due_date(D-041)가 있어야 마이그레이션한 DB 이다.
    if not {"tasks", "users", "sessions"} <= tables or not {"owner_id", "priority", "due_date"} <= task_columns:
        raise RuntimeError(
            "DB 가 아직 마이그레이션되지 않았습니다. backend 폴더에서 `uv run alembic upgrade head` 를 실행하세요."
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Task 는 모두 owner_id(로그인한 사용자)로 한정한다. 남의 Task 는 없는 것과 같다. (D-033)


def _today() -> str:
    # 기한 초과를 가르는 "오늘"은 서버 컴퓨터의 로컬 날짜이다. (D-042)
    return date.today().isoformat()


def _is_date(text: str) -> bool:
    try:
        return len(text) == 10 and date.fromisoformat(text).isoformat() == text
    except ValueError:
        return False


def _to_task(row: sqlite3.Row, today: str) -> dict:
    # 기한 초과는 저장하지 않고 응답할 때 계산한다: 마감일이 오늘보다 이전이고 완료가 아니다. (R-011, D-042)
    task = dict(row)
    # API 를 거치지 않고 DB 에 들어간 규칙 밖 우선순위는 보통으로 보고, 목록 전체가 깨지지 않게 한다. (D-048)
    if task["priority"] not in PRIORITIES:
        task["priority"] = "NORMAL"
    # 마감일도 같다. 실제 YYYY-MM-DD 날짜가 아닌 값은 마감일 없음으로 본다. 글자 비교로 가짜 기한 초과가 되는 것을 막는다. (D-048)
    if task["due_date"] is not None and not _is_date(task["due_date"]):
        task["due_date"] = None
    due = task["due_date"]
    task["is_overdue"] = due is not None and due < today and task["status"] != "DONE"
    return task


def _sort_key(task: dict) -> tuple:
    # 기한 초과 → 우선순위(HIGH 먼저) → 마감일 빠른 순(없으면 맨 뒤) → ID. (R-012, D-042)
    due = task["due_date"]
    return (
        not task["is_overdue"],
        PRIORITIES.index(task["priority"]) * -1,
        due is None,
        due or "",
        task["id"],
    )


def list_tasks(owner_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE owner_id = ?", (owner_id,)).fetchall()
    today = _today()
    return sorted((_to_task(row, today) for row in rows), key=_sort_key)


def create_task(title: str, description: str, owner_id: int, priority: str = "NORMAL", due_date: str | None = None) -> dict:
    now = _now()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at, owner_id) "
            "VALUES (?, ?, 'TODO', ?, ?, ?, ?, ?)",
            (title, description, priority, due_date, now, now, owner_id),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _to_task(row, _today())


def update_status(task_id: int, status: str, owner_id: int) -> dict | None:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
            (status, _now(), task_id, owner_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _to_task(row, _today())


def update_task(task_id: int, title: str, description: str, owner_id: int, extra: dict | None = None) -> dict | None:
    # extra 에는 요청에서 보낸 priority · due_date 만 들어 있다. 보내지 않은 값은 그대로 둔다. (D-041)
    extra = {key: value for key, value in (extra or {}).items() if key in ("priority", "due_date")}
    assignments = "".join(f", {key} = ?" for key in extra)
    with _connect() as conn:
        cursor = conn.execute(
            f"UPDATE tasks SET title = ?, description = ?, updated_at = ?{assignments} WHERE id = ? AND owner_id = ?",
            (title, description, _now(), *extra.values(), task_id, owner_id),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _to_task(row, _today())


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
