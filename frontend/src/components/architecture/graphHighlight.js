import * as d3 from 'd3'

// 하이라이트 상태 통합 처리
export function applyHighlightState(svgEl, opts) {
  const { selectedSlug, searchQuery, baseEdgeOpacity, edgeData, colorOf, edgeStyles } = opts
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
    // 조직 배지와 비공개 고리도 이름과 함께 흐려져야 한다.
    // 따로 두면 흐려진 노드에 배지와 고리만 또렷이 남는다
    const label = d3.select(this).selectAll('.node-label, .node-org, .openness-ring')
    const isSelected = d.slug === selectedSlug
    const isSearchMatch = lowerQuery && d.name.toLowerCase().includes(lowerQuery)
    const dimmed = lowerQuery && !isSearchMatch
    const isConnected = connectedSlugs.has(d.slug)
    const catColor = colorOf(d)

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
