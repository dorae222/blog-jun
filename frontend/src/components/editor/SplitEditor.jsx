import { useState, useCallback, useRef, useEffect } from 'react'
import MarkdownEditor from './MarkdownEditor'
import MarkdownRenderer from '../blog/MarkdownRenderer'

/**
 * 좌: 마크다운 소스, 우: 미리보기. 모바일(좁은 화면)에서는 위아래로 쌓는다.
 * 부모에는 300ms 디바운스로 알린다. 부모에서 내려온 content가 "내가 마지막으로 보낸 값"이면
 * 되돌려 받지 않는다(타이핑 중에 이전 값으로 덮이는 것을 막기 위함). 템플릿 적용·복구처럼
 * 밖에서 내용을 바꾼 경우에만 동기화한다.
 */
export default function SplitEditor({ content, onChange, onImageUpload, editorRef }) {
  const [markdown, setMarkdown] = useState(content || '')
  const debounceRef = useRef(null)
  const lastEmitted = useRef(content || '')

  useEffect(() => {
    if ((content || '') !== lastEmitted.current) {
      lastEmitted.current = content || ''
      setMarkdown(content || '')
    }
  }, [content])

  // 보기 모드를 바꾸느라 언마운트될 때 디바운스에 걸린 마지막 입력을 버리지 않고 넘긴다.
  const pendingRef = useRef(null)
  const onChangeRef = useRef(onChange)
  useEffect(() => { onChangeRef.current = onChange }, [onChange])
  useEffect(() => () => {
    clearTimeout(debounceRef.current)
    if (pendingRef.current !== null) onChangeRef.current?.(pendingRef.current)
  }, [])

  const handleChange = useCallback((value) => {
    setMarkdown(value)
    pendingRef.current = value
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      lastEmitted.current = value
      pendingRef.current = null
      onChangeRef.current?.(value)
    }, 300)
  }, [])

  const head = 'px-3 py-1.5 text-xs font-semibold border-b flex items-center gap-2'
  const headStyle = { borderColor: 'var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }

  return (
    <div className="flex flex-col md:flex-row flex-1 overflow-hidden h-full">
      <div className="h-1/2 md:h-auto md:w-1/2 flex flex-col border-b md:border-b-0 md:border-r" style={{ borderColor: 'var(--border)' }}>
        <div className={head} style={headStyle}><span>Markdown</span></div>
        <div className="flex-1 overflow-hidden">
          <MarkdownEditor ref={editorRef} value={markdown} onChange={handleChange} onImageUpload={onImageUpload} />
        </div>
      </div>
      <div className="h-1/2 md:h-auto md:w-1/2 flex flex-col">
        <div className={head} style={headStyle}><span>Preview</span></div>
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div data-toc-root><MarkdownRenderer content={markdown} /></div>
        </div>
      </div>
    </div>
  )
}
