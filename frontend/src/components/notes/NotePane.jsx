import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft, Pin, PinOff, Archive, ArchiveRestore, Trash2, FileOutput, Eye, Pencil, Check, LoaderCircle, AlertTriangle, Circle, Palette,
} from 'lucide-react'
import MarkdownEditor from '../editor/MarkdownEditor'
import MarkdownRenderer from '../blog/MarkdownRenderer'
import NoteTagsInput from './NoteTagsInput'
import { updateNote, NOTE_COLORS } from '../../api/notes'
import { uploadImage } from '../../api/posts'
import { timeAgo } from '../../utils/noteText'

const EDITABLE = ['title', 'content', 'tags', 'pinned', 'archived', 'color']
const pick = (n) => Object.fromEntries(EDITABLE.map((k) => [k, n[k] ?? (k === 'tags' ? [] : k === 'pinned' || k === 'archived' ? false : '')]))

/**
 * 메모 하나의 편집 화면. 바뀐 필드만 모아 0.8초 디바운스로 PATCH한다.
 * 저장 도중 또 바뀌면 끝난 뒤 이어서 저장하고, 실패한 필드는 다시 모아 두었다가 재시도한다.
 * 다른 메모로 넘어가거나 화면을 떠날 때(언마운트) 남은 변경을 마저 보낸다.
 */
