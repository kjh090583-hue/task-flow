import { MESSAGES } from '../api'
import { useCommand, visibleActions } from '../useCommand'
import { DEFAULT_PRIORITY, priorityLabel } from './statuses'

// 한 줄: 완료로 · 마감을 바꿈 · 새로 만들기. 제목은 id 로 현재 목록에서 찾는다.
function lineOf(action, byId) {
  if (action.kind === 'add') {
    return `${action.title} — 새 카드 (우선순위 ${priorityLabel(action.priority ?? DEFAULT_PRIORITY)} · 마감 ${action.due_date ?? '없음'})`
  }
  const task = byId.get(action.id)
  if (action.kind === 'done') return `${task.title} — 완료로`
  return `${task.title}(지금 마감 ${task.due_date ?? '없음'}) — 마감을 ${action.due_date} 으로`
}

function Card({ actions, tasks, applying, onApply, onClose }) {
  const lines = visibleActions(tasks, actions)
  // 그릴 수 있는 줄이 하나도 없으면 카드 대신 실패 문구를 보인다.
  if (lines.length === 0) {
    return (
      <p role="alert" className="briefing-note">
        {MESSAGES.commandFailed}
      </p>
    )
  }
  const byId = new Map(tasks.map((task) => [task.id, task]))
  return (
    <section className="briefing-card" aria-label="시키기 확인">
      <h3>이렇게 바꿀까요? {lines.length}개</h3>
      <ul>
        {lines.map((action, index) => (
          <li key={index}>{lineOf(action, byId)}</li>
        ))}
      </ul>
      <div>
        <button type="button" onClick={() => onApply(lines)} disabled={applying}>
          {applying ? '적용하는 중…' : '적용'}
        </button>{' '}
        <button type="button" onClick={onClose} disabled={applying}>
          취소
        </button>
      </div>
    </section>
  )
}

// 입력란과 [시키기] 버튼, 확인 카드. 기다리는 동안 이 버튼만 잠근다.
function CommandCard({ tasks, onChanged, onLoseLogin }) {
  const command = useCommand(tasks, onChanged, onLoseLogin)

  function handleSubmit(event) {
    event.preventDefault()
    command.request()
  }

  return (
    <>
      <form className="task-form" onSubmit={handleSubmit}>
        <input
          value={command.text}
          onChange={(event) => command.setText(event.target.value)}
          maxLength={200}
          placeholder="한 문장으로 시키기 (예: 보고서 마감을 금요일로)"
          aria-label="시킬 말"
          disabled={command.busy || command.applying}
        />
        <button type="submit" disabled={command.busy || command.applying || !command.text.trim()}>
          {command.busy ? MESSAGES.commanding : '시키기'}
        </button>
        {command.busy && (
          <span role="status" className="visually-hidden">
            {MESSAGES.commanding}
          </span>
        )}
      </form>
      <div className="briefing">
        {command.note && <p className="briefing-note">{command.note}</p>}
        {command.error && (
          <p role="alert" className="briefing-note">
            {command.error}
          </p>
        )}
        {command.result && (
          <Card
            actions={command.result.actions}
            tasks={tasks}
            applying={command.applying}
            onApply={command.apply}
            onClose={command.reset}
          />
        )}
      </div>
    </>
  )
}

export default CommandCard
