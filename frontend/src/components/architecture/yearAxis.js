// 계보 트리의 가로 눈금.
//
// AI 트리는 눈금이 연도이고 인프라 트리는 추상화 층이다. 축을 그리는 일은 같으므로
// 행 키와 라벨만 밖에서 받는다. `computeYearBands` 는 연도용 얇은 포장이다.
//
// 눈금 위치는 반드시 데이터에서 뽑는다. 배치가 해마다 소행 수를 달리 잡아 2015년은 한 줄,
// 2025년은 세 줄이다. 등간격으로 그으면 눈금과 노드가 어긋난다.
//
// 축은 줌 그룹 안이 아니라 화면 좌표에 그리고 변환을 따라 갱신한다. 그래야 라벨이
// 배율에 눌려 작아지지 않고, 옆으로 밀어도 연도가 왼쪽에 남는다.

const TOP_PAD = 70      // 맨 윗해 위로 띄우는 여백
const LABEL_GAP = 18    // 라벨끼리 이보다 가까우면 접는다

// 행별 y 구간을 낸다. 위가 y가 작으므로 top 오름차순이 곧 위에서 아래 순이다.
//
//   keyOf(node)   -> 그 노드가 선 행의 키. 빈 값이면 그 노드는 눈금에서 뺀다
//   labelOf(key)  -> 눈금에 적을 글자
export function computeAxisBands(nodes, keyOf, labelOf) {
  const spans = new Map()
  for (const node of nodes || []) {
    const y = node.tree_y
    if (!Number.isFinite(y)) continue
    const key = keyOf(node)
    if (key === null || key === undefined || key === '') continue
    const span = spans.get(key)
    if (span) {
      span.top = Math.min(span.top, y)
      span.bottom = Math.max(span.bottom, y)
    } else {
      spans.set(key, { key, label: labelOf ? labelOf(key) : key, top: y, bottom: y })
    }
  }

  const bands = [...spans.values()].sort((a, b) => a.top - b.top)
  // 눈금선은 해와 해 사이 빈 곳에 긋는다. 노드 줄 위를 지나가면 선이 라벨을 관통한다.
  return bands.map((band, i) => {
    const prev = bands[i - 1]
    const lineY = prev ? (prev.bottom + band.top) / 2 : band.top - TOP_PAD
    return { ...band, lineY }
  })
}

// 연도 축. AI 트리가 쓴다.
export function computeYearBands(nodes) {
  return computeAxisBands(
    nodes,
    n => {
      if (!n.release_date) return ''
      const y = Number(String(n.release_date).slice(0, 4))
      return Number.isFinite(y) ? y : ''
    },
    k => k,
  )
}

// 현재 줌 변환에 맞춰 눈금을 다시 그린다. 화면 밖으로 나간 행은 그리지 않는다.
export function drawYearAxis(axisG, bands, transform, width, height) {
  const rows = []
  let lastLabelY = -Infinity
  for (const band of bands) {
    const y = transform.applyY(band.lineY)
    if (y < -20 || y > height + 20) continue
    // 축소하면 연도가 붙어 겹친다. 앞 라벨과 너무 가까우면 선만 남기고 숫자를 접는다.
    const showLabel = y - lastLabelY >= LABEL_GAP
    if (showLabel) lastLabelY = y
    rows.push({ key: band.key, label: band.label, y, showLabel })
  }

  const tick = axisG.selectAll('g.year-tick').data(rows, d => d.key)
  tick.exit().remove()

  const entered = tick.enter().append('g').attr('class', 'year-tick')
  entered.append('line')
    .attr('x1', 0)
    .attr('stroke', 'var(--border)')
    .attr('stroke-dasharray', '2,6')
    .style('pointer-events', 'none')
  entered.append('text')
    .attr('x', 10)
    .attr('dy', 13)
    .attr('fill', 'var(--text-secondary)')
    .style('font-size', '11px')
    .style('font-weight', '600')
    .style('letter-spacing', '0.04em')
    .style('pointer-events', 'none')
    .style('user-select', 'none')
    // 눈금선과 노드 위에 얹히므로 글자 뒤를 배경색으로 한 번 깔아 준다
    .style('paint-order', 'stroke')
    .attr('stroke', 'var(--card-bg)')
    .attr('stroke-width', 3)

  const merged = entered.merge(tick)
  merged.attr('transform', d => `translate(0,${d.y})`)
  merged.select('line').attr('x2', width).style('opacity', 0.9)
  merged.select('text')
    .text(d => d.label)
    .style('opacity', d => (d.showLabel ? 1 : 0))
}
