import { useEffect, useImperativeHandle, useRef } from 'react'
import toast from 'react-hot-toast'

/**
 * 마크다운 소스 편집기(textarea).
 * onImageUpload(file) → url 을 넘기면 이미지 붙여넣기·끌어놓기를 받아 커서 자리에 넣는다.
 * 업로드가 끝나기 전에 계속 타이핑해도 되도록 자리표시 문자열을 먼저 넣고, 끝나면 그 자리만 바꾼다.
 */
export default function MarkdownEditor({ value, onChange, onDrop, onImageUpload, placeholder, autoFocus, className = '', ref }) {
  const taRef = useRef(null)
  const valueRef = useRef(value)
  useEffect(() => { valueRef.current = value }, [value])

  const insertAtCursor = (text) => {
    const el = taRef.current
    const cur = valueRef.current || ''
    const start = el ? el.selectionStart : cur.length
    const end = el ? el.selectionEnd : cur.length
    const next = cur.slice(0, start) + text + cur.slice(end)
    valueRef.current = next
    onChange(next)
    requestAnimationFrame(() => {
      if (!el) return
      el.selectionStart = el.selectionEnd = start + text.length
    })
  }

  // 부모(편집기)에서 커서 자리 삽입·목차 이동을 하려고 노출한다. (React 19: ref를 prop으로 받는다)
  useImperativeHandle(ref, () => ({
    insertAtCursor: (text) => { insertAtCursor(text); requestAnimationFrame(() => taRef.current?.focus()) },
    scrollToOffset: (offset) => {
      const el = taRef.current
      if (!el) return
      el.focus()
      el.setSelectionRange(offset, offset)
      const line = (valueRef.current || '').slice(0, offset).split('\n').length - 1
      const lh = parseFloat(getComputedStyle(el).lineHeight) || 22
      el.scrollTop = Math.max(0, line * lh - 48)
    },
    focus: () => taRef.current?.focus(),
  }))

  const uploadFiles = async (files) => {
    const images = files.filter((f) => f.type.startsWith('image/'))
    if (!images.length || !onImageUpload) return false
    for (const file of images) {
      const marker = `![업로드 중: ${file.name || 'image'} ${Date.now().toString(36)}]()`
      insertAtCursor(`${marker}\n`)
      try {
        const url = await onImageUpload(file)
        const alt = (file.name || 'image').replace(/\.[^.]+$/, '')
        const cur = valueRef.current || ''
        const next = cur.replace(marker, `![${alt}](${url})`)
        valueRef.current = next
        onChange(next)
      } catch {
        const cur = valueRef.current || ''
        const next = cur.replace(`${marker}\n`, '').replace(marker, '')
        valueRef.current = next
        onChange(next)
        toast.error('이미지 업로드에 실패했어요')
      }
    }
    return true
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      insertAtCursor('  ')
    }
  }

  const handlePaste = (e) => {
    const files = [...(e.clipboardData?.files || [])]
    if (files.some((f) => f.type.startsWith('image/')) && onImageUpload) {
      e.preventDefault()
      uploadFiles(files)
    }
  }

  const handleDrop = (e) => {
    if (onDrop) return onDrop(e)
    const files = [...(e.dataTransfer?.files || [])]
    if (files.some((f) => f.type.startsWith('image/')) && onImageUpload) {
      e.preventDefault()
      // 끌어놓은 위치로 커서를 옮길 방법이 textarea에는 없어서 현재 커서 자리에 넣는다.
      uploadFiles(files)
    }
  }

  return (
    <textarea
      ref={taRef}
      value={value}
      autoFocus={autoFocus}
      onChange={e => onChange(e.target.value)}
      onDrop={handleDrop}
      onPaste={handlePaste}
      onDragOver={e => e.preventDefault()}
      onKeyDown={handleKeyDown}
      className={`w-full h-full p-4 sm:p-6 resize-none outline-none font-mono text-sm leading-relaxed ${className}`}
      style={{ background: 'var(--bg)', color: 'var(--text)' }}
      placeholder={placeholder ?? (onImageUpload
        ? '마크다운으로 작성하세요. 이미지는 붙여넣기·끌어놓기로 올릴 수 있어요.'
        : 'Write your markdown here...')}
      spellCheck={false}
    />
  )
}
