import { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useNavigate } from 'react-router-dom'
import { Settings, Grid3x3, Info } from 'lucide-react'
import useAuth from '../hooks/useAuth'
import { getArchitectureTree, updateArchitecturePosition } from '../api/posts'
import ArchitectureTreeNode from '../components/architecture/ArchitectureTreeNode'
import TreeNodePopup from '../components/architecture/TreeNodePopup'

/* ── 색상 & 상수 ─────────────────────────────────────── */
const BRANCH_COLORS = {
  encoder_only: '#4ade80',
  encoder_decoder: '#86efac',
  decoder_only: '#93c5fd',
  ssm: '#22d3ee',
  diffusion: '#c084fc',
  vision: '#f472b6',
  multimodal: '#fb923c',
  agent: '#a3e635',
}

const BRANCH_LABELS = {
  encoder_only: 'Encoder-Only',
  encoder_decoder: 'Encoder-Decoder',
  decoder_only: 'Decoder-Only',
  ssm: 'SSM',
  diffusion: 'Diffusion',
  vision: 'Vision',
  multimodal: 'Multimodal',
  agent: 'Agent',
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
  evolved_from: { dash: undefined, opacity: 0.7, width: 2 },
  inspired_by: { dash: '8 5', opacity: 0.4, width: 1.5 },
  variant_of: { dash: '4 4', opacity: 0.5, width: 1.5 },
  technique_used: { dash: '3 6', opacity: 0.3, width: 1 },
}

/* ── 레이아웃 설정 (수직 트리) ───────────────────────── */
const BRANCH_ORDER = [
  'encoder_only', 'encoder_decoder', 'decoder_only',
  'ssm', 'diffusion', 'vision', 'multimodal', 'agent',
]

// 브랜치별 X 위치 (레퍼런스 이미지처럼 좌→우 배치)
const BRANCH_X = {
  encoder_only: -700,
  encoder_decoder: -350,
  decoder_only: 200,
  ssm: -500,
  diffusion: 700,
  vision: 1050,
  multimodal: 500,
  agent: 1300,
}

const Y_SPACING = 240     // 연도당 Y 간격
const NODE_GAP_X = 155     // 같은 연도+브랜치 내 X 간격
const REFERENCE_YEAR = 2027 // Y = (REFERENCE_YEAR - year) * Y_SPACING
const MIN_YEAR = 2015
const MAX_YEAR = 2026

const nodeTypes = { architectureNode: ArchitectureTreeNode }

