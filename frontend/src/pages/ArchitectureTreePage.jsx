import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Helmet } from 'react-helmet-async'
import { Search, Loader2, X, LayoutGrid, Network, Server, Brain } from 'lucide-react'
import ExploreNav from '../components/explore/ExploreNav'
import ArchitectureGraph from '../components/architecture/ArchitectureGraph'
import ArchitectureNodeDetail from '../components/architecture/ArchitectureNodeDetail'
import CloudServiceNodeDetail from '../components/architecture/CloudServiceNodeDetail'
import ArchitectureRelatedPanel from '../components/architecture/ArchitectureRelatedPanel'
import MobileCardView from '../components/architecture/MobileCardView'
import TreeViewControls from '../components/architecture/TreeViewControls'
import { getArchitectureTree, getCloudServiceTree, updateCloudServicePosition } from '../api/posts'
import { CATEGORY_COLORS, EDGE_STYLES, KIND_FILTER, lanesFromBranches } from '../data/architectureConstants'
import { CLOUD_DOMAIN_COLORS, CLOUD_EDGE_STYLES, INFRA_CATEGORIES, getCloudNodeRadius,
         infraLanesFromPayload, layersFromPayload, layerOf, LAYER_NONE } from '../data/cloudConstants'

const DOMAIN_CONFIGS = {
  ai: {
    // 종류 필터는 KIND_FILTER 한 곳만 본다. 무엇으로 가르는지는 그쪽에 적혀 있다
    categories: KIND_FILTER.options,
    categoryField: KIND_FILTER.field,
    filterParam: KIND_FILTER.param,
    categoryColors: CATEGORY_COLORS,
    edgeStyles: EDGE_STYLES,
    fetchTree: getArchitectureTree,
    // 발표 시점과 가지를 따라 좌표가 잡혀 있으므로 계보 배치를 기본으로 둔다
    hasLineage: true,
    defaultLayout: 'lineage',
    searchPlaceholder: '모델 검색...',
    emptyMsg: '해당 카테고리의 아키텍처 항목이 없습니다.',
    errorMsg: '아키텍처 트리를 불러올 수 없습니다.',
    title: '아키텍처 계보 | HJ Tech Blog',
    description: 'LLM, SSM, Diffusion 등 AI 모델 아키텍처 계보 트리 시각화.',
  },
  // 예전 이름은 `cloud` 였다. AWS 35개만 있던 시절의 이름이고, 지금은 컨테이너·DB·
  // 데이터·서빙·운영이 함께 들어와 인프라 전반을 그린다. `?domain=cloud` 로 들어온
  // 링크는 아래에서 `infra` 로 넘긴다.
  infra: {
    categories: INFRA_CATEGORIES,
    categoryColors: CLOUD_DOMAIN_COLORS,
    edgeStyles: CLOUD_EDGE_STYLES,
    categoryField: 'service_domain',
    fetchTree: getCloudServiceTree,
    filterParam: 'domain',
    // 세로축이 연도가 아니라 **추상화 층**이다. 인프라 기술의 값은 언제 나왔느냐가
    // 아니라 어느 층에 서느냐에 있다. EC2(2006)와 Fargate(2017)를 연도로 세우면
    // 둘 다 컴퓨트라는 것만 보이고, 층으로 세우면 가상화 위에 서버리스가 얹힌 관계가
    // 보인다. 그래서 힘배치를 걷고 계보 배치를 기본으로 둔다.
    hasLineage: true,
    defaultLayout: 'lineage',
    searchPlaceholder: '기술·서비스 검색...',
    emptyMsg: '해당 계열의 인프라 항목이 없습니다.',
    errorMsg: '인프라 트리를 불러올 수 없습니다.',
    title: '인프라 기술 맵 | HJ Tech Blog',
    description: '컨테이너, 데이터베이스, 데이터 처리, 서빙, 운영, AWS까지 인프라 기술 간의 관계를 시각화한다.',
    getNodeRadius: getCloudNodeRadius,
    onPositionUpdate: updateCloudServicePosition,
  },
}

