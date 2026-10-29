import { MESSAGES } from '../api'
import { useWeekPlan } from '../useWeekPlan'

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

// 'YYYY-MM-DD' 를 'MM-DD (요일)' 로 바꾼다. 요일만 이 글자에서 계산한다. (D-048)
function dayLabel(text) {
  const [year, month, day] = text.split('-').map(Number)
  return `${text.slice(5)} (${WEEKDAYS[new Date(year, month - 1, day).getDay()]})`
}

// 서버가 준 id 로 현재 목록에서 제목을 찾는다. 그 사이 삭제한 카드(못 찾는 id)는 뺀다. 완료로 바뀐 카드는 목록에 남아 있으면 그대로 보인다. (D-048) 할 일이 하나도 없는 날은 줄을 뺀다.
function rowsOf(tasks, days) {
  const byId = new Map(tasks.map((task) => [task.id, task.title]))
  return days
    .map((day) => ({ date: day.date, titles: day.ids.filter((id) => byId.has(id)).map((id) => byId.get(id)) }))
    .filter((row) => row.titles.length > 0)
}

function Card({ plan, tasks, onClose }) {
  const rows = rowsOf(tasks, plan.days)
  // 표에 그릴 수 있는 줄이 하나도 없으면 카드 대신 실패 문구를 보인다.
  if (rows.length === 0) {
    return (
      <p role="alert" className="briefing-note">
        {MESSAGES.weekplanFailed}
      </p>
    )
  }
  return (
    <section className="briefing-card" aria-label="이번 주 계획">
      <h3>이번 주 계획</h3>
      <table className="weekplan-table">
        <tbody>
          {rows.map((row) => (
            <tr key={row.date}>
              <th scope="row">{dayLabel(row.date)}</th>
              <td>{row.titles.join(' · ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="briefing-cheer">{plan.note}</p>
      <button type="button" onClick={onClose}>
        닫기
      </button>
    </section>
  )
}

// [이번 주 계획] 버튼과 요일별 표 카드. 기다리는 동안 이 버튼만 잠근다. (D-048)
function WeekPlanCard({ tasks, onWeekPlan }) {
  const weekPlan = useWeekPlan(onWeekPlan)

  return (
    <div className="briefing">
      <div className="briefing-bar">
        <button type="button" onClick={weekPlan.request} disabled={weekPlan.busy}>
          {weekPlan.busy ? MESSAGES.weekplan : '이번 주 계획'}
        </button>
        {weekPlan.busy && (
          <span role="status" className="visually-hidden">
            {MESSAGES.weekplan}
          </span>
        )}
      </div>
      {weekPlan.note && <p className="briefing-note">{weekPlan.note}</p>}
      {weekPlan.error && (
        <p role="alert" className="briefing-note">
          {weekPlan.error}
        </p>
      )}
      {weekPlan.result && <Card plan={weekPlan.result} tasks={tasks} onClose={weekPlan.reset} />}
    </div>
  )
}

export default WeekPlanCard
