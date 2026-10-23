import os
import sqlite3
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

OLD_TASKS = """
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

# 이전 전(users 표도 owner_id 도 없는) DB 에 넣을 표본. 세 상태를 모두 쓴다.
SAMPLE = [
    ("장보기", "우유", "TODO"),
    ("보고서", "", "IN_PROGRESS"),
    ("청소", "방", "DONE"),
]


def make_old_db(path, rows=SAMPLE):
    conn = sqlite3.connect(path)
    conn.execute(OLD_TASKS)
    for title, description, status in rows:
        conn.execute(
            "INSERT INTO tasks (title, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (title, description, status, "2026-10-20T00:00:00+00:00", "2026-10-20T00:00:00+00:00"),
        )
    conn.commit()
    conn.close()


def alembic(db_path, *args):
    env = {**os.environ, "TASKFLOW_DB": db_path}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(f"alembic {' '.join(args)} 실패:\n{result.stdout}\n{result.stderr}")


def content(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, title, description, status, created_at, updated_at FROM tasks ORDER BY id"
    ).fetchall()
    conn.close()
    return rows
