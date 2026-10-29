import { useState } from 'react'
import { useSuggest } from '../useSuggest'
import { SuggestButton, SuggestNote } from './SuggestBar'
import { PRIORITIES, priorityLabel, STATUSES } from './statuses'

function TaskCard({ task, onStatusChange, onUpdate, onDelete, onSuggest }) {
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [priority, setPriority] = useState(task.priority)
  const [dueDate, setDueDate] = useState(task.due_date ?? '')
  // AI 제안은 입력란만 채운다. 저장은 아래 [저장] 버튼이 한다. (D-044)
  const suggest = useSuggest(onSuggest)

  function handleSuggest() {
    suggest.suggest({ title, description }, (suggestion) => {
      setPriority(suggestion.priority)
      setDueDate(suggestion.due_date ?? '')
    })
  }

  // 실패하면 화면은 task 값을 그대로 보인다. (D-005)
  async function run(action) {
    setMessage('')
    try {
      await action()
      return true
    } catch (error) {
      setMessage(error.message)
      return false
    }
  }

  function startEdit() {
    setTitle(task.title)
    setDescription(task.description)
    setPriority(task.priority)
    setDueDate(task.due_date ?? '')
    setMessage('')
    suggest.reset()
    setEditing(true)
  }

  function cancelEdit() {
    suggest.reset()
    setEditing(false)
  }

  async function handleSave(event) {
    event.preventDefault()
    // 제목이 비었으면 요청을 보내지 않고 안내한다. (D-003)
    if (!title.trim()) {
      setMessage('제목을 입력하세요')
      return
    }
    // 마감일을 비우면 null 을 보내 마감일을 지운다. (D-041)
    if (await run(() => onUpdate(task.id, { title, description, priority, due_date: dueDate || null }))) {
      suggest.reset()
      setEditing(false)
    }
  }

  function handleDelete() {
    // 삭제 전에 한 번 묻는다. (D-015)
    if (window.confirm('이 카드를 삭제할까요? 삭제하면 되돌릴 수 없습니다.')) {
      run(() => onDelete(task.id))
    }
  }

  if (editing) {
    return (
      <li className="card">
        <form onSubmit={handleSave}>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            aria-label="제목"
          />
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            aria-label="설명"
          />
          <select value={priority} onChange={(event) => setPriority(event.target.value)} aria-label="우선순위">
            {PRIORITIES.map(({ priority: value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
            aria-label="마감일"
          />
          <div className="card-actions">
            <button type="submit">저장</button>
            <button type="button" onClick={cancelEdit}>
              취소
            </button>
            <SuggestButton busy={suggest.busy} onClick={handleSuggest} />
          </div>
          <SuggestNote reason={suggest.reason} error={suggest.error} />
        </form>
        {message && <p role="alert">{message}</p>}
      </li>
    )
  }

  return (
    <li className="card" data-overdue={task.is_overdue}>
      <span className="badge" data-status={task.status}>
        {task.status.replace('_', ' ')}
      </span>
      <strong>{task.title}</strong>
      <div className="card-meta">
        {/* 기한 초과 여부는 서버가 계산한 값을 그대로 보여 준다. (D-042) */}
        {task.is_overdue && <span className="chip overdue-chip">기한 초과</span>}
        <span className="chip" data-priority={task.priority}>
          {priorityLabel(task.priority)}
        </span>
        {task.due_date && <span className="due">마감 {task.due_date}</span>}
      </div>
      {task.description && <p>{task.description}</p>}
      <select
        value={task.status}
        onChange={(event) => run(() => onStatusChange(task.id, event.target.value))}
        aria-label="상태"
      >
        {STATUSES.map(({ status, label }) => (
          <option key={status} value={status}>
            {label}
          </option>
        ))}
      </select>
      <div className="card-actions">
        <button type="button" onClick={startEdit}>
          수정
        </button>
        <button type="button" onClick={handleDelete}>
          삭제
        </button>
      </div>
      {message && <p role="alert">{message}</p>}
    </li>
  )
}

export default TaskCard
