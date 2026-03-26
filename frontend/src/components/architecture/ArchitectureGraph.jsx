import { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react'
import * as d3 from 'd3'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { updateArchitecturePosition } from '../../api/posts'
import { CATEGORY_COLORS, EDGE_STYLES } from '../../data/architectureConstants'

function getNodeRadius(paramScale) {
  if (!paramScale) return 8
  const s = paramScale.toLowerCase()
  if (s.includes('b') || s.includes('billion')) {
    const num = parseFloat(s)
    if (num >= 100) return 22
    if (num >= 10) return 16
    return 12
  }
  if (s.includes('m') || s.includes('million')) return 6
  return 8
}

// 하이라이트 상태 통합 처리
function applyHighlightState(svg, { selectedSlug, searchQuery, baseEdgeOpacity, edgeData }) {
  const lowerQuery = (searchQuery || '').toLowerCase()

  // 선택 노드에 연결된 slug 셋 계산
  const connectedSlugs = new Set()
  if (selectedSlug) {
    for (const e of edgeData) {
      const src = typeof e.source === 'object' ? e.source.slug : e.source
      const tgt = typeof e.target === 'object' ? e.target.slug : e.target
      if (src === selectedSlug) connectedSlugs.add(tgt)
      if (tgt === selectedSlug) connectedSlugs.add(src)
    }
  }

  svg.selectAll('.node-group').each(function (d) {
    const circle = d3.select(this).select('circle')
    const label = d3.select(this).select('.node-label')
    const isSelected = d.slug === selectedSlug
    const isSearchMatch = lowerQuery && d.name.toLowerCase().includes(lowerQuery)
    const dimmed = lowerQuery && !isSearchMatch
    const isConnected = connectedSlugs.has(d.slug)
    const catColor = CATEGORY_COLORS[d.architecture_category] || '#8895A7'

    if (isSelected) {
      circle
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)
        .attr('stroke-opacity', 1)
        .attr('fill-opacity', 1)
        .style('opacity', 1)
        .attr('filter', 'url(#glow)')
      label.style('opacity', 1).style('font-weight', '700')
    } else if (dimmed) {
      circle
        .attr('stroke', catColor)
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.1)
        .attr('fill-opacity', 0.15)
        .style('opacity', 0.15)
        .attr('filter', null)
      label.style('opacity', 0.08).style('font-weight', '500')
    } else if (selectedSlug && !isConnected) {
      circle
        .attr('stroke', catColor)
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.1)
        .attr('fill-opacity', 0.12)
        .style('opacity', 0.15)
        .attr('filter', null)
      label.style('opacity', 0.08).style('font-weight', '500')
    } else if (isSearchMatch) {
      circle
        .attr('stroke', '#FBBF24')
        .attr('stroke-width', 3)
        .attr('stroke-opacity', 0.9)
        .attr('fill-opacity', 1)
        .style('opacity', 1)
        .attr('filter', 'url(#glow)')
      label.style('opacity', 1).style('font-weight', '600')
    } else if (isConnected) {
      circle
        .attr('stroke', catColor)
        .attr('stroke-width', 2.5)
        .attr('stroke-opacity', 0.6)
        .attr('fill-opacity', 1)
        .style('opacity', 1)
        .attr('filter', null)
      label.style('opacity', 1).style('font-weight', '500')
    } else {
      // 기본 상태
      circle
        .attr('stroke', catColor)
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.3)
        .attr('fill-opacity', 0.85)
        .style('opacity', 1)
        .attr('filter', null)
      label.style('opacity', 1).style('font-weight', '500')
    }
  })

  // 엣지 처리
  svg.selectAll('.links line').each(function (d) {
    const src = typeof d.source === 'object' ? d.source.slug : d.source
    const tgt = typeof d.target === 'object' ? d.target.slug : d.target
    const isConnected = selectedSlug && (src === selectedSlug || tgt === selectedSlug)
    const style = EDGE_STYLES[d.relation_type] || EDGE_STYLES.evolved_from

    if (lowerQuery) {
      d3.select(this).style('opacity', 0.04).attr('stroke-width', style.width)
    } else if (selectedSlug) {
      d3.select(this)
        .style('opacity', isConnected ? 0.8 : 0.04)
        .attr('stroke-width', isConnected ? style.width * 1.5 : style.width)
    } else {
      d3.select(this).style('opacity', baseEdgeOpacity ?? style.opacity).attr('stroke-width', style.width)
    }
  })
}

