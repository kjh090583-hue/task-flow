import { useEffect, useRef, useState } from 'react'

// [AI 제안]의 상태. 등록 폼과 카드 수정 폼이 같이 쓴다. (D-044)
// 제안 상태는 저장 오류와 따로 두어, 제안이 실패해도 등록 · 저장은 그대로 동작한다.
export function useSuggest(onSuggest) {
  const [busy, setBusy] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  // 요청마다 번호를 매겨, 그 사이에 폼이 닫히거나 비워졌으면 늦게 온 응답을 버린다. (D-043 과 같은 방식)
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
    setReason('')
    setError('')
  }

  // 제안을 받아 apply 로 입력란만 채운다. 저장은 하지 않는다.
  async function suggest({ title, description }, apply) {
    // 제목이 비었으면 요청을 보내지 않고 안내한다. (D-003)
    if (!title.trim()) {
      setReason('')
      setError('제목을 입력하세요')
      return
    }
    const run = ++latest.current
    setReason('')
    setError('')
    setBusy(true)
    try {
      const suggestion = await onSuggest({ title, description })
      if (run !== latest.current) return
      apply(suggestion)
      setReason(suggestion.reason)
    } catch (caught) {
      if (run === latest.current) setError(caught.message)
    } finally {
      if (run === latest.current) setBusy(false)
    }
  }

  return { busy, reason, error, suggest, reset }
}
