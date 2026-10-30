"""한 문장으로 시키기의 입력 규칙. 길이와 이유 문구를 한곳에 둔다."""

COMMAND_TEXT_MAX = 200


def check_command_text(value: str) -> str:
    # 앞뒤 공백을 지운 뒤 1 ~ 200자여야 한다. 공백뿐인 문장은 빈 문장이다. (D-013 과 같은 취지)
    value = value.strip()
    if not value:
        raise ValueError("시킬 말은 비워 둘 수 없습니다")
    if len(value) > COMMAND_TEXT_MAX:
        raise ValueError(f"시킬 말은 {COMMAND_TEXT_MAX}자 이하여야 합니다")
    return value
