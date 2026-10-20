from typing import Literal

from pydantic import BaseModel, field_validator

Status = Literal["TODO", "IN_PROGRESS", "DONE"]


class TaskCreate(BaseModel):
    title: str
    description: str = ""

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        # 공백만 있는 제목은 비어 있는 제목이다. (D-012, D-013)
        value = value.strip()
        if not value:
            raise ValueError("제목은 비워 둘 수 없습니다")
        return value


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    created_at: str
    updated_at: str


class StatusUpdate(BaseModel):
    status: Status
