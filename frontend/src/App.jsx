import { useEffect, useState } from 'react'
import { getHealth } from './api'

function App() {
  const [status, setStatus] = useState('확인 중')

  useEffect(() => {
    getHealth()
      .then(() => setStatus('정상'))
      .catch(() => setStatus('연결할 수 없음'))
  }, [])

  return (
    <main>
      <h1>task-flow</h1>
      <p>API 연결: {status}</p>
    </main>
  )
}

export default App
