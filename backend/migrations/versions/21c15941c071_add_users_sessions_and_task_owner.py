"""add users sessions and task owner

users · sessions 표를 만들고 tasks 에 owner_id(외래 키, NOT NULL)를 더한다. (D-036, D-037)
기존 Task 는 모두 이전용 계정 migrated@test.com 의 것이 된다. 이 계정은 처음에 비밀번호 해시가 없어 로그인할 수 없다.

SQLite 는 NOT NULL 외래 키 컬럼을 기존 표에 바로 더할 수 없어서, 새 표를 만들어 옮긴 뒤 바꾼다.
SQLite 의 DDL 은 한 번에 되돌려지지 않을 수 있으므로 적용 전에 DB 파일을 백업하고 복사본에서 먼저 확인한다.

Revision ID: 21c15941c071
Revises:
Create Date: 2026-10-23 09:13:00.593957

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21c15941c071'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MIGRATED_EMAIL = "migrated@test.com"

# app/db.py 의 현재 스키마와 같다. 아직 표가 없는 새 DB 에서도 이 마이그레이션이 돌아가게 한다.
_TASKS_OLD = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_USERS = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    created_at TEXT NOT NULL
)
"""

_SESSIONS = """
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

_TASKS_NEW = """
CREATE TABLE tasks_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id)
)
"""

_TASKS_PREVIOUS = _TASKS_OLD.replace("IF NOT EXISTS tasks", "tasks_previous")


def _keep_autoincrement(old: str, new: str) -> None:
    # AUTOINCREMENT 의 가장 큰 번호를 이어 받아 지운 카드의 id 가 다시 쓰이지 않게 한다.
    op.execute(sa.text("DELETE FROM sqlite_sequence WHERE name = :new").bindparams(new=new))
    op.execute(
        sa.text("INSERT INTO sqlite_sequence (name, seq) SELECT :new, seq FROM sqlite_sequence WHERE name = :old")
        .bindparams(new=new, old=old)
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(_TASKS_OLD)
    op.execute(_USERS)
    op.execute(_SESSIONS)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    op.execute(
        sa.text("INSERT INTO users (email, password_hash, created_at) VALUES (:email, NULL, :now)")
        .bindparams(email=MIGRATED_EMAIL, now=now)
    )

    op.execute(_TASKS_NEW)
    op.execute(
        sa.text(
            "INSERT INTO tasks_new (id, title, description, status, created_at, updated_at, owner_id) "
            "SELECT id, title, description, status, created_at, updated_at, "
            "(SELECT id FROM users WHERE email = :email) FROM tasks"
        ).bindparams(email=MIGRATED_EMAIL)
    )
    _keep_autoincrement("tasks", "tasks_new")
    op.execute("DROP TABLE tasks")
    op.execute("ALTER TABLE tasks_new RENAME TO tasks")
    op.execute("CREATE INDEX ix_tasks_owner_id ON tasks (owner_id)")


def downgrade() -> None:
    """Downgrade schema. 주인 정보와 users · sessions 는 사라진다."""
    op.execute("DROP INDEX IF EXISTS ix_tasks_owner_id")
    op.execute(_TASKS_PREVIOUS)
    op.execute(
        "INSERT INTO tasks_previous (id, title, description, status, created_at, updated_at) "
        "SELECT id, title, description, status, created_at, updated_at FROM tasks"
    )
    _keep_autoincrement("tasks", "tasks_previous")
    op.execute("DROP TABLE tasks")
    op.execute("ALTER TABLE tasks_previous RENAME TO tasks")
    op.execute("DROP TABLE sessions")
    op.execute("DROP TABLE users")
