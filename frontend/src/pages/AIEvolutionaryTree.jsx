import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useNavigate } from 'react-router-dom'
import { Maximize2, Settings, Grid3x3 } from 'lucide-react'
import useAuth from '../hooks/useAuth'
import { getArchitectureTree, updateArchitecturePosition } from '../api/posts'
import ArchitectureTreeNode from '../components/architecture/ArchitectureTreeNode'
import TreeNodePopup from '../components/architecture/TreeNodePopup'

const BRANCH_COLORS = {
  encoder_only: '#60a5fa',
  encoder_decoder: '#34d399',
  decoder_only: '#a78bfa',
  ssm: '#22d3ee',
  diffusion: '#fbbf24',
  vision: '#f472b6',
  multimodal: '#fb7185',
  agent: '#a3e635',
}

const CATEGORY_FILTERS = [
  { value: '', label: 'All' },
  { value: 'llm', label: 'LLM' },
  { value: 'ssm', label: 'SSM' },
  { value: 'diffusion', label: 'Diffusion' },
  { value: 'vision', label: 'Vision' },
  { value: 'multimodal', label: 'Multimodal' },
  { value: 'agent', label: 'Agent' },
]

const EDGE_STYLES = {
  evolved_from: { strokeDasharray: undefined, opacity: 0.7 },
  inspired_by: { strokeDasharray: '6 4', opacity: 0.4 },
  variant_of: { strokeDasharray: '3 3', opacity: 0.5 },
  technique_used: { strokeDasharray: '2 6', opacity: 0.25 },
}

const nodeTypes = { architectureNode: ArchitectureTreeNode }

// 자동 레이아웃: branch_type별 Y축, release_date별 X축 배치
function autoLayout(rawNodes) {
  const branchOrder = [
    'encoder_only', 'encoder_decoder', 'decoder_only',
    'ssm', 'diffusion', 'vision', 'multimodal', 'agent',
  ]
  const branchY = {}
  branchOrder.forEach((b, i) => { branchY[b] = i * 120 })

  // release_date 기반 X 정렬
  const sorted = [...rawNodes].sort((a, b) => {
    const da = a.release_date || '2020-01-01'
    const db = b.release_date || '2020-01-01'
    return da.localeCompare(db)
  })

  // 같은 branch 내에서 겹침 방지
  const branchCounters = {}

  return sorted.map((n) => {
    const branch = n.branch_type || 'decoder_only'
    if (!branchCounters[branch]) branchCounters[branch] = 0

    const yearStr = n.release_date?.slice(0, 4) || '2020'
    const year = parseInt(yearStr, 10)
    const baseX = (year - 2015) * 200
    const offset = branchCounters[branch] * 30
    branchCounters[branch]++

    return {
      id: n.slug,
      type: 'architectureNode',
      position: {
        x: n.tree_x ?? baseX + offset,
        y: n.tree_y ?? (branchY[branch] ?? 400),
      },
      data: n,
    }
  })
}

function buildEdges(rawEdges) {
  return rawEdges.map((e, i) => {
    const style = EDGE_STYLES[e.relation_type] || EDGE_STYLES.evolved_from
    const color = BRANCH_COLORS[
      // 엣지 색상은 from 노드의 branch 색상 사용
      'decoder_only'
    ] || '#a78bfa'

    return {
      id: `e-${i}`,
      source: e.from_slug,
      target: e.to_slug,
      type: 'default',
      animated: false,
      style: {
        stroke: '#ffffff30',
        strokeWidth: 1.5,
        strokeDasharray: style.strokeDasharray,
        opacity: style.opacity,
      },
      markerEnd: e.relation_type === 'evolved_from' ? {
        type: MarkerType.ArrowClosed,
        width: 12,
        height: 12,
        color: '#ffffff40',
      } : undefined,
      label: e.relation_type === 'technique_used' ? e.description : undefined,
      labelStyle: { fontSize: 9, fill: '#94a3b8' },
    }
  })
}

