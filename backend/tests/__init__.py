"""테스트는 임시 스키마와 임시 폴더만 쓴다. 실제 데이터는 건드리지 않는다. (D-050)

app 을 가져오기 전에 환경 변수를 정해야 하므로 이 파일에서 먼저 정한다.
접속 주소는 TEST_DATABASE_URL, 없으면 DATABASE_URL(환경 변수 또는 backend/.env)이다.
실행할 때마다 임시 스키마(tf_test_...)를 만들어 supabase/schema.sql 을 적용하고, 끝나면 지운다.
실행: backend 폴더에서 `uv run python -m unittest discover -s tests -t .`
"""
import atexit
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import psycopg
from psycopg.conninfo import make_conninfo

from app import config  # backend/.env 를 환경 변수로 읽어 들인다.

TMP_DIR = tempfile.mkdtemp(prefix="taskflow-test-")
# 예전 SQLite 파일. 옛 DB 를 마이그레이션하는 시험(test_migration)만 쓴다.
os.environ["TASKFLOW_DB"] = os.path.join(TMP_DIR, "api.db")
os.environ["SESSION_SECRET"] = "test-secret-not-for-real-use"
atexit.register(shutil.rmtree, TMP_DIR, ignore_errors=True)

_SCHEMA_SQL = Path(__file__).resolve().parent.parent / "supabase" / "schema.sql"


def _setup_test_schema() -> None:
    base = os.environ.get("TEST_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if not base:
        raise RuntimeError(
            "시험용 DB 주소가 없습니다. backend/.env 나 환경 변수에 TEST_DATABASE_URL(또는 DATABASE_URL)을 넣으세요."
        )
    schema = f"tf_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(base, autocommit=True) as conn:
        conn.execute(f"CREATE SCHEMA {schema}")

    def drop_schema() -> None:
        try:
            with psycopg.connect(base, autocommit=True) as conn:
                conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        except psycopg.Error:
            pass

    atexit.register(drop_schema)
    scoped = make_conninfo(base, options=f"-c search_path={schema}")
    with psycopg.connect(scoped, autocommit=True) as conn:
        conn.execute(_SCHEMA_SQL.read_text(encoding="utf-8"))
    os.environ["DATABASE_URL"] = scoped


_setup_test_schema()
