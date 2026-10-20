import { useEffect, useState } from 'react'
import { createTask, getTasks } from './api'
import Board from './components/Board'
import TaskForm from './components/TaskForm'

function App() {
  const [tasks, setTasks] = useState([])
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    getTasks()
      .then(setTasks)
      .catch((error) => setLoadError(error.message))
  }, [])

  // API 가 성공을 응답한 뒤에만 화면에 카드를 더한다. (D-005)
  async function handleCreate(input) {
    const created = await createTask(input)
    setTasks((current) => [...current, created])
  }

  return (
    <main>
      <h1>task-flow</h1>
      <TaskForm onCreate={handleCreate} />
      {loadError ? <p role="alert">목록을 불러오지 못했습니다: {loadError}</p> : <Board tasks={tasks} />}
    </main>
  )
}

export default App
