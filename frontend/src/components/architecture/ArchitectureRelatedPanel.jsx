import { useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, GitFork, ChevronDown } from 'lucide-react'
import { CATEGORY_COLORS } from '../../data/architectureConstants'

const RELATION_LABELS = {
  evolved_from: 'evolved',
  inspired_by: 'inspired',
  variant_of: 'variant',
  technique_used: 'technique',
}

function RelatedItem({ item, nodeMap, onNodeFocus }) {
  const meta = nodeMap.get(item.slug)
  const color = CATEGORY_COLORS[meta?.architecture_category] || '#8895A7'
  const displayName = item.name || meta?.name || item.slug
  const org = meta?.organization
  const year = meta?.release_date?.slice(0, 4)

  return (
    <button
      onClick={() => onNodeFocus(item.slug)}
      className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50/5 transition-colors group"
    >
      <div className="flex items-start gap-2">
        <span
          className="w-2 h-2 rounded-full shrink-0 mt-1.5"
          style={{ background: color }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span
              className="text-sm font-medium truncate"
              style={{ color: 'var(--text)' }}
            >
              {displayName}
            </span>
            <span
              className="text-[10px] px-1.5 py-0.5 rounded shrink-0"
              style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
            >
              {RELATION_LABELS[item.type] || item.type}
            </span>
          </div>
          {(org || year) && (
            <div className="flex items-center gap-1.5 mt-0.5 text-[11px]" style={{ color: 'var(--text-secondary)' }}>
              {org && <span>{org}</span>}
              {org && year && <span>·</span>}
              {year && <span>{year}</span>}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

function Section({ icon: Icon, title, items, nodeMap, onNodeFocus, defaultExpanded = true, maxItems = 0 }) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const [showAll, setShowAll] = useState(false)

  if (items.length === 0) return null

  const visible = maxItems > 0 && !showAll ? items.slice(0, maxItems) : items
  const hasMore = maxItems > 0 && items.length > maxItems

  return (
    <div className="py-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 px-3 py-1 w-full text-left"
      >
        <Icon size={12} style={{ color: 'var(--text-secondary)' }} />
        <span
          className="text-[11px] font-semibold uppercase tracking-wider flex-1"
          style={{ color: 'var(--text-secondary)' }}
        >
          {title}
        </span>
        <span
          className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
          style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
        >
          {items.length}
        </span>
        <ChevronDown
          size={12}
          className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
          style={{ color: 'var(--text-secondary)' }}
        />
      </button>
      {expanded && (
        <div className="mt-1 space-y-0.5">
          {visible.map(item => (
            <RelatedItem
              key={item.slug}
              item={item}
              nodeMap={nodeMap}
              onNodeFocus={onNodeFocus}
            />
          ))}
          {hasMore && !showAll && (
            <button
              onClick={() => setShowAll(true)}
              className="w-full text-center text-[11px] py-1.5 rounded-lg hover:bg-gray-50/5 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              +{items.length - maxItems}개 더보기
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default function ArchitectureRelatedPanel({ node, edges, nodes, onNodeFocus }) {
  if (!node) return null

  const nodeMap = useMemo(() => {
    const map = new Map()
    nodes.forEach(n => map.set(n.slug, n))
    return map
  }, [nodes])

  const { parents, children, siblings } = useMemo(() => {
    const parents = edges
      .filter(e => e.to_slug === node.slug)
      .map(e => ({ slug: e.from_slug, name: e.from_name, type: e.relation_type }))

    const children = edges
      .filter(e => e.from_slug === node.slug)
      .map(e => ({ slug: e.to_slug, name: e.to_name, type: e.relation_type }))

    // Siblings: 같은 부모의 다른 자식
    const parentSlugs = new Set(parents.map(p => p.slug))
    const siblingMap = new Map()
    edges.forEach(e => {
      if (parentSlugs.has(e.from_slug) && e.to_slug !== node.slug) {
        if (!siblingMap.has(e.to_slug)) {
          siblingMap.set(e.to_slug, { slug: e.to_slug, name: e.to_name, type: e.relation_type })
        }
      }
    })

    return { parents, children, siblings: [...siblingMap.values()] }
  }, [node.slug, edges])

  const catColor = CATEGORY_COLORS[node.architecture_category] || '#8895A7'
  const total = parents.length + children.length

  return (
    <div
      className="h-full flex flex-col"
      style={{ background: 'var(--card-bg)', borderRight: `3px solid ${catColor}` }}
    >
      {/* 헤더 */}
      <div className="px-4 pt-3 pb-2 shrink-0">
        <h3 className="text-sm font-bold" style={{ color: 'var(--text)' }}>
          Related Models
        </h3>
        {total > 0 && (
          <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            {parents.length > 0 && `${parents.length} parent${parents.length > 1 ? 's' : ''}`}
            {parents.length > 0 && children.length > 0 && ' · '}
            {children.length > 0 && `${children.length} derived`}
          </p>
        )}
      </div>

      {/* 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto px-1 pb-4" style={{ scrollbarWidth: 'thin' }}>
        {total === 0 && siblings.length === 0 ? (
          <div className="px-3 py-8 text-center text-xs" style={{ color: 'var(--text-secondary)' }}>
            관련 모델이 없습니다.
          </div>
        ) : (
          <>
            <Section
              icon={ArrowLeft}
              title="Parent Models"
              items={parents}
              nodeMap={nodeMap}
              onNodeFocus={onNodeFocus}
            />

            {parents.length > 0 && children.length > 0 && (
              <div className="mx-3 border-t" style={{ borderColor: 'var(--border)' }} />
            )}

            <Section
              icon={ArrowRight}
              title="Derived Models"
              items={children}
              nodeMap={nodeMap}
              onNodeFocus={onNodeFocus}
            />

            {siblings.length > 0 && (
              <>
                <div className="mx-3 border-t" style={{ borderColor: 'var(--border)' }} />
                <Section
                  icon={GitFork}
                  title="Siblings"
                  items={siblings}
                  nodeMap={nodeMap}
                  onNodeFocus={onNodeFocus}
                  defaultExpanded={false}
                  maxItems={8}
                />
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
