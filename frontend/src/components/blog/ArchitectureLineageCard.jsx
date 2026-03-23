import { Link } from 'react-router-dom'
import {
  GitBranch, ArrowRight, ArrowLeft, Layers,
  FileText, Code2, BookOpen, Calendar, Cpu, ExternalLink,
} from 'lucide-react'

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
      <span className="font-medium">{item.name}</span>
      {direction === 'out' && <ArrowRight size={10} className="text-primary-600" />}
    </>
  )

  const baseClass = "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all"

  if (item.post_slug) {
    return (
      <Link
        to={`/post/${item.post_slug}`}
        className={`${baseClass} hover:shadow-sm hover:-translate-y-0.5`}
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
      >
        {inner}
        <ExternalLink size={9} className="opacity-40" />
      </Link>
    )
  }

  return (
    <span
      className={`${baseClass} cursor-default`}
      style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)', opacity: 0.75 }}
      title="관련 포스트 없음"
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

function SpecBadge({ icon: Icon, label }) {
  if (!label) return null
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium"
      style={{ background: 'var(--card-bg)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}
    >
      <Icon size={11} className="shrink-0" />
      {label}
    </span>
  )
}

function ConceptTag({ concept }) {
  const bgColor = concept.color ? `${concept.color}18` : 'var(--card-bg)'
  const textColor = concept.color || 'var(--text-secondary)'
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold"
      style={{ background: bgColor, color: textColor, border: `1px solid ${concept.color || 'var(--border)'}40` }}
    >
      {concept.abbreviation || concept.name}
    </span>
  )
}

function ExternalLinkButton({ href, icon: Icon, label }) {
  if (!href) return null
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full
        border hover:shadow-sm transition-all hover:-translate-y-0.5"
      style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--card-bg)' }}
    >
      <Icon size={12} />
      {label}
    </a>
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

      {entries.map(entry => {
        const catColor = ARCH_CATEGORY_COLORS[entry.architecture_category] || 'var(--color-primary-500)'
        const releaseYear = entry.release_date ? new Date(entry.release_date).getFullYear() : null
        const hasSpecs = entry.param_scale || entry.context_length || entry.attention_type
        const hasConcepts = entry.concepts?.length > 0
        const hasLinks = entry.paper_url || entry.code_url || entry.related_post_slug
        const hasParents = entry.parent_names?.length > 0
        const hasChildren = entry.child_names?.length > 0

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
            {/* Header: figure + name + badges + org/year */}
            <div className="flex items-start gap-3 mb-3">
              {/* Figure thumbnail */}
              <div
                className="w-12 h-12 rounded-lg shrink-0 flex items-center justify-center overflow-hidden"
                style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}
              >
                {entry.figure_url ? (
                  <img
                    src={entry.figure_url}
                    alt={entry.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <Cpu size={20} style={{ color: catColor }} />
                )}
              </div>

              <div className="flex-1 min-w-0">
                {/* Name + category/branch badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className="font-semibold text-sm"
                    style={{ color: 'var(--text)' }}
                  >
                    {entry.name}
                  </span>
                  {entry.architecture_category && (
                    <span
                      className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                      style={{ background: `${catColor}20`, color: catColor }}
                    >
                      {entry.architecture_category.toUpperCase()}
                    </span>
                  )}
                  {entry.branch_type && (
                    <span
                      className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                      style={{ background: 'var(--color-primary-500)', color: '#fff' }}
                    >
                      {entry.branch_type?.replace('_', ' ')}
                    </span>
                  )}
                </div>

                {/* Organization + release year */}
                <div className="flex items-center gap-1.5 mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {entry.organization && <span>{entry.organization}</span>}
                  {entry.organization && releaseYear && <span>·</span>}
                  {releaseYear && (
                    <span className="inline-flex items-center gap-0.5">
                      <Calendar size={10} />
                      {releaseYear}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Key detail summary */}
            {entry.key_detail && (
              <p
                className="text-xs leading-relaxed mb-3 line-clamp-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                {entry.key_detail}
              </p>
            )}

            {/* Spec badges */}
            {hasSpecs && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                <SpecBadge icon={Cpu} label={entry.param_scale} />
                <SpecBadge icon={Layers} label={entry.context_length} />
                <SpecBadge icon={GitBranch} label={entry.attention_type} />
              </div>
            )}

            {/* Concept tags */}
            {hasConcepts && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {entry.concepts.slice(0, 6).map(concept => (
                  <ConceptTag key={concept.id || concept.slug} concept={concept} />
                ))}
              </div>
            )}

            {/* Lineage: Parents and Children */}
            {(hasParents || hasChildren) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs mb-4">
                {/* Influenced by */}
                <div>
                  <div className="flex items-center gap-1 mb-2 font-medium" style={{ color: 'var(--text-secondary)' }}>
                    <ArrowLeft size={12} /> Influenced by
                  </div>
                  {hasParents ? (
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
                  {hasChildren ? (
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
            )}

            {/* External links */}
            {hasLinks && (
              <div className="flex flex-wrap gap-2 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                <ExternalLinkButton href={entry.paper_url} icon={FileText} label="Paper" />
                <ExternalLinkButton href={entry.code_url} icon={Code2} label="Code" />
                {entry.related_post_slug && (
                  <Link
                    to={`/post/${entry.related_post_slug}`}
                    className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full
                      border hover:shadow-sm transition-all hover:-translate-y-0.5"
                    style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--card-bg)' }}
                  >
                    <BookOpen size={12} />
                    Post
                  </Link>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
