import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PenLine, StickyNote, Pin, Plus, Zap, HardDrive } from 'lucide-react'
import { getPosts } from '../../api/posts'
import { getNotes } from '../../api/notes'
import useWorkspace from '../../hooks/useWorkspace'
import { listDrafts } from '../../utils/editorDraft'
import { timeAgo, noteTitleFrom } from '../../utils/noteText'

const card = { background: 'var(--card-bg)', borderColor: 'var(--border)' }

function Panel({ icon: Icon, title, action, children }) {
  return (
    <section className="rounded-xl border p-4 min-w-0" style={card}>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={15} className="text-primary-600" />
        <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</h2>
        <div className="ml-auto flex items-center gap-1">{action}</div>
      </div>
      {children}
    </section>
  )
}

const rowCls = 'flex items-center gap-2 px-2 py-1.5 -mx-2 rounded-lg text-sm hover:bg-black/5 transition-colors'

/** 대시보드 상단: "이어 쓰기"(서버 초안 + 이 브라우저의 임시본) / "최근 메모". */
export default function WorkspaceWidgets() {
  const notesVersion = useWorkspace((s) => s.notesVersion)
  const openQuickNote = useWorkspace((s) => s.openQuickNote)
  const [drafts, setDrafts] = useState(null)
  const [notes, setNotes] = useState(null)
  const [notesError, setNotesError] = useState(false)
  const [localDrafts] = useState(() => listDrafts().slice(0, 3))

  useEffect(() => {
    getPosts({ status: 'draft', page_size: 5 })
      .then((r) => setDrafts(r.data.results || r.data || []))
      .catch(() => setDrafts([]))
  }, [])

  useEffect(() => {
    getNotes({ archived: 'false', page: 1 })
      .then((r) => {
        const list = r.data.results || (Array.isArray(r.data) ? r.data : [])
        const sorted = [...list].sort((a, b) => (Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)))
          || (Date.parse(b.updated_at || 0) - Date.parse(a.updated_at || 0)))
        setNotes(sorted.slice(0, 5))
        setNotesError(false)
      })
      .catch(() => { setNotes([]); setNotesError(true) })
  }, [notesVersion])

  const small = 'inline-flex items-center gap-1 text-xs px-2 py-1 rounded-lg border hover:bg-black/5'
  const smallStyle = { borderColor: 'var(--border)', color: 'var(--text-secondary)' }

  return (
    <div className="grid gap-3 md:grid-cols-2 mb-6">
      <Panel icon={PenLine} title="이어 쓰기"
        action={<Link to="/editor" className={small} style={smallStyle} title="새 글 (n)"><Plus size={12} /> 새 글</Link>}>
        {localDrafts.length > 0 && (
          <ul className="mb-2">
            {localDrafts.map((d) => (
              <li key={d.key}>
                <Link to={d.key === 'new' ? '/editor' : `/editor/${encodeURIComponent(d.key)}`} className={rowCls}>
                  <HardDrive size={12} className="shrink-0 text-amber-600" aria-label="이 브라우저 임시저장본" />
                  <span className="truncate" style={{ color: 'var(--text)' }}>{d.form.title || '제목 없는 새 글'}</span>
                  <span className="ml-auto text-[11px] shrink-0 text-amber-700">임시본 · {timeAgo(d.savedAt)}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
        {drafts === null && <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>불러오는 중…</p>}
        {drafts?.length === 0 && localDrafts.length === 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>쓰다 만 초안이 없어요.</p>
        )}
        <ul>
          {drafts?.map((p) => (
            <li key={p.slug}>
              <Link to={`/editor/${encodeURIComponent(p.slug)}`} className={rowCls}>
                <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: '#f59e0b' }} />
                <span className="truncate" style={{ color: 'var(--text)' }}>{p.title || p.slug}</span>
                <span className="ml-auto text-[11px] shrink-0" style={{ color: 'var(--text-secondary)' }}>
                  {p.category?.name || '카테고리 없음'} · {timeAgo(p.updated_at || p.created_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel icon={StickyNote} title="최근 메모"
        action={<>
          <button onClick={openQuickNote} className={small} style={smallStyle} title="빠른 메모 (m)"><Zap size={12} /> 빠른 메모</button>
          <Link to="/notes" className={small} style={smallStyle}>전체</Link>
        </>}>
        {notes === null && <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>불러오는 중…</p>}
        {notesError && <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>메모를 불러오지 못했어요.</p>}
        {notes?.length === 0 && !notesError && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>아직 메모가 없어요.<span className="kbd-hint"> 어디서든 <kbd className="px-1 border rounded" style={{ borderColor: 'var(--border)' }}>m</kbd>으로 적어 두세요.</span></p>
        )}
        <ul>
          {notes?.map((n) => (
            <li key={n.id}>
              <Link to={`/notes?id=${n.id}`} className={rowCls}>
                {n.pinned ? <Pin size={12} className="shrink-0 text-primary-600" /> : <span className="w-3 shrink-0" />}
                <span className="truncate" style={{ color: 'var(--text)' }}>{n.title || noteTitleFrom(n.content, 40)}</span>
                {n.tags?.length > 0 && (
                  <span className="hidden xs:inline-flex gap-1 shrink-0 text-[10px] text-primary-700">
                    {n.tags.slice(0, 3).map((t) => <span key={t}>#{t}</span>)}
                    {n.tags.length > 3 && <span style={{ color: 'var(--text-secondary)' }}>+{n.tags.length - 3}</span>}
                  </span>
                )}
                <span className="ml-auto text-[11px] shrink-0" style={{ color: 'var(--text-secondary)' }}>{timeAgo(n.updated_at)}</span>
              </Link>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
