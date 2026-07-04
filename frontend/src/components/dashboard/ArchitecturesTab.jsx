import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Eye, Pencil, Trash2, Plus, Search, Image, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ArchitecturesTab({
  archEntries, archCatFilter, setArchCatFilter,
  loadArchitectures, deleteArchitecture,
  ARCH_CATEGORIES,
}) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState('name') // 'name' | 'date' | 'category'
  const [sortAsc, setSortAsc] = useState(true)

  const filtered = useMemo(() => {
    let items = archEntries
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      items = items.filter(e =>
        e.name?.toLowerCase().includes(q) || e.organization?.toLowerCase().includes(q)
      )
    }
    return [...items].sort((a, b) => {
      let cmp = 0
      if (sortField === 'name') cmp = (a.name || '').localeCompare(b.name || '')
      else if (sortField === 'date') cmp = (a.release_date || '').localeCompare(b.release_date || '')
      else if (sortField === 'category') cmp = (a.architecture_category || '').localeCompare(b.architecture_category || '')
      return sortAsc ? cmp : -cmp
    })
  }, [archEntries, searchQuery, sortField, sortAsc])

  const handleSort = (field) => {
    if (sortField === field) setSortAsc(!sortAsc)
    else { setSortField(field); setSortAsc(true) }
  }

  const sortIndicator = (field) => sortField === field ? (sortAsc ? ' ↑' : ' ↓') : ''

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {filtered.length}개 Architecture
          </p>
          <select
            value={archCatFilter}
            onChange={e => setArchCatFilter(e.target.value)}
            className="text-sm px-3 py-1.5 rounded-lg border"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
          >
            {ARCH_CATEGORIES.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          {/* 검색 */}
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-secondary)' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="이름/조직 검색"
              className="text-sm pl-8 pr-3 py-1.5 rounded-lg border outline-none focus:border-primary-400"
              style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
            />
          </div>
        </div>
        <Link to="/editor"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700 shrink-0">
          <Plus size={15} /> 새 Architecture
        </Link>
      </div>
      <div className="sm:hidden space-y-2">
        {filtered.length === 0 && (
          <div className="px-4 py-8 rounded-xl border text-center text-sm"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text-secondary)' }}>
            {searchQuery ? '검색 결과가 없습니다.' : 'Architecture가 없습니다.'}
          </div>
        )}
        {filtered.map(entry => (
          <div key={entry.id} className="rounded-xl border p-3"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold break-words" style={{ color: 'var(--text)' }}>{entry.name}</p>
                <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {[entry.architecture_category?.toUpperCase(), entry.branch_type, entry.organization, entry.release_date?.slice(0, 4)]
                    .filter(Boolean).join(' · ')}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-0.5">
                {entry.related_post_slug && (
                  <Link to={`/post/${entry.related_post_slug}`} title="포스트 보기"
                    className="p-2 rounded-lg hover:bg-gray-100" style={{ color: 'var(--text-secondary)' }}>
                    <Eye size={15} />
                  </Link>
                )}
                <Link
                  to={entry.related_post_slug ? `/editor/${entry.related_post_slug}` : `/editor`}
                  title="편집"
                  className="p-2 rounded-lg hover:bg-blue-50 hover:text-blue-600" style={{ color: 'var(--text-secondary)' }}>
                  <Pencil size={15} />
                </Link>
                <button
                  onClick={async () => {
                    if (!confirm(`"${entry.name}" 삭제?`)) return
                    try {
                      await deleteArchitecture(entry.slug)
                      toast.success('삭제 완료')
                      loadArchitectures()
                    } catch { toast.error('삭제 실패') }
                  }}
                  title="삭제"
                  className="p-2 rounded-lg hover:bg-red-50 hover:text-red-600"
                  style={{ color: 'var(--text-secondary)' }}>
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="hidden sm:block rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th className="px-3 py-2 text-left font-medium cursor-pointer select-none" style={{ color: 'var(--text-secondary)' }}
                onClick={() => handleSort('name')}>
                Name{sortIndicator('name')}
              </th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell cursor-pointer select-none" style={{ color: 'var(--text-secondary)' }}
                onClick={() => handleSort('category')}>
                Category{sortIndicator('category')}
              </th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>Branch</th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>Org</th>
              <th className="px-3 py-2 text-center font-medium hidden lg:table-cell" style={{ color: 'var(--text-secondary)' }}>Figure</th>
              <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>액션</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                  {searchQuery ? '검색 결과가 없습니다.' : 'Architecture가 없습니다.'}
                </td>
              </tr>
            )}
            {filtered.map(entry => (
              <tr key={entry.id} className="border-t hover:bg-gray-50 transition-colors" style={{ borderColor: 'var(--border)' }}>
                <td className="px-3 py-2">
                  <span className="font-medium" style={{ color: 'var(--text)' }}>{entry.name}</span>
                  <span className="text-xs ml-1" style={{ color: 'var(--text-secondary)' }}>
                    {entry.release_date?.slice(0, 4)}
                  </span>
                </td>
                <td className="px-3 py-2 hidden md:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {entry.architecture_category?.toUpperCase()}
                </td>
                <td className="px-3 py-2 hidden md:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {entry.branch_type}
                </td>
                <td className="px-3 py-2 hidden md:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {entry.organization}
                </td>
                <td className="px-3 py-2 hidden lg:table-cell text-center">
                  {entry.figure_url && !entry.figure_placeholder ? (
                    <Image size={14} className="inline-block" style={{ color: '#10B981' }} />
                  ) : entry.figure_placeholder ? (
                    <span title="Placeholder figure"><AlertTriangle size={14} className="inline-block" style={{ color: '#F59E0B' }} /></span>
                  ) : (
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>-</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-0.5 justify-end">
                    {entry.related_post_slug && (
                      <Link to={`/post/${entry.related_post_slug}`} title="포스트 보기"
                        className="p-1.5 rounded hover:bg-gray-100" style={{ color: 'var(--text-secondary)' }}>
                        <Eye size={14} />
                      </Link>
                    )}
                    <Link
                      to={entry.related_post_slug ? `/editor/${entry.related_post_slug}` : `/editor`}
                      title="편집"
                      className="p-1.5 rounded hover:bg-blue-50 hover:text-blue-600" style={{ color: 'var(--text-secondary)' }}>
                      <Pencil size={14} />
                    </Link>
                    <button
                      onClick={async () => {
                        if (!confirm(`"${entry.name}" 삭제?`)) return
                        try {
                          await deleteArchitecture(entry.slug)
                          toast.success('삭제 완료')
                          loadArchitectures()
                        } catch { toast.error('삭제 실패') }
                      }}
                      title="삭제"
                      className="p-1.5 rounded hover:bg-red-50 hover:text-red-600"
                      style={{ color: 'var(--text-secondary)' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
