// API 호출은 이 모듈을 통해서만 한다.
const BASE_URL = '/api'

// 실패 안내 문구. (D-027) 로그인 관련 문구는 제안이며 아직 확정이 아니다.
export const MESSAGES = {
  network: '서버에 연결할 수 없습니다. API 가 실행 중인지 확인하세요.',
  saveFailed: '저장하지 못했습니다. 다시 시도하세요.',
  notFound: '이미 삭제된 카드입니다. 목록을 새로 불러왔습니다.',
  listFailed: '목록을 불러오지 못했습니다.',
  sessionExpired: '로그인이 만료되었습니다. 다시 로그인하세요.',
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, options)
  } catch {
    throw new ApiError(MESSAGES.network, 0)
  }
  if (!response.ok) {
    // 로그인이 없거나 만료되면 401 이다. 화면이 로그인 화면으로 돌아가게 한다. (D-033)
    if (response.status === 401) throw new ApiError(MESSAGES.sessionExpired, 401)
    const message = response.status === 404 ? MESSAGES.notFound : MESSAGES.saveFailed
    throw new ApiError(message, response.status)
  }
  return response.status === 204 ? null : response.json()
}

// 서버의 오류 문구(detail)를 읽는다. 입력 검사 오류는 목록이라 첫 번째 문구만 쓴다.
function readDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg.replace(/^Value error, /, '')
  return ''
}

// 가입 · 로그인은 서버가 알려 주는 문구를 그대로 보여 준다. (D-038)
async function authRequest(path, options) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, options)
  } catch {
    throw new ApiError(MESSAGES.network, 0)
  }
  if (!response.ok) {
    let detail = ''
    try {
      detail = readDetail((await response.json()).detail)
    } catch {
      // 본문이 없으면 아래에서 저장 실패 문구를 쓴다.
    }
    const message = response.status >= 500 || !detail ? MESSAGES.saveFailed : detail
    throw new ApiError(message, response.status)
  }
  return response.status === 204 ? null : response.json()
}

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export function getHealth() {
  return request('/health')
}

export function getMe() {
  return authRequest('/auth/me')
}

export function register({ email, password }) {
  return authRequest('/auth/register', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  })
}

export function login({ email, password }) {
  return authRequest('/auth/login', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  })
}

export function logout() {
  return authRequest('/auth/logout', { method: 'POST' })
}

export function getTasks() {
  return request('/tasks')
}

export function createTask({ title, description }) {
  return request('/tasks', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ title, description }),
  })
}

export function updateStatus(id, status) {
  return request(`/tasks/${id}/status`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify({ status }),
  })
}

export function updateTask(id, { title, description }) {
  return request(`/tasks/${id}`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify({ title, description }),
  })
}

export function deleteTask(id) {
  return request(`/tasks/${id}`, { method: 'DELETE' })
}
