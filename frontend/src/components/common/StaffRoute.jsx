import { Navigate, useLocation } from 'react-router-dom'
import useAuth from '../../hooks/useAuth'

/**
 * staff만 들어올 수 있는 화면을 감싼다.
 * 비로그인 → 로그인 화면으로(돌아올 경로를 next로 넘김), 로그인했지만 staff가 아니면 → 404처럼 홈으로.
 * 인증 상태를 아직 모르면(loading) 아무것도 그리지 않아, 남의 화면이 잠깐 비치는 일을 막는다.
 */
export default function StaffRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm" style={{ color: 'var(--text-secondary)' }}>
        Loading...
      </div>
    )
  }
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  if (!user.is_staff) return <Navigate to="/" replace />
  return children
}
