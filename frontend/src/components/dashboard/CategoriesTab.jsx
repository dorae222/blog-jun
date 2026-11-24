import { useCallback, useEffect, useState } from 'react'
import { confirmDialog } from '../../hooks/useDialog'
import toast from 'react-hot-toast'
import { Plus, Save, Trash2, ChevronDown, ChevronRight, FolderTree, AlertTriangle } from 'lucide-react'
import client from '../../api/client'

/**
 * 카테고리 관리.
 *
 * 카테고리 트리는 이제 프런트에 하드코딩돼 있지 않고 이 API가 유일한 원천이라,
 * 여기서 만들고 지우면 사이트 네비게이션이 바로 따라온다.
 *
 * 규칙 하나를 화면에서도 지킨다: 글은 소분류에만 붙인다. 하위가 있는 대탭에
 * 글이 직접 달려 있으면 목록에서 새어 나가므로 경고를 띄운다.
 */
export default function CategoriesTab() {
  const [tree, setTree] = useState([])
  const [open, setOpen] = useState({})
  const [edit, setEdit] = useState(null)     // {id, name, slug, color, order, parent}
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    client.get('/categories/', { params: { page_size: 200 } })
      .then((r) => setTree(r.data?.results ?? r.data ?? []))
      .catch(() => toast.error('카테고리를 불러오지 못했습니다'))
  }, [])

  useEffect(() => { load() }, [load])

  async function save() {
    if (!edit) return
    setBusy(true)
    try {
      const body = {
        name: edit.name, slug: edit.slug,
        color: edit.color || '', order: Number(edit.order) || 0,
        parent: edit.parent ?? null,
      }
      if (edit.id) await client.patch(`/categories/${edit.id}/`, body)
      else await client.post('/categories/', body)
      toast.success('저장했습니다')
      setEdit(null); load()
    } catch (e) {
      toast.error(e?.response?.data?.slug?.[0] || '저장에 실패했습니다')
    } finally { setBusy(false) }
  }

  async function remove(c) {
    const total = c.total_count ?? c.post_count ?? 0
    if (total > 0) {
      toast.error(`글 ${total}편이 남아 있어 지울 수 없습니다. 먼저 옮기세요.`)
      return
    }
    if (!(await confirmDialog({ title: '카테고리 삭제', message: `"${c.name}" 카테고리를 지웁니다.`, confirmLabel: '삭제', variant: 'danger' }))) return
    try {
      await client.delete(`/categories/${c.id}/`)
      toast.success('삭제했습니다'); load()
    } catch { toast.error('삭제에 실패했습니다') }
  }

  function Row({ c, depth = 0 }) {
    const kids = c.children || []
    const total = c.total_count ?? c.post_count ?? 0
    const own = c.post_count ?? 0
    const leaking = kids.length > 0 && own > 0
    const isOpen = open[c.id] ?? depth === 0

    return (
      <>
        <div className="flex items-center gap-2 px-3 py-2 border-b"
          style={{ borderColor: 'var(--border)', paddingLeft: 12 + depth * 20 }}>
          {kids.length > 0 ? (
            <button onClick={() => setOpen((o) => ({ ...o, [c.id]: !isOpen }))}
              className="p-0.5 rounded hover:bg-black/5">
              {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : <span className="w-[22px]" />}

          <span className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
            style={{ background: c.color || '#94a3b8' }} />

          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{c.name}</span>
          <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{c.slug}</span>

          <span className="text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            {total}편{kids.length ? ` (직속 ${own})` : ''}
          </span>

          {leaking && (
            <span className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded"
              style={{ background: '#fef3c7', color: '#92400e' }}
              title="하위가 있는데 이 카테고리에 글이 직접 붙어 있습니다. 소분류로 옮기세요.">
              <AlertTriangle size={11} /> 직속 글 {own}
            </span>
          )}
          {total === 0 && (
            <span className="text-[11px] px-1.5 py-0.5 rounded"
              style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
              화면에서 숨김
            </span>
          )}

          <span className="ml-auto flex items-center gap-1">
            {depth === 0 && (
              <button
                onClick={() => setEdit({ name: '', slug: '', color: c.color, order: 0, parent: c.id })}
                className="text-xs px-2 py-1 rounded border hover:bg-black/5"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                <Plus size={12} />
              </button>
            )}
            <button
              onClick={() => setEdit({
                id: c.id, name: c.name, slug: c.slug,
                color: c.color || '', order: c.order || 0, parent: c.parent ?? null,
              })}
              className="text-xs px-2 py-1 rounded border hover:bg-black/5"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              수정
            </button>
            <button onClick={() => remove(c)}
              className="p-1 rounded hover:bg-black/5" title="삭제">
              <Trash2 size={13} style={{ color: '#dc2626' }} />
            </button>
          </span>
        </div>
        {isOpen && kids.map((k) => <Row key={k.id} c={k} depth={depth + 1} />)}
      </>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          <FolderTree size={14} className="inline mr-1" />
          글은 소분류에만 답니다. 글이 0편인 카테고리는 사이트 메뉴에서 자동으로 숨습니다.
        </p>
        <button
          onClick={() => setEdit({ name: '', slug: '', color: '#64748b', order: 0, parent: null })}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-sm hover:bg-black/5"
          style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
          <Plus size={14} /> 대탭 추가
        </button>
      </div>

      <div className="rounded-xl border overflow-hidden"
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
        {tree.map((c) => <Row key={c.id} c={c} />)}
      </div>

      {edit && (
        <div className="rounded-xl border p-4 space-y-3"
          style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
          <h4 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            {edit.id ? '카테고리 수정' : (edit.parent ? '소분류 추가' : '대탭 추가')}
          </h4>
          <div className="grid gap-3 sm:grid-cols-4">
            {[['name', '이름'], ['slug', '슬러그'], ['color', '색 (#RRGGBB)'], ['order', '정렬']].map(([k, label]) => (
              <label key={k} className="block">
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                <input value={edit[k] ?? ''}
                  onChange={(e) => setEdit({ ...edit, [k]: e.target.value })}
                  className="w-full mt-1 px-3 py-1.5 rounded-md border text-sm"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />
              </label>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={busy || !edit.name || !edit.slug}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-white disabled:opacity-40"
              style={{ background: 'var(--color-primary-600, #2563eb)' }}>
              <Save size={14} /> 저장
            </button>
            <button onClick={() => setEdit(null)}
              className="px-3 py-1.5 rounded-md border text-sm"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
