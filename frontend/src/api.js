// API 호출은 이 모듈을 통해서만 한다.
const BASE_URL = '/api'

export async function getHealth() {
  const response = await fetch(`${BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`API 응답 오류: ${response.status}`)
  }
  return response.json()
}
