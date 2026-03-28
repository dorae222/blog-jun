import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Flame } from 'lucide-react'
import { searchPosts, getPopularPosts } from '../../api/posts'
import InlineMath from './InlineMath'

const isMac = typeof navigator !== 'undefined' && navigator.platform?.includes('Mac')

export default function SearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [popularPosts, setPopularPosts] = useState([])
  const inputRef = useRef(null)
  const listRef = useRef(null)
  const debounceRef = useRef(null)
  const navigate = useNavigate()

  // 인기글 로드
  useEffect(() => {
    if (isOpen) {
      getPopularPosts(5)
        .then((r) => setPopularPosts(r.data || []))
        .catch(() => {})
    }
  }, [isOpen])

  // 모달 열릴 때 초기화 + autofocus
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setResults([])
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // 디바운스 검색
  const doSearch = useCallback(async (q) => {
    if (!q.trim()) {
      setResults([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const res = await searchPosts(q.trim())
      const data = res.data || []
      setResults(data.slice(0, 8))
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleInputChange = (e) => {
    const val = e.target.value
    setQuery(val)
    setSelectedIndex(0)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => doSearch(val), 300)
  }

  // cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  // 표시할 아이템 결정
  const displayItems = query.trim() ? results : popularPosts
  const showPopularLabel = !query.trim() && popularPosts.length > 0

  // 키보드 네비게이션
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.min(prev + 1, displayItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (displayItems[selectedIndex]) {
        navigate(`/post/${displayItems[selectedIndex].slug}`)
        onClose()
      }
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  // 선택된 항목이 보이도록 스크롤
  useEffect(() => {
    if (listRef.current) {
      const selected = listRef.current.children[showPopularLabel ? selectedIndex + 1 : selectedIndex]
      if (selected) {
        selected.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [selectedIndex, showPopularLabel])

  // 오버레이 클릭 시 닫기
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  // body 스크롤 잠금
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={handleOverlayClick}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden"
            style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}
          >
            {/* 검색 입력 */}
            <div className="flex items-center gap-3 px-4 py-3"
              style={{ borderBottom: '1px solid var(--border)' }}>
              <Search size={18} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="검색어를 입력하세요..."
                className="flex-1 bg-transparent outline-none text-sm"
                style={{ color: 'var(--text)' }}
              />
              {loading && (
                <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
              )}
            </div>

            {/* 결과 리스트 */}
            <div ref={listRef} className="max-h-[360px] overflow-y-auto py-1">
              {showPopularLabel && (
                <div className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium"
                  style={{ color: 'var(--text-secondary)' }}>
                  <Flame size={12} /> 인기 글
                </div>
              )}

              {displayItems.length === 0 && query.trim() && !loading && (
                <div className="px-4 py-8 text-center text-sm"
                  style={{ color: 'var(--text-secondary)' }}>
                  검색 결과가 없습니다.
                </div>
              )}

              {displayItems.map((item, idx) => (
                <button
                  key={item.slug}
                  onClick={() => {
                    navigate(`/post/${item.slug}`)
                    onClose()
                  }}
                  className="flex flex-col gap-0.5 w-full text-left px-4 py-2.5 transition-colors"
                  style={{
                    minHeight: '44px',
                    background: idx === selectedIndex ? 'var(--primary-50, rgba(99,102,241,0.06))' : 'transparent',
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium line-clamp-1" style={{ color: 'var(--text)' }}>
                      {item.title}
                    </span>
                    {item.category_name && (
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded-full shrink-0"
                        style={{
                          background: item.category_color ? `${item.category_color}18` : 'var(--border)',
                          color: item.category_color || 'var(--text-secondary)',
                        }}
                      >
                        {item.category_name}
                      </span>
                    )}
                  </div>
                  {item.summary && (
                    <p className="text-xs line-clamp-1" style={{ color: 'var(--text-secondary)' }}>
                      <InlineMath text={item.summary} />
                    </p>
                  )}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-0.5">
                      {item.tags.slice(0, 3).map((tag) => (
                        <span key={typeof tag === 'string' ? tag : tag.name}
                          className="text-[10px] px-1 py-0 rounded"
                          style={{ color: 'var(--text-secondary)', background: 'var(--border)' }}>
                          #{typeof tag === 'string' ? tag : tag.name}
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>

            {/* 하단 힌트 */}
            <div className="flex items-center gap-3 px-4 py-2 text-[11px]"
              style={{ borderTop: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
              <span>
                <kbd className="px-1 py-0.5 rounded border text-[10px]"
                  style={{ borderColor: 'var(--border)' }}>
                  {isMac ? '⌘K' : 'Ctrl+K'}
                </kbd>
                {' '}열기
              </span>
              <span>
                <kbd className="px-1 py-0.5 rounded border text-[10px]"
                  style={{ borderColor: 'var(--border)' }}>Enter</kbd>
                {' '}선택
              </span>
              <span>
                <kbd className="px-1 py-0.5 rounded border text-[10px]"
                  style={{ borderColor: 'var(--border)' }}>↑↓</kbd>
                {' '}이동
              </span>
              <span>
                <kbd className="px-1 py-0.5 rounded border text-[10px]"
                  style={{ borderColor: 'var(--border)' }}>Esc</kbd>
                {' '}닫기
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
