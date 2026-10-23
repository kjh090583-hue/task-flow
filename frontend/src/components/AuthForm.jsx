import { useState } from 'react'

// 로그인 · 가입 화면. 화면 문구는 제안이며 아직 확정이 아니다.
function AuthForm({ onLogin, onRegister }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const isRegister = mode === 'register'

  function switchMode() {
    setMode(isRegister ? 'login' : 'register')
    setMessage('')
    setPassword('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    // 비었으면 요청을 보내지 않고 안내한다. 서버도 다시 검사한다. (D-003)
    if (!email.trim()) {
      setMessage('이메일을 입력하세요')
      return
    }
    if (!password) {
      setMessage('비밀번호를 입력하세요')
      return
    }
    if (isRegister && password.length < 8) {
      setMessage('비밀번호는 8자 이상이어야 합니다')
      return
    }
    setSubmitting(true)
    setMessage('')
    try {
      await (isRegister ? onRegister : onLogin)({ email, password })
    } catch (error) {
      // 실패하면 입력을 남긴다. (D-021)
      setMessage(error.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>{isRegister ? '가입' : '로그인'}</h2>
      <input
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="이메일"
        aria-label="이메일"
        autoComplete="email"
      />
      <input
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        placeholder={isRegister ? '비밀번호 (8자 이상)' : '비밀번호'}
        aria-label="비밀번호"
        autoComplete={isRegister ? 'new-password' : 'current-password'}
      />
      <button type="submit" disabled={submitting}>
        {isRegister ? '가입' : '로그인'}
      </button>
      {message && <p role="alert">{message}</p>}
      <p className="auth-switch">
        {isRegister ? '이미 계정이 있나요?' : '계정이 없나요?'}{' '}
        <button type="button" className="link" onClick={switchMode}>
          {isRegister ? '로그인' : '가입하기'}
        </button>
      </p>
    </form>
  )
}

export default AuthForm
