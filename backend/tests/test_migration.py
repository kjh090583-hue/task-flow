"""마이그레이션이 Task 를 잃거나 바꾸지 않는지 확인한다. (D-036, D-037)"""
import os
import shutil
import sqlite3
import unittest

from . import TMP_DIR
from .helpers import BACKEND, SAMPLE, alembic, content, make_old_db

MIGRATED = "migrated@test.com"
FIRST_REVISION = "21c15941c071"  # users · sessions · owner_id
NEW_REVISION = "7c4e1a9b3d52"  # priority · due_date
VERSIONS = os.path.join(BACKEND, "migrations", "versions")


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

    def test_existing_tasks_get_normal_priority_and_no_due_date(self):
        alembic(self.path, "upgrade", "head")
        self.assertEqual(self.query("SELECT DISTINCT priority FROM tasks"), [("NORMAL",)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM tasks WHERE due_date IS NOT NULL"), [(0,)])

    def test_two_step_upgrade_keeps_the_owner_step_result(self):
        # 로그인 도입 단계(21c15941c071)까지 올린 DB 에서 우선순위 · 마감일 단계로 올려도 값이 그대로이다. (D-041)
        alembic(self.path, "upgrade", FIRST_REVISION)
        owner_step = self.query("SELECT id, owner_id FROM tasks ORDER BY id")
        alembic(self.path, "upgrade", "head")
        self.assertEqual(content(self.path), self.before)
        self.assertEqual(self.query("SELECT id, owner_id FROM tasks ORDER BY id"), owner_step)
        self.assertEqual(self.query("SELECT COUNT(*) FROM users"), [(1,)])

    def test_upgrade_head_twice_changes_nothing(self):
        alembic(self.path, "upgrade", "head")
        after_first = self.query("SELECT * FROM tasks ORDER BY id")
        alembic(self.path, "upgrade", "head")
        self.assertEqual(self.query("SELECT * FROM tasks ORDER BY id"), after_first)

    def test_deleted_task_id_is_not_reused_after_the_new_step(self):
        alembic(self.path, "upgrade", FIRST_REVISION)
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

    def test_new_columns_reject_values_outside_the_rules(self):
        alembic(self.path, "upgrade", "head")
        conn = sqlite3.connect(self.path)
        insert = (
            "INSERT INTO tasks (title, description, status, created_at, updated_at, owner_id, priority, due_date) "
            "VALUES ('x', '', 'TODO', 'x', 'x', 1, ?, ?)"
        )
        conn.execute(insert, ("HIGH", "2026-10-20"))  # 지난 날짜도 저장된다
        conn.execute(insert, ("LOW", None))  # 마감일은 비울 수 있다
        for priority, due in (("URGENT", None), (None, None), ("NORMAL", "내일"), ("NORMAL", "2026/10/20")):
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(insert, (priority, due))
        conn.close()

    def test_new_step_has_no_downgrade(self):
        # 되돌리기는 백업 파일로 한다. 새 마이그레이션에는 downgrade 를 두지 않는다. (D-041)
        source = os.path.join(VERSIONS, [f for f in os.listdir(VERSIONS) if f.startswith(NEW_REVISION)][0])
        with open(source, encoding="utf-8") as file:
            self.assertNotIn("def downgrade", file.read())

    def test_backup_file_restores_the_state_before_upgrade(self):
        backup = os.path.join(TMP_DIR, "backup.db")
        shutil.copyfile(self.path, backup)
        alembic(self.path, "upgrade", "head")
        shutil.copyfile(backup, self.path)
        self.assertEqual(content(self.path), self.before)
        columns = {row[1] for row in self.query("PRAGMA table_info(tasks)")}
        self.assertNotIn("priority", columns)

    def test_empty_database_migrates(self):
        empty = os.path.join(TMP_DIR, "empty.db")
        alembic(empty, "upgrade", "head")
        conn = sqlite3.connect(empty)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        conn.close()
        self.assertTrue({"tasks", "users", "sessions"} <= tables)
        conn = sqlite3.connect(empty)
        columns = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
        conn.close()
        self.assertTrue({"owner_id", "priority", "due_date"} <= columns)


if __name__ == "__main__":
    unittest.main()
