import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import useAuth from './useAuth'
import useWorkspace from './useWorkspace'
import { isTypingTarget } from '../utils/noteText'

/**
 * staff 전용 전역 단축키.
 *   n → 새 글(/editor),  m → 빠른 메모
 * 입력 중(input/textarea/contenteditable)이거나 수정키가 눌렸거나, 다른 모달이 떠 있으면 무시한다.
 * 에디터 화면에서는 n을 끈다(작성 중인 글에서 실수로 나가지 않게).
 */
export default function useWorkspaceHotkeys() {
  const user = useAuth((s) => s.user)
  const openQuickNote = useWorkspace((s) => s.openQuickNote)
  const quickNoteOpen = useWorkspace((s) => s.quickNoteOpen)
  const navigate = useNavigate()
  const { pathname } = useLocation()

  useEffect(() => {
    if (!user?.is_staff) return
    const onKey = (e) => {
      if (e.defaultPrevented || e.repeat) return
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (isTypingTarget(e.target) || isTypingTarget(document.activeElement)) return
      if (quickNoteOpen || document.querySelector('[aria-modal="true"]')) return
      const key = e.key.toLowerCase()
      if (key === 'n' && !pathname.startsWith('/editor')) {
        e.preventDefault()
        navigate('/editor')
      } else if (key === 'm') {
        e.preventDefault()
        openQuickNote()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [user, pathname, navigate, openQuickNote, quickNoteOpen])
}