const ArchitectureGraph = forwardRef(function ArchitectureGraph({
  nodes,
  edges,
  onNodeClick,
  onNodeDoubleClick,
  selectedSlug,
  searchQuery,
}, ref) {
  const containerRef = useRef(null)
  const svgRef = useRef(null)
  const simulationRef = useRef(null)
  const saveTimerRef = useRef(null)
  const initialZoomTimerRef = useRef(null)
  const zoomRef = useRef(null)
  const nodeDataRef = useRef([])
  const edgeDataRef = useRef([])
  const baseEdgeOpacityRef = useRef(0.5)

  // focusOnNode API 노출
  useImperativeHandle(ref, () => ({
    focusOnNode(slug) {
      const node = nodeDataRef.current.find(n => n.slug === slug)
      if (!node || !svgRef.current || !zoomRef.current) return
      const svg = d3.select(svgRef.current)
      const container = containerRef.current
      if (!container) return
      const width = container.clientWidth
      const height = container.clientHeight
      const scale = 1.5
      const tx = width / 2 - node.x * scale
      const ty = height / 2 - node.y * scale
      svg.transition().duration(500)
        .call(zoomRef.current.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
    },
  }), [])

  // 디바운스된 위치 저장
  const debouncedSavePosition = useCallback((slug, x, y) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(async () => {
      try {
        await updateArchitecturePosition(slug, Math.round(x), Math.round(y))
      } catch { /* 위치 저장 실패는 무시 */ }
    }, 500)
  }, [])

  useEffect(() => {
    if (!nodes.length || !svgRef.current || !containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // 노드/엣지 복사 (D3가 mutate하므로)
    const nodeData = nodes.map(n => ({
      ...n,
      x: n.tree_x || undefined,
      y: n.tree_y || undefined,
      radius: getNodeRadius(n.param_scale),
    }))
    nodeDataRef.current = nodeData

    const edgeData = edges
      .filter(e => {
        const hasSource = nodeData.some(n => n.slug === e.from_slug)
        const hasTarget = nodeData.some(n => n.slug === e.to_slug)
        return hasSource && hasTarget
      })
      .map(e => ({
        ...e,
        source: e.from_slug,
        target: e.to_slug,
      }))
    edgeDataRef.current = edgeData

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // 줌 그룹
    const g = svg.append('g')

    // 줌 동작
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
        const scale = event.transform.k
        // 줌 레벨에 따라 레이블 표시
        g.selectAll('.node-label')
          .style('display', scale > 0.4 ? 'block' : 'none')
          .style('font-size', `${Math.min(12, 11 / scale)}px`)
        // 줌 레벨에 따른 엣지 투명도
        baseEdgeOpacityRef.current = Math.max(0.15, Math.min(0.6, scale * 0.35))
      })

    svg.call(zoom)
    zoomRef.current = zoom

    // SVG defs: 화살표 + 글로우 필터
    const defs = svg.append('defs')

    // 글로우 필터
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%')
    filter.append('feGaussianBlur')
      .attr('in', 'SourceGraphic')
      .attr('stdDeviation', '4')
      .attr('result', 'blur')
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'blur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // 화살표 마커
    Object.entries(EDGE_STYLES).forEach(([type, style]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('fill', style.stroke)
        .style('opacity', 0.6)
    })

    // 엣지 렌더링
    const linkGroup = g.append('g').attr('class', 'links')
    const links = linkGroup.selectAll('line')
      .data(edgeData)
      .join('line')
      .attr('stroke', d => (EDGE_STYLES[d.relation_type] || EDGE_STYLES.evolved_from).stroke)
      .attr('stroke-width', d => (EDGE_STYLES[d.relation_type] || EDGE_STYLES.evolved_from).width)
      .attr('stroke-dasharray', d => (EDGE_STYLES[d.relation_type] || EDGE_STYLES.evolved_from).dasharray)
      .attr('marker-end', d => `url(#arrow-${d.relation_type || 'evolved_from'})`)
      .style('opacity', d => (EDGE_STYLES[d.relation_type] || EDGE_STYLES.evolved_from).opacity)

    // 노드 그룹
    const nodeGroup = g.append('g').attr('class', 'nodes')
    const nodeGs = nodeGroup.selectAll('g')
      .data(nodeData)
      .join('g')
      .attr('class', 'node-group')
      .style('cursor', 'pointer')

    // 노드 원 — 개선된 렌더링
    nodeGs.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => CATEGORY_COLORS[d.architecture_category] || '#8895A7')
      .attr('fill-opacity', 0.85)
      .attr('stroke', d => CATEGORY_COLORS[d.architecture_category] || '#8895A7')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.3)

    // 노드 레이블
    nodeGs.append('text')
      .attr('class', 'node-label')
      .attr('dy', d => d.radius + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text)')
      .style('font-size', '11px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('user-select', 'none')
      .text(d => d.name.length > 20 ? d.name.slice(0, 18) + '...' : d.name)

    // 툴팁
    const tooltip = d3.select(container)
      .append('div')
      .attr('class', 'architecture-tooltip')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', 'var(--card-bg)')
      .style('border', '1px solid var(--border)')
      .style('border-radius', '10px')
      .style('padding', '10px 14px')
      .style('font-size', '12px')
      .style('color', 'var(--text)')
      .style('box-shadow', '0 8px 24px rgba(0,0,0,0.12)')
      .style('opacity', 0)
      .style('z-index', 50)
      .style('max-width', '280px')
      .style('transition', 'opacity 0.15s')
      .style('backdrop-filter', 'blur(8px)')

    // 호버 인터랙션 — 연결 노드/엣지 하이라이트
    nodeGs
      .on('mouseenter', (event, d) => {
        const catColor = CATEGORY_COLORS[d.architecture_category] || '#8895A7'

        // 호버된 노드에 글로우
        d3.select(event.currentTarget).select('circle')
          .attr('filter', 'url(#glow)')
          .attr('stroke', catColor)
          .attr('stroke-width', 3)
          .attr('stroke-opacity', 0.7)
          .attr('fill-opacity', 1)

        // 연결된 노드/엣지 하이라이트
        const connectedSlugs = new Set()
        edgeData.forEach(e => {
          const src = typeof e.source === 'object' ? e.source.slug : e.source
          const tgt = typeof e.target === 'object' ? e.target.slug : e.target
          if (src === d.slug) connectedSlugs.add(tgt)
          if (tgt === d.slug) connectedSlugs.add(src)
        })

        // 다른 노드 dimming
        svg.selectAll('.node-group').each(function (nd) {
          if (nd.slug === d.slug) return
          const isConn = connectedSlugs.has(nd.slug)
          d3.select(this).select('circle')
            .style('opacity', isConn ? 1 : 0.12)
            .attr('fill-opacity', isConn ? 0.9 : 0.12)
          d3.select(this).select('.node-label')
            .style('opacity', isConn ? 1 : 0.06)
        })

        // 엣지 dimming
        svg.selectAll('.links line').each(function (e) {
          const src = typeof e.source === 'object' ? e.source.slug : e.source
          const tgt = typeof e.target === 'object' ? e.target.slug : e.target
          const isConn = src === d.slug || tgt === d.slug
          d3.select(this)
            .style('opacity', isConn ? 0.8 : 0.03)
            .attr('stroke-width', isConn
              ? (EDGE_STYLES[e.relation_type] || EDGE_STYLES.evolved_from).width * 1.5
              : (EDGE_STYLES[e.relation_type] || EDGE_STYLES.evolved_from).width
            )
        })

        // 툴팁
        const catBadge = d.architecture_category
          ? `<span style="display:inline-block;background:${catColor}20;color:${catColor};font-size:10px;padding:1px 6px;border-radius:9px;margin-left:6px;font-weight:600">${d.architecture_category.toUpperCase()}</span>`
          : ''
        const org = d.organization
          ? `<div style="color:var(--text-secondary);margin-top:2px;font-size:11px">${d.organization}${d.release_date ? ` (${d.release_date.slice(0, 4)})` : ''}</div>`
          : ''
        const snippet = d.key_detail
          ? `<div style="margin-top:4px;color:var(--text-secondary);font-size:11px;line-height:1.4">${d.key_detail.slice(0, 120)}${d.key_detail.length > 120 ? '...' : ''}</div>`
          : ''

        tooltip
          .html(`<strong>${d.name}</strong>${catBadge}${org}${snippet}`)
          .style('opacity', 1)
      })
      .on('mousemove', (event) => {
        const rect = container.getBoundingClientRect()
        tooltip
          .style('left', `${event.clientX - rect.left + 14}px`)
          .style('top', `${event.clientY - rect.top - 12}px`)
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0)
        // 선택/검색 상태에 따라 복원
        applyHighlightState(svg, {
          selectedSlug,
          searchQuery,
          baseEdgeOpacity: baseEdgeOpacityRef.current,
          edgeData,
        })
      })
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeClick?.(d)
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation()
        event.preventDefault()
        onNodeDoubleClick?.(d)
      })

    // 빈 영역 클릭 시 선택 해제
    svg.on('click', () => onNodeClick?.(null))

    // 드래그
    const drag = d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulationRef.current?.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulationRef.current?.alphaTarget(0)
        d.fx = null
        d.fy = null
        debouncedSavePosition(d.slug, d.x, d.y)
      })

    nodeGs.call(drag)

    // 포스 시뮬레이션
    const simulation = d3.forceSimulation(nodeData)
      .force('link', d3.forceLink(edgeData)
        .id(d => d.slug)
        .distance(100)
        .strength(0.4)
      )
      .force('charge', d3.forceManyBody()
        .strength(-250)
        .distanceMax(400)
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => d.radius + 6))
      .force('x', d3.forceX(width / 2).strength(0.03))
      .force('y', d3.forceY(height / 2).strength(0.03))

    simulationRef.current = simulation

    simulation.on('tick', () => {
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      nodeGs.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // 저장된 위치가 있으면 빠르게 안정화
    const hasPositions = nodeData.some(n => n.x !== undefined && n.y !== undefined)
    if (hasPositions) {
      simulation.alpha(0.1).alphaDecay(0.05)
    } else {
      simulation.alpha(1).alphaDecay(0.02)
    }

    // 초기 줌 — 모든 노드가 보이게
    initialZoomTimerRef.current = setTimeout(() => {
      if (!nodeData.length) return
      const xs = nodeData.map(n => n.x || width / 2)
      const ys = nodeData.map(n => n.y || height / 2)
      const minX = Math.min(...xs) - 60
      const maxX = Math.max(...xs) + 60
      const minY = Math.min(...ys) - 60
      const maxY = Math.max(...ys) + 60
      const bw = maxX - minX
      const bh = maxY - minY
      const scale = Math.min(width / bw, height / bh, 1.5) * 0.85
      const tx = width / 2 - (minX + bw / 2) * scale
      const ty = height / 2 - (minY + bh / 2) * scale

      svg.transition().duration(600)
        .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
    }, 800)

    return () => {
      simulation.stop()
      tooltip.remove()
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      if (initialZoomTimerRef.current) clearTimeout(initialZoomTimerRef.current)
    }
  }, [nodes, edges, onNodeClick, onNodeDoubleClick, debouncedSavePosition])

  // 선택/검색 하이라이트 업데이트 (시뮬레이션 재시작 없이)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    applyHighlightState(svg, {
      selectedSlug,
      searchQuery,
      baseEdgeOpacity: baseEdgeOpacityRef.current,
      edgeData: edgeDataRef.current,
    })
  }, [selectedSlug, searchQuery])

  const [legendOpen, setLegendOpen] = useState(false)

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ background: 'transparent', touchAction: 'none' }}
      />
      {/* 접이식 범례 */}
      <div
        className="absolute bottom-3 left-3 rounded-xl text-xs"
        style={{
          background: 'var(--card-bg)',
          border: '1px solid var(--border)',
          opacity: 0.92,
          backdropFilter: 'blur(8px)',
        }}
      >
        <button
          onClick={() => setLegendOpen(!legendOpen)}
          className="flex items-center gap-1.5 px-3 py-2 w-full font-semibold"
          style={{ color: 'var(--text)' }}
        >
          Legend
          {legendOpen ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
        </button>
        {legendOpen && (
          <div className="px-3 pb-2.5 space-y-2.5">
            <div className="flex flex-wrap gap-x-3 gap-y-1.5">
              {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                <span key={cat} className="flex items-center gap-1.5">
                  <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{cat.toUpperCase()}</span>
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1.5">
              {Object.entries(EDGE_STYLES).map(([type, style]) => (
                <span key={type} className="flex items-center gap-1.5">
                  <svg width="22" height="8">
                    <line x1="0" y1="4" x2="22" y2="4" stroke={style.stroke} strokeWidth={style.width} strokeDasharray={style.dasharray || undefined} opacity={style.opacity} />
                  </svg>
                  <span style={{ color: 'var(--text-secondary)' }}>{style.label}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

export default ArchitectureGraph
