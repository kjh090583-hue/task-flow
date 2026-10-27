// 화면 표시 이름. 상태는 이 세 가지뿐이다. (PRD R-006)
export const STATUSES = [
  { status: 'TODO', label: '할 일' },
  { status: 'IN_PROGRESS', label: '진행 중' },
  { status: 'DONE', label: '완료' },
]

// 화면 표시 이름. 우선순위는 이 세 가지뿐이고 기본은 보통이다. (D-041, D-043)
export const PRIORITIES = [
  { priority: 'HIGH', label: '높음' },
  { priority: 'NORMAL', label: '보통' },
  { priority: 'LOW', label: '낮음' },
]

export const DEFAULT_PRIORITY = 'NORMAL'

export function priorityLabel(priority) {
  return PRIORITIES.find((item) => item.priority === priority)?.label ?? priority
}

// 마감일은 `MM-DD` 로 보이고, 올해가 아니면 연도를 붙인다. (D-043)
export function formatDue(dueDate) {
  return dueDate.startsWith(`${new Date().getFullYear()}-`) ? dueDate.slice(5) : dueDate
}
