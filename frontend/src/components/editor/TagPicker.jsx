import { useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { X, Hash, Plus } from 'lucide-react'
import { createTag } from '../../api/posts'
import { slugify } from '../../utils/noteText'

/**
 * 글 태그 선택기(칩). value는 태그 id 배열(서버 PostWrite.tags 형식).
 * 입력하면 기존 태그를 이름으로 걸러 보여 주고(↑↓ 이동, Enter 선택), 맞는 게 없으면 Enter로 새 태그를 만든다.
 * 새 태그 slug는 서버 규칙(ASCII)에 맞춰 이름에서 만들고, 한글뿐이면 tag-<무작위>로 둔다.
 */
export default function TagPicker({ value = [], onChange, allTags = [], onTagCreated, compact = false }) {
  const [input, setInput] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const [busy, setBusy] = useState(false)
  const inputRef = useRef(null)

  const byId = useMemo(() => new Map(allTags.map((t) => [String(t.id), t])), [allTags])
  const selected = value.map((id) => byId.get(String(id))).filter(Boolean)
  const q = input.trim().replace(/^#/, '').toLowerCase()
  const suggestions = useMemo(() => {
    const chosen = new Set(value.map(String))
    return allTags
      .filter((t) => !chosen.has(String(t.id)) && (!q || t.name.toLowerCase().includes(q) || t.slug?.includes(q)))
      .sort((a, b) => (b.post_count || 0) - (a.post_count || 0))
      .slice(0, 8)
  }, [allTags, value, q])
  const exact = allTags.find((t) => t.name.toLowerCase() === q)

  const add = (tag) => {
    if (!value.map(String).includes(String(tag.id))) onChange([...value, tag.id])
    setInput('')
    setActive(0)
    inputRef.current?.focus()
  }

  const createNew = async () => {
    const name = input.trim().replace(/^#/, '')
    if (!name || busy) return
    setBusy(true)
    try {
      const base = slugify(name, 40)
      const slug = base || `tag-${Math.random().toString(36).slice(2, 8)}`
      let res
      try {
        res = await createTag({ name, slug })
      } catch (err) {
        if (err?.response?.data?.slug) res = await createTag({ name, slug: `${slug}-${Math.random().toString(36).slice(2, 5)}` })
        else throw err
      }
      onTagCreated?.(res.data)
      add(res.data)
      toast.success(`새 태그 #${name}`)
    } catch (err) {
      const d = err?.response?.data
      toast.error(d?.name ? `태그를 만들 수 없어요: ${[].concat(d.name).join(' ')}` : '태그를 만들 수 없어요')
    } finally {
      setBusy(false)
    }
  }

  const onKeyDown = (e) => {
    if (e.nativeEvent.isComposing) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive((i) => Math.min(i + 1, suggestions.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)) }
    else if (e.key === 'Enter' || e.key === ',') {
      if (!q) return
      e.preventDefault()
      if (exact) add(exact)
      else if (open && suggestions[active] && suggestions[active].name.toLowerCase().includes(q)) add(suggestions[active])
      else createNew()
    } else if (e.key === 'Backspace' && !input && value.length) onChange(value.slice(0, -1))
    else if (e.key === 'Escape' && open) { e.stopPropagation(); setOpen(false) }
  }

  return (
    <div className="relative min-w-0">
      <div className={`flex flex-wrap items-center gap-1 rounded-lg border px-2 ${compact ? 'py-0.5' : 'py-1.5'}`}
        style={{ borderColor: 'var(--border)', background: 'var(--bg)' }} onClick={() => inputRef.current?.focus()}>
        {selected.map((t) => (
          <span key={t.id} className="inline-flex items-center gap-0.5 text-xs pl-2 pr-1 py-0.5 rounded-full bg-primary-50 text-primary-700">
            <Hash size={10} />{t.name}
            <button type="button" onClick={(e) => { e.stopPropagation(); onChange(value.filter((id) => String(id) !== String(t.id))) }}
              className="p-0.5 rounded-full hover:bg-primary-100" aria-label={`${t.name} 태그 빼기`}>
              <X size={10} />
            </button>
          </span>
        ))}
        <input ref={inputRef} value={input}
          onChange={(e) => { setInput(e.target.value); setOpen(true); setActive(0) }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={onKeyDown}
          placeholder={selected.length ? '' : '태그 (Enter로 추가)'}
          aria-label="태그 추가" role="combobox" aria-expanded={open} aria-autocomplete="list"
          className="min-w-[6rem] flex-1 bg-transparent text-sm outline-none py-0.5" style={{ color: 'var(--text)' }} />
      </div>
      {open && (suggestions.length > 0 || (q && !exact)) && (
        <ul role="listbox" className="absolute z-30 mt-1 w-full min-w-[14rem] max-h-60 overflow-y-auto rounded-xl border shadow-lg py-1"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
          {suggestions.map((t, i) => (
            <li key={t.id} role="option" aria-selected={i === active}>
              <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => add(t)}
                className="w-full flex items-center gap-1 px-3 py-1.5 text-sm text-left"
                style={{ background: i === active ? 'var(--bg-secondary)' : undefined, color: 'var(--text)' }}>
                <Hash size={11} className="text-primary-600" />{t.name}
                <span className="ml-auto text-[11px]" style={{ color: 'var(--text-secondary)' }}>{t.post_count ?? ''}</span>
              </button>
            </li>
          ))}
          {q && !exact && (
            <li>
              <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={createNew} disabled={busy}
                className="w-full flex items-center gap-1 px-3 py-1.5 text-sm text-left text-primary-600 border-t"
                style={{ borderColor: 'var(--border)' }}>
                <Plus size={12} /> 새 태그 “{input.trim().replace(/^#/, '')}” 만들기
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  )
}
