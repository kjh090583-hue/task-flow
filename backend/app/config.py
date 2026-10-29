import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# 세션 쿠키 이름과 로그인 유지 시간. (D-034, D-038)
SESSION_COOKIE_NAME = "session"
SESSION_MINUTES = 30


def _load_env_file(path: Path) -> None:
    # 환경 변수가 이미 있으면 그대로 두고, 없는 값만 backend/.env 에서 채운다. 값은 출력하지 않는다. (D-035)
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(ENV_PATH)


def anthropic_api_key() -> str:
    # AI 제안용 키. 없으면 빈 문자열이고 제안 요청만 503 이다. 앞뒤 공백과 줄바꿈은 지운다. 값은 출력하지 않는다. (D-044)
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def session_secret() -> bytes:
    value = os.environ.get("SESSION_SECRET", "")
    if not value:
        raise RuntimeError("SESSION_SECRET 이 없습니다. backend/.env 를 확인하세요. (backend/.env.example 참고)")
    return value.encode("utf-8")
