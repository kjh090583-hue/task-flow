import { useState } from 'react'
import { useSuggest } from '../useSuggest'
import { SuggestButton, SuggestNote } from './SuggestBar'
import { DEFAULT_PRIORITY, PRIORITIES } from './statuses'

function TaskForm({ onCreate, onSuggest }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState(DEFAULT_PRIORITY)
  const [dueDate, setDueDate] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  // AI 제안은 입력란만 채운다. 저장은 아래 [저장] 버튼이 한다. (D-044)
  const suggest = useSuggest(onSuggest)

  function handleSuggest() {
    suggest.suggest({ title, description }, (suggestion) => {
      setPriority(suggestion.priority)
      setDueDate(suggestion.due_date ?? '')
    })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    // 제목이 비었으면 요청을 보내지 않고 안내한다. (D-003)
    if (!title.trim()) {
      setMessage('제목을 입력하세요')
      return
    }
    setSaving(true)
    setMessage('')
    try {
      await onCreate({ title, description, priority, due_date: dueDate || null })
      setTitle('')
      setDescription('')
      setPriority(DEFAULT_PRIORITY)
      setDueDate('')
      suggest.reset()
    } catch (error) {
      // 실패하면 입력을 남긴다. (D-021)
      setMessage(error.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="제목"
        aria-label="제목"
      />
      <input
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="설명 (선택)"
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
        className="due-input"
        value={dueDate}
        onChange={(event) => setDueDate(event.target.value)}
        aria-label="마감일"
      />
      <button type="submit" disabled={saving}>
        저장
      </button>
      <SuggestButton busy={suggest.busy} onClick={handleSuggest} />
      <SuggestNote reason={suggest.reason} error={suggest.error} />
      {message && <p role="alert">{message}</p>}
    </form>
  )
}

export default TaskForm
