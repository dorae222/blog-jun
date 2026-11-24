import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh/`, { refresh })
          localStorage.setItem('access_token', data.access)
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
          original.headers.Authorization = `Bearer ${data.access}`
          return client(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    // 429는 화면을 비우지 말고 이유를 알린다. 이전에는 조용히 실패해서
    // 목록이 통째로 빈 화면으로 보였고, 콘텐츠가 없는 것과 구분이 안 됐다.
    if (error.response?.status === 429) {
      const wait = error.response.data?.detail || '잠시 후 다시 시도해 주세요.'
      window.dispatchEvent(new CustomEvent('api:throttled', { detail: wait }))
      error.isThrottled = true
      return Promise.reject(error)
    }

    // Retry on network errors or 5xx (except 401 which is handled above)
    if (!original._retryNetwork && error.response?.status !== 401 &&
      (error.code === 'ECONNABORTED' || !error.response || error.response.status >= 500)) {
      original._retryNetwork = true
      await new Promise(r => setTimeout(r, 1000))
      return client(original)
    }
    return Promise.reject(error)
  }
)

export default client
