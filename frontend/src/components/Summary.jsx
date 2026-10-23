// 전체 Task 수와 완료 비율. 목록에서 계산하며 API 는 바꾸지 않는다. (D-039)
function Summary({ tasks }) {
  const total = tasks.length
  const done = tasks.filter((task) => task.status === 'DONE').length
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)

  return (
    <div className="summary">
      <div className="summary-box">
        <small>전체 Task</small>
        <strong>{total}개</strong>
      </div>
      <div className="summary-box summary-progress">
        <small>완료 진행률</small>
        <div
          className="progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
          aria-label="완료 진행률"
        >
          <div className="progress-fill" style={{ width: `${percent}%` }} />
        </div>
        <strong>{percent}%</strong>
      </div>
    </div>
  )
}

export default Summary
