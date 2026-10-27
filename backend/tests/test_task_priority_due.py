"""우선순위 · 마감일 · 기한 초과 · 정렬을 확인한다. (R-009 ~ R-012, D-041, D-042)"""
import unittest
from datetime import date, timedelta

from fastapi.testclient import TestClient

from .helpers import get_app

PASSWORD = "Passw0rd!long-enough"
app = None


def setUpModule():
    global app
    app = get_app()


def day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


class PriorityDueTest(unittest.TestCase):
    count = 0

    def setUp(self):
        # 테스트마다 새 사용자로 시작해 서로 섞이지 않게 한다.
        PriorityDueTest.count += 1
        self.client = TestClient(app)
        self.client.__enter__()
        response = self.client.post(
            "/auth/register", json={"email": f"pd{self.count}@test.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 201, response.text)

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def create(self, title="카드", status=None, **extra):
        response = self.client.post("/tasks", json={"title": title, "description": "", **extra})
        self.assertEqual(response.status_code, 201, response.text)
        task = response.json()
        if status:
            task = self.client.patch(f"/tasks/{task['id']}/status", json={"status": status}).json()
        return task

    def edit(self, task, **body):
        return self.client.patch(
            f"/tasks/{task['id']}", json={"title": task["title"], "description": task["description"], **body}
        )

    # ---- 등록 (R-009, R-010)

    def test_create_without_new_fields_uses_defaults(self):
        task = self.create()  # 새 필드 없이 보내는 기존 등록
        self.assertEqual((task["priority"], task["due_date"], task["is_overdue"]), ("NORMAL", None, False))

    def test_create_with_priority_and_due_date(self):
        task = self.create(priority="HIGH", due_date="2030-01-31")
        self.assertEqual((task["priority"], task["due_date"]), ("HIGH", "2030-01-31"))
        listed = self.client.get("/tasks").json()[0]
        self.assertEqual((listed["priority"], listed["due_date"]), ("HIGH", "2030-01-31"))

    def test_past_due_date_is_allowed(self):
        task = self.create(due_date=day(-10))
        self.assertEqual(task["due_date"], day(-10))

    def test_invalid_values_are_rejected_with_422(self):
        def post(**extra):
            return self.client.post("/tasks", json={"title": "x", "description": "", **extra}).status_code

        self.assertEqual(post(priority="URGENT"), 422)
        self.assertEqual(post(priority="high"), 422)
        self.assertEqual(post(priority=None), 422)  # 등록에서도 null 은 거절한다. (D-042)
        for bad in ("내일", "2026/10/20", "2026-13-01", "2026-02-30", "20261020", "2026-10-20T00:00:00", 20261020):
            self.assertEqual(post(due_date=bad), 422, bad)
        self.assertEqual(self.client.get("/tasks").json(), [])  # 거절한 값은 저장되지 않는다

    # ---- 수정 (생략 · 비움 구분, 회귀)

    def test_edit_without_new_fields_keeps_priority_and_due_date(self):
        task = self.create(priority="HIGH", due_date="2030-01-31")
        edited = self.client.patch(f"/tasks/{task['id']}", json={"title": "제목만 수정", "description": "설명"})
        self.assertEqual(edited.status_code, 200)
        body = edited.json()
        self.assertEqual((body["title"], body["priority"], body["due_date"]), ("제목만 수정", "HIGH", "2030-01-31"))

    def test_edit_can_change_and_clear_due_date(self):
        task = self.create(due_date="2030-01-31")
        self.assertEqual(self.edit(task, due_date="2031-02-01").json()["due_date"], "2031-02-01")
        cleared = self.edit(task, due_date=None)
        self.assertEqual(cleared.status_code, 200)
        self.assertIsNone(cleared.json()["due_date"])

    def test_edit_can_change_priority_but_not_clear_it(self):
        task = self.create(priority="LOW")
        self.assertEqual(self.edit(task, priority="HIGH").json()["priority"], "HIGH")
        self.assertEqual(self.edit(task, priority=None).status_code, 422)
        self.assertEqual(self.edit(task, priority="URGENT").status_code, 422)
        self.assertEqual(self.client.get("/tasks").json()[0]["priority"], "HIGH")

    def test_edit_with_bad_date_changes_nothing(self):
        task = self.create(priority="HIGH", due_date="2030-01-31")
        self.assertEqual(self.edit(task, title="바꿈", due_date="내일").status_code, 422)
        saved = self.client.get("/tasks").json()[0]
        self.assertEqual((saved["title"], saved["due_date"]), ("카드", "2030-01-31"))

    def test_status_change_does_not_touch_priority_or_due_date(self):
        task = self.create(priority="HIGH", due_date=day(-1))
        changed = self.client.patch(f"/tasks/{task['id']}/status", json={"status": "DONE"}).json()
        self.assertEqual((changed["priority"], changed["due_date"]), ("HIGH", day(-1)))
        self.assertEqual(changed["is_overdue"], False)  # 완료하면 기한 초과가 아니다
        back = self.client.patch(f"/tasks/{task['id']}/status", json={"status": "TODO"}).json()
        self.assertEqual((back["priority"], back["due_date"], back["is_overdue"]), ("HIGH", day(-1), True))

    # ---- 기한 초과 판정표 (R-011)

    def test_overdue_table(self):
        for due, expected in ((day(-1), True), (day(0), False), (day(1), False), (None, False)):
            for status in ("TODO", "IN_PROGRESS"):
                task = self.create(due_date=due, status=status)
                self.assertEqual(task["is_overdue"], expected, (due, status))
            done = self.create(due_date=due, status="DONE")
            self.assertFalse(done["is_overdue"], (due, "DONE"))

    def test_every_task_response_has_is_overdue(self):
        task = self.create(due_date=day(-3))
        self.assertTrue(task["is_overdue"])
        self.assertTrue(self.edit(task, title="x") .json()["is_overdue"])
        self.assertTrue(self.client.get("/tasks").json()[0]["is_overdue"])

    # ---- 정렬 (R-012)

    def test_list_is_sorted_by_overdue_priority_due_date_id(self):
        # IMPACT-ANALYSIS.md 8-2 의 예시 여덟 개. 만든 순서가 곧 ID 순서이다.
        rows = [
            ("보고서", "TODO", "HIGH", day(-2)),
            ("청구서", "IN_PROGRESS", "NORMAL", day(-5)),
            ("영수증 정리", "DONE", "NORMAL", day(-1)),
            ("회의 준비", "TODO", "HIGH", day(0)),
            ("아이디어 메모", "TODO", "NORMAL", None),
            ("발표 자료", "TODO", "HIGH", day(3)),
            ("책 반납", "IN_PROGRESS", "LOW", day(1)),
            ("장보기", "TODO", "HIGH", day(3)),
        ]
        for title, status, priority, due in rows:
            self.create(title, status, priority=priority, due_date=due)
        titles = [task["title"] for task in self.client.get("/tasks").json()]
        self.assertEqual(
            titles, ["보고서", "청구서", "회의 준비", "발표 자료", "장보기", "영수증 정리", "아이디어 메모", "책 반납"]
        )

    def test_earlier_due_date_first_and_no_due_date_last_within_same_priority(self):
        self.create("없음")
        self.create("늦음", due_date=day(9))
        self.create("이름", due_date=day(2))
        titles = [task["title"] for task in self.client.get("/tasks").json()]
        self.assertEqual(titles, ["이름", "늦음", "없음"])

    def test_overdue_task_comes_before_higher_priority_task(self):
        self.create("높음", priority="HIGH", due_date=day(5))
        self.create("기한 초과", priority="LOW", due_date=day(-1))
        titles = [task["title"] for task in self.client.get("/tasks").json()]
        self.assertEqual(titles, ["기한 초과", "높음"])

    def test_ties_fall_back_to_id(self):
        first = self.create("먼저")
        second = self.create("나중")
        self.assertEqual([t["id"] for t in self.client.get("/tasks").json()], [first["id"], second["id"]])

    # ---- 기존 응답 모양, 로그인 보호 (회귀)

    def test_existing_response_fields_are_unchanged(self):
        task = self.create("기존", description="설명")
        for key in ("id", "title", "description", "status", "created_at", "updated_at"):
            self.assertIn(key, task)
        self.assertEqual((task["title"], task["description"], task["status"]), ("기존", "설명", "TODO"))
        self.assertEqual(task["created_at"], task["updated_at"])

    def test_new_fields_keep_login_and_owner_rules(self):
        other = TestClient(app)
        other.__enter__()
        try:
            other.post("/auth/register", json={"email": f"pdo{self.count}@test.com", "password": PASSWORD})
            task = self.create(priority="HIGH", due_date="2030-01-31")
            body = {"title": "x", "description": "", "priority": "LOW", "due_date": None}
            self.assertEqual(other.patch(f"/tasks/{task['id']}", json=body).status_code, 404)
            self.assertEqual(other.get("/tasks").json(), [])
            saved = self.client.get("/tasks").json()[0]
            self.assertEqual((saved["priority"], saved["due_date"]), ("HIGH", "2030-01-31"))
        finally:
            other.__exit__(None, None, None)
        anonymous = TestClient(app)
        self.assertEqual(
            anonymous.post("/tasks", json={"title": "x", "description": "", "priority": "HIGH"}).status_code, 401
        )
        self.assertEqual(anonymous.patch("/tasks/1", json={"title": "x", "description": "", "due_date": None}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
