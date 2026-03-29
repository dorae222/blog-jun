import { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react'
import * as d3 from 'd3'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { updateArchitecturePosition } from '../../api/posts'
import { CATEGORY_COLORS, EDGE_STYLES } from '../../data/architectureConstants'

function getAINodeRadius(node) {
  const paramScale = node.param_scale
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

// 모든 노드가 보이도록 줌 fit
function fitToNodes(svg, zoom, container, nodeData, duration = 600) {
  if (!nodeData.length || !container) return
  const width = container.clientWidth
  const height = container.clientHeight
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
  svg.transition().duration(duration)
    .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
}

// 하이라이트 상태 통합 처리
function applyHighlightState(svgEl, opts) {
  const { selectedSlug, searchQuery, baseEdgeOpacity, edgeData, categoryColors, edgeStyles, categoryField } = opts
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

  svgEl.selectAll('.node-group').each(function (d) {
    const circle = d3.select(this).select('circle')
    const label = d3.select(this).select('.node-label')
    const isSelected = d.slug === selectedSlug
    const isSearchMatch = lowerQuery && d.name.toLowerCase().includes(lowerQuery)
    const dimmed = lowerQuery && !isSearchMatch
    const isConnected = connectedSlugs.has(d.slug)
    const catColor = categoryColors[d[categoryField]] || '#8895A7'

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
  svgEl.selectAll('.links path').each(function (d) {
    const src = typeof d.source === 'object' ? d.source.slug : d.source
    const tgt = typeof d.target === 'object' ? d.target.slug : d.target
    const isConnected = selectedSlug && (src === selectedSlug || tgt === selectedSlug)
    const style = edgeStyles[d.relation_type] || Object.values(edgeStyles)[0]

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
  categoryColors = CATEGORY_COLORS,
  edgeStyles = EDGE_STYLES,
  getNodeRadius: getNodeRadiusFn = getAINodeRadius,
  categoryField = 'architecture_category',
  onPositionUpdate = updateArchitecturePosition,
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

  // API 노출: focusOnNode, zoomIn, zoomOut, fitAll
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
    zoomIn() {
      if (!svgRef.current || !zoomRef.current) return
      d3.select(svgRef.current).transition().duration(300)
        .call(zoomRef.current.scaleBy, 1.4)
    },
    zoomOut() {
      if (!svgRef.current || !zoomRef.current) return
      d3.select(svgRef.current).transition().duration(300)
        .call(zoomRef.current.scaleBy, 1 / 1.4)
    },
    fitAll() {
      if (!svgRef.current || !zoomRef.current) return
      fitToNodes(d3.select(svgRef.current), zoomRef.current, containerRef.current, nodeDataRef.current)
    },
  }), [])

  // 디바운스된 위치 저장
  const debouncedSavePosition = useCallback((slug, x, y) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(async () => {
      try {
        await onPositionUpdate(slug, Math.round(x), Math.round(y))
      } catch { /* 위치 저장 실패는 무시 */ }
    }, 500)
  }, [onPositionUpdate])

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
      radius: getNodeRadiusFn(n),
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
        // 라벨 항상 표시, 축소 시 크기만 줄임
        g.selectAll('.node-label')
          .style('display', 'block')
          .style('font-size', `${Math.max(8, Math.min(12, 11 / scale))}px`)
          .style('opacity', scale > 0.3 ? 1 : Math.max(0.4, scale * 2))
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
    Object.entries(edgeStyles).forEach(([type, style]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('fill', style.stroke)
        .style('opacity', 0.6)
    })

    // 엣지 렌더링 (곡선 path)
    const linkGroup = g.append('g').attr('class', 'links')
    const links = linkGroup.selectAll('path')
      .data(edgeData)
      .join('path')
      .attr('fill', 'none')
      .attr('stroke', d => (edgeStyles[d.relation_type] || Object.values(edgeStyles)[0]).stroke)
      .attr('stroke-width', d => (edgeStyles[d.relation_type] || Object.values(edgeStyles)[0]).width)
      .attr('stroke-dasharray', d => (edgeStyles[d.relation_type] || Object.values(edgeStyles)[0]).dasharray)
      .attr('marker-end', d => `url(#arrow-${d.relation_type || Object.keys(edgeStyles)[0]})`)
      .style('opacity', d => (edgeStyles[d.relation_type] || Object.values(edgeStyles)[0]).opacity)

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
      .attr('fill', d => categoryColors[d[categoryField]] || '#8895A7')
      .attr('fill-opacity', 0.85)
      .attr('stroke', d => categoryColors[d[categoryField]] || '#8895A7')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.4)

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
        const catColor = categoryColors[d[categoryField]] || '#8895A7'

        // 선택 상태에서는 tooltip만 표시, 노드/엣지 시각 변경 안 함
        if (!selectedSlug) {
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

          // 다른 노드 dimming (완화된 강도)
          svg.selectAll('.node-group').each(function (nd) {
            if (nd.slug === d.slug) return
            const isConn = connectedSlugs.has(nd.slug)
            const el = d3.select(this)
            el.select('circle')
              .style('opacity', isConn ? 1 : 0.2)
              .attr('fill-opacity', isConn ? 0.9 : 0.2)
              .attr('stroke-width', isConn ? 2.5 : 2)
            el.select('.node-label')
              .style('opacity', isConn ? 1 : 0.15)
          })

          // 엣지 dimming
          svg.selectAll('.links path').each(function (e) {
            const src = typeof e.source === 'object' ? e.source.slug : e.source
            const tgt = typeof e.target === 'object' ? e.target.slug : e.target
            const isConn = src === d.slug || tgt === d.slug
            const eStyle = edgeStyles[e.relation_type] || Object.values(edgeStyles)[0]
            d3.select(this)
              .style('opacity', isConn ? 0.9 : 0.08)
              .attr('stroke-width', isConn ? eStyle.width * 1.5 : eStyle.width)
          })
        }

        // 툴팁은 항상 표시
        const catValue = d[categoryField]
        const catBadge = catValue
          ? `<span style="display:inline-block;background:${catColor}20;color:${catColor};font-size:10px;padding:1px 6px;border-radius:9px;margin-left:6px;font-weight:600">${catValue.toUpperCase()}</span>`
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
        const tooltipEl = tooltip.node()
        const tw = tooltipEl.offsetWidth || 200
        const th = tooltipEl.offsetHeight || 80
        const mx = event.clientX - rect.left
        const my = event.clientY - rect.top
        const left = (mx + 14 + tw > rect.width) ? mx - tw - 14 : mx + 14
        const top = (my + th > rect.height) ? my - th - 8 : my - 12
        tooltip
          .style('left', `${left}px`)
          .style('top', `${top}px`)
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0)
        // 선택 상태에서는 복원 불필요 (변경하지 않았으므로)
        if (!selectedSlug) {
          applyHighlightState(svg, {
            selectedSlug,
            searchQuery,
            baseEdgeOpacity: baseEdgeOpacityRef.current,
            edgeData,
            categoryColors,
            edgeStyles,
            categoryField,
          })
        }
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

    // 카테고리별 클러스터 중심점 계산
    const categories = [...new Set(nodeData.map(n => n[categoryField]))]
    const catCenters = {}
    categories.forEach((cat, i) => {
      const angle = (2 * Math.PI * i) / categories.length - Math.PI / 2
      const radius = Math.min(width, height) * 0.25
      catCenters[cat] = {
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
      }
    })

    // 포스 시뮬레이션
    const simulation = d3.forceSimulation(nodeData)
      .force('link', d3.forceLink(edgeData)
        .id(d => d.slug)
        .distance(120)
        .strength(0.4)
      )
      .force('charge', d3.forceManyBody()
        .strength(-300)
        .distanceMax(400)
      )
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => d.radius + 10))
      .force('clusterX', d3.forceX(d => catCenters[d[categoryField]]?.x || width / 2).strength(0.08))
      .force('clusterY', d3.forceY(d => catCenters[d[categoryField]]?.y || height / 2).strength(0.08))

    simulationRef.current = simulation

    simulation.on('tick', () => {
      links.attr('d', d => {
        const dx = d.target.x - d.source.x
        const dy = d.target.y - d.source.y
        const dr = Math.sqrt(dx * dx + dy * dy) * 0.8
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`
      })

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
      fitToNodes(svg, zoom, container, nodeData)
    }, 800)

    return () => {
      simulation.stop()
      tooltip.remove()
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      if (initialZoomTimerRef.current) clearTimeout(initialZoomTimerRef.current)
    }
  }, [nodes, edges, onNodeClick, onNodeDoubleClick, debouncedSavePosition, categoryColors, edgeStyles, getNodeRadiusFn, categoryField])

  // 선택/검색 하이라이트 업데이트 (시뮬레이션 재시작 없이)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    applyHighlightState(svg, {
      selectedSlug,
      searchQuery,
      baseEdgeOpacity: baseEdgeOpacityRef.current,
      edgeData: edgeDataRef.current,
      categoryColors,
      edgeStyles,
      categoryField,
    })
  }, [selectedSlug, searchQuery, categoryColors, edgeStyles, categoryField])

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
              {Object.entries(categoryColors).map(([cat, color]) => (
                <span key={cat} className="flex items-center gap-1.5">
                  <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{cat.toUpperCase()}</span>
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1.5">
              {Object.entries(edgeStyles).map(([type, style]) => (
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
