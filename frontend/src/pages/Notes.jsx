import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import toast from 'react-hot-toast'
import { Plus, Search, Pin, Archive, Hash, StickyNote, X, Zap } from 'lucide-react'
import NotePane from '../components/notes/NotePane'
import ConfirmDialog from '../components/common/ConfirmDialog'
import useWorkspace from '../hooks/useWorkspace'
import {
  getNotes, getNote, createNote, deleteNote, getNoteTags, convertNoteToPost, noteSwatch,
} from '../api/notes'
import { timeAgo, noteTitleFrom } from '../utils/noteText'

const sortNotes = (list) => [...list].sort((a, b) =>
  (Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)))
  || (Date.parse(b.updated_at || 0) - Date.parse(a.updated_at || 0)))

const snippet = (s, n = 90) => {
  const t = String(s || '').replace(/[#>*_`[\]()!-]/g, ' ').replace(/\s+/g, ' ').trim()
  return t.length > n ? `${t.slice(0, n)}…` : t
}

/**
 * 개인 메모. 좌측 목록(검색·태그·보관함) + 우측 편집기.
 * 선택한 메모는 주소의 ?id= 로 들고 있어서 새로고침·뒤로 가기에도 그대로다.
 * 모바일에서는 목록과 편집기를 한 번에 하나만 보여 준다.
 */
export default function Notes() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get('id')
  const notesVersion = useWorkspace((s) => s.notesVersion)
  const openQuickNote = useWorkspace((s) => s.openQuickNote)

  const [qInput, setQInput] = useState('')
  const [q, setQ] = useState('')
  const [tag, setTag] = useState('')
  const [archived, setArchived] = useState(false)
  const [notes, setNotes] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [listState, setListState] = useState('loading') // loading | ready | error
  const [tags, setTags] = useState([])
  const [extraNote, setExtraNote] = useState(null) // 목록 필터 밖에 있는 선택 메모
  const [toDelete, setToDelete] = useState(null)
  const [converting, setConverting] = useState(false)
  const [creating, setCreating] = useState(false)
  const deletedIds = useRef(new Set())

  useEffect(() => {
    const t = setTimeout(() => setQ(qInput.trim()), 300)
    return () => clearTimeout(t)
  }, [qInput])

  const loadTags = useCallback(() => {
    getNoteTags().then((r) => setTags(Array.isArray(r.data) ? r.data : (r.data.results || []))).catch(() => {})
  }, [])

  const load = useCallback(async (pageNum = 1) => {
    if (pageNum === 1) setListState('loading')
    try {
      const params = { page: pageNum, archived: archived ? 'true' : 'false' }
      if (q) params.q = q
      if (tag) params.tag = tag
      const { data } = await getNotes(params)
      const results = data.results || (Array.isArray(data) ? data : [])
      setNotes((prev) => (pageNum === 1 ? results : [...prev, ...results.filter((n) => !prev.some((p) => p.id === n.id))]))
      setCount(data.count ?? results.length)
      setHasNext(Boolean(data.next))
      setPage(pageNum)
      setListState('ready')
    } catch {
      setListState('error')
    }
  }, [q, tag, archived])

  useEffect(() => { load(1) }, [load, notesVersion])
  useEffect(() => { loadTags() }, [loadTags, notesVersion])

  const sorted = useMemo(() => sortNotes(notes), [notes])
  const selected = useMemo(() => {
    if (!selectedId) return null
    return notes.find((n) => String(n.id) === selectedId) || (extraNote && String(extraNote.id) === selectedId ? extraNote : null)
  }, [notes, extraNote, selectedId])

  // 목록에 없는 메모(다른 필터, 빠른 메모 토스트의 "열기")는 따로 불러온다.
  useEffect(() => {
    if (!selectedId || listState !== 'ready') return
    if (notes.some((n) => String(n.id) === selectedId)) return
    if (deletedIds.current.has(selectedId)) return
    if (extraNote && String(extraNote.id) === selectedId) return
    let alive = true
    getNote(selectedId).then((r) => { if (alive) setExtraNote(r.data) }).catch(() => {
      if (!alive) return
      toast.error('메모를 찾을 수 없어요')
      setSearchParams({}, { replace: true })
    })
    return () => { alive = false }
  }, [selectedId, notes, extraNote, listState, setSearchParams])

  const select = (id) => setSearchParams(id ? { id: String(id) } : {})

  const handleSaved = useCallback((updated) => {
    // 보관/해제로 지금 목록 조건에서 벗어나면 목록에서는 빼되, 편집 중인 화면은 extraNote로 유지한다.
    const fits = Boolean(updated.archived) === archived
    const stamp = updated.updated_at || new Date().toISOString()
    setNotes((prev) => (fits
      ? prev.map((n) => (n.id === updated.id ? { ...n, ...updated, updated_at: stamp } : n))
      : prev.filter((n) => n.id !== updated.id)))
    setExtraNote((prev) => {
      if (!fits) return { ...(prev && prev.id === updated.id ? prev : {}), ...updated }
      return prev && prev.id === updated.id ? { ...prev, ...updated } : prev
    })
  }, [archived])

  const handleNew = async () => {
    if (creating) return
    setCreating(true)
    try {
      const { data } = await createNote({ title: '', content: '', tags: tag ? [tag] : [] })
      if (archived) setArchived(false)
      setNotes((prev) => [data, ...prev])
      setCount((c) => c + 1)
      select(data.id)
    } catch {
      toast.error('메모를 만들지 못했어요')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async () => {
    const n = toDelete
    setToDelete(null)
    if (!n) return
    try {
      await deleteNote(n.id)
      deletedIds.current.add(String(n.id))
      if (String(n.id) === selectedId) select(null)
      setNotes((prev) => prev.filter((x) => x.id !== n.id))
      setCount((c) => Math.max(0, c - 1))
      loadTags()
      toast.success('삭제했어요')
    } catch {
      toast.error('삭제에 실패했어요')
    }
  }

  const handleConvert = async (n) => {
    setConverting(true)
    try {
      const { data } = await convertNoteToPost(n.id)
      if (!data?.slug) throw new Error('no slug')
      toast.success('초안 글을 만들었어요')
      navigate(`/editor/${encodeURIComponent(data.slug)}`)
    } catch {
      toast.error('글로 변환하지 못했어요')
    } finally {
      setConverting(false)
    }
  }

  const chip = (active) => ({
    background: active ? 'var(--color-primary-600)' : 'var(--bg)',
    color: active ? '#fff' : 'var(--text-secondary)',
    borderColor: active ? 'var(--color-primary-600)' : 'var(--border)',
  })

  return (
    <div className="h-[calc(100dvh-4rem)] flex overflow-hidden">
      <Helmet><title>메모 · HJ Tech</title><meta name="robots" content="noindex" /></Helmet>

      {/* 목록 */}
      <aside className={`${selected ? 'hidden md:flex' : 'flex'} w-full md:w-80 lg:w-96 shrink-0 flex-col border-r`}
        style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }} aria-label="메모 목록">
        <div className="p-3 space-y-2 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
              <StickyNote size={16} className="text-primary-600" /> 메모
            </h1>
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{count}</span>
            <button onClick={openQuickNote} className="ml-auto p-1.5 rounded-lg border hover:bg-black/5"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }} title="빠른 메모 (m)" aria-label="빠른 메모">
              <Zap size={14} />
            </button>
            <button onClick={handleNew} disabled={creating}
              className="inline-flex items-center gap-1 text-sm px-2.5 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50">
              <Plus size={14} /> 새 메모
            </button>
          </div>
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-secondary)' }} />
            <input value={qInput} onChange={(e) => setQInput(e.target.value)} placeholder="메모 검색" aria-label="메모 검색"
              className="w-full text-sm pl-8 pr-7 py-1.5 rounded-lg border outline-none focus:ring-2 focus:ring-primary-500"
              style={{ background: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }} />
            {qInput && (
              <button onClick={() => setQInput('')} className="absolute right-2 top-1/2 -translate-y-1/2" aria-label="검색어 지우기">
                <X size={13} style={{ color: 'var(--text-secondary)' }} />
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1">
            <button onClick={() => setArchived((v) => !v)} className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border"
              style={chip(archived)} aria-pressed={archived}>
              <Archive size={11} /> 보관함
            </button>
            {tag && !tags.some((t) => t.name === tag) && (
              <button onClick={() => setTag('')} className="text-xs px-2 py-0.5 rounded-full border" style={chip(true)}>#{tag}</button>
            )}
            {tags.slice(0, 30).map((t) => (
              <button key={t.name} onClick={() => setTag(tag === t.name ? '' : t.name)}
                className="inline-flex items-center gap-0.5 text-xs px-2 py-0.5 rounded-full border" style={chip(tag === t.name)}
                aria-pressed={tag === t.name}>
                <Hash size={10} />{t.name}<span className="opacity-60 ml-0.5">{t.count}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {listState === 'loading' && <p className="p-4 text-sm" style={{ color: 'var(--text-secondary)' }}>불러오는 중…</p>}
          {listState === 'error' && (
            <div className="p-4 text-sm space-y-2" style={{ color: 'var(--text-secondary)' }}>
              <p>메모를 불러오지 못했어요.</p>
              <button onClick={() => load(1)} className="px-3 py-1 rounded-lg border" style={{ borderColor: 'var(--border)' }}>다시 시도</button>
            </div>
          )}
          {listState === 'ready' && sorted.length === 0 && (
            <div className="p-6 text-center text-sm space-y-1" style={{ color: 'var(--text-secondary)' }}>
              <p>{q || tag ? '조건에 맞는 메모가 없어요.' : archived ? '보관한 메모가 없어요.' : '아직 메모가 없어요.'}</p>
              {!q && !tag && !archived && <p className="text-xs">어디서든 <kbd className="px-1 border rounded" style={{ borderColor: 'var(--border)' }}>m</kbd> 을 눌러 빠르게 적을 수 있어요.</p>}
            </div>
          )}
          <ul>
            {sorted.map((n) => {
              const active = String(n.id) === selectedId
              return (
                <li key={n.id}>
                  <button onClick={() => select(n.id)} aria-current={active ? 'true' : undefined}
                    className="w-full text-left px-3 py-2.5 border-b transition-colors"
                    style={{
                      borderColor: 'var(--border)',
                      background: active ? 'var(--bg)' : noteSwatch(n.color),
                      boxShadow: active ? 'inset 3px 0 0 var(--color-primary-600)' : undefined,
                    }}>
                    <div className="flex items-center gap-1.5">
                      {n.pinned && <Pin size={12} className="text-primary-600 shrink-0" aria-label="고정됨" />}
                      <span className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{n.title || noteTitleFrom(n.content, 40)}</span>
                      <span className="ml-auto text-[11px] shrink-0" style={{ color: 'var(--text-secondary)' }}>{timeAgo(n.updated_at)}</span>
                    </div>
                    {n.content && <p className="text-xs mt-0.5 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>{snippet(n.content)}</p>}
                    {n.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {n.tags.slice(0, 4).map((t) => <span key={t} className="text-[10px] text-primary-700">#{t}</span>)}
                      </div>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
          {hasNext && listState === 'ready' && (
            <button onClick={() => load(page + 1)} className="w-full py-3 text-sm text-primary-600 hover:underline">더 보기</button>
          )}
        </div>
      </aside>

      {/* 편집기 */}
      <section className={`${selected ? 'flex' : 'hidden md:flex'} flex-1 min-w-0`} style={{ background: 'var(--bg)' }}>
        {selected ? (
          <NotePane
            key={selected.id}
            note={selected}
            allTags={tags}
            onSaved={handleSaved}
            onDeleteRequest={setToDelete}
            onConvert={handleConvert}
            converting={converting}
            onBack={() => select(null)}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
            <StickyNote size={28} className="opacity-40" />
            <p>왼쪽에서 메모를 고르거나 새로 만드세요.</p>
          </div>
        )}
      </section>

      <ConfirmDialog
        isOpen={Boolean(toDelete)}
        title="메모를 삭제할까요?"
        message={toDelete ? `“${toDelete.title || '제목 없는 메모'}”를 지우면 되돌릴 수 없어요. 남겨 두려면 보관을 쓰세요.` : ''}
        confirmLabel="삭제"
        variant="danger"
        onConfirm={handleDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  )
}
