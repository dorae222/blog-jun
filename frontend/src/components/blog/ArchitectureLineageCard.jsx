import { Link } from 'react-router-dom'
import { GitBranch, ArrowRight, ArrowLeft, ExternalLink, Layers } from 'lucide-react'

function LineageChip({ item, direction }) {
  return (
    <Link
      to={`/post/${item.slug}`}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium
        transition-all hover:shadow-sm hover:-translate-y-0.5"
      style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
    >
      {direction === 'in' && <ArrowLeft size={10} className="text-primary-600" />}
      {item.name}
      {direction === 'out' && <ArrowRight size={10} className="text-primary-600" />}
    </Link>
  )
}

export default function ArchitectureLineageCard({ entries }) {
  if (!entries?.length) return null

  return (
    <div className="mt-8 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Layers size={16} className="text-primary-600" />
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Architecture Lineage</h3>
      </div>

      {entries.map(entry => (
        <div
          key={entry.slug}
          className="p-5 rounded-xl border-l-4"
          style={{
            background: 'var(--bg-secondary)',
            borderColor: 'var(--border)',
            borderLeftColor: 'var(--color-primary-500)',
            border: '1px solid var(--border)',
            borderLeft: '4px solid var(--color-primary-500)',
          }}
        >
          {/* Entry header */}
          <div className="flex items-center gap-2 mb-4">
            <GitBranch size={16} className="text-primary-600 shrink-0" />
            <Link
              to={`/post/${entry.slug}`}
              className="font-semibold text-sm hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text)' }}
            >
              {entry.name}
            </Link>
            {entry.branch_type && (
              <span
                className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                style={{ background: 'var(--color-primary-500)', color: '#fff' }}
              >
                {entry.branch_type?.replace('_', ' ')}
              </span>
            )}
          </div>

          {/* Parents and Children */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            {/* Influenced by */}
            <div>
              <div className="flex items-center gap-1 mb-2 font-medium" style={{ color: 'var(--text-secondary)' }}>
                <ArrowLeft size={12} /> Influenced by
              </div>
              {entry.parent_names?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {entry.parent_names.map(p => (
                    <LineageChip key={p.slug} item={p} direction="in" />
                  ))}
                </div>
              ) : (
                <div
                  className="px-3 py-2 rounded-lg border border-dashed text-center"
                  style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
                >
                  No known parents
                </div>
              )}
            </div>

            {/* Influenced */}
            <div>
              <div className="flex items-center gap-1 mb-2 font-medium" style={{ color: 'var(--text-secondary)' }}>
                Influenced <ArrowRight size={12} />
              </div>
              {entry.child_names?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {entry.child_names.map(c => (
                    <LineageChip key={c.slug} item={c} direction="out" />
                  ))}
                </div>
              ) : (
                <div
                  className="px-3 py-2 rounded-lg border border-dashed text-center"
                  style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
                >
                  No known descendants
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="mt-4 flex gap-2">
            <Link
              to={`/post/${entry.slug}`}
              className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full
                bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              <ExternalLink size={11} /> Detail
            </Link>
            <Link
              to="/posts/ai"
              className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full
                border hover:bg-gray-50 transition-colors"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            >
              <Layers size={11} /> AI Posts
            </Link>
          </div>
        </div>
      ))}
    </div>
  )
}
