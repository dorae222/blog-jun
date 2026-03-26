import { useRef, useEffect, useCallback, useState } from 'react'
import * as d3 from 'd3'
import { ChevronDown, ChevronUp } from 'lucide-react'

const CATEGORY_COLORS = {
  llm: '#3B82F6',
  ssm: '#10B981',
  diffusion: '#F59E0B',
  multimodal: '#8B5CF6',
  agent: '#EF4444',
  technique: '#6B7280',
  vision: '#EC4899',
}

const EDGE_STYLES = {
  evolved_from: { stroke: '#3B82F6', dasharray: null, width: 1.8, label: 'evolved' },
  inspired_by: { stroke: '#8B5CF6', dasharray: '6,3', width: 1.4, label: 'inspired' },
  variant_of: { stroke: '#10B981', dasharray: '8,3,2,3', width: 1.4, label: 'variant' },
  technique_used: { stroke: '#9CA3AF', dasharray: '2,3', width: 1, label: 'technique' },
}

function getNodeRadius(paramScale) {
  if (!paramScale) return 8
  const s = paramScale.toLowerCase()
  if (s.includes('b') || s.includes('billion')) {
    const num = parseFloat(s)
    if (num >= 100) return 18
    if (num >= 10) return 14
    return 11
  }
  if (s.includes('m') || s.includes('million')) return 7
  return 8
}

export default function ArchitectureGraph({
  nodes,
  edges,
  onNodeClick,
  onNodeDoubleClick,
  selectedSlug,
  searchQuery,
}) {
  const containerRef = useRef(null)
  const svgRef = useRef(null)
  const simulationRef = useRef(null)
  const saveTimerRef = useRef(null)

  // 디바운스된 위치 저장
  const debouncedSavePosition = useCallback((slug, x, y) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(async () => {
      try {
        const { updateArchitecturePosition } = await import('../../api/posts')
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

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // 줌 그룹
    const g = svg.append('g')

    // 줌 동작
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
        // 줌 레벨에 따라 레이블 표시
        const scale = event.transform.k
        g.selectAll('.node-label')
          .style('display', scale > 0.5 ? 'block' : 'none')
          .style('font-size', `${Math.min(12, 11 / scale)}px`)
      })

    svg.call(zoom)

    // 화살표 마커 정의
    const defs = svg.append('defs')
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
        .style('opacity', 0.7)
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
      .style('opacity', 0.5)

    // 노드 그룹
    const nodeGroup = g.append('g').attr('class', 'nodes')
    const nodeGs = nodeGroup.selectAll('g')
      .data(nodeData)
      .join('g')
      .attr('class', 'node-group')
      .style('cursor', 'pointer')

    // 노드 원
    nodeGs.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => CATEGORY_COLORS[d.architecture_category] || '#6B7280')
      .attr('stroke', 'transparent')
      .attr('stroke-width', 3)
      .style('transition', 'stroke 0.2s, stroke-width 0.2s')

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
      .style('border-radius', '8px')
      .style('padding', '8px 12px')
      .style('font-size', '12px')
      .style('color', 'var(--text)')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.15)')
      .style('opacity', 0)
      .style('z-index', 50)
      .style('max-width', '260px')
      .style('transition', 'opacity 0.15s')

    // 인터랙션
    nodeGs
      .on('mouseenter', (event, d) => {
        d3.select(event.currentTarget).select('circle')
          .attr('stroke', CATEGORY_COLORS[d.architecture_category] || '#6B7280')
          .attr('stroke-width', 3)
          .attr('stroke-opacity', 0.4)

        const snippet = d.key_detail
          ? d.key_detail.slice(0, 100) + (d.key_detail.length > 100 ? '...' : '')
          : ''
        const org = d.organization ? `<div style="color:var(--text-secondary);margin-bottom:2px">${d.organization}</div>` : ''

        tooltip
          .html(`<strong>${d.name}</strong>${org}${snippet ? `<div style="margin-top:4px;color:var(--text-secondary)">${snippet}</div>` : ''}`)
          .style('opacity', 1)
      })
      .on('mousemove', (event) => {
        const rect = container.getBoundingClientRect()
        tooltip
          .style('left', `${event.clientX - rect.left + 12}px`)
          .style('top', `${event.clientY - rect.top - 10}px`)
      })
      .on('mouseleave', (event, d) => {
        const isSelected = d.slug === selectedSlug
        d3.select(event.currentTarget).select('circle')
          .attr('stroke', isSelected ? '#fff' : 'transparent')
          .attr('stroke-width', isSelected ? 3 : 3)
          .attr('stroke-opacity', 1)
        tooltip.style('opacity', 0)
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
    setTimeout(() => {
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
    }
  }, [nodes, edges, onNodeClick, onNodeDoubleClick, debouncedSavePosition])

  // 선택/검색 하이라이트 업데이트 (시뮬레이션 재시작 없이)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)

    const lowerQuery = (searchQuery || '').toLowerCase()

    svg.selectAll('.node-group').each(function (d) {
      const circle = d3.select(this).select('circle')
      const label = d3.select(this).select('.node-label')
      const isSelected = d.slug === selectedSlug
      const isSearchMatch = lowerQuery && d.name.toLowerCase().includes(lowerQuery)
      const dimmed = lowerQuery && !isSearchMatch

      circle
        .attr('stroke', isSelected ? '#fff' : isSearchMatch ? '#FBBF24' : 'transparent')
        .attr('stroke-width', isSelected ? 3 : isSearchMatch ? 2.5 : 3)
        .style('opacity', dimmed ? 0.15 : 1)

      label.style('opacity', dimmed ? 0.1 : 1)
    })

    svg.selectAll('.links line')
      .style('opacity', lowerQuery ? 0.08 : 0.5)
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
          opacity: 0.9,
        }}
      >
        <button
          onClick={() => setLegendOpen(!legendOpen)}
          className="flex items-center gap-1.5 px-3 py-2 w-full font-semibold"
          style={{ color: 'var(--text)' }}
        >
          범례
          {legendOpen ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
        </button>
        {legendOpen && (
          <div className="px-3 pb-2 space-y-2">
            <div className="flex flex-wrap gap-x-3 gap-y-1">
              {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                <span key={cat} className="flex items-center gap-1">
                  <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{cat.toUpperCase()}</span>
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1">
              {Object.entries(EDGE_STYLES).map(([type, style]) => (
                <span key={type} className="flex items-center gap-1">
                  <svg width="20" height="8">
                    <line x1="0" y1="4" x2="20" y2="4" stroke={style.stroke} strokeWidth={style.width} strokeDasharray={style.dasharray || undefined} />
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
}