/* ── 자동 레이아웃: 수직 트리 ──────────────────────────── */
function autoLayout(rawNodes) {
  // 연도+브랜치별로 그룹화
  const groups = {}
  const sorted = [...rawNodes].sort((a, b) => {
    const da = a.release_date || '2020-01-01'
    const db = b.release_date || '2020-01-01'
    return da.localeCompare(db)
  })

  sorted.forEach((n) => {
    const branch = n.branch_type || 'decoder_only'
    const yearStr = n.release_date?.slice(0, 4) || '2020'
    const key = `${branch}-${yearStr}`
    if (!groups[key]) groups[key] = []
    groups[key].push(n)
  })

  const layoutNodes = []

  // 연도 마커 노드 (좌측에 수직으로)
  for (let year = MIN_YEAR; year <= MAX_YEAR; year++) {
    const y = (REFERENCE_YEAR - year) * Y_SPACING
    layoutNodes.push({
      id: `year-${year}`,
      type: 'default',
      position: { x: -950, y: y - 15 },
      data: { label: String(year) },
      selectable: false,
      draggable: false,
      connectable: false,
      style: {
        background: '#1e293b',
        border: '2px solid #334155',
        borderRadius: '9999px',
        color: '#94a3b8',
        fontSize: '13px',
        fontWeight: 700,
        padding: '4px 16px',
        pointerEvents: 'none',
        width: 'auto',
        textAlign: 'center',
      },
    })
  }

  // 브랜치 라벨 (하단에)
  BRANCH_ORDER.forEach((branch) => {
    const x = BRANCH_X[branch]
    const y = (REFERENCE_YEAR - MIN_YEAR) * Y_SPACING + 80
    layoutNodes.push({
      id: `label-${branch}`,
      type: 'default',
      position: { x: x - 40, y },
      data: { label: BRANCH_LABELS[branch] },
      selectable: false,
      draggable: false,
      connectable: false,
      style: {
        background: `${BRANCH_COLORS[branch]}15`,
        border: `1.5px solid ${BRANCH_COLORS[branch]}40`,
        borderRadius: '8px',
        color: BRANCH_COLORS[branch],
        fontSize: '11px',
        fontWeight: 700,
        padding: '4px 12px',
        pointerEvents: 'none',
        width: 'auto',
        whiteSpace: 'nowrap',
      },
    })
  })

  // 실제 아키텍처 노드 배치
  Object.entries(groups).forEach(([key, nodes]) => {
    const [branch, yearStr] = key.split(/-(.+)/)
    const year = parseInt(yearStr, 10)
    const centerX = BRANCH_X[branch] ?? 0
    const baseY = (REFERENCE_YEAR - year) * Y_SPACING

    nodes.forEach((n, idx) => {
      // 같은 연도+브랜치 내 노드들을 centerX 기준으로 수평 분포
      const count = nodes.length
      const offsetX = (idx - (count - 1) / 2) * NODE_GAP_X
      const x = n.tree_x ?? (centerX + offsetX)
      const y = n.tree_y ?? baseY

      layoutNodes.push({
        id: n.slug,
        type: 'architectureNode',
        position: { x, y },
        data: n,
      })
    })
  })

  return layoutNodes
}

/* ── 엣지 빌드 (parent→child 방향, 색상 적용) ─────── */
function buildEdges(rawEdges, nodeMap) {
  return rawEdges.map((e, i) => {
    const style = EDGE_STYLES[e.relation_type] || EDGE_STYLES.evolved_from
    const sourceData = nodeMap[e.to_slug]     // parent (older, bottom)
    const targetData = nodeMap[e.from_slug]    // child (newer, top)
    const color = BRANCH_COLORS[sourceData?.branch_type] || '#93c5fd'

    return {
      id: `e-${i}`,
      source: e.to_slug,       // parent (older → bottom)
      target: e.from_slug,     // child (newer → top)
      type: 'default',         // bezier curve
      animated: false,
      style: {
        stroke: color,
        strokeWidth: style.width,
        strokeDasharray: style.dash,
        opacity: style.opacity,
      },
      markerEnd: e.relation_type === 'evolved_from' ? {
        type: MarkerType.ArrowClosed,
        width: 8,
        height: 8,
        color,
      } : undefined,
    }
  })
}

