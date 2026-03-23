import { useState, useEffect, useRef, useCallback } from 'react'
import { Search, Link2, X } from 'lucide-react'
import { searchPosts } from '../../api/posts'

export default function PostLinkModal({ isOpen, onClose, onInsert }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(0)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const timerRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setResults([])
      setSelected(0)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Debounced search
  useEffect(() => {
    if (!query.trim()) { setResults([]); return }
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const { data } = await searchPosts(query)
        setResults(data.results || data || [])
        setSelected(0)
      } catch { setResults([]) }
      setLoading(false)
    }, 300)
    return () => clearTimeout(timerRef.current)
  }, [query])

  // Keyboard: Escape, ArrowUp/Down, Enter
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') { onClose(); return }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)) }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)) }
    if (e.key === 'Enter' && results[selected]) {
      e.preventDefault()
      handleSelect(results[selected])
    }
  }, [results, selected, onClose])

  const handleSelect = (post) => {
    onInsert(`[${post.title}](/post/${post.slug})`)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div className="w-full max-w-lg rounded-2xl overflow-hidden shadow-2xl"
        style={{ background: 'var(--card-bg)' }}
        onClick={e => e.stopPropagation()}
        onKeyDown={handleKeyDown}>
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <Search size={18} style={{ color: 'var(--text-secondary)' }} />
          <input ref={inputRef} value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search posts to link..."
            className="flex-1 bg-transparent outline-none text-sm" style={{ color: 'var(--text)' }} />
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
            <X size={16} style={{ color: 'var(--text-secondary)' }} />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-64 overflow-y-auto">
          {loading && <div className="px-4 py-3 text-sm" style={{ color: 'var(--text-secondary)' }}>Searching...</div>}
          {!loading && results.length === 0 && query && (
            <div className="px-4 py-6 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
              No posts found
            </div>
          )}
          {results.map((post, i) => (
            <button key={post.slug} onClick={() => handleSelect(post)}
              className="w-full text-left px-4 py-3 flex items-center gap-3 transition-colors"
              style={{
                background: i === selected ? 'var(--bg-secondary)' : 'transparent',
              }}
              onMouseEnter={() => setSelected(i)}>
              <Link2 size={14} className="shrink-0" style={{ color: 'var(--text-secondary)' }} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{post.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  {post.category?.name && (
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                      style={{ background: `${post.category?.color || '#6366f1'}15`, color: post.category?.color || '#6366f1' }}>
                      {post.category.name}
                    </span>
                  )}
                  {post.summary && (
                    <span className="text-[11px] truncate" style={{ color: 'var(--text-secondary)' }}>
                      {post.summary.slice(0, 60)}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Footer hint */}
        <div className="px-4 py-2 border-t text-[11px] flex gap-4" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
          <span>Arrow keys to navigate</span>
          <span>Enter to select</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  )
}
