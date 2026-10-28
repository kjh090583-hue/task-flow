import { priorityLabel } from './statuses'

// AI 가 만든 할 일의 미리 보기. [모두 등록]을 눌러야 저장된다. (D-045)
function DraftPreview({ drafts, message, registering, onRegisterAll, onCancel }) {
  return (
    <section className="draft-preview" aria-label="AI 가 만든 할 일">
      <h3>AI 가 만든 할 일 {drafts.length}개</h3>
      <ul>
        {drafts.map((draft, index) => (
          <li key={index}>
            <span>{draft.title}</span>
            <span className="chip" data-priority={draft.priority}>
              {priorityLabel(draft.priority)}
            </span>
            {draft.due_date && <span className="due">마감 {draft.due_date}</span>}
          </li>
        ))}
      </ul>
      {message && <p role="alert">{message}</p>}
      <div className="card-actions">
        <button type="button" onClick={onRegisterAll} disabled={registering}>
          모두 등록
        </button>
        <button type="button" onClick={onCancel} disabled={registering}>
          취소
        </button>
      </div>
    </section>
  )
}

export default DraftPreview