export default function NotePane({ note, allTags, onSaved, onDeleteRequest, onConvert, onBack, converting }) {
  const [draft, setDraft] = useState(() => pick(note))
  const [status, setStatus] = useState('saved') // saved | changed | saving | error
  const [savedAt, setSavedAt] = useState(note.updated_at ? Date.parse(note.updated_at) : null)
  const [mode, setMode] = useState('edit')
  const [showColors, setShowColors] = useState(false)
  const [, setTick] = useState(0)
  const draftRef = useRef(draft)
  const dirtyFields = useRef(new Set())
  const savingRef = useRef(false)
  const titleRef = useRef(null)
  useEffect(() => { draftRef.current = draft }, [draft])

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 5000)
    return () => clearInterval(t)
  }, [])

  // 막 만든 빈 메모면 제목에 바로 커서를 둔다.
  useEffect(() => {
    if (!note.content && titleRef.current) { titleRef.current.focus(); titleRef.current.select() }
  }, [note.id, note.content])

  const flush = useCallback(async () => {
    if (savingRef.current || dirtyFields.current.size === 0) return
    const fields = [...dirtyFields.current]
    dirtyFields.current.clear()
    const payload = Object.fromEntries(fields.map((k) => [k, draftRef.current[k]]))
    savingRef.current = true
    setStatus('saving')
    try {
      const { data } = await updateNote(note.id, payload)
      onSaved?.({ ...note, ...payload, ...(data || {}) })
      setSavedAt(Date.now())
      setStatus(dirtyFields.current.size ? 'changed' : 'saved')
    } catch {
      fields.forEach((f) => dirtyFields.current.add(f))
      setStatus('error')
    } finally {
      savingRef.current = false
    }
  }, [note, onSaved])

  const flushRef = useRef(flush)
  useEffect(() => { flushRef.current = flush }, [flush])
  useEffect(() => () => { flushRef.current() }, [])

  useEffect(() => {
    if (status !== 'changed') return
    const t = setTimeout(() => flushRef.current(), 800)
    return () => clearTimeout(t)
  }, [draft, status])

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') { e.preventDefault(); flushRef.current() }
    }
    const onUnload = (e) => {
      if (dirtyFields.current.size || savingRef.current) { e.preventDefault(); e.returnValue = '' }
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('beforeunload', onUnload)
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('beforeunload', onUnload) }
  }, [])

  const update = (patch) => {
    setDraft((d) => ({ ...d, ...patch }))
    Object.keys(patch).forEach((k) => dirtyFields.current.add(k))
    setStatus('changed')
  }

  const handleImageUpload = useCallback(async (file) => {
    const fd = new FormData()
    fd.append('image', file)
    const { data } = await uploadImage(fd)
    return data.image
  }, [])

  const convert = async () => {
    await flushRef.current()
    onConvert?.(note)
  }

  // blog-api는 linked_post_slug를 준다. (계약 초안의 linked_post 객체 형태도 받아 둔다)
  const linkedSlug = note.linked_post_slug
    || (note.linked_post && typeof note.linked_post === 'object' ? note.linked_post.slug : null)

  const btn = 'inline-flex items-center gap-1 text-xs px-2 py-1 rounded-lg border transition-colors hover:bg-black/5'
  const btnStyle = { borderColor: 'var(--border)', color: 'var(--text-secondary)' }

  let statusNode
  if (status === 'saving') statusNode = <span className="inline-flex items-center gap-1" style={{ color: '#f59e0b' }}><LoaderCircle size={12} className="animate-spin" /> 저장 중</span>
  else if (status === 'error') statusNode = <button onClick={() => flushRef.current()} className="inline-flex items-center gap-1 text-red-500 hover:underline"><AlertTriangle size={12} /> 저장 실패 · 재시도</button>
  else if (status === 'changed') statusNode = <span className="inline-flex items-center gap-1" style={{ color: '#6366f1' }}><Circle size={8} className="fill-current" /> 변경됨</span>
  else statusNode = <span className="inline-flex items-center gap-1" style={{ color: '#10b981' }}><Check size={12} /> 저장됨 {savedAt ? timeAgo(savedAt) : ''}</span>

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      <div className="flex flex-wrap items-center gap-1.5 px-3 sm:px-4 py-2 border-b" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <button onClick={onBack} className="md:hidden p-1.5 -ml-1 rounded-lg hover:bg-black/5" aria-label="목록으로">
          <ArrowLeft size={18} />
        </button>
        <button onClick={() => update({ pinned: !draft.pinned })} className={btn} style={btnStyle} aria-pressed={draft.pinned} title="상단 고정">
          {draft.pinned ? <PinOff size={13} /> : <Pin size={13} />}<span className="hidden sm:inline">{draft.pinned ? '고정 해제' : '고정'}</span>
        </button>
        <button onClick={() => update({ archived: !draft.archived })} className={btn} style={btnStyle} aria-pressed={draft.archived} title="보관함">
          {draft.archived ? <ArchiveRestore size={13} /> : <Archive size={13} />}<span className="hidden sm:inline">{draft.archived ? '보관 해제' : '보관'}</span>
        </button>
        <div className="relative">
          <button onClick={() => setShowColors((v) => !v)} className={btn} style={btnStyle} aria-expanded={showColors} title="색상">
            <Palette size={13} />
            <span className="w-3 h-3 rounded-full border" style={{ background: NOTE_COLORS.find((c) => c.key === (draft.color || ''))?.swatch, borderColor: 'var(--border)' }} />
          </button>
          {showColors && (
            <div className="absolute z-20 mt-1 left-0 flex gap-1 p-2 rounded-xl border shadow-lg" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
              {NOTE_COLORS.map((c) => (
                <button key={c.key || 'default'} onClick={() => { update({ color: c.key }); setShowColors(false) }}
                  className={`w-6 h-6 rounded-full border-2 ${(draft.color || '') === c.key ? 'border-primary-600' : ''}`}
                  style={{ background: c.swatch, borderColor: (draft.color || '') === c.key ? undefined : 'var(--border)' }}
                  title={c.label} aria-label={`색상 ${c.label}`} />
              ))}
            </div>
          )}
        </div>
        <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }} role="group" aria-label="보기">
          {[{ id: 'edit', I: Pencil, l: '편집' }, { id: 'preview', I: Eye, l: '미리보기' }].map(({ id, I, l }) => (
            <button key={id} onClick={() => setMode(id)} aria-pressed={mode === id}
              className="inline-flex items-center gap-1 text-xs px-2 py-1"
              style={{ background: mode === id ? 'var(--bg)' : 'transparent', color: mode === id ? 'var(--text)' : 'var(--text-secondary)' }}>
              <I size={13} /><span className="hidden sm:inline">{l}</span>
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs" aria-live="polite">{statusNode}</span>
        {linkedSlug ? (
          <Link to={`/editor/${linkedSlug}`} className={btn} style={btnStyle} title="이 메모에서 만든 글">
            <FileOutput size={13} /><span className="hidden sm:inline">연결된 글</span>
          </Link>
        ) : (
          <button onClick={convert} disabled={converting} className={btn} style={btnStyle} title="이 메모로 초안 글 만들기">
            <FileOutput size={13} /><span className="hidden sm:inline">{converting ? '변환 중' : '글로 변환'}</span>
          </button>
        )}
        <button onClick={() => onDeleteRequest?.(note)} className={`${btn} text-red-500`} style={{ borderColor: 'var(--border)' }} title="삭제" aria-label="메모 삭제">
          <Trash2 size={13} />
        </button>
      </div>

      <div className="px-4 sm:px-6 pt-4 pb-2 space-y-2">
        <input
          ref={titleRef}
          value={draft.title}
          onChange={(e) => update({ title: e.target.value })}
          placeholder="제목"
          aria-label="메모 제목"
          className="w-full text-lg sm:text-xl font-semibold bg-transparent outline-none"
          style={{ color: 'var(--text)' }}
        />
        <NoteTagsInput value={draft.tags || []} onChange={(tags) => update({ tags })} suggestions={allTags} />
      </div>

      <div className="flex-1 overflow-hidden border-t" style={{ borderColor: 'var(--border)' }}>
        {mode === 'edit' ? (
          <MarkdownEditor
            value={draft.content}
            onChange={(content) => update({ content })}
            onImageUpload={handleImageUpload}
            placeholder="마크다운으로 자유롭게. 이미지는 붙여넣기·끌어놓기. Cmd/Ctrl+S로 바로 저장."
          />
        ) : (
          <div className="h-full overflow-y-auto px-4 sm:px-6 py-4">
            {draft.content.trim() ? <MarkdownRenderer content={draft.content} /> : <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>내용이 없어요.</p>}
          </div>
        )}
      </div>
    </div>
  )
}
