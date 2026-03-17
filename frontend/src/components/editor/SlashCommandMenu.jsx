import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import {
  Heading1, Heading2, Heading3, Type, Quote, Minus, AlertCircle,
  Image, Video, Table, Code, Calculator, CheckSquare
} from 'lucide-react'

const SLASH_ITEMS = [
  { category: 'Basic', items: [
    { id: 'heading1', label: 'Heading 1', desc: '대제목', icon: Heading1, command: (editor) => editor.chain().focus().toggleHeading({ level: 1 }).run() },
    { id: 'heading2', label: 'Heading 2', desc: '중제목', icon: Heading2, command: (editor) => editor.chain().focus().toggleHeading({ level: 2 }).run() },
    { id: 'heading3', label: 'Heading 3', desc: '소제목', icon: Heading3, command: (editor) => editor.chain().focus().toggleHeading({ level: 3 }).run() },
    { id: 'text', label: 'Text', desc: '일반 텍스트', icon: Type, command: (editor) => editor.chain().focus().setParagraph().run() },
    { id: 'quote', label: 'Quote', desc: '인용 블록', icon: Quote, command: (editor) => editor.chain().focus().toggleBlockquote().run() },
    { id: 'divider', label: 'Divider', desc: '구분선', icon: Minus, command: (editor) => editor.chain().focus().setHorizontalRule().run() },
    { id: 'callout', label: 'Callout', desc: '콜아웃 박스', icon: AlertCircle, command: (editor) => editor.chain().focus().toggleBlockquote().run() },
  ]},
  { category: 'Media', items: [
    { id: 'image', label: 'Image', desc: '이미지 업로드', icon: Image, command: null },
    { id: 'video', label: 'Video', desc: '비디오 임베드', icon: Video, command: null },
    { id: 'table', label: 'Table', desc: '테이블 삽입', icon: Table, command: (editor) => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() },
  ]},
  { category: 'Advanced', items: [
    { id: 'code', label: 'Code Block', desc: '코드 블록', icon: Code, command: (editor) => editor.chain().focus().toggleCodeBlock().run() },
    { id: 'math', label: 'Math Block', desc: 'KaTeX 수식', icon: Calculator, command: null },
    { id: 'todo', label: 'Todo List', desc: '체크리스트', icon: CheckSquare, command: (editor) => editor.chain().focus().toggleTaskList().run() },
  ]},
]

export default function SlashCommandMenu({ editor, query, onSelect, onClose }) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const menuRef = useRef(null)
  const itemRefs = useRef([])

  // query로 필터링된 아이템 목록
  const filteredGroups = useMemo(() => {
    const q = (query || '').toLowerCase()
    return SLASH_ITEMS
      .map(group => ({
        ...group,
        items: group.items.filter(item =>
          item.label.toLowerCase().includes(q) ||
          item.desc.toLowerCase().includes(q) ||
          item.id.toLowerCase().includes(q)
        ),
      }))
      .filter(group => group.items.length > 0)
  }, [query])

  // 전체 flat 아이템 목록 (키보드 네비게이션용)
  const allItems = useMemo(() =>
    filteredGroups.flatMap(g => g.items),
    [filteredGroups]
  )

  // 필터 변경 시 선택 초기화
  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  // 선택된 아이템이 보이도록 스크롤
  useEffect(() => {
    itemRefs.current[selectedIndex]?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  // 키보드 네비게이션
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => (prev + 1) % allItems.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => (prev - 1 + allItems.length) % allItems.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (allItems[selectedIndex]) {
        onSelect(allItems[selectedIndex])
      }
    } else if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }, [allItems, selectedIndex, onSelect, onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown, true)
    return () => document.removeEventListener('keydown', handleKeyDown, true)
  }, [handleKeyDown])

  // 메뉴 바깥 클릭 시 닫기
  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [onClose])

  if (allItems.length === 0) {
    return (
      <div
        ref={menuRef}
        className="slash-menu rounded-lg shadow-lg border p-3 text-sm"
        style={{
          background: 'var(--bg)',
          borderColor: 'var(--border)',
          color: 'var(--text-secondary)',
        }}
      >
        No results
      </div>
    )
  }

  let globalIndex = 0

  return (
    <div
      ref={menuRef}
      className="slash-menu rounded-lg shadow-lg border overflow-hidden"
      style={{
        background: 'var(--bg)',
        borderColor: 'var(--border)',
        maxHeight: '320px',
        width: '280px',
        overflowY: 'auto',
      }}
    >
      {filteredGroups.map(group => (
        <div key={group.category}>
          <div
            className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-secondary)', background: 'var(--bg-secondary)' }}
          >
            {group.category}
          </div>
          {group.items.map(item => {
            const idx = globalIndex++
            const Icon = item.icon
            const isSelected = idx === selectedIndex
            return (
              <button
                key={item.id}
                ref={el => itemRefs.current[idx] = el}
                className="w-full flex items-center gap-3 px-3 py-2 text-left transition-colors"
                style={{
                  background: isSelected ? 'var(--bg-secondary)' : 'transparent',
                  color: 'var(--text)',
                }}
                onMouseEnter={() => setSelectedIndex(idx)}
                onClick={() => onSelect(item)}
              >
                <div
                  className="w-8 h-8 rounded flex items-center justify-center shrink-0"
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                >
                  <Icon size={16} style={{ color: 'var(--text-secondary)' }} />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{item.label}</div>
                  <div className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>{item.desc}</div>
                </div>
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}

export { SLASH_ITEMS }