export default function ArchitectureTreePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // `?domain=cloud` 는 예전 이름이다. 기존 링크가 깨지지 않게 `infra` 로 받아 준다
  const [domain, setDomain] = useState(() => {
    const d = searchParams.get('domain')
    return d === 'cloud' ? 'infra' : (d || 'ai')
  })
  const config = DOMAIN_CONFIGS[domain] || DOMAIN_CONFIGS.ai

  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  // 가지 설정은 트리 응답이 들고 온다. 화면에 상수로 적어 두면 가지가 늘 때 한쪽만 바뀐다
  const [branches, setBranches] = useState([])
  // 인프라 트리의 레인(계열)과 세로축(층). AI 쪽 `branches` 와 같은 자리다
  const [domains, setDomains] = useState([])
  const [layers, setLayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [category, setCategory] = useState(searchParams.get('category') || 'all')
  const [mobileView, setMobileView] = useState('graph')
  const [matchIndex, setMatchIndex] = useState(0)
  const [layoutMode, setLayoutMode] = useState(config.defaultLayout)
  const [hiddenLanes, setHiddenLanes] = useState([])
  // 좌측 관련 모델 패널을 여는 기준. 1024에서는 좌우 패널이 함께 열리면 그래프가
  // 300px대로 눌린다. 1280부터만 둘을 같이 열고, 그 아래에서는 관계를 상세 패널 안에 담는다
  const [isWideScreen, setIsWideScreen] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 1280 : true
  )
  // 태블릿 세로(768~1023)는 그래프에 줄 폭이 모자란다. 사이드 패널을 옆으로 밀면
  // 그래프가 400px대로 눌려 계보가 안 보인다. 그 구간에서는 패널을 그래프 위에 겹친다.
  // 아이패드 세로 768·834, 갤럭시 탭 800이 전부 여기 들어온다.
  const [isRoomyScreen, setIsRoomyScreen] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : true
  )

  const graphRef = useRef(null)

  // 화면 크기 감지 (좌측 패널 표시 여부)
  useEffect(() => {
    const handler = () => {
      setIsWideScreen(window.innerWidth >= 1280)
      setIsRoomyScreen(window.innerWidth >= 1024)
    }
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  // 상세 패널 폭. 넓은 화면에서만 넓힌다. 좁은 화면에서 넓히면 그래프가 남지 않는다
  const detailPanelWidth = isWideScreen ? 400 : 360

  // 검색 매칭 slug 배열
  const matchedSlugs = useMemo(() => {
    if (!searchQuery) return []
    const q = searchQuery.toLowerCase()
    return nodes.filter(n => n.name.toLowerCase().includes(q)).map(n => n.slug)
  }, [nodes, searchQuery])

  // 레인 설정. 도메인마다 레인이 다르다. AI 는 가지, 인프라는 계열이다.
  // 둘 다 응답에서 만든다. 상수로 적어 두면 한쪽만 늘어난다
  const isInfra = domain === 'infra'
  const laneConfig = useMemo(
    () => (isInfra ? infraLanesFromPayload(domains) : lanesFromBranches(branches)),
    [isInfra, domains, branches]
  )
  const laneOf = laneConfig.laneOf

  // 계보 축. AI 는 연도, 인프라는 추상화 층이다
  const layerConfig = useMemo(() => layersFromPayload(layers), [layers])
  const axisKeyOf = useMemo(
    () => (isInfra ? (n => layerOf(n)) : null),
    [isInfra]
  )
  const axisLabelOf = useMemo(
    () => (isInfra ? (k => (k === LAYER_NONE ? LAYER_NONE : (layerConfig.labels[k] || k))) : null),
    [isInfra, layerConfig]
  )

  // 데이터에 실제로 있는 가지만 추린다. 비어 있는 레인까지 칩으로 내걸면 눌러도 아무 일이 없다
  const lanes = useMemo(
    () => laneConfig.order.filter(lane => nodes.some(n => laneOf(n) === lane)),
    [nodes, laneConfig, laneOf]
  )
  const laneCounts = useMemo(() => {
    const counts = {}
    for (const node of nodes) {
      const lane = laneOf(node)
      counts[lane] = (counts[lane] || 0) + 1
    }
    return counts
  }, [nodes, laneOf])

  const handleToggleLane = useCallback((lane) => {
    setHiddenLanes(prev => (prev.includes(lane) ? prev.filter(l => l !== lane) : [...prev, lane]))
  }, [])

  // 힘 배치에는 가지 칩이 없다. 접어 둔 채로 넘어가면 되살릴 단추가 사라지므로 여기서 편다
  const handleLayoutModeChange = useCallback((mode) => {
    setLayoutMode(mode)
    if (mode !== 'lineage') setHiddenLanes([])
  }, [])

  // 도메인 전환
  const handleDomainChange = useCallback((d) => {
    setDomain(d)
    setCategory('all')
    setSelectedNode(null)
    setSearchQuery('')
    setLayoutMode(DOMAIN_CONFIGS[d]?.defaultLayout || 'force')
    setHiddenLanes([])
    setSearchParams(d === 'ai' ? {} : { domain: d })
  }, [setSearchParams])

  // 데이터 로드
  const fetchTree = useCallback(async (cat) => {
    setLoading(true)
    setError(null)
    try {
      const params = cat && cat !== 'all' ? { [config.filterParam]: cat } : {}
      const { data } = await config.fetchTree(params)
      setNodes(data.nodes || [])
      setEdges(data.edges || [])
      setBranches(data.branches || [])
      setDomains(data.domains || [])
      setLayers(data.layers || [])
    } catch {
      setError(config.errorMsg)
    } finally {
      setLoading(false)
    }
  }, [config])

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
    <>
    <Helmet>
      <title>{config.title}</title>
      <meta name="description" content={config.description} />
    </Helmet>
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col"
      style={{ height: 'calc(100vh - 64px)' }}
    >
      {/* Explore 탭바 */}
      <div className="shrink-0 px-4" style={{ background: 'var(--card-bg)' }}>
        <ExploreNav />
      </div>

      {/* 상단 바 */}
      <div
        className="shrink-0 border-b px-2 xs:px-4 py-2 xs:py-2.5"
        style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
      >
        <div className="max-w-full mx-auto flex flex-col sm:flex-row sm:items-center gap-2">
          {/* 도메인 탭 + 카테고리 필터 */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide flex-1">
            {/* 도메인 전환 */}
            <div className="flex items-center border rounded-lg overflow-hidden shrink-0 mr-1.5" style={{ borderColor: 'var(--border)' }}>
              <button
                onClick={() => handleDomainChange('ai')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium transition-colors"
                style={{
                  background: domain === 'ai' ? 'var(--text)' : 'transparent',
                  color: domain === 'ai' ? '#fff' : 'var(--text-secondary)',
                }}
              >
                <Brain size={12} /> AI/ML
              </button>
              <button
                onClick={() => handleDomainChange('infra')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium transition-colors"
                style={{
                  background: domain === 'infra' ? 'var(--text)' : 'transparent',
                  color: domain === 'infra' ? '#fff' : 'var(--text-secondary)',
                }}
              >
                <Server size={12} /> Infra
              </button>
            </div>
            {config.categories.map(cat => {
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

          <div className="flex items-center gap-2 min-w-0">
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
            <div className="relative min-w-0 flex-1 sm:flex-none sm:w-56">
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
                placeholder={config.searchPlaceholder}
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

      {/* 배치 모드 + 가지 접기 (계보 좌표가 있는 도메인에서만) */}
      {config.hasLineage && !loading && !error && nodes.length > 0 && (
        <div
          className="shrink-0 border-b px-4 py-1.5 hidden md:block"
          style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
        >
          <TreeViewControls
            layoutMode={layoutMode}
            onLayoutModeChange={handleLayoutModeChange}
            lanes={lanes}
            laneCounts={laneCounts}
            laneColors={laneConfig.colors}
            laneLabels={laneConfig.labels}
            hiddenLanes={hiddenLanes}
            onToggleLane={handleToggleLane}
            onResetLanes={() => setHiddenLanes([])}
          />
        </div>
      )}

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
              {config.emptyMsg}
            </p>
          </div>
        ) : (
          <>
            {/* 데스크탑: 좌측 패널 + 그래프 + 우측 패널 */}
            <div className="hidden md:flex flex-1 relative">
              {/* 좌측 관련 모델 패널 - 넓은 화면에서만 */}
              <AnimatePresence>
                {isWideScreen && selectedNode && (
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
                      categoryColors={config.categoryColors}
                      categoryField={config.categoryField}
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
                  selectedNode={selectedNode}
                  searchQuery={searchQuery}
                  categoryColors={config.categoryColors}
                  edgeStyles={config.edgeStyles}
                  categoryField={config.categoryField}
                  layoutMode={layoutMode}
                  lanes={lanes}
                  laneColors={laneConfig.colors}
                  laneLabels={laneConfig.labels}
                  laneOf={laneOf}
                  axisKeyOf={axisKeyOf}
                  axisLabelOf={axisLabelOf}
                  hiddenLanes={hiddenLanes}
                  {...(config.getNodeRadius && { getNodeRadius: config.getNodeRadius })}
                  {...(config.onPositionUpdate && { onPositionUpdate: config.onPositionUpdate })}
                />
              </div>

              {/* 우측 상세 패널 */}
              <AnimatePresence>
                {selectedNode && (
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: detailPanelWidth, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                    className={isRoomyScreen
                      ? 'shrink-0 overflow-hidden border-l'
                      : 'absolute top-0 right-0 bottom-0 z-30 overflow-hidden border-l shadow-2xl'}
                    style={{ borderColor: 'var(--border)' }}
                  >
                    {domain === 'infra' ? (
                      <CloudServiceNodeDetail
                        node={selectedNode}
                        edges={edges}
                        onClose={() => setSelectedNode(null)}
                        onNodeFocus={handleNodeFocus}
                        layout="side"
                        hideRelations={isWideScreen}
                      />
                    ) : (
                      <ArchitectureNodeDetail
                        node={selectedNode}
                        edges={edges}
                        onClose={() => setSelectedNode(null)}
                        onNodeFocus={handleNodeFocus}
                        layout="side"
                        hideRelations={isWideScreen}
                      />
                    )}
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
                  selectedNode={selectedNode}
                  searchQuery={searchQuery}
                  categoryColors={config.categoryColors}
                  edgeStyles={config.edgeStyles}
                  categoryField={config.categoryField}
                  layoutMode={layoutMode}
                  lanes={lanes}
                  laneColors={laneConfig.colors}
                  laneLabels={laneConfig.labels}
                  laneOf={laneOf}
                  axisKeyOf={axisKeyOf}
                  axisLabelOf={axisLabelOf}
                  hiddenLanes={hiddenLanes}
                  {...(config.getNodeRadius && { getNodeRadius: config.getNodeRadius })}
                  {...(config.onPositionUpdate && { onPositionUpdate: config.onPositionUpdate })}
                />
              ) : (
                <MobileCardView
                  nodes={nodes}
                  searchQuery={searchQuery}
                  onNodeClick={handleNodeClick}
                  selectedNode={selectedNode}
                  categoryColors={config.categoryColors}
                  categoryField={config.categoryField}
                />
              )}
              {/* 모바일 하단 시트 */}
              <AnimatePresence>
                {selectedNode && (
                  domain === 'infra' ? (
                    <CloudServiceNodeDetail
                      node={selectedNode}
                      edges={edges}
                      onClose={() => setSelectedNode(null)}
                      onNodeFocus={handleNodeFocus}
                      layout="bottom"
                    />
                  ) : (
                    <ArchitectureNodeDetail
                      node={selectedNode}
                      edges={edges}
                      onClose={() => setSelectedNode(null)}
                      onNodeFocus={handleNodeFocus}
                      layout="bottom"
                    />
                  )
                )}
              </AnimatePresence>
            </div>
          </>
        )}
      </div>
    </motion.div>
    </>
  )
}
