"""add task priority and due date

tasks 에 priority(기본 NORMAL)와 due_date(비울 수 있음)를 더한다. (D-041)
표를 다시 만들지 않고 컬럼만 더하므로 id · AUTOINCREMENT · owner_id · 인덱스는 그대로이고,
기존 Task 는 priority NORMAL, due_date 없음이 된다.

downgrade 는 만들지 않는다. 되돌리기는 적용 전에 만든 백업 파일로 한다. (D-041)

Revision ID: 7c4e1a9b3d52
Revises: 21c15941c071
Create Date: 2026-10-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7c4e1a9b3d52'
down_revision: Union[str, Sequence[str], None] = '21c15941c071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'NORMAL' "
        "CHECK (priority IN ('LOW', 'NORMAL', 'HIGH'))"
    )
    # 날짜만 저장한다(YYYY-MM-DD). 실제 날짜인지는 API 가 검사한다. 비어 있으면 NULL.
    op.execute(
        "ALTER TABLE tasks ADD COLUMN due_date TEXT "
        "CHECK (due_date IS NULL OR due_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')"
    )
