// 모든 화면 상태에서 보이는 머리글. 로그인한 사용자가 있으면 이메일과 로그아웃을 함께 보인다. (D-039)
function Header({ user, onLogout }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          TF
        </span>
        <div>
          <h1>Task Flow</h1>
          <p>내 작업을 상태별로 관리합니다</p>
        </div>
      </div>
      {user && (
        <div className="user-bar">
          <span className="user-chip">
            <small>로그인 사용자</small>
            <strong>{user.email}</strong>
          </span>
          <button type="button" onClick={onLogout}>
            로그아웃
          </button>
        </div>
      )}
    </header>
  )
}

export default Header
