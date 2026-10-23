import { useState } from 'react'
import { STATUSES } from './statuses'

function TaskCard({ task, onStatusChange, onUpdate, onDelete }) {
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)

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
    setMessage('')
    setEditing(true)
  }

  async function handleSave(event) {
    event.preventDefault()
    // 제목이 비었으면 요청을 보내지 않고 안내한다. (D-003)
    if (!title.trim()) {
      setMessage('제목을 입력하세요')
      return
    }
    if (await run(() => onUpdate(task.id, { title, description }))) {
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
          <div className="card-actions">
            <button type="submit">저장</button>
            <button type="button" onClick={() => setEditing(false)}>
              취소
            </button>
          </div>
        </form>
        {message && <p role="alert">{message}</p>}
      </li>
    )
  }

  return (
    <li className="card">
      <span className="badge" data-status={task.status}>
        {task.status.replace('_', ' ')}
      </span>
      <strong>{task.title}</strong>
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
