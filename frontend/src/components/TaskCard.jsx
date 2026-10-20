import { useState } from 'react'
import { STATUSES } from './statuses'

function TaskCard({ task, onStatusChange }) {
  const [message, setMessage] = useState('')

  // 실패하면 select 는 task.status 를 따르므로 화면이 바뀌지 않는다. (D-005)
  async function handleChange(event) {
    setMessage('')
    try {
      await onStatusChange(task.id, event.target.value)
    } catch (error) {
      setMessage(error.message)
    }
  }

  return (
    <li className="card">
      <strong>{task.title}</strong>
      {task.description && <p>{task.description}</p>}
      <select value={task.status} onChange={handleChange} aria-label="상태">
        {STATUSES.map(({ status, label }) => (
          <option key={status} value={status}>
            {label}
          </option>
        ))}
      </select>
      {message && <p role="alert">{message}</p>}
    </li>
  )
}

export default TaskCard
