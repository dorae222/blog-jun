import { Link } from 'react-router-dom'
import { GitBranch, ArrowRight, ArrowLeft } from 'lucide-react'

export default function ArchitectureLineageCard({ entries }) {
  if (!entries?.length) return null

  return (
    <div className="mt-8 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
      {entries.map(entry => (
        <div
          key={entry.slug}
          className="p-4 rounded-xl border"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <GitBranch size={16} className="text-primary-600" />
            <Link to={`/post/${entry.slug}`} className="font-semibold text-sm hover:text-primary-600 transition-colors" style={{ color: 'var(--text)' }}>
              {entry.name}
            </Link>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
              {entry.branch_type?.replace('_', ' ')}
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            {/* 부모 (영향받은 모델) */}
            <div className="flex-1">
              {entry.parent_names?.length > 0 ? (
                <div className="space-y-1">
                  <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>
                    <ArrowLeft size={10} className="inline" /> Influenced by
                  </span>
                  {entry.parent_names.map(p => (
                    <Link key={p.slug} to={`/post/${p.slug}`}
                      className="block text-primary-600 hover:underline">
                      {p.name}
                    </Link>
                  ))}
                </div>
              ) : (
                <span style={{ color: 'var(--text-secondary)' }}>No known parents</span>
              )}
            </div>

            {/* 자식 (후속 모델) */}
            <div className="flex-1 text-right">
              {entry.child_names?.length > 0 ? (
                <div className="space-y-1">
                  <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>
                    Influenced <ArrowRight size={10} className="inline" />
                  </span>
                  {entry.child_names.map(c => (
                    <Link key={c.slug} to={`/post/${c.slug}`}
                      className="block text-primary-600 hover:underline">
                      {c.name}
                    </Link>
                  ))}
                </div>
              ) : (
                <span style={{ color: 'var(--text-secondary)' }}>No known descendants</span>
              )}
            </div>
          </div>

          <div className="mt-3 flex gap-2">
            <Link to={`/post/${entry.slug}`}
              className="text-xs px-2.5 py-1 rounded-lg border hover:bg-gray-50 transition-colors"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              Detail
            </Link>
            <Link to="/posts/ai"
              className="text-xs px-2.5 py-1 rounded-lg border hover:bg-gray-50 transition-colors"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
              AI Posts
            </Link>
          </div>
        </div>
      ))}
    </div>
  )
}
