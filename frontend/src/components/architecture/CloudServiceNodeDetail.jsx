import { motion } from 'framer-motion'
import {
  X, ExternalLink, FileText, Calendar,
  ArrowRight, ArrowLeft, Cloud, Server, Cog,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { CLOUD_DOMAIN_COLORS } from '../../data/cloudConstants'

const PROVIDER_COLORS = {
  AWS: '#FF9900',
  GCP: '#4285F4',
  Azure: '#0078D4',
  Cloudflare: '#F38020',
  Docker: '#2496ED',
}

const RELATION_LABELS = {
  integrates_with: 'integrates',
  depends_on: 'depends on',
  alternative_to: 'alternative',
  part_of: 'part of',
  evolved_from: 'evolved from',
}

export default function CloudServiceNodeDetail({
  node,
  edges,
  onClose,
  onNodeFocus,
  layout = 'bottom',
  hideRelations = false,
}) {
  const navigate = useNavigate()
  if (!node) return null

  const domainColor = CLOUD_DOMAIN_COLORS[node.service_domain] || '#6B7280'
  const providerColor = PROVIDER_COLORS[node.provider] || '#6B7280'

  // 부모/자식 — hideRelations 시 빈 배열
  const parents = hideRelations ? [] : edges
    .filter(e => e.to_slug === node.slug)
    .map(e => ({ slug: e.from_slug, name: e.from_name, type: e.relation_type }))

  const children = hideRelations ? [] : edges
    .filter(e => e.from_slug === node.slug)
    .map(e => ({ slug: e.to_slug, name: e.to_name, type: e.relation_type }))

  const isSide = layout === 'side'

  const motionProps = isSide
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } }
    : { initial: { y: '100%', opacity: 0 }, animate: { y: 0, opacity: 1 }, exit: { y: '100%', opacity: 0 } }

  const containerClass = isSide
    ? 'h-full overflow-hidden flex flex-col'
    : 'absolute bottom-0 left-0 right-0 z-30 rounded-t-2xl shadow-2xl overflow-hidden'

  const containerStyle = isSide
    ? { background: 'var(--card-bg)', boxShadow: `inset 0 3px 0 ${domainColor}`, borderRight: '1px solid var(--border)' }
    : { background: 'var(--card-bg)', borderTop: `3px solid ${domainColor}`, maxHeight: '50vh' }

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
            <h3
              className={`${isSide ? 'text-base' : 'text-lg'} font-bold truncate`}
              style={{ color: 'var(--text-primary)' }}
            >
              {node.name}
            </h3>
            {node.provider && (
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
                style={{ backgroundColor: providerColor + '20', color: providerColor }}
              >
                {node.provider}
              </span>
            )}
            {node.service_domain && (
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
                style={{ backgroundColor: domainColor + '20', color: domainColor }}
              >
                {(node.service_domain || '').replace(/_/g, ' ')}
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

      {/* 태그 행 */}
      {(node.is_serverless || node.is_managed || node.launch_year) && (
        <div className="flex flex-wrap gap-1.5 px-4 pb-2 shrink-0">
          {node.is_serverless && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: '#10B98120', color: '#10B981' }}
            >
              Serverless
            </span>
          )}
          {node.is_managed && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: '#3B82F620', color: '#3B82F6' }}
            >
              Managed
            </span>
          )}
          {node.launch_year && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full flex items-center gap-1"
              style={{ backgroundColor: '#6B728020', color: '#6B7280' }}
            >
              <Calendar size={11} /> {node.launch_year}
            </span>
          )}
        </div>
      )}

      {/* 링크 버튼 — 스크롤 영역 밖 */}
      {(node.docs_url || node.related_post_slug) && (
        <div className="flex flex-wrap gap-2 px-4 pb-2 shrink-0">
          {node.docs_url && (
            <a
              href={node.docs_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:opacity-80"
              style={{ background: domainColor + '15', color: domainColor }}
            >
              <ExternalLink size={13} /> Docs
            </a>
          )}
          {node.related_post_slug && (
            <button
              onClick={() => navigate(`/post/${node.related_post_slug}`)}
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:opacity-80"
              style={{ background: 'var(--bg)', color: 'var(--text-primary)' }}
            >
              <FileText size={13} /> Blog Post
            </button>
          )}
        </div>
      )}

      <div className="px-4 pb-4" style={scrollStyle}>
        {/* Key Detail (plain text) */}
        {node.key_detail && (
          <div
            className="text-sm leading-relaxed mb-3 whitespace-pre-line"
            style={{ color: 'var(--text-secondary)' }}
          >
            {node.key_detail}
          </div>
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
                  <ArrowLeft size={12} /> Depends On
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {parents.map((p, i) => (
                    <button
                      key={`${p.slug}-${i}`}
                      onClick={() => onNodeFocus?.(p.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text-primary)' }}
                    >
                      {p.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({RELATION_LABELS[p.type] || p.type?.replace(/_/g, ' ')})
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
                  <ArrowRight size={12} /> Integrates With
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {children.map((c, i) => (
                    <button
                      key={`${c.slug}-${i}`}
                      onClick={() => onNodeFocus?.(c.slug)}
                      className="text-xs px-2.5 py-1 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1"
                      style={{ background: 'var(--bg)', color: 'var(--text-primary)' }}
                    >
                      {c.name}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                        ({RELATION_LABELS[c.type] || c.type?.replace(/_/g, ' ')})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
