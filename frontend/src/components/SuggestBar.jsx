import { MESSAGES } from '../api'

// [AI 제안] 버튼. 기다리는 동안 이 버튼만 잠근다. 저장 버튼은 그대로 동작한다. (D-044)
export function SuggestButton({ busy, onClick }) {
  return (
    <>
      <button type="button" className="suggest-button" onClick={onClick} disabled={busy}>
        AI 제안
      </button>
      {busy && (
        <span className="suggest-status" role="status">
          {MESSAGES.suggesting}
        </span>
      )}
    </>
  )
}

// 실패 안내 또는 이유 한 줄.
export function SuggestNote({ reason, error }) {
  if (error) return <p role="alert">{error}</p>
  if (reason) return <p className="suggest-reason">이유: {reason}</p>
  return null
}
