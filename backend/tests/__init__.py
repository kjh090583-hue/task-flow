"""테스트는 임시 폴더의 DB 만 쓴다. 실제 taskflow.db 는 건드리지 않는다.

app 을 가져오기 전에 환경 변수를 정해야 하므로 이 파일에서 먼저 정한다.
실행: backend 폴더에서 `uv run python -m unittest discover -s tests -t .`
"""
import atexit
import os
import shutil
import tempfile

TMP_DIR = tempfile.mkdtemp(prefix="taskflow-test-")
os.environ["TASKFLOW_DB"] = os.path.join(TMP_DIR, "api.db")
os.environ["SESSION_SECRET"] = "test-secret-not-for-real-use"
atexit.register(shutil.rmtree, TMP_DIR, ignore_errors=True)
