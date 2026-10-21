// API 호출은 이 모듈을 통해서만 한다.
const BASE_URL = '/api'

// 실패 안내 문구. (D-027)
export const MESSAGES = {
  network: '서버에 연결할 수 없습니다. API 가 실행 중인지 확인하세요.',
  saveFailed: '저장하지 못했습니다. 다시 시도하세요.',
  notFound: '이미 삭제된 카드입니다. 목록을 새로 불러왔습니다.',
  listFailed: '목록을 불러오지 못했습니다.',
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
    const message = response.status === 404 ? MESSAGES.notFound : MESSAGES.saveFailed
    throw new ApiError(message, response.status)
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

export function updateTask(id, { title, description }) {
  return request(`/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })
}

export function deleteTask(id) {
  return request(`/tasks/${id}`, { method: 'DELETE' })
}
