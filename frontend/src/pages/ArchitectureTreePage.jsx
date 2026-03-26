import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, GitFork, X, LayoutGrid, Network, Building2, Calendar, Cpu, FileText } from 'lucide-react'
import ArchitectureGraph from '../components/architecture/ArchitectureGraph'
import ArchitectureNodeDetail from '../components/architecture/ArchitectureNodeDetail'
import ArchitectureRelatedPanel from '../components/architecture/ArchitectureRelatedPanel'
import { getArchitectureTree } from '../api/posts'
import { CATEGORY_COLORS, CATEGORIES } from '../data/architectureConstants'

// 모바일 카드 뷰 컴포넌트
function MobileCardView({ nodes, searchQuery, onNodeClick, selectedNode }) {
  const lowerQuery = (searchQuery || '').toLowerCase()
  const filtered = lowerQuery
    ? nodes.filter(n => n.name.toLowerCase().includes(lowerQuery) || n.organization?.toLowerCase().includes(lowerQuery))
    : nodes

  // 카테고리별 그룹핑
  const grouped = useMemo(() => {
    const groups = {}
    for (const node of filtered) {
      const cat = node.architecture_category || 'technique'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(node)
    }
    for (const cat of Object.keys(groups)) {
      groups[cat].sort((a, b) => (b.release_date || '').localeCompare(a.release_date || ''))
    }
    return groups
  }, [filtered])

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
            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: CATEGORY_COLORS[cat] || '#8895A7' }} />
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: CATEGORY_COLORS[cat] || 'var(--text-secondary)' }}>
              {cat} ({catNodes.length})
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {catNodes.map(node => {
              const color = CATEGORY_COLORS[node.architecture_category] || '#8895A7'
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

export default function ArchitectureTreePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [category, setCategory] = useState(searchParams.get('category') || 'all')
  const [mobileView, setMobileView] = useState('graph')
  const [matchIndex, setMatchIndex] = useState(0)
  const [isLgScreen, setIsLgScreen] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : true
  )

  const graphRef = useRef(null)

  // 화면 크기 감지 (좌측 패널 표시 여부)
  useEffect(() => {
    const handler = () => setIsLgScreen(window.innerWidth >= 1024)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  // 검색 매칭 slug 배열
  const matchedSlugs = useMemo(() => {
    if (!searchQuery) return []
    const q = searchQuery.toLowerCase()
    return nodes.filter(n => n.name.toLowerCase().includes(q)).map(n => n.slug)
  }, [nodes, searchQuery])

  // 데이터 로드
  const fetchTree = useCallback(async (cat) => {
    setLoading(true)
    setError(null)
    try {
      const params = cat && cat !== 'all' ? { category: cat } : {}
      const { data } = await getArchitectureTree(params)
      setNodes(data.nodes || [])
      setEdges(data.edges || [])
    } catch {
      setError('아키텍처 트리를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTree(category)
  }, [category, fetchTree])

  // URL ?selected= 파라미터로 초기 선택 복구
  useEffect(() => {
    if (!loading && nodes.length > 0) {
      const selectedSlug = searchParams.get('selected')
      if (selectedSlug && !selectedNode) {
        const target = nodes.find(n => n.slug === selectedSlug)
        if (target) setSelectedNode(target)
      }
    }
  }, [loading, nodes, searchParams])

  // Escape 키로 패널 닫기
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape' && selectedNode) setSelectedNode(null)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedNode])

  // 카테고리 변경
  const handleCategoryChange = useCallback((key) => {
    setCategory(key)
    setSelectedNode(null)
    setSearchParams(key === 'all' ? {} : { category: key })
  }, [setSearchParams])

  // 노드 클릭
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
  }, [])

  // 노드 더블 클릭 → 포스트 이동
  const handleNodeDoubleClick = useCallback((node) => {
    if (node?.related_post_slug) {
      navigate(`/post/${node.related_post_slug}`)
    }
  }, [navigate])

  // 상세 패널에서 관계 노드 포커스
  const handleNodeFocus = useCallback((slug) => {
    const target = nodes.find(n => n.slug === slug)
    if (target) {
      setSelectedNode(target)
      graphRef.current?.focusOnNode(slug)
    }
  }, [nodes])

  // 검색 Enter → 다음 매칭 포커스 이동
  const handleSearchKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && matchedSlugs.length > 0) {
      const nextIdx = (matchIndex + 1) % matchedSlugs.length
      setMatchIndex(nextIdx)
      const slug = matchedSlugs[nextIdx]
      graphRef.current?.focusOnNode(slug)
      const target = nodes.find(n => n.slug === slug)
      if (target) setSelectedNode(target)
    }
  }, [matchedSlugs, matchIndex, nodes])

  // matchIndex 리셋 when search changes
  useEffect(() => {
    setMatchIndex(0)
  }, [searchQuery])

  const nodeCount = nodes.length
  const edgeCount = edges.length

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col"
      style={{ height: 'calc(100vh - 64px)' }}
    >
      {/* 상단 바 */}
      <div
        className="shrink-0 border-b px-4 py-2.5"
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
      >
        <div className="max-w-full mx-auto flex flex-col sm:flex-row sm:items-center gap-2">
          {/* 카테고리 필터 */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide flex-1">
            <GitFork size={16} style={{ color: 'var(--text-secondary)' }} className="shrink-0 mr-1" />
            {CATEGORIES.map(cat => {
              const active = category === cat.key
              return (
                <button
                  key={cat.key}
                  onClick={() => handleCategoryChange(cat.key)}
                  className="text-xs font-medium px-2.5 py-1.5 rounded-full transition-all shrink-0 min-h-[36px]"
                  style={{
                    background: active ? cat.color + '20' : 'transparent',
                    color: active ? cat.color : 'var(--text-secondary)',
                    border: active ? `1px solid ${cat.color}40` : '1px solid transparent',
                  }}
                >
                  {cat.label}
                </button>
              )
            })}
            {/* 노드/엣지 카운트 */}
            <span
              className="text-xs ml-1 hidden sm:inline shrink-0"
              style={{ color: 'var(--text-secondary)' }}
            >
              {nodeCount} nodes / {edgeCount} edges
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* 모바일 뷰 토글 */}
            <div className="flex items-center border rounded-lg overflow-hidden md:hidden shrink-0"
              style={{ borderColor: 'var(--border)' }}>
              <button
                onClick={() => setMobileView('graph')}
                className="p-1.5 transition-colors"
                style={{
                  background: mobileView === 'graph' ? 'var(--text)' : 'transparent',
                  color: mobileView === 'graph' ? '#fff' : 'var(--text-secondary)',
                }}
                aria-label="그래프 뷰"
              >
                <Network size={14} />
              </button>
              <button
                onClick={() => setMobileView('list')}
                className="p-1.5 transition-colors"
                style={{
                  background: mobileView === 'list' ? 'var(--text)' : 'transparent',
                  color: mobileView === 'list' ? '#fff' : 'var(--text-secondary)',
                }}
                aria-label="리스트 뷰"
              >
                <LayoutGrid size={14} />
              </button>
            </div>

            {/* 검색 */}
            <div className="relative shrink-0 w-full sm:w-56">
              <Search
                size={14}
                className="absolute left-2.5 top-1/2 -translate-y-1/2"
                style={{ color: 'var(--text-secondary)' }}
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="모델 검색..."
                className="w-full text-sm pl-8 pr-16 py-1.5 rounded-lg border outline-none focus:border-primary-400"
                style={{
                  borderColor: 'var(--border)',
                  background: 'var(--bg)',
                  color: 'var(--text)',
                }}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {searchQuery && matchedSlugs.length > 0 && (
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded-md font-mono"
                    style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                  >
                    {matchIndex + 1}/{matchedSlugs.length}
                  </span>
                )}
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="p-0.5 rounded hover:bg-gray-200/20"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 영역 */}
      <div className="flex-1 relative overflow-hidden flex">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 size={32} className="animate-spin" style={{ color: 'var(--text-secondary)' }} />
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{error}</p>
              <button
                onClick={() => fetchTree(category)}
                className="text-sm px-4 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
              >
                다시 시도
              </button>
            </div>
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              해당 카테고리의 아키텍처 항목이 없습니다.
            </p>
          </div>
        ) : (
          <>
            {/* 데스크탑: 좌측 패널 + 그래프 + 우측 패널 */}
            <div className="hidden md:flex flex-1">
              {/* 좌측 관련 모델 패널 — lg+ 에서만 */}
              <AnimatePresence>
                {isLgScreen && selectedNode && (
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 260, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                    className="shrink-0 overflow-hidden border-r"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <ArchitectureRelatedPanel
                      node={selectedNode}
                      edges={edges}
                      nodes={nodes}
                      onNodeFocus={handleNodeFocus}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* 그래프 */}
              <div className="relative flex-1">
                <ArchitectureGraph
                  ref={graphRef}
                  nodes={nodes}
                  edges={edges}
                  onNodeClick={handleNodeClick}
                  onNodeDoubleClick={handleNodeDoubleClick}
                  selectedSlug={selectedNode?.slug}
                  searchQuery={searchQuery}
                />
              </div>

              {/* 우측 상세 패널 */}
              <AnimatePresence>
                {selectedNode && (
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 360, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                    className="shrink-0 overflow-hidden border-l"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <ArchitectureNodeDetail
                      node={selectedNode}
                      edges={edges}
                      onClose={() => setSelectedNode(null)}
                      onNodeFocus={handleNodeFocus}
                      layout="side"
                      hideRelations={isLgScreen}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 모바일: 그래프 or 리스트 뷰 */}
            <div className="md:hidden flex-1 relative">
              {mobileView === 'graph' ? (
                <ArchitectureGraph
                  nodes={nodes}
                  edges={edges}
                  onNodeClick={handleNodeClick}
                  onNodeDoubleClick={handleNodeDoubleClick}
                  selectedSlug={selectedNode?.slug}
                  searchQuery={searchQuery}
                />
              ) : (
                <MobileCardView
                  nodes={nodes}
                  searchQuery={searchQuery}
                  onNodeClick={handleNodeClick}
                  selectedNode={selectedNode}
                />
              )}
              {/* 모바일 하단 시트 */}
              <AnimatePresence>
                {selectedNode && (
                  <ArchitectureNodeDetail
                    node={selectedNode}
                    edges={edges}
                    onClose={() => setSelectedNode(null)}
                    onNodeFocus={handleNodeFocus}
                    layout="bottom"
                  />
                )}
              </AnimatePresence>
            </div>
          </>
        )}
      </div>
    </motion.div>
  )
}
