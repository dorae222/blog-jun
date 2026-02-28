import { useRef } from 'react'

export default function MarkdownEditor({ value, onChange, onDrop }) {
  const ref = useRef(null)

  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const start = e.target.selectionStart
      const end = e.target.selectionEnd
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      onChange(newValue)
      setTimeout(() => {
        e.target.selectionStart = e.target.selectionEnd = start + 2
      }, 0)
    }
  }

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={e => onChange(e.target.value)}
      onDrop={onDrop}
      onDragOver={e => e.preventDefault()}
      onKeyDown={handleKeyDown}
      className="w-full h-full p-6 resize-none outline-none font-mono text-sm leading-relaxed"
      style={{ background: 'var(--bg)', color: 'var(--text)' }}
      placeholder="Write your markdown here... (Drag & drop images supported)"
      spellCheck={false}
    />
  )
}
