// 通用请求封装

const apiBase = import.meta.env.VITE_API_BASE || ''

export async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers })
  const rawText = response.status === 204 ? '' : await response.text()
  let data = null
  if (rawText) {
    try {
      data = JSON.parse(rawText)
    } catch (error) {
      data = { detail: rawText }
    }
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.error || '请求失败')
  }
  return data
}
