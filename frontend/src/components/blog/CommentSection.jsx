import { useState, useEffect, useCallback } from 'react'
import { MessageCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuth from '../../hooks/useAuth'
import { getComments, createComment, updateComment, deleteComment } from '../../api/comments'
import { getGithubLoginUrl, getGoogleLoginUrl } from '../../api/auth'
import CommentForm from './CommentForm'
import CommentItem from './CommentItem'

export default function CommentSection({ postSlug }) {
  const user = useAuth((s) => s.user)
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchComments = useCallback(async () => {
    try {
      const { data } = await getComments(postSlug)
      setComments(data)
    } catch {
      // 댓글 로드 실패 시 조용히 처리
    } finally {
      setLoading(false)
    }
  }, [postSlug])

  useEffect(() => {
    fetchComments()
  }, [fetchComments])

  const handleCreate = async (content) => {
    try {
      await createComment(postSlug, { content })
      await fetchComments()
      toast.success('댓글이 등록되었습니다')
    } catch (err) {
      const detail = err.response?.data?.detail
      toast.error(detail || '댓글 등록에 실패했습니다')
    }
  }

  const handleReply = async (parentId, content) => {
    try {
      await createComment(postSlug, { content, parent: parentId })
      await fetchComments()
      toast.success('답글이 등록되었습니다')
    } catch (err) {
      const detail = err.response?.data?.detail
      toast.error(detail || '답글 등록에 실패했습니다')
    }
  }

  const handleEdit = async (id, content) => {
    try {
      await updateComment(id, { content })
      await fetchComments()
      toast.success('댓글이 수정되었습니다')
    } catch {
      toast.error('댓글 수정에 실패했습니다')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return
    try {
      await deleteComment(id)
      await fetchComments()
      toast.success('댓글이 삭제되었습니다')
    } catch {
      toast.error('댓글 삭제에 실패했습니다')
    }
  }

  const handleSocialLogin = (provider) => {
    // 현재 페이지 저장 (로그인 후 복귀용)
    localStorage.setItem('login_return_to', window.location.pathname)
    if (provider === 'github') {
      window.location.href = getGithubLoginUrl()
    } else {
      window.location.href = getGoogleLoginUrl()
    }
  }

  const totalCount = comments.reduce((acc, c) => acc + 1 + (c.replies?.length || 0), 0)

  return (
    <div className="mt-12 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-6">
        <MessageCircle size={20} style={{ color: 'var(--text)' }} />
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
          댓글 {totalCount > 0 && <span className="text-sm font-normal" style={{ color: 'var(--text-tertiary)' }}>({totalCount})</span>}
        </h2>
      </div>

      {/* 댓글 작성 영역 */}
      {user ? (
        <div className="mb-8">
          <CommentForm onSubmit={handleCreate} />
        </div>
      ) : (
        <div
          className="mb-8 p-6 rounded-xl text-center border"
          style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
        >
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
            로그인하여 댓글을 남겨보세요
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => handleSocialLogin('github')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors hover:opacity-90"
              style={{ background: '#24292f', color: '#fff' }}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
              GitHub
            </button>
            <button
              onClick={() => handleSocialLogin('google')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors border hover:opacity-90"
              style={{ background: 'var(--card-bg)', color: 'var(--text)', borderColor: 'var(--border)' }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Google
            </button>
          </div>
        </div>
      )}

      {/* 댓글 목록 */}
      {loading ? (
        <div className="text-center py-8" style={{ color: 'var(--text-tertiary)' }}>
          <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm">댓글 불러오는 중...</p>
        </div>
      ) : comments.length === 0 ? (
        <p className="text-center py-8 text-sm" style={{ color: 'var(--text-tertiary)' }}>
          아직 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!
        </p>
      ) : (
        <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              onReply={handleReply}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
