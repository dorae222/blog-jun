import { Link } from 'react-router-dom'
import { GitBranch, ArrowRight, ArrowLeft, ExternalLink, Layers } from 'lucide-react'

const RELATION_LABELS = {
  evolved_from: '발전 기반',
  inspired_by: '영감',
  variant_of: '변형',
  technique_used: '기법 적용',
}

const ARCH_CATEGORY_COLORS = {
  llm: '#3B82F6',
  ssm: '#10B981',
  diffusion: '#F59E0B',
  multimodal: '#8B5CF6',
  agent: '#EF4444',
  technique: '#6B7280',
  vision: '#EC4899',
}

function LineageChip({ item, direction }) {
  const inner = (
    <>
      {direction === 'in' && <ArrowLeft size={10} className="text-primary-600" />}
      {item.name}
      {direction === 'out' && <ArrowRight size={10} className="text-primary-600" />}
    </>
  )

  const className = "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all"

  if (item.post_slug) {
    return (
      <Link
        to={`/post/${item.post_slug}`}
        className={`${className} hover:shadow-sm hover:-translate-y-0.5`}
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
      >
        {inner}
      </Link>
    )
  }

  return (
    <span
      className={`${className} opacity-60 cursor-default`}
      style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
    >
      {inner}
    </span>
  )
}

function groupByRelationType(items) {
  const groups = {}
  for (const item of items) {
    const type = item.relation_type || 'evolved_from'
    if (!groups[type]) groups[type] = []
    groups[type].push(item)
  }
  return groups
}

export default function ArchitectureLineageCard({ entries }) {
  if (!entries?.length) return null

  return (
    <div className="mt-8 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Layers size={16} className="text-primary-600" />
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Architecture Lineage</h3>
      </div>

      {entries.map(entry => {
        const catColor = ARCH_CATEGORY_COLORS[entry.architecture_category] || 'var(--color-primary-500)'

        return (
          <div
            key={entry.slug}
            className="p-5 rounded-xl"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderLeft: `4px solid ${catColor}`,
            }}
          >
            {/* Entry header */}
            <div className="flex items-center gap-2 mb-4">
              <GitBranch size={16} className="text-primary-600 shrink-0" />
              <span
                className="font-semibold text-sm"
                style={{ color: 'var(--text)' }}
              >
                {entry.name}
              </span>
              {entry.branch_type && (
                <span
                  className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                  style={{ background: 'var(--color-primary-500)', color: '#fff' }}
                >
                  {entry.branch_type?.replace('_', ' ')}
                </span>
              )}
              {entry.architecture_category && (
                <span
                  className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                  style={{ background: `${catColor}20`, color: catColor }}
                >
                  {entry.architecture_category}
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
                  <div className="space-y-2">
                    {Object.entries(groupByRelationType(entry.parent_names)).map(([type, items]) => (
                      <div key={type}>
                        <span
                          className="text-[10px] font-medium mb-1 block"
                          style={{ color: 'var(--text-secondary)' }}
                        >
                          {RELATION_LABELS[type] || type}
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {items.map(p => (
                            <LineageChip key={p.slug} item={p} direction="in" />
                          ))}
                        </div>
                      </div>
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
                  <div className="space-y-2">
                    {Object.entries(groupByRelationType(entry.child_names)).map(([type, items]) => (
                      <div key={type}>
                        <span
                          className="text-[10px] font-medium mb-1 block"
                          style={{ color: 'var(--text-secondary)' }}
                        >
                          {RELATION_LABELS[type] || type}
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {items.map(c => (
                            <LineageChip key={c.slug} item={c} direction="out" />
                          ))}
                        </div>
                      </div>
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
                to={`/posts/ai`}
                className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full
                  border hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
              >
                <Layers size={11} /> AI Posts
              </Link>
            </div>
          </div>
        )
      })}
    </div>
  )
}
