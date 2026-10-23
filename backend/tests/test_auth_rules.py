"""가입 · 로그인 입력 규칙, 비밀번호와 세션의 저장 방식, 입력 검사를 확인한다. (D-033 ~ D-038)"""
import os
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from .helpers import get_app

PASSWORD = "Passw0rd!long-enough"
DB = os.environ["TASKFLOW_DB"]
app = None


def setUpModule():
    global app
    app = get_app()


def query(sql, *args):
    conn = sqlite3.connect(DB)
    rows = conn.execute(sql, args).fetchall()
    conn.commit()
    conn.close()
    return rows


class AuthRulesTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def register(self, email, password=PASSWORD):
        return self.client.post("/auth/register", json={"email": email, "password": password})

    def test_email_is_trimmed_and_lowercased_and_duplicates_ignore_case(self):
        first = self.register("  Rule-Case@Test.COM ")
        self.assertEqual((first.status_code, first.json()["email"]), (201, "rule-case@test.com"))
        other = TestClient(app)
        again = other.post("/auth/register", json={"email": "RULE-CASE@test.com", "password": PASSWORD})
        self.assertEqual(again.status_code, 409)

    def test_bad_email_is_rejected(self):
        for email in ("plain", "a@b", "a b@test.com", "@test.com", ""):
            with self.subTest(email=email):
                self.assertEqual(self.register(email).status_code, 422)

    def test_password_length_limits(self):
        self.assertEqual(self.register("len7@test.com", "a" * 7).status_code, 422)
        self.assertEqual(self.register("len129@test.com", "a" * 129).status_code, 422)
        self.assertEqual(self.register("len8@test.com", "a" * 8).status_code, 201)

    def test_response_has_only_id_and_email(self):
        body = self.register("shape@test.com").json()
        self.assertEqual(set(body), {"id", "email"})

    def test_password_is_stored_only_as_argon2_hash(self):
        self.register("hash@test.com")
        (stored,) = query("SELECT password_hash FROM users WHERE email = ?", "hash@test.com")[0]
        self.assertTrue(stored.startswith("$argon2"))
        self.assertNotIn(PASSWORD, stored)

    def test_cookie_flags_and_token_is_not_stored_as_is(self):
        response = self.register("cookie@test.com")
        header = response.headers["set-cookie"].lower()
        self.assertIn("httponly", header)
        self.assertIn("max-age=1800", header)
        self.assertIn("samesite=lax", header)
        token = self.client.cookies.get("session")
        stored = [row[0] for row in query("SELECT token_hash FROM sessions")]
        self.assertNotIn(token, stored)

    def test_expired_session_is_401(self):
        self.register("expire@test.com")
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
        query("UPDATE sessions SET expires_at = ? WHERE user_id = (SELECT id FROM users WHERE email = ?)", past, "expire@test.com")
        self.assertEqual(self.client.get("/tasks").status_code, 401)

    def test_session_is_extended_by_activity(self):
        self.register("slide@test.com")
        soon = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(timespec="seconds")
        sql = "SELECT expires_at FROM sessions WHERE user_id = (SELECT id FROM users WHERE email = ?)"
        query("UPDATE sessions SET expires_at = ? WHERE user_id = (SELECT id FROM users WHERE email = ?)", soon, "slide@test.com")
        self.assertEqual(self.client.get("/tasks").status_code, 200)
        (new_expiry,) = query(sql, "slide@test.com")[0]
        self.assertGreater(datetime.fromisoformat(new_expiry), datetime.now(timezone.utc) + timedelta(minutes=20))

    def test_task_input_rules(self):
        self.register("input@test.com")
        for title in ("", "   "):
            with self.subTest(title=title):
                self.assertEqual(self.client.post("/tasks", json={"title": title, "description": ""}).status_code, 422)
        task = self.client.post("/tasks", json={"title": "  앞뒤 공백  ", "description": "  설명  "}).json()
        self.assertEqual((task["title"], task["description"]), ("앞뒤 공백", "  설명  "))
        self.assertEqual(self.client.patch(f"/tasks/{task['id']}/status", json={"status": "ARCHIVED"}).status_code, 422)
        self.assertEqual(self.client.patch("/tasks/999999/status", json={"status": "DONE"}).status_code, 404)
        self.assertEqual(self.client.delete("/tasks/999999").status_code, 404)

    def test_same_status_is_success(self):
        self.register("same@test.com")
        task = self.client.post("/tasks", json={"title": "같은 상태", "description": ""}).json()
        self.assertEqual(self.client.patch(f"/tasks/{task['id']}/status", json={"status": "TODO"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
