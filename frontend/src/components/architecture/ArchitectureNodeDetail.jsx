import { motion } from 'framer-motion'
import {
  X, ExternalLink, FileText, Calendar, Building2,
  ArrowRight, ArrowLeft,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { CATEGORY_COLORS } from '../../data/architectureConstants'

export default function ArchitectureNodeDetail({
  node,
  edges,
  onClose,
  onNodeFocus,
  layout = 'bottom', // 'bottom' | 'side'
}) {
  const navigate = useNavigate()
  if (!node) return null

  const color = CATEGORY_COLORS[node.architecture_category] || '#6B7280'

  // 부모: 이 노드를 가리키는 엣지 (to_slug === node.slug)
  const parents = edges
    .filter(e => e.to_slug === node.slug)
    .map(e => ({ slug: e.from_slug, name: e.from_name, type: e.relation_type }))

  // 자식: 이 노드에서 출발하는 엣지 (from_slug === node.slug)
  const children = edges
    .filter(e => e.from_slug === node.slug)
    .map(e => ({ slug: e.to_slug, name: e.to_name, type: e.relation_type }))

  const releaseYear = node.release_date?.slice(0, 4)

  const specs = [
    { label: 'Parameters', value: node.param_scale },
    { label: 'Context', value: node.context_length },
    { label: 'Decoder', value: node.decoder_type?.replace(/_/g, ' ') },
    { label: 'Branch', value: node.branch_type },
  ].filter(s => s.value)

  const isSide = layout === 'side'

  const motionProps = isSide
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { y: '100%', opacity: 0 }, animate: { y: 0, opacity: 1 }, exit: { y: '100%', opacity: 0 } }

  const containerClass = isSide
    ? 'h-full overflow-hidden flex flex-col'
    : 'absolute bottom-0 left-0 right-0 z-30 rounded-t-2xl shadow-2xl overflow-hidden'

  const containerStyle = isSide
    ? { background: 'var(--card-bg)', borderLeft: `3px solid ${color}` }
    : { background: 'var(--card-bg)', borderTop: `3px solid ${color}`, maxHeight: '50vh' }

  const scrollStyle = isSide
    ? { flex: 1, overflowY: 'auto' }
    : { maxHeight: 'calc(50vh - 70px)', overflowY: 'auto' }

  return (
    <motion.div
      {...motionProps}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      className={containerClass}
      style={containerStyle}
    >
      {/* 헤더 */}
      <div className="flex items-start justify-between px-4 pt-3 pb-2 shrink-0">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className={`${isSide ? 'text-base' : 'text-lg'} font-bold truncate`} style={{ color: 'var(--text)' }}>
              {node.name}
            </h3>
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
              style={{ backgroundColor: color + '20', color }}
            >
              {(node.architecture_category || '').toUpperCase()}
            </span>
            {node.is_open_source && (
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ backgroundColor: '#10B98120', color: '#10B981' }}
              >
                Open Source
              </span>
            )}
          </div>
          <div
            className="flex items-center gap-3 mt-1 text-sm"
            style={{ color: 'var(--text-secondary)' }}
          >
            {node.organization && (
              <span className="flex items-center gap-1">
                <Building2 size={13} /> {node.organization}
              </span>
            )}
            {releaseYear && (
              <span className="flex items-center gap-1">
                <Calendar size={13} /> {releaseYear}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-gray-100/10 transition-colors shrink-0 ml-2"
          style={{ color: 'var(--text-secondary)' }}
          aria-label="닫기"
        >
          <X size={18} />
        </button>
      </div>

      <div className="px-4 pb-4" style={scrollStyle}>
        {/* Figure 썸네일 */}
        {node.figure_url && (
          <div
            className="rounded-xl overflow-hidden mb-3 flex items-center justify-center"
            style={{ background: 'var(--bg)', maxHeight: isSide ? '200px' : '160px' }}
          >
            <img
              src={node.figure_url}
              alt={node.name}
              className={`max-w-full ${isSide ? 'max-h-[200px]' : 'max-h-[160px]'} object-contain p-2`}
              loading="lazy"
            />
          </div>
        )}

        {/* Specs 그리드 */}
        {specs.length > 0 && (
          <div className={`grid ${isSide ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-4'} gap-2 mb-3`}>
            {specs.map(s => (
              <div
                key={s.label}
                className="rounded-lg px-3 py-2 text-center"
                style={{ background: 'var(--bg)' }}
              >
                <div className="text-xs mb-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {s.label}
                </div>
                <div className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
                  {s.value}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Detail */}
        {node.key_detail && (
          <p
            className="text-sm leading-relaxed mb-3"
            style={{ color: 'var(--text-secondary)' }}
          >
            {node.key_detail}
          </p>
        )}

        {/* 관계 (부모/자식) */}
        {(parents.length > 0 || children.length > 0) && (
          <div className="mb-3 space-y-2">
            {parents.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <ArrowLeft size={12} /> Parent Models
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {parents.map((p, i) => (
                    <button
                      key={`${p.slug}-${i}`}
                      onClick={() => onNodeFocus?.(p.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text)' }}
                    >
                      {p.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({p.type?.replace(/_/g, ' ')})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {children.length > 0 && (
              <div>
                <div
                  className="text-xs font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <ArrowRight size={12} /> Derived Models
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {children.map((c, i) => (
                    <button
                      key={`${c.slug}-${i}`}
                      onClick={() => onNodeFocus?.(c.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text)' }}
                    >
                      {c.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({c.type?.replace(/_/g, ' ')})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 링크 버튼 */}
        <div className="flex flex-wrap gap-2">
          {node.paper_url && (
            <a
              href={node.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:opacity-80"
              style={{ background: color + '15', color }}
            >
              <ExternalLink size={13} /> Paper
            </a>
          )}
          {node.related_post_slug && (
            <button
              onClick={() => navigate(`/post/${node.related_post_slug}`)}
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:opacity-80"
              style={{ background: 'var(--bg)', color: 'var(--text)' }}
            >
              <FileText size={13} /> Blog Post
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}
