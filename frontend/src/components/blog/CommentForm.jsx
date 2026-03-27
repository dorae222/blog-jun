import { useState } from 'react'
import { Send } from 'lucide-react'

export default function CommentForm({ onSubmit, placeholder = '댓글을 남겨보세요...', initialValue = '', autoFocus = false }) {
  const [content, setContent] = useState(initialValue)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const trimmed = content.trim()
    if (!trimmed) return

    setSubmitting(true)
    try {
      await onSubmit(trimmed)
      setContent('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 sm:gap-3 items-end">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        maxLength={2000}
        rows={2}
        autoFocus={autoFocus}
        className="flex-1 resize-none rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 text-sm border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30"
        style={{
          background: 'var(--bg-secondary)',
          color: 'var(--text)',
          borderColor: 'var(--border)',
        }}
      />
      <button
        type="submit"
        disabled={!content.trim() || submitting}
        className="shrink-0 p-2.5 sm:p-3 rounded-xl transition-all disabled:opacity-40"
        style={{ background: 'var(--primary-600, #2563eb)', color: '#fff' }}
      >
        <Send size={18} />
      </button>
    </form>
  )
}
