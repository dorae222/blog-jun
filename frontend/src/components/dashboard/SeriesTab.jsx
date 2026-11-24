import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { confirmDialog, promptDialog } from '../../hooks/useDialog'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Plus, Save, Trash2, Upload, GripVertical, X, Search, ExternalLink, Layers,
} from 'lucide-react'
import client from '../../api/client'

/**
 * 시리즈 관리.
 * 시리즈를 만들고 고치고, 표지를 올리고, 편 순서를 끌어서 바꾸고, 글을 넣고 뺀다.
 * 지금까지 이 작업은 전부 서버에 붙어 스크립트로 했는데, 한 편 순서 하나 바꾸자고
 * 그럴 일은 아니라서 화면으로 내렸다.
 */
export default function SeriesTab() {
  const [list, setList] = useState([])
  const [active, setActive] = useState(null)      // slug
  const [posts, setPosts] = useState([])
  const [form, setForm] = useState({ name: '', slug: '', description: '' })
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [cand, setCand] = useState([])
  const dragFrom = useRef(null)
  const fileRef = useRef(null)

  const load = useCallback(() => {
    client.get('/series/', { params: { page_size: 200 } })
      .then((r) => setList(r.data?.results ?? r.data ?? []))
      .catch(() => toast.error('시리즈 목록을 불러오지 못했습니다'))
  }, [])

  useEffect(() => { load() }, [load])

  const current = useMemo(() => list.find((s) => s.slug === active), [list, active])

  useEffect(() => {
    if (!active) { setPosts([]); return }
    client.get('/posts/', { params: { series__slug: active, page_size: 200 } })
      .then((r) => {
        const rows = r.data?.results ?? r.data ?? []
        rows.sort((a, b) => (a.series_order || 0) - (b.series_order || 0))
        setPosts(rows)
      })
      .catch(() => setPosts([]))
  }, [active])

  useEffect(() => {
    if (!current) return
    setForm({
      name: current.name || '',
      slug: current.slug || '',
      description: current.description || '',
    })
    setDirty(false)
  }, [current])

  async function pick(slug) {
    if (dirty && !(await confirmDialog({ title: '저장하지 않은 변경', message: '저장하지 않은 변경이 있습니다. 이동할까요?', confirmLabel: '이동' }))) return
    setActive(slug)
  }

  async function save() {
    if (!current) return
    setBusy(true)
    try {
      await client.patch(`/series/${current.slug}/`, {
        name: form.name, description: form.description,
      })
      toast.success('저장했습니다')
      setDirty(false)
      load()
    } catch {
      toast.error('저장에 실패했습니다')
    } finally { setBusy(false) }
  }

  async function create() {
    const name = await promptDialog({ title: '새 시리즈', label: '시리즈 이름', confirmLabel: '다음' })
    if (!name) return
    const slug = await promptDialog({
      title: '새 시리즈', label: '슬러그 (영문 kebab-case)', confirmLabel: '만들기',
      defaultValue: name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    })
    if (!slug) return
    try {
      await client.post('/series/', { name, slug, description: '' })
      toast.success('만들었습니다')
      load(); setActive(slug)
    } catch {
      toast.error('생성에 실패했습니다. 슬러그가 겹치지 않는지 확인하세요')
    }
  }

  async function remove() {
    if (!current) return
    if (!(await confirmDialog({ title: '시리즈 삭제', message: `"${current.name}" 시리즈를 지웁니다. 속한 글은 시리즈 없음이 됩니다.`, confirmLabel: '삭제', variant: 'danger' }))) return
    try {
      await client.delete(`/series/${current.slug}/`)
      toast.success('삭제했습니다')
      setActive(null); load()
    } catch { toast.error('삭제에 실패했습니다') }
  }

  async function uploadCover(e) {
    const f = e.target.files?.[0]
    if (!f || !current) return
    const fd = new FormData()
    fd.append('file', f)
    setBusy(true)
    try {
      await client.post(`/series/${current.slug}/cover/`, fd,
        { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('표지를 올렸습니다')
      load()
    } catch {
      toast.error('업로드에 실패했습니다')
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  // 순서는 끌어서 바꾸고, 놓는 순간 서버에 반영한다
  function onDrop(idx) {
    const from = dragFrom.current
    dragFrom.current = null
    if (from == null || from === idx) return
    const next = [...posts]
    const [moved] = next.splice(from, 1)
    next.splice(idx, 0, moved)
    setPosts(next)
    client.post(`/series/${active}/reorder/`, { slugs: next.map((p) => p.slug) })
      .then(() => toast.success('순서를 바꿨습니다'))
      .catch(() => toast.error('순서 저장에 실패했습니다'))
  }

  function searchCandidates() {
    if (!q.trim()) { setCand([]); return }
    client.get('/posts/', { params: { search: q, page_size: 20 } })
      .then((r) => setCand((r.data?.results ?? r.data ?? []).filter((p) => !p.series_name)))
      .catch(() => setCand([]))
  }

  function members(add = [], rm = []) {
    client.post(`/series/${active}/members/`, { add, remove: rm })
      .then(() => {
        toast.success(add.length ? '추가했습니다' : '뺐습니다')
        setActive((s) => s)
        client.get('/posts/', { params: { series__slug: active, page_size: 200 } })
          .then((r) => {
            const rows = r.data?.results ?? r.data ?? []
            rows.sort((a, b) => (a.series_order || 0) - (b.series_order || 0))
            setPosts(rows)
          })
        setCand((c) => c.filter((p) => !add.includes(p.slug)))
        load()
      })
      .catch(() => toast.error('반영에 실패했습니다'))
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
      {/* 왼쪽: 시리즈 목록 */}
      <div className="rounded-xl border overflow-hidden"
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
        <div className="flex items-center justify-between px-3 py-2 border-b"
          style={{ borderColor: 'var(--border)' }}>
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            시리즈 {list.length}
          </span>
          <button onClick={create}
            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border hover:bg-black/5"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
            <Plus size={12} /> 새로
          </button>
        </div>
        <div className="max-h-[560px] overflow-y-auto">
          {list.map((s) => (
            <button key={s.slug} onClick={() => pick(s.slug)}
              className="w-full text-left px-3 py-2 border-b transition-colors hover:bg-black/5"
              style={{
                borderColor: 'var(--border)',
                background: active === s.slug ? 'var(--bg-secondary)' : 'transparent',
              }}>
              <div className="text-sm font-medium line-clamp-1" style={{ color: 'var(--text)' }}>
                {s.name}
              </div>
              <div className="text-[11px] mt-0.5 flex items-center gap-2"
                style={{ color: 'var(--text-secondary)' }}>
                <span className="inline-flex items-center gap-0.5"><Layers size={10} />{s.post_count}편</span>
                <span className="truncate">{s.slug}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 오른쪽: 상세 */}
      {!current ? (
        <div className="rounded-xl border flex items-center justify-center text-sm"
          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', minHeight: 320 }}>
          왼쪽에서 시리즈를 고르세요
        </div>
      ) : (
        <div className="space-y-5">
          <div className="rounded-xl border p-4"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <div className="grid gap-4 md:grid-cols-[240px_1fr]">
              <div>
                <div className="aspect-[16/10] rounded-lg overflow-hidden border mb-2"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
                  {current.cover_image_url && (
                    <img src={current.cover_image_url} alt={current.name}
                      className="w-full h-full object-cover" />
                  )}
                </div>
                <input ref={fileRef} type="file" accept="image/*" hidden onChange={uploadCover} />
                <button onClick={() => fileRef.current?.click()} disabled={busy}
                  className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5
                    rounded-md border text-xs font-medium hover:bg-black/5 disabled:opacity-50"
                  style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                  <Upload size={13} /> 표지 올리기
                </button>
              </div>

              <div className="space-y-3">
                <label className="block">
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>이름</span>
                  <input value={form.name}
                    onChange={(e) => { setForm({ ...form, name: e.target.value }); setDirty(true) }}
                    className="w-full mt-1 px-3 py-1.5 rounded-md border text-sm"
                    style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />
                </label>
                <label className="block">
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>설명</span>
                  <textarea rows={3} value={form.description}
                    onChange={(e) => { setForm({ ...form, description: e.target.value }); setDirty(true) }}
                    className="w-full mt-1 px-3 py-1.5 rounded-md border text-sm resize-y"
                    style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />
                </label>
                <div className="flex items-center gap-2">
                  <button onClick={save} disabled={!dirty || busy}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium
                      text-white disabled:opacity-40"
                    style={{ background: 'var(--color-primary-600, #2563eb)' }}>
                    <Save size={14} /> 저장
                  </button>
                  <Link to={`/series?s=${current.slug}`} target="_blank"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-sm"
                    style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                    <ExternalLink size={14} /> 보기
                  </Link>
                  <button onClick={remove}
                    className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-sm"
                    style={{ borderColor: '#fecaca', color: '#dc2626' }}>
                    <Trash2 size={14} /> 삭제
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 편 순서 */}
          <div className="rounded-xl border overflow-hidden"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <div className="px-4 py-2 border-b text-sm font-semibold"
              style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
              편 순서 · {posts.length}편 <span className="font-normal text-xs"
                style={{ color: 'var(--text-secondary)' }}>끌어서 바꾸면 바로 저장됩니다</span>
            </div>
            <ul>
              {posts.map((p, i) => (
                <li key={p.slug}
                  draggable
                  onDragStart={() => { dragFrom.current = i }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => onDrop(i)}
                  className="flex items-center gap-3 px-4 py-2 border-b cursor-grab active:cursor-grabbing"
                  style={{ borderColor: 'var(--border)' }}>
                  <GripVertical size={14} style={{ color: 'var(--text-secondary)' }} />
                  <span className="w-7 text-xs font-bold tabular-nums"
                    style={{ color: 'var(--text-secondary)' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  {p.cover_image_url && (
                    <img src={p.cover_image_url} alt="" className="w-14 h-9 object-cover rounded" />
                  )}
                  <span className="flex-1 text-sm line-clamp-1" style={{ color: 'var(--text)' }}>
                    {p.title}
                  </span>
                  <Link to={`/editor/${p.slug}`}
                    className="text-xs px-2 py-1 rounded border hover:bg-black/5"
                    style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                    편집
                  </Link>
                  <button onClick={() => members([], [p.slug])}
                    className="p-1 rounded hover:bg-black/5" title="시리즈에서 빼기">
                    <X size={14} style={{ color: '#dc2626' }} />
                  </button>
                </li>
              ))}
              {!posts.length && (
                <li className="px-4 py-6 text-sm text-center" style={{ color: 'var(--text-secondary)' }}>
                  아직 글이 없습니다. 아래에서 찾아 넣으세요.
                </li>
              )}
            </ul>
          </div>

          {/* 글 추가 */}
          <div className="rounded-xl border p-4"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <div className="flex items-center gap-2 mb-3">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--text-secondary)' }} />
                <input value={q}
                  onChange={(e) => setQ(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchCandidates()}
                  placeholder="시리즈에 넣을 글 검색 (시리즈 없는 글만 나옵니다)"
                  className="w-full pl-8 pr-3 py-1.5 rounded-md border text-sm"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />
              </div>
              <button onClick={searchCandidates}
                className="px-3 py-1.5 rounded-md border text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                찾기
              </button>
            </div>
            <ul className="space-y-1 max-h-60 overflow-y-auto">
              {cand.map((p) => (
                <li key={p.slug} className="flex items-center gap-2 text-sm">
                  <button onClick={() => members([p.slug])}
                    className="px-2 py-0.5 rounded border text-xs hover:bg-black/5"
                    style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                    <Plus size={12} />
                  </button>
                  <span className="line-clamp-1" style={{ color: 'var(--text)' }}>{p.title}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
