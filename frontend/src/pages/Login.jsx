import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import useAuth from '../hooks/useAuth'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  // 보호된 화면(/notes, /editor 등)에서 튕겨 왔으면 로그인 뒤 그 자리로 돌려보낸다. 같은 사이트 경로만 허용.
  const nextRaw = params.get('next') || ''
  const next = nextRaw.startsWith('/') && !nextRaw.startsWith('//') ? nextRaw : '/dashboard'

  // Enter 제출이 안 먹던 문제: 브라우저/비밀번호 관리자 자동완성은 React onChange 없이 값만 채워서
  // 상태(username/password)가 비어 있는 채로 제출될 수 있다. 제출 시점에는 폼 요소의 실제 값을 읽는다.
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    const fd = new FormData(e.currentTarget)
    const u = String(fd.get('username') ?? username).trim()
    const p = String(fd.get('password') ?? password)
    if (!u || !p) { toast.error('아이디와 비밀번호를 입력하세요'); return }
    setLoading(true)
    try {
      await login(u, p)
      toast.success('로그인 성공')
      navigate(next, { replace: true })
    } catch {
      toast.error('로그인 실패')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="max-w-md mx-auto px-4 py-12 sm:py-24"
    >
      <div className="p-8 rounded-2xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
        <h1 className="text-2xl font-bold mb-6 text-center" style={{ color: 'var(--text)' }}>Login</h1>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="login-username" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Username</label>
            <input
              id="login-username"
              name="username"
              autoComplete="username"
              autoCapitalize="none"
              autoFocus
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border outline-none focus:ring-2 focus:ring-primary-500"
              style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
              required
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Password</label>
            <input
              id="login-password"
              name="password"
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border outline-none focus:ring-2 focus:ring-primary-500"
              style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </motion.div>
  )
}
