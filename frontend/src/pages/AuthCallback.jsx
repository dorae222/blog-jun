import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import useAuth from '../hooks/useAuth'

export default function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const handleSocialCallback = useAuth((s) => s.handleSocialCallback)
  const [error, setError] = useState(null)

  useEffect(() => {
    const access = searchParams.get('access')
    const refresh = searchParams.get('refresh')
    const errorParam = searchParams.get('error')

    if (errorParam) {
      setError('로그인에 실패했습니다. 다시 시도해주세요.')
      return
    }

    if (access && refresh) {
      handleSocialCallback(access, refresh)
        .then(() => {
          // 로그인 전 페이지로 복귀 (없으면 홈으로)
          const returnTo = localStorage.getItem('login_return_to') || '/'
          localStorage.removeItem('login_return_to')
          navigate(returnTo, { replace: true })
        })
        .catch(() => {
          setError('토큰 처리 중 오류가 발생했습니다.')
        })
    } else {
      setError('인증 정보가 누락되었습니다.')
    }
  }, [searchParams, handleSocialCallback, navigate])

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="text-center" style={{ color: 'var(--text-secondary)' }}>
          <p className="text-lg mb-4">{error}</p>
          <button
            onClick={() => navigate('/', { replace: true })}
            className="px-4 py-2 rounded-lg text-sm"
            style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-center" style={{ color: 'var(--text-secondary)' }}>
        <div className="w-8 h-8 border-2 border-current border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p>로그인 처리 중...</p>
      </div>
    </div>
  )
}
