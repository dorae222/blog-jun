import { Link } from 'react-router-dom'
import { Eye, Pencil, Trash2, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ArchitecturesTab({
  archEntries, archCatFilter, setArchCatFilter,
  loadArchitectures, deleteArchitecture,
  ARCH_CATEGORIES,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {archEntries.length}개 Architecture
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
        </div>
        <Link to="/editor"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm hover:bg-primary-700">
          <Plus size={15} /> 새 Architecture
        </Link>
      </div>
      <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>Name</th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>Category</th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>Branch</th>
              <th className="px-3 py-2 text-left font-medium hidden md:table-cell" style={{ color: 'var(--text-secondary)' }}>Org</th>
              <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>액션</th>
            </tr>
          </thead>
          <tbody>
            {archEntries.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                  Architecture가 없습니다.
                </td>
              </tr>
            )}
            {archEntries.map(entry => (
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
