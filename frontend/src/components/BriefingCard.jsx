import { MESSAGES } from '../api'
import { useBriefing } from '../useBriefing'

const MARKS = ['①', '②', '③']

// 서버가 준 id 로 현재 목록에서 제목을 찾는다. 그 사이 삭제하거나 완료한 카드(못 찾는 id)는 뺀다. (D-047)
function titlesOf(tasks, picks) {
  const byId = new Map(tasks.map((task) => [task.id, task.title]))
  return picks.filter((pick) => byId.has(pick.id)).map((pick) => ({ ...pick, title: byId.get(pick.id) }))
}

function Card({ briefing, tasks, onClose }) {
  const picks = titlesOf(tasks, briefing.top3)
  const later = titlesOf(
    tasks,
    briefing.later.map((id) => ({ id })),
  )
  // 먼저 할 일을 하나도 그릴 수 없으면 카드 대신 실패 문구를 보인다.
  if (picks.length === 0) {
    return (
      <p role="alert" className="briefing-note">
        {MESSAGES.briefingFailed}
      </p>
    )
  }
  return (
    <section className="briefing-card" aria-label="오늘 브리핑">
      <h3>먼저 할 일</h3>
      <ol>
        {picks.map((pick, index) => (
          <li key={pick.id}>
            <span className="briefing-mark">{MARKS[index]}</span>
            <strong>{pick.title}</strong> — {pick.reason}
          </li>
        ))}
      </ol>
      {later.length > 0 && (
        <>
          <h3>미뤄도 되는 일</h3>
          <ul>
            {later.map((task) => (
              <li key={task.id}>{task.title}</li>
            ))}
          </ul>
        </>
      )}
      <p className="briefing-cheer">{briefing.cheer}</p>
      <button type="button" onClick={onClose}>
        닫기
      </button>
    </section>
  )
}

// [오늘 브리핑] 버튼과 결과 카드. 기다리는 동안 이 버튼만 잠근다. (D-047)
function BriefingCard({ tasks, onBriefing }) {
  const briefing = useBriefing(onBriefing)

  return (
    <div className="briefing">
      <div className="briefing-bar">
        <button type="button" onClick={briefing.request} disabled={briefing.busy}>
          {briefing.busy ? MESSAGES.briefing : '오늘 브리핑'}
        </button>
        {briefing.busy && (
          <span role="status" className="visually-hidden">
            {MESSAGES.briefing}
          </span>
        )}
      </div>
      {briefing.note && <p className="briefing-note">{briefing.note}</p>}
      {briefing.error && (
        <p role="alert" className="briefing-note">
          {briefing.error}
        </p>
      )}
      {briefing.result && <Card briefing={briefing.result} tasks={tasks} onClose={briefing.reset} />}
    </div>
  )
}

export default BriefingCard
