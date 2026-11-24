import { useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'
import * as d3 from 'd3'
import { updateArchitecturePosition } from '../../api/posts'
import { CATEGORY_COLORS, EDGE_STYLES, LANE_COLORS, LANE_LABELS, NON_MODEL_KINDS, laneOf as fallbackLaneOf } from '../../data/architectureConstants'
import { escapeHtml, mathToPlainText } from '../../utils/mathText'
import { computeAxisBands, computeYearBands, drawYearAxis } from './yearAxis'
import { applyHighlightState } from './graphHighlight'
import TreeLegend from './TreeLegend'
import NodeLinkBar from './NodeLinkBar'

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
  // 계보 배치는 맨 윗해의 y가 0이다. `n.y || ...`로 쓰면 0이 화면 중앙으로 바뀌어
  // 위쪽 경계가 통째로 어긋난다.
  const xs = nodeData.map(n => (Number.isFinite(n.x) ? n.x : width / 2))
  const ys = nodeData.map(n => (Number.isFinite(n.y) ? n.y : height / 2))
  const minX = Math.min(...xs) - 60
  const maxX = Math.max(...xs) + 60
  const minY = Math.min(...ys) - 60
  const maxY = Math.max(...ys) + 60
  const bw = maxX - minX
  const bh = maxY - minY
  const scale = Math.min(width / bw, height / bh, 1.5) * 0.85
  const tx = width / 2 - (minX + bw / 2) * scale
  const ty = height / 2 - (minY + bh / 2) * scale
  const target = d3.zoomIdentity.translate(tx, ty).scale(scale)
  // duration 0은 애니메이션 없이 바로 맞춘다. d3 transition은 rAF를 타는데 탭이 뒤에 있으면
  // rAF가 멈춰 화면이 어중간한 배율에 얼어붙는다. 사람이 누른 fitAll만 움직여 보이고
  // 저절로 도는 fit은 즉시 맞춘다
  if (duration > 0) {
    svg.transition().duration(duration).call(zoom.transform, target)
  } else {
    svg.call(zoom.transform, target)
  }
}

