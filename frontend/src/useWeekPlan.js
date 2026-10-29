import { useEffect, useRef, useState } from 'react'
import { MESSAGES } from './api'

// [이번 주 계획]의 상태. 계획은 저장하지 않고 목록도 바꾸지 않는다. (D-048)
// 상태는 등록 · 저장 오류와 따로 두어, 계획이 실패해도 보드와 등록 폼은 그대로 동작한다.
export function useWeekPlan(onWeekPlan) {
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  // 카드 없이 한 줄로 보이는 안내(빈 날)와 실패 문구.
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  // 요청마다 번호를 매겨, 그 사이에 닫았거나 화면이 사라졌으면 늦게 온 응답을 버린다. (useBriefing 과 같은 방식)
  const latest = useRef(0)

  useEffect(() => {
    const current = latest
    return () => {
      current.current += 1
    }
  }, [])

  function reset() {
    latest.current += 1
    setBusy(false)
    setResult(null)
    setNote('')
    setError('')
  }

  async function request() {
    const run = ++latest.current
    setResult(null)
    setNote('')
    setError('')
    setBusy(true)
    try {
      const plan = await onWeekPlan()
      if (run !== latest.current) return
      // 서버는 할 일이 없으면 빈 days 로 답한다. 카드 대신 한 줄만 보인다.
      if (plan.days.length === 0) setNote(MESSAGES.briefingEmpty)
      else setResult(plan)
    } catch (caught) {
      if (run === latest.current) setError(caught.message)
    } finally {
      if (run === latest.current) setBusy(false)
    }
  }

  return { busy, result, note, error, request, reset }
}
