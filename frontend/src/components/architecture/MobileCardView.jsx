import { useMemo } from 'react'
import { Building2, Calendar, Cpu, FileText } from 'lucide-react'
import { CATEGORY_COLORS } from '../../data/architectureConstants'

// 좁은 화면에서는 그래프 대신 카드 목록을 보여 준다. 손가락으로 줌·팬 하며
// 계보를 따라가기가 어려워 카테고리별 묶음이 더 읽힌다.
export default function MobileCardView({
  nodes,
  searchQuery,
  onNodeClick,
  selectedNode,
  categoryColors = CATEGORY_COLORS,
  categoryField = 'architecture_category',
}) {
  const lowerQuery = (searchQuery || '').toLowerCase()
  const filtered = lowerQuery
    ? nodes.filter(n => n.name.toLowerCase().includes(lowerQuery) || n.organization?.toLowerCase().includes(lowerQuery))
    : nodes

  // 카테고리별 그룹핑
  const grouped = useMemo(() => {
    const groups = {}
    for (const node of filtered) {
      const cat = node[categoryField] || 'technique'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(node)
    }
    for (const cat of Object.keys(groups)) {
      groups[cat].sort((a, b) => (b.release_date || b.name || '').localeCompare(a.release_date || a.name || ''))
    }
    return groups
  }, [filtered, categoryField])

  if (filtered.length === 0) {
    return (
      <div className="py-12 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
        {searchQuery ? `"${searchQuery}"에 대한 결과가 없습니다.` : '아키텍처 항목이 없습니다.'}
      </div>
    )
  }

  return (
    <div className="px-4 py-4 space-y-6 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 120px)' }}>
      {Object.entries(grouped).map(([cat, catNodes]) => (
        <div key={cat}>
          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: categoryColors[cat] || '#8895A7' }} />
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: categoryColors[cat] || 'var(--text-secondary)' }}>
              {cat} ({catNodes.length})
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {catNodes.map(node => {
              const color = categoryColors[node[categoryField]] || '#8895A7'
              const isSelected = selectedNode?.slug === node.slug
              return (
                <button
                  key={node.slug}
                  onClick={() => onNodeClick(node)}
                  className="text-left p-3 rounded-xl border transition-all"
                  style={{
                    borderColor: isSelected ? color : 'var(--border)',
                    background: isSelected ? color + '08' : 'var(--card-bg)',
                  }}
                >
                  <div className="flex items-start gap-2.5">
                    {node.figure_url ? (
                      <div className="w-10 h-10 rounded-lg shrink-0 overflow-hidden" style={{ background: 'var(--bg)' }}>
                        <img src={node.figure_url} alt="" className="w-full h-full object-cover" loading="lazy" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center" style={{ background: color + '12' }}>
                        <Cpu size={16} style={{ color }} />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{node.name}</div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {node.organization && <span className="flex items-center gap-0.5"><Building2 size={10} /> {node.organization}</span>}
                        {node.release_date && <span className="flex items-center gap-0.5"><Calendar size={10} /> {node.release_date.slice(0, 4)}</span>}
                        {node.param_scale && <span>{node.param_scale}</span>}
                      </div>
                    </div>
                    {node.related_post_slug && (
                      <FileText size={12} className="shrink-0 mt-1" style={{ color: 'var(--text-secondary)' }} />
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
