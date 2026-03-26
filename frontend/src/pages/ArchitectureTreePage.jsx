import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, GitFork, X } from 'lucide-react'
import ArchitectureGraph from '../components/architecture/ArchitectureGraph'
import ArchitectureNodeDetail from '../components/architecture/ArchitectureNodeDetail'
import { getArchitectureTree } from '../api/posts'

const CATEGORIES = [
  { key: 'all', label: 'All', color: '#6B7280' },
  { key: 'llm', label: 'LLM', color: '#3B82F6' },
  { key: 'ssm', label: 'SSM', color: '#10B981' },
  { key: 'diffusion', label: 'Diffusion', color: '#F59E0B' },
  { key: 'vision', label: 'Vision', color: '#EC4899' },
  { key: 'multimodal', label: 'Multimodal', color: '#8B5CF6' },
  { key: 'agent', label: 'Agent', color: '#EF4444' },
  { key: 'technique', label: 'Technique', color: '#6B7280' },
]

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

  // 데이터 로드
  const fetchTree = useCallback(async (cat) => {
    setLoading(true)
    setError(null)
    try {
      const params = cat && cat !== 'all' ? { category: cat } : {}
      const { data } = await getArchitectureTree(params)
      setNodes(data.nodes || [])
      setEdges(data.edges || [])
    } catch (err) {
      setError('Failed to load architecture tree.')
      console.error('Architecture tree fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTree(category)
  }, [category, fetchTree])

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
    }
  }, [nodes])

  // 검색 필터 적용 (그래프에 전달만, 필터링은 하지 않음 — dim 처리로 대응)
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
          <div className="flex items-center gap-1.5 flex-wrap flex-1">
            <GitFork size={16} style={{ color: 'var(--text-secondary)' }} className="shrink-0 mr-1" />
            {CATEGORIES.map(cat => {
              const active = category === cat.key
              return (
                <button
                  key={cat.key}
                  onClick={() => handleCategoryChange(cat.key)}
                  className="text-xs font-medium px-2.5 py-1 rounded-full transition-all"
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
              className="text-xs ml-1 hidden sm:inline"
              style={{ color: 'var(--text-secondary)' }}
            >
              {nodeCount} nodes / {edgeCount} edges
            </span>
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
              placeholder="Search models..."
              className="w-full text-sm pl-8 pr-8 py-1.5 rounded-lg border outline-none focus:border-primary-400"
              style={{
                borderColor: 'var(--border)',
                background: 'var(--bg)',
                color: 'var(--text)',
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-gray-200/20"
                style={{ color: 'var(--text-secondary)' }}
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 메인 영역 */}
      <div className="flex-1 relative overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 size={32} className="animate-spin" style={{ color: 'var(--text-secondary)' }} />
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{error}</p>
              <button
                onClick={() => fetchTree(category)}
                className="text-sm px-4 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : nodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              No architecture entries found for this category.
            </p>
          </div>
        ) : (
          <ArchitectureGraph
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
            selectedSlug={selectedNode?.slug}
            searchQuery={searchQuery}
            category={category}
          />
        )}

        {/* 하단 상세 패널 */}
        <AnimatePresence>
          {selectedNode && (
            <ArchitectureNodeDetail
              node={selectedNode}
              edges={edges}
              onClose={() => setSelectedNode(null)}
              onNodeFocus={handleNodeFocus}
            />
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