const ArchitectureGraph = forwardRef(function ArchitectureGraph({
  nodes,
  edges,
  onNodeClick,
  onNodeDoubleClick,
  selectedSlug,
  selectedNode,
  searchQuery,
  categoryColors = CATEGORY_COLORS,
  edgeStyles = EDGE_STYLES,
  getNodeRadius: getNodeRadiusFn = getAINodeRadius,
  categoryField = 'architecture_category',
  onPositionUpdate = updateArchitecturePosition,
  layoutMode = 'force',
  lanes = [],
  // 레인 설정은 트리 응답에서 만들어 내려온다(ArchitectureTreePage의 laneConfig).
  // 기본값은 상수 대비책이라, 가지가 늘어도 이 파일을 고칠 일이 없다
  laneColors = LANE_COLORS,
  laneLabels = LANE_LABELS,
  laneOf = fallbackLaneOf,
  hiddenLanes = [],
  // 계보 축. AI 트리는 연도, 인프라 트리는 추상화 층이다. 넘기지 않으면 연도다
  axisKeyOf = null,
  axisLabelOf = null,
}, ref) {
  const containerRef = useRef(null)
  const svgRef = useRef(null)
  const simulationRef = useRef(null)
  const saveTimersRef = useRef(new Map())
  const initialZoomTimerRef = useRef(null)
  const zoomRef = useRef(null)
  const nodeDataRef = useRef([])
  const edgeDataRef = useRef([])
  const baseEdgeOpacityRef = useRef(0.5)

  const lineage = layoutMode === 'lineage'

  // 노드 색이 뜻하는 바가 모드마다 다르다. 계보에서는 가지(레인)를, 힘 기반에서는 카테고리를 뜻한다
  const colorOf = useCallback(
    (d) => (lineage ? laneColors[laneOf(d)] : categoryColors[d[categoryField]]) || '#8895A7',
    [lineage, categoryColors, categoryField, laneColors, laneOf]
  )

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

  // 디바운스된 위치 저장. 타이머를 노드별로 두는 이유는 여러 개를 잇달아 옮겼을 때
  // 앞의 저장이 뒤의 타이머에 지워지지 않게 하기 위해서다
  const debouncedSavePosition = useCallback((slug, x, y) => {
    const timers = saveTimersRef.current
    if (timers.has(slug)) clearTimeout(timers.get(slug))
    timers.set(slug, setTimeout(async () => {
      timers.delete(slug)
      try {
        await onPositionUpdate(slug, Math.round(x), Math.round(y))
      } catch { /* 위치 저장 실패는 무시 */ }
    }, 500))
  }, [onPositionUpdate])

  useEffect(() => {
    if (!nodes.length || !svgRef.current || !containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight
    const saveTimers = saveTimersRef.current

    // 노드/엣지 복사 (D3가 mutate하므로)
    const nodeData = nodes.map(n => {
      const placed = Number.isFinite(n.tree_x) && Number.isFinite(n.tree_y)
      return {
        ...n,
        placed,
        x: placed ? n.tree_x : undefined,
        y: placed ? n.tree_y : undefined,
        // 계보 모드에서는 좌표가 있는 노드를 못 박는다. 이 두 줄이 없으면
        // forceLink와 clusterX가 파이프라인이 잡아 준 배치를 도로 흩어 버린다
        fx: lineage && placed ? n.tree_x : null,
        fy: lineage && placed ? n.tree_y : null,
        radius: getNodeRadiusFn(n),
      }
    })
    nodeDataRef.current = nodeData

    // source/target을 노드 객체로 미리 풀어 둔다. 시뮬레이션을 돌리지 않는 계보 모드에서는
    // forceLink가 슬러그를 풀어 주지 않아 선을 그릴 좌표가 없다
    const bySlug = new Map(nodeData.map(n => [n.slug, n]))
    const edgeData = edges
      .filter(e => bySlug.has(e.from_slug) && bySlug.has(e.to_slug))
      .map(e => ({
        ...e,
        source: bySlug.get(e.from_slug),
        target: bySlug.get(e.to_slug),
      }))
    edgeDataRef.current = edgeData

    // 좌표가 없는 노드는 이웃 옆에 놓고 시작한다. 화면 원점에서 출발하면
    // 트리에서 한참 떨어진 곳에서 끌려오느라 초기 화면이 넓게 벌어진다
    const loose = nodeData.filter(n => !n.placed)
    if (lineage && loose.length) {
      const placedNodes = nodeData.filter(n => n.placed)
      const cx = d3.mean(placedNodes, n => n.x) ?? width / 2
      const cy = d3.mean(placedNodes, n => n.y) ?? height / 2
      const neighbors = new Map(loose.map(n => [n.slug, []]))
      for (const e of edgeData) {
        if (neighbors.has(e.source.slug) && e.target.placed) neighbors.get(e.source.slug).push(e.target)
        if (neighbors.has(e.target.slug) && e.source.placed) neighbors.get(e.target.slug).push(e.source)
      }
      for (const n of loose) {
        const near = neighbors.get(n.slug)
        n.x = near.length ? d3.mean(near, m => m.x) : cx
        n.y = near.length ? d3.mean(near, m => m.y) : cy
      }
    }

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // 연도 축은 줌 그룹 바깥(화면 좌표)에 둔다. 줌 그룹 안에 넣으면 배율에 눌려
    // 글자가 읽히지 않는다. g보다 먼저 붙여야 노드 밑에 깔린다
    const axisG = svg.append('g').attr('class', 'year-axis')
    const yearBands = !lineage
      ? []
      : (axisKeyOf ? computeAxisBands(nodes, axisKeyOf, axisLabelOf) : computeYearBands(nodes))
    const paintAxis = (transform) => {
      if (!yearBands.length) return
      drawYearAxis(axisG, yearBands, transform, container.clientWidth, container.clientHeight)
    }

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
        // 조직 배지는 이름보다 한 단계 작게 두고, 많이 축소하면 아예 접는다.
        // 투명도는 선택·검색 하이라이트가 쥐고 있으므로 여기서는 display만 건드린다
        g.selectAll('.node-org')
          .style('font-size', `${Math.max(6.5, Math.min(9.5, 9 / scale))}px`)
          .style('display', scale > 0.45 ? null : 'none')
        // 줌 레벨에 따른 엣지 투명도
        baseEdgeOpacityRef.current = Math.max(0.15, Math.min(0.6, scale * 0.35))
        paintAxis(event.transform)
      })

    svg.call(zoom)
    zoomRef.current = zoom
    // 다시 그릴 때 줌 상태는 svg에 남아 있다. 항등 변환으로 그리면 눈금이 한 박자 어긋난다
    paintAxis(d3.zoomTransform(svg.node()))

    // 사람이 직접 확대·이동했는지 기억한다. 프로그램이 건 변환은 sourceEvent가 없다.
    // 시뮬레이션이 잦아든 뒤 다시 맞출 때 사람이 보던 자리를 뺏지 않으려고 둔다
    let userMovedView = false
    zoom.on('zoom.user', (event) => { if (event.sourceEvent) userMovedView = true })

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

    // 노드 원 - 개선된 렌더링
    nodeGs.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', colorOf)
      .attr('fill-opacity', 0.85)
      .attr('stroke', colorOf)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.4)

    // 가중치가 비공개인 모델은 점선 고리를 두른다. 원 자체의 테두리를 끊어 보면
    // 반지름이 8px밖에 안 돼 점선인지 알아볼 수가 없어 바깥에 따로 둘렀다.
    // 본체 원보다 뒤에 붙여야 하이라이트의 select('circle')이 본체를 집는다
    if (lineage) {
      nodeGs.filter(d => d.is_open_source === false)
        .append('circle')
        .attr('class', 'openness-ring')
        .attr('r', d => d.radius + 4)
        .attr('fill', 'none')
        .attr('stroke', colorOf)
        .attr('stroke-width', 1.4)
        .attr('stroke-dasharray', '3,3')
        .attr('stroke-opacity', 0.85)
        .style('pointer-events', 'none')
    }

    // 모델이 아닌 노드(기법·프로토콜·프레임워크와 논문 한 편이 정본인 기법)는
    // 마름모 표식을 두른다. `entry_kind`가 뭘 가르는지 화면에서 보이는 자리다.
    // 원이 아니라 rect로 그린다. 하이라이트가 select('circle')로 본체를 집기 때문에
    // 원을 하나 더 붙이면 그쪽이 잡힐 수 있다.
    if (lineage) {
      nodeGs.filter(d => NON_MODEL_KINDS.has(d.entry_kind))
        .append('rect')
        .attr('class', 'kind-marker')
        .attr('x', d => -(d.radius + 3))
        .attr('y', d => -(d.radius + 3))
        .attr('width', d => (d.radius + 3) * 2)
        .attr('height', d => (d.radius + 3) * 2)
        .attr('transform', 'rotate(45)')
        .attr('fill', 'none')
        .attr('stroke', colorOf)
        .attr('stroke-width', 1.4)
        .attr('stroke-opacity', 0.75)
        .style('pointer-events', 'none')
    }

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

    // 조직 배지. 이름 아래에 깔아 이름을 가리지 않게 한다
    if (lineage) {
      nodeGs.filter(d => !!d.organization)
        .append('text')
        .attr('class', 'node-org')
        .attr('dy', d => d.radius + 25)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-secondary)')
        .attr('fill-opacity', 0.75)
        .style('font-size', '9px')
        .style('pointer-events', 'none')
        .style('user-select', 'none')
        .text(d => (d.organization.length > 14 ? d.organization.slice(0, 13) + '…' : d.organization))
    }

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

    // 호버 인터랙션 - 연결 노드/엣지 하이라이트
    nodeGs
      .on('mouseenter', (event, d) => {
        const catColor = colorOf(d)

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
            el.selectAll('.node-label, .node-org, .openness-ring')
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

        // 툴팁은 항상 표시.
        // 여기는 d3가 innerHTML로 그리는 자리라 React 컴포넌트를 못 쓴다. 그래서
        // KaTeX로 조판하지 않고 수식을 읽을 수 있는 평문으로 벗겨서 넣는다.
        // 120자짜리 미리보기 안에서 조판까지 돌리는 것은 과하고, 그대로 두면
        // 달러와 백슬래시가 화면에 그대로 보인다.
        const catValue = d[categoryField]
        const catBadge = catValue
          ? `<span style="display:inline-block;background:${catColor}20;color:${catColor};font-size:10px;padding:1px 6px;border-radius:9px;margin-left:6px;font-weight:600">${escapeHtml(catValue.toUpperCase())}</span>`
          : ''
        const org = d.organization
          ? `<div style="color:var(--text-secondary);margin-top:2px;font-size:11px">${escapeHtml(d.organization)}${d.release_date ? ` (${escapeHtml(d.release_date.slice(0, 4))})` : ''}</div>`
          : ''
        const openness = d.is_open_source === false ? '비공개 가중치' : '공개 가중치'
        const meta = `<div style="color:var(--text-secondary);margin-top:2px;font-size:10px">${laneLabels[laneOf(d)] || ''} · ${openness}</div>`
        const detail = mathToPlainText(d.key_detail)
        const snippet = detail
          ? `<div style="margin-top:4px;color:var(--text-secondary);font-size:11px;line-height:1.4">${escapeHtml(detail.slice(0, 120))}${detail.length > 120 ? '...' : ''}</div>`
          : ''

        tooltip
          .html(`<strong>${escapeHtml(d.name)}</strong>${catBadge}${org}${meta}${snippet}`)
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
            colorOf,
            edgeStyles,
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

    // 선과 노드를 지금 좌표로 다시 그린다. 시뮬레이션이 돌 때는 tick마다,
    // 계보 모드처럼 안 돌 때는 배치가 바뀐 순간에만 부른다
    const render = () => {
      links.attr('d', d => {
        if (lineage) {
          // 계보에서는 y가 시간이다. 위아래로 휘는 베지에가 세대 흐름을 그대로 보여 준다.
          // 힘 배치에서 쓰던 큰 호를 그대로 두면 선이 트리를 가로질러 계보가 안 읽힌다
          const my = (d.source.y + d.target.y) / 2
          return `M${d.source.x},${d.source.y}C${d.source.x},${my} ${d.target.x},${my} ${d.target.x},${d.target.y}`
        }
        const dx = d.target.x - d.source.x
        const dy = d.target.y - d.source.y
        const dr = Math.sqrt(dx * dx + dy * dy) * 0.8
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`
      })

      nodeGs.attr('transform', d => `translate(${d.x},${d.y})`)
    }

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
        // 시뮬레이션이 없으면 tick이 안 오므로 여기서 직접 그린다
        if (!simulationRef.current) {
          d.x = event.x
          d.y = event.y
          render()
        }
      })
      .on('end', (event, d) => {
        if (!event.active) simulationRef.current?.alphaTarget(0)
        // 계보 모드에서는 손으로 옮긴 자리에 그대로 못 박는다. 놓자마자 힘이 도로 끌어가면
        // 저장한 좌표와 눈에 보이는 자리가 어긋난다
        if (!lineage) {
          d.fx = null
          d.fy = null
        }
        debouncedSavePosition(d.slug, d.x, d.y)
      })

    nodeGs.call(drag)

    // 계보 모드에서 좌표가 다 있으면 시뮬레이션을 돌릴 이유가 없다. 한 번 그리고 끝낸다.
    // 좌표가 없는 노드가 섞여 있으면 그것만 자리를 잡도록 힘을 최소로 걸어 돌린다
    if (lineage && !loose.length) {
      simulationRef.current = null
      render()
    } else {
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
        .force('collision', d3.forceCollide().radius(d => d.radius + 10))

      if (!lineage) {
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
        // 화면 중앙으로 모으는 힘은 계보에서는 독이다. 못 박히지 않은 노드를
        // 트리 밖 한가운데로 끌어내므로 힘 기반일 때만 건다
        simulation
          .force('center', d3.forceCenter(width / 2, height / 2))
          .force('clusterX', d3.forceX(d => catCenters[d[categoryField]]?.x || width / 2).strength(0.08))
          .force('clusterY', d3.forceY(d => catCenters[d[categoryField]]?.y || height / 2).strength(0.08))
      }

      simulationRef.current = simulation
      simulation.on('tick', render)
      // 힘 배치는 노드가 한참 움직인 뒤에야 자리를 잡는다. 800ms에 한 번 맞춘 화면은
      // 대개 어긋나 있으므로 다 잦아들면 한 번 더 맞춘다
      simulation.on('end', () => {
        if (!userMovedView) fitToNodes(svg, zoom, container, nodeData, 0)
      })

      // 저장된 위치가 있으면 빠르게 안정화
      const hasPositions = nodeData.some(n => n.placed)
      if (lineage) {
        simulation.alpha(0.4).alphaDecay(0.04)
      } else if (hasPositions) {
        simulation.alpha(0.1).alphaDecay(0.05)
      } else {
        simulation.alpha(1).alphaDecay(0.02)
      }
    }

    // 초기 줌 - 모든 노드가 보이게.
    // 계보는 좌표가 이미 정해져 있으니 시뮬레이션이 잦아들기를 기다릴 필요가 없다
    initialZoomTimerRef.current = setTimeout(() => {
      fitToNodes(svg, zoom, container, nodeData, 0)
    }, lineage ? 60 : 800)

    // 패널이 열리고 닫히면 컨테이너 폭이 바뀐다. 연도 눈금선이 옛 폭에서 끊기지 않게 다시 그린다
    const resizeObserver = new ResizeObserver(() => paintAxis(d3.zoomTransform(svg.node())))
    resizeObserver.observe(container)

    return () => {
      simulationRef.current?.stop()
      resizeObserver.disconnect()
      tooltip.remove()
      for (const timer of saveTimers.values()) clearTimeout(timer)
      saveTimers.clear()
      if (initialZoomTimerRef.current) clearTimeout(initialZoomTimerRef.current)
    }
  }, [nodes, edges, onNodeClick, onNodeDoubleClick, debouncedSavePosition, categoryColors, edgeStyles, getNodeRadiusFn, categoryField, lineage, colorOf])

  // 선택/검색 하이라이트 업데이트 (시뮬레이션 재시작 없이)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    applyHighlightState(svg, {
      selectedSlug,
      searchQuery,
      baseEdgeOpacity: baseEdgeOpacityRef.current,
      edgeData: edgeDataRef.current,
      colorOf,
      edgeStyles,
    })
  }, [selectedSlug, searchQuery, colorOf, edgeStyles])

  // 가지 접기·펴기. 노드를 다시 그리지 않고 display만 끄므로 줌과 선택 상태가 살아 있다.
  // 하이라이트는 opacity를 쓰고 여기는 display를 쓰므로 서로 덮어쓰지 않는다
  useEffect(() => {
    if (!svgRef.current) return
    const hidden = new Set(hiddenLanes)
    const svg = d3.select(svgRef.current)
    const isHidden = d => hidden.has(laneOf(d))
    svg.selectAll('.node-group').style('display', d => (isHidden(d) ? 'none' : null))
    svg.selectAll('.links path')
      .style('display', d => (isHidden(d.source) || isHidden(d.target) ? 'none' : null))
  }, [hiddenLanes, nodes, edges, lineage, laneOf])

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ background: 'transparent', touchAction: 'none' }}
      />
      <TreeLegend
        lanes={lineage ? lanes : []}
        laneColors={laneColors}
        laneLabels={laneLabels}
        categoryColors={categoryColors}
        edgeStyles={edgeStyles}
        showOpenSource={lineage}
      />
      {/* 링크 두 개는 범례와 같은 하단 줄 가운데에 둔다. 상세 패널은 오른쪽 끝이라
          그래프를 보다가 눈을 크게 옮겨야 닿는다. 노드를 안 고르면 안 그린다 */}
      <NodeLinkBar node={selectedNode} />
    </div>
  )
})

export default ArchitectureGraph
