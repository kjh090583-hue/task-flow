import re
from typing import Literal

from pydantic import BaseModel, field_validator

Status = Literal["TODO", "IN_PROGRESS", "DONE"]

# 이메일은 @ 앞뒤가 있고 점이 있는 도메인이면 된다. (D-038)
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_PATTERN.match(value):
            raise ValueError("이메일 형식이 올바르지 않습니다")
        return value

    @field_validator("password")
    @classmethod
    def password_length(cls, value: str) -> str:
        # 비밀번호는 8자 이상 128자 이하이다. 앞뒤 공백도 비밀번호의 일부라 지우지 않는다. (D-038)
        if not 8 <= len(value) <= 128:
            raise ValueError("비밀번호는 8자 이상 128자 이하여야 합니다")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_normalize(cls, value: str) -> str:
        return value.strip().lower()


class User(BaseModel):
    # 응답에는 id 와 email 만 담는다. 비밀번호 해시는 담지 않는다. (D-033, D-035)
    id: int
    email: str
