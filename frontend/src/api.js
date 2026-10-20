// API 호출은 이 모듈을 통해서만 한다.
const BASE_URL = '/api'

async function request(path, options) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, options)
  } catch {
    throw new Error('API 에 연결할 수 없습니다')
  }
  if (!response.ok) {
    throw new Error(`API 응답 오류: ${response.status}`)
  }
  return response.status === 204 ? null : response.json()
}

export function getHealth() {
  return request('/health')
}

export function getTasks() {
  return request('/tasks')
}

export function createTask({ title, description }) {
  return request('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })
}

export function updateStatus(id, status) {
  return request(`/tasks/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}
