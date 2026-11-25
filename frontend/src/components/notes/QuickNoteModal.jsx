import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { StickyNote, Hash, CornerDownLeft } from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import useWorkspace from '../../hooks/useWorkspace'
import useFocusTrap from '../../hooks/useFocusTrap'
import { createNote } from '../../api/notes'
import { parseQuickNote, noteTitleFrom } from '../../utils/noteText'

/**
 * 어디서든 여는 빠른 메모(단축키 m, 헤더 버튼).
 * 한 줄 쓰고 Enter면 저장, `#태그`는 태그로 뺀다. Shift+Enter는 줄바꿈(길게 적고 싶을 때).
 * 저장에 실패하면 입력을 지우지 않는다(다시 Enter만 누르면 되게).
 */
export default function QuickNoteModal() {
  const user = useAuth((s) => s.user)
  const open = useWorkspace((s) => s.quickNoteOpen)
  const close = useWorkspace((s) => s.closeQuickNote)
  const bumpNotes = useWorkspace((s) => s.bumpNotes)
  const navigate = useNavigate()
  const [value, setValue] = useState('')
  const [saving, setSaving] = useState(false)
  const boxRef = useRef(null)
  const inputRef = useRef(null)

  useFocusTrap(boxRef, open, close)

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30)
  }, [open])

  if (!user?.is_staff) return null

  const { text, tags } = parseQuickNote(value)

  const save = async () => {
    if (!text || saving) return
    setSaving(true)
    try {
      const { data } = await createNote({ title: noteTitleFrom(text), content: text, tags })
      setValue('')
      close()
      bumpNotes()
      toast.success((t) => (
        <span className="text-sm">
          메모를 저장했어요{' '}
          <button
            className="underline text-primary-600"
            onClick={() => { toast.dismiss(t.id); navigate(`/notes?id=${data.id}`) }}
          >
            열기
          </button>
        </span>
      ), { duration: 8000 })
    } catch {
      toast.error('메모 저장에 실패했어요. 내용은 그대로 남겨 뒀어요.')
    } finally {
      setSaving(false)
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      save()
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[15vh]"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/40" onClick={close} />
          <motion.div
            ref={boxRef}
            role="dialog" aria-modal="true" aria-labelledby="quick-note-title"
            className="relative w-full max-w-lg rounded-2xl border shadow-2xl p-4"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            initial={{ y: -10, scale: 0.98 }} animate={{ y: 0, scale: 1 }} exit={{ y: -10, scale: 0.98 }}
            transition={{ duration: 0.15 }}
          >
            <div className="flex items-center gap-2 mb-3">
              <StickyNote size={16} className="text-primary-600" />
              <h2 id="quick-note-title" className="text-sm font-semibold" style={{ color: 'var(--text)' }}>빠른 메모</h2>
              <span className="ml-auto text-[11px]" style={{ color: 'var(--text-secondary)' }}>
                Enter 저장 · Shift+Enter 줄바꿈 · Esc 닫기
              </span>
            </div>
            <textarea
              ref={inputRef}
              rows={value.includes('\n') ? 4 : 1}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="떠오른 걸 적어 두세요  #태그"
              aria-label="메모 내용"
              className="w-full resize-none rounded-lg border px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500"
              style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
            />
            <div className="mt-2 flex items-center gap-2 min-h-[1.75rem]">
              <div className="flex flex-wrap gap-1">
                {tags.map((t) => (
                  <span key={t} className="inline-flex items-center gap-0.5 text-xs px-2 py-0.5 rounded-full bg-primary-50 text-primary-700">
                    <Hash size={10} />{t}
                  </span>
                ))}
              </div>
              <button
                onClick={save}
                disabled={!text || saving}
                className="ml-auto inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40"
              >
                <CornerDownLeft size={14} /> {saving ? '저장 중' : '저장'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
