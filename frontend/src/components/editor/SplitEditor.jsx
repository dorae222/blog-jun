import { useState, useCallback, useRef, useEffect } from 'react'
import MarkdownEditor from './MarkdownEditor'
import MarkdownRenderer from '../blog/MarkdownRenderer'

export default function SplitEditor({ content, onChange }) {
  const [markdown, setMarkdown] = useState(content || '')
  const debounceRef = useRef(null)

  // 외부 content가 바뀌면 동기화
  useEffect(() => {
    setMarkdown(content || '')
  }, [content])

  const handleChange = useCallback((value) => {
    setMarkdown(value)
    // 디바운스: 300ms 후 부모에 전달
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onChange?.(value)
    }, 300)
  }, [onChange])

  return (
    <div className="flex flex-1 overflow-hidden h-full">
      {/* 좌측: 마크다운 소스 */}
      <div className="w-1/2 flex flex-col border-r" style={{ borderColor: 'var(--border)' }}>
        <div
          className="px-3 py-1.5 text-xs font-semibold border-b flex items-center gap-2"
          style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
        >
          <span>Markdown</span>
        </div>
        <div className="flex-1 overflow-hidden">
          <MarkdownEditor value={markdown} onChange={handleChange} />
        </div>
      </div>

      {/* 우측: 실시간 프리뷰 */}
      <div className="w-1/2 flex flex-col">
        <div
          className="px-3 py-1.5 text-xs font-semibold border-b flex items-center gap-2"
          style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
        >
          <span>Preview</span>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <MarkdownRenderer content={markdown} />
        </div>
      </div>
    </div>
  )
}
