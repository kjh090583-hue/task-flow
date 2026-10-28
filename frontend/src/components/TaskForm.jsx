import { useEffect, useRef, useState } from 'react'
import { MESSAGES } from '../api'
import DraftPreview from './DraftPreview'
import { DEFAULT_PRIORITY, PRIORITIES } from './statuses'

function TaskForm({ onCreate, onGenerate, onRegisterAll }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState(DEFAULT_PRIORITY)
  const [dueDate, setDueDate] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  // AI 로 할 일 만들기: 미리 보기(drafts)는 [모두 등록]을 눌러야 저장된다. (D-045)
  const [generating, setGenerating] = useState(false)
  const [registering, setRegistering] = useState(false)
  const [drafts, setDrafts] = useState(null)
  const [draftMessage, setDraftMessage] = useState('')
  // 폼을 비우거나 로그아웃한 뒤 늦게 온 응답을 버리는 데 쓴다. (D-043 과 같은 방식)
  const generation = useRef(0)

  useEffect(() => {
    const current = generation
    return () => {
      current.current += 1
    }
  }, [])

  // 폼을 비울 때 만들거나 등록하던 것을 모두 놓는다.
  function discardDrafts() {
    generation.current += 1
    setGenerating(false)
    setRegistering(false)
    setDrafts(null)
    setDraftMessage('')
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
      discardDrafts()
    } catch (error) {
      // 실패하면 입력을 남긴다. (D-021)
      setMessage(error.message)
    } finally {
      setSaving(false)
    }
  }

  // 제목 입력란의 글을 주제로 보낸다. 저장 버튼은 기다리는 동안에도 그대로 동작한다. (D-045)
  async function handleGenerate() {
    if (!title.trim()) {
      setMessage('제목을 입력하세요')
      return
    }
    const run = ++generation.current
    setMessage('')
    setDrafts(null)
    setDraftMessage('')
    setGenerating(true)
    try {
      const tasks = await onGenerate(title)
      if (run === generation.current) setDrafts(tasks)
    } catch (error) {
      if (run === generation.current) setMessage(error.message)
    } finally {
      if (run === generation.current) setGenerating(false)
    }
  }

  // 모두 성공하면 미리 보기를 닫고 제목을 비운다. 실패한 것만 남겨 다시 등록할 수 있게 한다. (D-045)
  async function handleRegisterAll() {
    const run = generation.current
    setDraftMessage('')
    setRegistering(true)
    try {
      const failed = await onRegisterAll(drafts)
      if (run !== generation.current) return
      if (failed.length === 0) {
        setDrafts(null)
        setTitle('')
      } else {
        setDrafts(failed)
        setDraftMessage(`${failed.length}개 등록하지 못했습니다.`)
      }
    } catch (error) {
      if (run === generation.current) setDraftMessage(error.message)
    } finally {
      if (run === generation.current) setRegistering(false)
    }
  }

  function handleCancelDrafts() {
    setDrafts(null)
    setDraftMessage('')
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
      <button type="button" className="ai-button" onClick={handleGenerate} disabled={generating || registering}>
        AI 로 할 일 만들기
      </button>
      {generating && (
        <p className="status" role="status">
          {MESSAGES.generating}
        </p>
      )}
      {message && <p role="alert">{message}</p>}
      {drafts && (
        <DraftPreview
          drafts={drafts}
          message={draftMessage}
          registering={registering}
          onRegisterAll={handleRegisterAll}
          onCancel={handleCancelDrafts}
        />
      )}
    </form>
  )
}

export default TaskForm
