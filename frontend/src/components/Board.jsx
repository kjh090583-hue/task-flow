import Column from './Column'

// 화면 표시 이름. 상태는 이 세 가지뿐이다. (PRD R-006)
const COLUMNS = [
  { status: 'TODO', label: '할 일' },
  { status: 'IN_PROGRESS', label: '진행 중' },
  { status: 'DONE', label: '완료' },
]

function Board({ tasks }) {
  return (
    <div className="board">
      {COLUMNS.map(({ status, label }) => (
        <Column
          key={status}
          label={label}
          tasks={tasks.filter((task) => task.status === status)}
        />
      ))}
    </div>
  )
}

export default Board
