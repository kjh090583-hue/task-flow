import TaskCard from './TaskCard'

function Column({ label, tasks, onStatusChange }) {
  return (
    <section className="column">
      <h2>{label}</h2>
      <ul>
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onStatusChange={onStatusChange} />
        ))}
      </ul>
    </section>
  )
}

export default Column