export default function AIEvolutionaryTree() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [adminMode, setAdminMode] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [popupPos, setPopupPos] = useState(null)
  const reactFlowRef = useRef(null)
  const posUpdateTimer = useRef(null)
  const allNodesRef = useRef([])
  const allEdgesRef = useRef([])

  useEffect(() => {
    setLoading(true)
    getArchitectureTree()
      .then((r) => {
        const data = r.data
        const layoutNodes = autoLayout(data.nodes || [])
        const layoutEdges = buildEdges(data.edges || [])
        allNodesRef.current = layoutNodes
        allEdgesRef.current = layoutEdges
        setNodes(layoutNodes)
        setEdges(layoutEdges)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // 카테고리 필터 적용
  useEffect(() => {
    if (!categoryFilter) {
      setNodes(allNodesRef.current)
      setEdges(allEdgesRef.current)
      return
    }
    const visibleSlugs = new Set(
      allNodesRef.current
        .filter(n => n.data.architecture_category === categoryFilter)
        .map(n => n.id)
    )
    setNodes(allNodesRef.current.filter(n => visibleSlugs.has(n.id)))
    setEdges(
      allEdgesRef.current.filter(
        e => visibleSlugs.has(e.source) && visibleSlugs.has(e.target)
      )
    )
  }, [categoryFilter])

  const onNodeClick = useCallback((event, node) => {
    const rect = event.currentTarget?.getBoundingClientRect?.()
    setSelectedNode(node.data)
    setPopupPos(rect ? { x: rect.left + rect.width / 2, y: rect.top } : null)
  }, [])

  const onNodeDoubleClick = useCallback((_, node) => {
    navigate(`/architectures/${node.id}`)
  }, [navigate])

  const onNodeDragStop = useCallback((_, node) => {
    if (!adminMode || !user) return
    clearTimeout(posUpdateTimer.current)
    posUpdateTimer.current = setTimeout(() => {
      updateArchitecturePosition(node.id, node.position.x, node.position.y).catch(console.error)
    }, 500)
  }, [adminMode, user])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // 연도 마커 계산
  const yearMarkers = useMemo(() => {
    const years = []
    for (let y = 2015; y <= 2026; y++) {
      years.push({ year: y, x: (y - 2015) * 200 })
    }
    return years
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-[calc(100vh-4rem)] flex flex-col"
      style={{ background: '#0a0f1a' }}
    >
      {/* Toolbar */}
      <div
        className="flex items-center gap-3 px-4 py-2 border-b shrink-0"
        style={{ borderColor: '#1e293b', background: 'rgba(15, 23, 42, 0.9)' }}
      >
        <h1 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="text-xl">🌳</span> AI Evolutionary Tree
        </h1>

        <div className="flex-1" />

        {/* 카테고리 필터 */}
        <div className="hidden md:flex gap-1">
          {CATEGORY_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setCategoryFilter(f.value)}
              className={`text-xs px-3 py-1 rounded-full transition-colors ${
                categoryFilter === f.value
                  ? 'bg-white/20 text-white font-medium'
                  : 'text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* 모바일 필터 */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="md:hidden text-xs px-2 py-1 rounded border bg-transparent text-white"
          style={{ borderColor: '#334155' }}
        >
          {CATEGORY_FILTERS.map((f) => (
            <option key={f.value} value={f.value} style={{ background: '#0f172a' }}>
              {f.label}
            </option>
          ))}
        </select>

        {/* 갤러리 전환 */}
        <button
          onClick={() => navigate('/architectures')}
          className="p-1.5 rounded hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
          title="갤러리 보기"
        >
          <Grid3x3 size={18} />
        </button>

        {/* 관리 모드 */}
        {user && (
          <button
            onClick={() => setAdminMode(!adminMode)}
            className={`p-1.5 rounded transition-colors ${
              adminMode ? 'bg-amber-500/20 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-white/10'
            }`}
            title="관리 모드"
          >
            <Settings size={18} />
          </button>
        )}
      </div>

      {/* Tree Canvas */}
      <div className="flex-1 relative">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400 text-sm">Loading tree...</div>
          </div>
        ) : (
          <ReactFlow
            ref={reactFlowRef}
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeDragStop={onNodeDragStop}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            nodesDraggable={adminMode}
            panOnDrag
            zoomOnPinch
            panOnScroll={false}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            minZoom={0.1}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
            style={{ background: '#0a0f1a' }}
          >
            <Background
              gap={40}
              size={1}
              color="#1e293b40"
              variant="dots"
            />
            <Controls
              showInteractive={false}
              className="!bg-slate-900/80 !border-slate-700 !rounded-xl !shadow-lg [&>button]:!bg-transparent [&>button]:!border-slate-700 [&>button]:!text-gray-400 [&>button:hover]:!bg-white/10"
            />
            <MiniMap
              nodeStrokeColor={() => '#334155'}
              nodeColor={(n) => BRANCH_COLORS[n.data?.branch_type] || '#a78bfa'}
              nodeBorderRadius={12}
              maskColor="rgba(10, 15, 26, 0.85)"
              className="!bg-slate-900/80 !border-slate-700 !rounded-xl hidden md:block"
              style={{ width: 160, height: 100 }}
            />
          </ReactFlow>
        )}

        {/* 팝업 */}
        {selectedNode && (
          <TreeNodePopup
            node={selectedNode}
            position={popupPos}
            onClose={() => setSelectedNode(null)}
          />
        )}

        {/* 관리 모드 인디케이터 */}
        {adminMode && (
          <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-medium">
            관리 모드 — 노드 드래그로 위치 조정
          </div>
        )}
      </div>
    </motion.div>
  )
}
