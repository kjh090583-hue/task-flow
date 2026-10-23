"""마이그레이션이 Task 를 잃거나 바꾸지 않는지 확인한다. (D-036, D-037)"""
import os
import sqlite3
import unittest

from . import TMP_DIR
from .helpers import SAMPLE, alembic, content, make_old_db

MIGRATED = "migrated@test.com"


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(TMP_DIR, f"{self._testMethodName}.db")
        make_old_db(self.path)
        self.before = content(self.path)

    def query(self, sql, *args):
        conn = sqlite3.connect(self.path)
        rows = conn.execute(sql, args).fetchall()
        conn.close()
        return rows

    def test_count_status_and_content_are_kept(self):
        alembic(self.path, "upgrade", "head")
        self.assertEqual(len(self.before), len(SAMPLE))
        self.assertEqual(content(self.path), self.before)
        statuses = dict(self.query("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
        self.assertEqual(statuses, {"TODO": 1, "IN_PROGRESS": 1, "DONE": 1})

    def test_every_task_goes_to_the_migrated_account(self):
        alembic(self.path, "upgrade", "head")
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL"), [(0,)])
        owners = self.query("SELECT DISTINCT u.email FROM tasks t JOIN users u ON u.id = t.owner_id")
        self.assertEqual(owners, [(MIGRATED,)])

    def test_migrated_account_has_no_password_yet(self):
        alembic(self.path, "upgrade", "head")
        self.assertEqual(self.query("SELECT password_hash FROM users WHERE email = ?", MIGRATED), [(None,)])

    def test_deleted_task_id_is_not_reused(self):
        conn = sqlite3.connect(self.path)
        conn.execute("DELETE FROM tasks WHERE id = 3")
        conn.commit()
        conn.close()
        alembic(self.path, "upgrade", "head")
        conn = sqlite3.connect(self.path)
        conn.execute(
            "INSERT INTO tasks (title, description, status, created_at, updated_at, owner_id) "
            "VALUES ('새', '', 'TODO', 'x', 'x', 1)"
        )
        conn.commit()
        new_id = conn.execute("SELECT MAX(id) FROM tasks").fetchone()[0]
        conn.close()
        self.assertEqual(new_id, 4)

    def test_downgrade_restores_the_same_content(self):
        alembic(self.path, "upgrade", "head")
        alembic(self.path, "downgrade", "base")
        self.assertEqual(content(self.path), self.before)

    def test_empty_database_migrates(self):
        empty = os.path.join(TMP_DIR, "empty.db")
        alembic(empty, "upgrade", "head")
        conn = sqlite3.connect(empty)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        conn.close()
        self.assertTrue({"tasks", "users", "sessions"} <= tables)


if __name__ == "__main__":
    unittest.main()
