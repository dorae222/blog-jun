import { useState } from 'react'
import { X, Hash } from 'lucide-react'

/** 태그 칩 입력. Enter·쉼표로 추가, 빈 칸에서 Backspace면 마지막 태그 삭제. */
export default function NoteTagsInput({ value = [], onChange, suggestions = [] }) {
  const [input, setInput] = useState('')

  const add = (raw) => {
    const t = raw.trim().replace(/^#/, '').toLowerCase()
    if (!t || value.includes(t)) { setInput(''); return }
    onChange([...value, t])
    setInput('')
  }

  return (
    <div className="flex flex-wrap items-center gap-1 min-w-0">
      {value.map((t) => (
        <span key={t} className="inline-flex items-center gap-0.5 text-xs pl-2 pr-1 py-0.5 rounded-full bg-primary-50 text-primary-700">
          <Hash size={10} />{t}
          <button type="button" onClick={() => onChange(value.filter((x) => x !== t))}
            className="p-0.5 rounded-full hover:bg-primary-100" aria-label={`${t} 태그 빼기`}>
            <X size={10} />
          </button>
        </span>
      ))}
      <input
        value={input}
        list="note-tag-suggestions"
        onChange={(e) => {
          const v = e.target.value
          if (v.endsWith(',')) add(v.slice(0, -1))
          else setInput(v)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.nativeEvent.isComposing) { e.preventDefault(); add(input) }
          else if (e.key === 'Backspace' && !input && value.length) onChange(value.slice(0, -1))
        }}
        onBlur={() => input && add(input)}
        placeholder={value.length ? '' : '태그 추가'}
        aria-label="태그 추가"
        className="min-w-[5rem] flex-1 bg-transparent text-xs outline-none py-0.5"
        style={{ color: 'var(--text)' }}
      />
      <datalist id="note-tag-suggestions">
        {suggestions.filter((s) => !value.includes(s.name)).map((s) => <option key={s.name} value={s.name} />)}
      </datalist>
    </div>
  )
}
