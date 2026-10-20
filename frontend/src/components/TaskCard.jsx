function TaskCard({ task }) {
  return (
    <li className="card">
      <strong>{task.title}</strong>
      {task.description && <p>{task.description}</p>}
    </li>
  )
}

export default TaskCard
