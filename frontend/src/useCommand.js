import { useEffect, useRef, useState } from 'react'
import { commandText, createTask, MESSAGES, updateStatus, updateTask } from './api'
import { DEFAULT_PRIORITY } from './components/statuses'

// 현재 목록에 있는 카드를 가리키는 줄만 남긴다. 그 사이 삭제한 카드(못 찾는 id)의 줄은 뺀다.
export function visibleActions(tasks, actions) {
  const ids = new Set(tasks.map((task) => task.id))
  return actions.filter((action) => action.kind === 'add' || ids.has(action.id))
}

// [시키기]의 상태. 제안은 저장하지 않고, [적용]을 눌러야 기존 API 로 하나씩 저장한다.
// 상태는 등록 · 저장 오류와 따로 두어, 시키기가 실패해도 보드와 등록 폼은 그대로 동작한다.
export function useCommand(tasks, onChanged, onLoseLogin) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState(null)
  // 카드 없이 한 줄로 보이는 되묻는 말과 실패 문구.
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  // 요청마다 번호를 매겨, 그 사이에 닫았거나 화면이 사라졌으면 늦게 온 응답을 버린다. (useBriefing 과 같은 방식)
  const latest = useRef(0)
  const tasksRef = useRef(tasks)

  useEffect(() => {
    tasksRef.current = tasks
  }, [tasks])

  useEffect(() => {
    const current = latest
    return () => {
      current.current += 1
    }
  }, [])

  function clear() {
    setResult(null)
    setNote('')
    setError('')
  }

  function reset() {
    latest.current += 1
    setBusy(false)
    setApplying(false)
    clear()
  }

  async function request() {
    const sentence = text.trim()
    if (!sentence) return
    const run = ++latest.current
    clear()
    setApplying(false)
    setBusy(true)
    try {
      const answer = await commandText(sentence)
      if (run !== latest.current) return
      if (answer.ask) setNote(answer.ask)
      else if (answer.actions.length > 0) setResult(answer)
      else setError(MESSAGES.commandFailed)
    } catch (caught) {
      if (run !== latest.current) return
      if (caught.status === 401) onLoseLogin(caught)
      else setError(caught.message)
    } finally {
      if (run === latest.current) setBusy(false)
    }
  }

  // 줄마다 기존 API 를 한 번씩, 차례로 부른다. 실패하면 그 줄에서 멈추고 앞서 적용한 것은 그대로 둔다. 끝나면 목록을 다시 받는다.
  async function apply(actions) {
    const run = ++latest.current
    setApplying(true)
    setError('')
    let done = 0
    let failure = null
    let failedTitle = ''
    for (const action of actions) {
      if (run !== latest.current) return
      try {
        await applyOne(action, tasksRef.current)
        done += 1
      } catch (caught) {
        failure = caught
        failedTitle = action.kind === 'add' ? action.title : tasksRef.current.find((item) => item.id === action.id)?.title
        break
      }
    }
    if (run !== latest.current) return
    if (failure && failure.status === 401) {
      onLoseLogin(failure)
      return
    }
    await onChanged()
    if (run !== latest.current) return
    setApplying(false)
    if (failure) {
      setResult(null)
      setError(`${done}개 적용했고 '${failedTitle}'은(는) 못 했습니다: ${failure.message}`)
    } else {
      setResult(null)
      setText('')
    }
  }

  return { text, setText, busy, applying, result, note, error, request, apply, reset }
}

// 한 줄을 기존 API 한 번으로 바꾼다. due 는 제목 · 설명을 지금 값 그대로 보내고 우선순위는 보내지 않아 그대로 둔다. (D-029, D-041)
function applyOne(action, tasks) {
  if (action.kind === 'add') {
    return createTask({
      title: action.title,
      description: '',
      priority: action.priority ?? DEFAULT_PRIORITY,
      due_date: action.due_date ?? null,
    })
  }
  if (action.kind === 'done') return updateStatus(action.id, 'DONE')
  const task = tasks.find((item) => item.id === action.id)
  return updateTask(action.id, {
    title: task.title,
    description: task.description,
    due_date: action.due_date,
  })
}
