import TaskCard from './TaskCard'

function Column({ label, tasks }) {
  return (
    <section className="column">
      <h2>{label}</h2>
      <ul>
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </ul>
    </section>
  )
}

export default Column
