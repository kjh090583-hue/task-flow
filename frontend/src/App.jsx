import { useEffect, useState } from 'react'
import {
  createTask,
  deleteTask,
  getMe,
  getTasks,
  login,
  logout,
  MESSAGES,
  register,
  updateStatus,
  updateTask,
} from './api'
import AuthForm from './components/AuthForm'
import Board from './components/Board'
import Header from './components/Header'
import Summary from './components/Summary'
import TaskForm from './components/TaskForm'

function App() {
  // 로그인한 사용자. 없으면 로그인 화면을 보인다. (D-033)
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)
  const [authError, setAuthError] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [tasks, setTasks] = useState([])
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')

  // 로그인하면 보드를 불러오는 중으로 바꾸고 사용자를 정한다. 보드는 사용자가 정해지면 불러온다.
  function applyLogin(loggedIn) {
    setLoading(true)
    setLoadError('')
    setUser(loggedIn)
  }

  // 처음 열 때 로그인 상태를 확인한다. 401 이면 로그인 화면, 그 밖의 실패는 안내와 다시 시도를 보인다.
  function checkLogin() {
    getMe()
      .then(applyLogin)
      .catch((error) => {
        if (error.status !== 401) setAuthError(error.message)
      })
      .finally(() => setChecking(false))
  }

  function retryCheckLogin() {
    setChecking(true)
    setAuthError('')
    checkLogin()
  }

  useEffect(checkLogin, [])

  // 로그인이 없거나 만료되면 보드를 비우고 로그인 화면으로 돌아간다.
  function loseLogin(error) {
    setUser(null)
    setTasks([])
    setNotice('')
    setAuthNotice(error.message)
  }

  // 목록 실패는 빈 목록처럼 보이지 않게 따로 알리고, 다시 시도로 이 함수를 다시 부른다.
  function fetchTasks() {
    getTasks()
      .then(setTasks)
      .catch((error) => {
        if (error.status === 401) loseLogin(error)
        else setLoadError(MESSAGES.listFailed)
      })
      .finally(() => setLoading(false))
  }

  function loadTasks() {
    setLoading(true)
    setLoadError('')
    fetchTasks()
  }

  useEffect(() => {
    if (user) fetchTasks()
  }, [user])

  async function handleLogin(input) {
    const loggedIn = await login(input)
    setAuthNotice('')
    applyLogin(loggedIn)
  }

  async function handleRegister(input) {
    const registered = await register(input)
    setAuthNotice('')
    applyLogin(registered)
  }

  async function handleLogout() {
    try {
      await logout()
    } catch (error) {
      if (error.status !== 401) {
        setNotice(error.message)
        return
      }
    }
    setUser(null)
    setTasks([])
    setNotice('')
    setAuthNotice('')
  }

  // API 가 성공을 응답한 뒤에만 화면에 카드를 더한다. (D-005)
  async function handleCreate(input) {
    setNotice('')
    try {
      const created = await createTask(input)
      setTasks((current) => [...current, created])
    } catch (error) {
      if (error.status === 401) loseLogin(error)
      throw error
    }
  }

  // 성공 응답을 받은 뒤에만 카드의 상태를 바꾼다. 카드가 없으면(404) 목록을 다시 불러온다. (D-005)
  // 카드가 사라지면 카드 아래 안내도 함께 사라지므로, 이 경우의 안내는 보드 위에 보인다. (D-027)
  // 로그인이 만료되면(401) 로그인 화면으로 돌아간다.
  async function handleFailure(error) {
    if (error.status === 401) {
      loseLogin(error)
    } else if (error.status === 404) {
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
      await handleFailure(error)
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
      await handleFailure(error)
      throw error
    }
  }

  if (checking) {
    return (
      <main>
        <Header />
        <p className="notice">불러오는 중...</p>
      </main>
    )
  }

  if (authError) {
    return (
      <main>
        <Header />
        <div className="notice" role="alert">
          <p>{authError}</p>
          <button type="button" onClick={retryCheckLogin}>
            다시 시도
          </button>
        </div>
      </main>
    )
  }

  if (!user) {
    return (
      <main>
        <Header />
        {authNotice && (
          <p className="notice" role="alert">
            {authNotice}
          </p>
        )}
        <AuthForm onLogin={handleLogin} onRegister={handleRegister} />
      </main>
    )
  }

  return (
    <main>
      <Header user={user} onLogout={handleLogout} />
      <div className="board-title">
        <h2>내 Task 보드</h2>
        <p>현재 로그인한 사용자의 Task 만 표시됩니다.</p>
      </div>
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
          <Summary tasks={tasks} />
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
