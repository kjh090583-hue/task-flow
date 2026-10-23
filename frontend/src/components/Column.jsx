import TaskCard from './TaskCard'

function Column({ label, status, tasks, ...handlers }) {
  return (
    <section className="column" data-status={status}>
      <div className="column-head">
        <h2>{label}</h2>
        <span className="count">{tasks.length}</span>
      </div>
      <ul>
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} {...handlers} />
        ))}
      </ul>
    </section>
  )
}

export default Column
