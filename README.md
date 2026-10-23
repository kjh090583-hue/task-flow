# task-flow

개인용 Task 관리 웹 앱. 현재 M0(프로젝트 기본 구조)까지만 있다. Task 기능, 데이터베이스, 로그인은 아직 없다.

- `frontend/` — 화면 (React · Vite)
- `backend/` — API (FastAPI)

## 실행
처음 한 번, API 를 켜기 전에 `backend` 에서 설정 파일과 DB 를 준비한다.

```
cd backend
cp .env.example .env             # SESSION_SECRET 값을 채운다 (이 파일은 Git 에 올리지 않는다)
uv run alembic upgrade head      # DB 파일(backend/taskflow.db)과 표를 만든다
```

터미널 두 개에서 각각 실행한다.

```
cd backend
uv run fastapi dev app/main.py   # http://127.0.0.1:8000
```

```
cd frontend
npm install                      # 처음 한 번
npm run dev                      # http://localhost:5173
```

브라우저에서 http://localhost:5173 을 열면 "API 연결: 정상" 이 보인다. API 를 끄면 "연결할 수 없음" 으로 바뀐다.
화면은 `/api/...` 로 호출하고, Vite 개발 서버가 이를 API(8000 포트)로 전달한다. (`frontend/vite.config.js`)

## 테스트
임시 폴더의 DB 만 쓰므로 실제 `taskflow.db` 는 바뀌지 않는다. `backend` 에서 실행한다.

```
uv run python -m unittest discover -s tests -t .
```

마이그레이션(Task 수 · 상태 · 내용 · 주인 · 되돌리기)과 로그인 보호(401, 남의 Task 404)를 확인한다.
