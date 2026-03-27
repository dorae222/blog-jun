import client from './client'

export const login = (username, password) =>
  client.post('/auth/login/', { username, password })

export const getCurrentUser = () => client.get('/auth/me/')

/**
 * 소셜 로그인 URL 반환.
 * allauth 플로우: 백엔드 /accounts/github/login/ → GitHub OAuth → 콜백 → JWT
 */
const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || ''

export const getGithubLoginUrl = () =>
  `${API_ORIGIN}/accounts/github/login/`

export const getGoogleLoginUrl = () =>
  `${API_ORIGIN}/accounts/google/login/`
