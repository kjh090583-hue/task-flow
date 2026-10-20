import Column from './Column'
import { STATUSES } from './statuses'

function Board({ tasks, onStatusChange }) {
  return (
    <div className="board">
      {STATUSES.map(({ status, label }) => (
        <Column
          key={status}
          label={label}
          tasks={tasks.filter((task) => task.status === status)}
          onStatusChange={onStatusChange}
        />
      ))}
    </div>
  )
}

export default Board
