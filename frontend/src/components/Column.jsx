import TaskCard from './TaskCard'

function Column({ label, tasks, ...handlers }) {
  return (
    <section className="column">
      <h2>{label}</h2>
      <ul>
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} {...handlers} />
        ))}
      </ul>
    </section>
  )
}

export default Column
