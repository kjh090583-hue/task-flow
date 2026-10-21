import { useEffect, useState } from 'react'
import { createTask, deleteTask, getTasks, MESSAGES, updateStatus, updateTask } from './api'
import Board from './components/Board'
import TaskForm from './components/TaskForm'

function App() {
  const [tasks, setTasks] = useState([])
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')

  // 목록 실패는 빈 목록처럼 보이지 않게 따로 알리고, 다시 시도로 이 함수를 다시 부른다.
  function fetchTasks() {
    getTasks()
      .then(setTasks)
      .catch(() => setLoadError(MESSAGES.listFailed))
      .finally(() => setLoading(false))
  }

  function loadTasks() {
    setLoading(true)
    setLoadError('')
    fetchTasks()
  }

  useEffect(fetchTasks, [])

  // API 가 성공을 응답한 뒤에만 화면에 카드를 더한다. (D-005)
  async function handleCreate(input) {
    setNotice('')
    const created = await createTask(input)
    setTasks((current) => [...current, created])
  }

  // 성공 응답을 받은 뒤에만 카드의 상태를 바꾼다. 카드가 없으면(404) 목록을 다시 불러온다. (D-005)
  // 카드가 사라지면 카드 아래 안내도 함께 사라지므로, 이 경우의 안내는 보드 위에 보인다. (D-027)
  async function reloadAfterNotFound(error) {
    if (error.status === 404) {
      setNotice(error.message)
      setTasks(await getTasks())
    }
  }

  async function changeTask(id, request) {
    setNotice('')
    try {
      const updated = await request()
      setTasks((current) => current.map((task) => (task.id === id ? updated : task)))
    } catch (error) {
      await reloadAfterNotFound(error)
      throw error
    }
  }

  const handleStatusChange = (id, status) => changeTask(id, () => updateStatus(id, status))
  const handleUpdate = (id, input) => changeTask(id, () => updateTask(id, input))

  // 삭제도 성공 응답 뒤에 화면에서 없앤다. 이미 지운 카드(404)면 목록을 다시 불러온다. (D-005)
  async function handleDelete(id) {
    setNotice('')
    try {
      await deleteTask(id)
      setTasks((current) => current.filter((task) => task.id !== id))
    } catch (error) {
      await reloadAfterNotFound(error)
      throw error
    }
  }

  return (
    <main>
      <h1>task-flow</h1>
      <TaskForm onCreate={handleCreate} />
      {notice && (
        <p className="notice" role="alert">
          {notice}
        </p>
      )}
      {loading && <p className="notice">불러오는 중...</p>}
      {!loading && loadError && (
        <div className="notice" role="alert">
          <p>{loadError}</p>
          <button type="button" onClick={loadTasks}>
            다시 시도
          </button>
        </div>
      )}
      {!loading && !loadError && (
        <>
          {tasks.length === 0 && <p className="notice">아직 Task 가 없습니다. 위에서 첫 Task 를 만들어 보세요.</p>}
          <Board
            tasks={tasks}
            onStatusChange={handleStatusChange}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
          />
        </>
      )}
    </main>
  )
}

export default App
