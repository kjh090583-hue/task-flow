import Column from './Column'
import { STATUSES } from './statuses'

function Board({ tasks, ...handlers }) {
  return (
    <div className="board">
      {STATUSES.map(({ status, label }) => (
        <Column
          key={status}
          label={label}
          status={status}
          tasks={tasks.filter((task) => task.status === status)}
          {...handlers}
        />
      ))}
    </div>
  )
}

export default Board