/* ── 메인 트리 컴포넌트 ──────────────────────────────── */
function TreeContent() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { fitView } = useReactFlow()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [adminMode, setAdminMode] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [popupPos, setPopupPos] = useState(null)
  const [showLegend, setShowLegend] = useState(false)
  const posUpdateTimer = useRef(null)
  const allNodesRef = useRef([])
  const allEdgesRef = useRef([])
  const nodeMapRef = useRef({})

  useEffect(() => {
    setLoading(true)
    getArchitectureTree()
      .then((r) => {
        const data = r.data
        const nodeMap = {}
        ;(data.nodes || []).forEach((n) => { nodeMap[n.slug] = n })
        nodeMapRef.current = nodeMap

        const layoutNodes = autoLayout(data.nodes || [])
        const layoutEdges = buildEdges(data.edges || [], nodeMap)
        allNodesRef.current = layoutNodes
        allEdgesRef.current = layoutEdges
        setNodes(layoutNodes)
        setEdges(layoutEdges)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // 카테고리 필터
  useEffect(() => {
    if (!categoryFilter) {
      setNodes(allNodesRef.current)
      setEdges(allEdgesRef.current)
      setTimeout(() => fitView({ padding: 0.3, duration: 400 }), 100)
      return
    }
    const categoryBranches = {
      llm: new Set(['encoder_only', 'encoder_decoder', 'decoder_only']),
      ssm: new Set(['ssm']),
      diffusion: new Set(['diffusion']),
      vision: new Set(['vision']),
      multimodal: new Set(['multimodal']),
      agent: new Set(['agent']),
    }
    const validBranches = categoryBranches[categoryFilter] || new Set()

    const visibleSlugs = new Set(
      allNodesRef.current
        .filter((n) => n.data?.architecture_category === categoryFilter)
        .map((n) => n.id)
    )
    setNodes(
      allNodesRef.current.filter((n) => {
        if (n.id.startsWith('year-')) return true
        if (n.id.startsWith('label-')) return validBranches.has(n.id.replace('label-', ''))
        return visibleSlugs.has(n.id)
      })
    )
    setEdges(
      allEdgesRef.current.filter(
        (e) => visibleSlugs.has(e.source) && visibleSlugs.has(e.target)
      )
    )
    setTimeout(() => fitView({ padding: 0.4, duration: 400 }), 100)
  }, [categoryFilter])

  const onNodeClick = useCallback((event, node) => {
    if (node.id.startsWith('label-') || node.id.startsWith('year-')) return
    const rect = event.currentTarget?.getBoundingClientRect?.()
    setSelectedNode(node.data)
    setPopupPos(rect ? { x: rect.left + rect.width / 2, y: rect.top } : null)
  }, [])

  const onNodeDoubleClick = useCallback((_, node) => {
    if (node.id.startsWith('label-') || node.id.startsWith('year-')) return
    navigate(`/architectures/${node.id}`)
  }, [navigate])

  const onNodeDragStop = useCallback((_, node) => {
    if (!adminMode || !user) return
    if (node.id.startsWith('label-') || node.id.startsWith('year-')) return
    clearTimeout(posUpdateTimer.current)
    posUpdateTimer.current = setTimeout(() => {
      updateArchitecturePosition(node.id, node.position.x, node.position.y).catch(console.error)
    }, 500)
  }, [adminMode, user])

  const onPaneClick = useCallback(() => setSelectedNode(null), [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-[calc(100vh-4rem)] flex flex-col"
      style={{ background: '#f8fafc' }}
    >
      {/* Toolbar */}
      <div
        className="flex items-center gap-3 px-4 py-2 border-b shrink-0"
        style={{ borderColor: '#e2e8f0', background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(8px)' }}
      >
        <h1 className="text-lg font-bold flex items-center gap-2" style={{ color: '#0f172a' }}>
          <span className="text-xl">🌳</span>
          <span className="hidden sm:inline">Evolutionary Tree</span>
          <span className="sm:hidden">AI Tree</span>
        </h1>

        <div className="flex-1" />

        {/* 카테고리 필터 - 데스크톱 */}
        <div className="hidden md:flex gap-1">
          {CATEGORY_FILTERS.map((f) => {
            const isActive = categoryFilter === f.value
            return (
              <button
                key={f.value}
                onClick={() => setCategoryFilter(f.value)}
                className={`text-xs px-3 py-1.5 rounded-full transition-all font-medium ${
                  isActive
                    ? 'bg-slate-800 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                {f.label}
              </button>
            )
          })}
        </div>

        {/* 카테고리 필터 - 모바일 */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="md:hidden text-xs px-2 py-1.5 rounded-lg border bg-white text-slate-700"
          style={{ borderColor: '#e2e8f0' }}
        >
          {CATEGORY_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>

        {/* 범례 */}
        <button
          onClick={() => setShowLegend(!showLegend)}
          className={`p-1.5 rounded-lg transition-colors ${
            showLegend ? 'bg-slate-200 text-slate-700' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
          }`}
          title="범례"
        >
          <Info size={18} />
        </button>

        {/* 갤러리 */}
        <button
          onClick={() => navigate('/architectures')}
          className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-700"
          title="갤러리 보기"
        >
          <Grid3x3 size={18} />
        </button>

        {/* 관리 */}
        {user && (
          <button
            onClick={() => setAdminMode(!adminMode)}
            className={`p-1.5 rounded-lg transition-colors ${
              adminMode ? 'bg-amber-100 text-amber-600' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
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
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
              <div className="w-8 h-8 border-2 border-t-transparent border-blue-400 rounded-full animate-spin mx-auto mb-3" />
              <div className="text-slate-400 text-sm">Loading tree...</div>
            </motion.div>
          </div>
        ) : (
          <ReactFlow
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
            minZoom={0.05}
            maxZoom={2.5}
            proOptions={{ hideAttribution: true }}
            style={{ background: '#f8fafc' }}
          >
            <Background gap={60} size={1} color="#e2e8f020" variant="dots" />
            <Controls
              showInteractive={false}
              className="!bg-white/90 !border-slate-200 !rounded-xl !shadow-lg [&>button]:!bg-transparent [&>button]:!border-slate-200 [&>button]:!text-slate-500 [&>button:hover]:!bg-slate-50"
            />
            <MiniMap
              nodeStrokeColor={() => '#e2e8f0'}
              nodeColor={(n) => {
                if (n.id?.startsWith('label-') || n.id?.startsWith('year-')) return 'transparent'
                return BRANCH_COLORS[n.data?.branch_type] || '#93c5fd'
              }}
              nodeBorderRadius={12}
              maskColor="rgba(248, 250, 252, 0.85)"
              className="!bg-white/90 !border-slate-200 !rounded-xl hidden md:block"
              style={{ width: 180, height: 120 }}
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

        {/* 범례 */}
        <AnimatePresence>
          {showLegend && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 16 }}
              transition={{ duration: 0.2 }}
              className="absolute bottom-4 left-4 p-4 rounded-xl shadow-xl z-20"
              style={{ background: 'rgba(255,255,255,0.97)', border: '1px solid #e2e8f0' }}
            >
              <h3 className="text-slate-700 text-xs font-bold mb-3">Branch Types</h3>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 mb-4">
                {BRANCH_ORDER.map((b) => (
                  <div key={b} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm shrink-0" style={{ background: BRANCH_COLORS[b] }} />
                    <span className="text-slate-600 text-[11px]">{BRANCH_LABELS[b]}</span>
                  </div>
                ))}
              </div>
              <h3 className="text-slate-700 text-xs font-bold mb-2">Relationships</h3>
              <div className="space-y-1.5">
                {[
                  { dash: '', label: 'Evolved from', w: 2 },
                  { dash: '8 5', label: 'Inspired by', w: 1.5 },
                  { dash: '4 4', label: 'Variant of', w: 1.5 },
                  { dash: '3 6', label: 'Technique used', w: 1 },
                ].map((r) => (
                  <div key={r.label} className="flex items-center gap-2">
                    <svg width="28" height="8">
                      <line x1="0" y1="4" x2="28" y2="4" stroke="#64748b" strokeWidth={r.w} strokeDasharray={r.dash || undefined} />
                    </svg>
                    <span className="text-slate-600 text-[11px]">{r.label}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-4 mt-3 pt-2 border-t" style={{ borderColor: '#e2e8f0' }}>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-sm" style={{ background: '#d4a574' }} />
                  <span className="text-slate-500 text-[10px]">Open Source</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-sm border" style={{ borderColor: '#cbd5e1', background: 'white' }} />
                  <span className="text-slate-500 text-[10px]">Closed Source</span>
                </div>
              </div>
              <p className="text-slate-400 text-[10px] mt-2">Click: preview · Double-click: detail</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 관리 모드 */}
        {adminMode && (
          <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-medium z-10">
            관리 모드 — 노드 드래그로 위치 조정
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function AIEvolutionaryTree() {
  return (
    <ReactFlowProvider>
      <TreeContent />
    </ReactFlowProvider>
  )
}
