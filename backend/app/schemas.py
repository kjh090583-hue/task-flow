import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictInt, field_validator

Status = Literal["TODO", "IN_PROGRESS", "DONE"]
Priority = Literal["LOW", "NORMAL", "HIGH"]

# 마감일은 날짜만 받는다. (D-041)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 이메일은 @ 앞뒤가 있고 점이 있는 도메인이면 된다. (D-038)
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_due_date(value):
    if value is None:
        return None
    if not isinstance(value, str) or not _DATE_PATTERN.match(value):
        raise ValueError("마감일은 YYYY-MM-DD 날짜여야 합니다")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError("마감일은 YYYY-MM-DD 날짜여야 합니다")
    return value


def _check_title(value: str) -> str:
    # 공백만 있는 제목은 비어 있는 제목이다. (D-012, D-013)
    value = value.strip()
    if not value:
        raise ValueError("제목은 비워 둘 수 없습니다")
    return value


class TaskCreate(BaseModel):
    # 등록과 수정이 같이 쓴다. priority · due_date 는 수정에서 보내지 않으면 그대로 둔다. (D-041)
    # priority 는 null 을 받지 않는다(422). due_date 는 null 이면 마감일이 없다.
    title: str
    description: str = ""
    priority: Priority = "NORMAL"
    due_date: str | None = None

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_format(cls, value):
        return _check_due_date(value)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        return _check_title(value)


class SuggestRequest(BaseModel):
    # AI 제안의 요청. 제목이 비었거나 공백뿐이면 422 이다. 설명은 없어도 된다. (D-044)
    title: str
    description: str = ""

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        return _check_title(value)


class Suggestion(BaseModel):
    # AI 가 제안한 값. 저장하지 않으며, AI 의 답 검사와 응답에 같이 쓴다. (D-044)
    model_config = ConfigDict(extra="forbid")

    priority: Priority
    due_date: str | None
    reason: str

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_format(cls, value):
        return _check_due_date(value)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("이유는 비워 둘 수 없습니다")
        return value


def _check_sentence(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} 는 비워 둘 수 없습니다")
    return value


class BriefingPick(BaseModel):
    # 먼저 할 일 하나. id 는 정수만 받는다(문자열 · true/false 는 거절). (D-046)
    model_config = ConfigDict(extra="forbid")

    id: StrictInt
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        return _check_sentence(value, "이유")


class Briefing(BaseModel):
    # AI 가 만든 오늘 브리핑. 저장하지 않으며, AI 의 답 검사와 응답에 같이 쓴다. (D-046)
    model_config = ConfigDict(extra="forbid")

    top3: list[BriefingPick]
    later: list[StrictInt]
    cheer: str

    @field_validator("cheer")
    @classmethod
    def cheer_not_blank(cls, value: str) -> str:
        return _check_sentence(value, "응원")


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    due_date: str | None
    is_overdue: bool  # 저장하지 않고 응답할 때 계산한다. (D-042)
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
