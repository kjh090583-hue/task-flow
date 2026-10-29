"""로그인 없이는 401, 남의 Task 는 404 인지 확인한다. (D-033)"""
import unittest

from fastapi.testclient import TestClient

from .helpers import get_app

PASSWORD = "Passw0rd!long-enough"
app = None


def setUpModule():
    # 이전 전 모양의 DB 를 실제와 같은 방법(alembic)으로 이전한 앱을 받는다.
    global app
    app = get_app()


class TaskProtectionTest(unittest.TestCase):
    def setUp(self):
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.__exit__(None, None, None)

    def new_client(self, email=None):
        client = TestClient(app)
        client.__enter__()
        self.clients.append(client)
        if email:
            response = client.post("/auth/register", json={"email": email, "password": PASSWORD})
            self.assertEqual(response.status_code, 201, response.text)
        return client

    def test_every_task_request_needs_login(self):
        anonymous = self.new_client()
        self.assertEqual(anonymous.get("/tasks").status_code, 401)
        self.assertEqual(anonymous.post("/tasks", json={"title": "x", "description": ""}).status_code, 401)
        self.assertEqual(anonymous.patch("/tasks/1", json={"title": "x", "description": ""}).status_code, 401)
        self.assertEqual(anonymous.patch("/tasks/1/status", json={"status": "DONE"}).status_code, 401)
        self.assertEqual(anonymous.delete("/tasks/1").status_code, 401)
        self.assertEqual(anonymous.get("/auth/me").status_code, 401)

    # /tasks 아래의 모든 주소. 새 주소를 만들면 이 목록에 한 줄을 더해야 하고, 그러면 아래 두 시험이 그 주소의 로그인 보호도 확인한다.
    TASK_ADDRESSES = {
        ("GET", "/tasks"),
        ("POST", "/tasks"),
        ("POST", "/tasks/suggest"),
        ("POST", "/tasks/briefing"),
        ("POST", "/tasks/weekplan"),
        ("PATCH", "/tasks/{task_id}/status"),
        ("PATCH", "/tasks/{task_id}"),
        ("DELETE", "/tasks/{task_id}"),
    }

    def test_task_address_list_is_complete(self):
        # 이 FastAPI 는 라우터를 겹쳐 담아 app.routes 로는 안 보여서, 문서(OpenAPI)의 주소 목록을 쓴다.
        actual = {
            (method.upper(), path)
            for path, methods in app.openapi()["paths"].items()
            if path.startswith("/tasks")
            for method in methods
        }
        self.assertEqual(actual, self.TASK_ADDRESSES)

    def test_every_task_address_needs_login(self):
        anonymous = self.new_client()
        for method, path in sorted(self.TASK_ADDRESSES):
            response = anonymous.request(method, path.replace("{task_id}", "1"))
            self.assertEqual(response.status_code, 401, f"{method} {path}")

    def test_other_users_task_is_404_and_unchanged(self):
        a = self.new_client("iso-a@test.com")
        b = self.new_client("iso-b@test.com")
        task = b.post("/tasks", json={"title": "B 의 카드", "description": "비공개"}).json()
        self.assertEqual(a.get("/tasks").json(), [])
        self.assertEqual(a.patch(f"/tasks/{task['id']}", json={"title": "바꿔 보기", "description": ""}).status_code, 404)
        self.assertEqual(a.patch(f"/tasks/{task['id']}/status", json={"status": "DONE"}).status_code, 404)
        self.assertEqual(a.delete(f"/tasks/{task['id']}").status_code, 404)
        mine = b.get("/tasks").json()
        self.assertEqual((mine[0]["title"], mine[0]["status"]), ("B 의 카드", "TODO"))

    def test_new_task_belongs_to_the_logged_in_user_even_if_body_names_another_owner(self):
        a = self.new_client("own-a@test.com")
        b = self.new_client("own-b@test.com")
        a.post("/tasks", json={"title": "A 의 카드", "description": "", "owner_id": 1})
        self.assertEqual([t["title"] for t in a.get("/tasks").json()], ["A 의 카드"])
        self.assertEqual(b.get("/tasks").json(), [])

    def test_logout_ends_access(self):
        c = self.new_client("out@test.com")
        self.assertEqual(c.get("/tasks").status_code, 200)
        self.assertEqual(c.post("/auth/logout").status_code, 204)
        self.assertEqual(c.get("/tasks").status_code, 401)

    def test_login_failures_look_the_same(self):
        self.new_client("fail@test.com")
        anonymous = self.new_client()
        wrong = anonymous.post("/auth/login", json={"email": "fail@test.com", "password": "x" * 12})
        unknown = anonymous.post("/auth/login", json={"email": "nobody@test.com", "password": "x" * 12})
        self.assertEqual((wrong.status_code, unknown.status_code), (401, 401))
        self.assertEqual(wrong.json(), unknown.json())

    def test_first_signup_with_migrated_email_gets_old_tasks_once(self):
        anonymous = self.new_client()
        before = anonymous.post("/auth/login", json={"email": "migrated@test.com", "password": PASSWORD})
        self.assertEqual(before.status_code, 401)
        claimed = self.new_client("migrated@test.com")
        self.assertEqual([t["title"] for t in claimed.get("/tasks").json()], ["옛 카드 1", "옛 카드 2"])
        again = self.new_client().post("/auth/register", json={"email": "migrated@test.com", "password": PASSWORD})
        self.assertEqual(again.status_code, 409)

    def test_create_change_delete_scenario(self):
        c = self.new_client("flow@test.com")
        task = c.post("/tasks", json={"title": "시나리오", "description": ""}).json()
        self.assertEqual(task["status"], "TODO")
        changed = c.patch(f"/tasks/{task['id']}/status", json={"status": "IN_PROGRESS"}).json()
        self.assertEqual(changed["status"], "IN_PROGRESS")
        self.assertEqual(c.delete(f"/tasks/{task['id']}").status_code, 204)
        self.assertEqual(c.get("/tasks").json(), [])


if __name__ == "__main__":
    unittest.main()
