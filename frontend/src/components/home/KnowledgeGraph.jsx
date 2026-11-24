import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as d3 from 'd3'
import client from '../../api/client'

/**
 * 글 사이의 위키링크를 힘-기반 그래프로 그린다.
 * 장식이 아니라 실제 연결 구조라서, 어느 주제가 촘촘한지 한눈에 보이고 클릭하면 그 글로 간다.
 */
const GROUP_LABEL = {
  'ai-ml': 'AI / ML',
  ml: 'ML',
  cloud: 'Cloud',
  'data-engineering': 'Data',
  tool: 'Tool',
}

const GROUP_COLORS = {
  'ai-ml': '#7c8cf8',
  ml: '#5ec2a8',
  cloud: '#4a9ee0',
  'data-engineering': '#e0a34a',
  tool: '#e07a5f',
}

export default function KnowledgeGraph({ height = 420 }) {
  const svgRef = useRef(null)
  const wrapRef = useRef(null)
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [hover, setHover] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let alive = true
    client.get('/knowledge-graph/', { params: { limit: 150 } })
      .then((r) => { if (alive) setData(r.data) })
      .catch(() => { if (alive) setFailed(true) })
    return () => { alive = false }
  }, [])

  const legend = useMemo(() => {
    if (!data) return []
    const counts = {}
    data.nodes.forEach((n) => { counts[n.group] = (counts[n.group] || 0) + 1 })
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5)
  }, [data])

  useEffect(() => {
    if (!data?.nodes?.length || !svgRef.current || !wrapRef.current) return
    const width = wrapRef.current.clientWidth || 900
    const nodes = data.nodes.map((n) => ({ ...n }))
    const byId = new Map(nodes.map((n) => [n.id, n]))
    const links = data.edges
      .filter((e) => byId.has(e.source) && byId.has(e.target))
      .map((e) => ({ ...e }))

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('viewBox', [0, 0, width, height]).attr('width', '100%').attr('height', height)

    const g = svg.append('g')
    svg.call(
      d3.zoom().scaleExtent([0.4, 4]).on('zoom', (ev) => g.attr('transform', ev.transform)),
    )

    // 카테고리를 원 둘레에 앉히고, 같은 그룹은 그 자리로 끌어당긴다.
    // 힘에만 맡기면 골고루 퍼져 무엇이 무엇인지 안 보인다 - 자리를 먼저 정해 준다.
    const groups = [...new Set(nodes.map((n) => n.group))]
      .sort((a, b) =>
        nodes.filter((n) => n.group === b).length - nodes.filter((n) => n.group === a).length)
    const cx = width / 2
    const cy = height / 2
    const ringR = Math.min(width, height) * 0.31
    const anchor = {}
    groups.forEach((grp, i) => {
      const t = (i / groups.length) * Math.PI * 2 - Math.PI / 2
      anchor[grp] = { x: cx + ringR * Math.cos(t), y: cy + ringR * Math.sin(t), t }
    })

    nodes.forEach((n) => {
      const a = anchor[n.group] || { x: cx, y: cy }
      n.x = a.x + (Math.random() - 0.5) * 40
      n.y = a.y + (Math.random() - 0.5) * 40
    })

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d) => d.id).distance(26).strength(0.06))
      .force('charge', d3.forceManyBody().strength(-26))
      .force('gx', d3.forceX((d) => (anchor[d.group] || { x: cx }).x).strength(0.28))
      .force('gy', d3.forceY((d) => (anchor[d.group] || { y: cy }).y).strength(0.28))
      // 전체를 하나의 원 안에 가둔다
      .force('ring', d3.forceRadial(Math.min(width, height) * 0.36, cx, cy).strength(0.05))
      .force('collide', d3.forceCollide().radius((d) => 7 + Math.min(d.degree, 12) * 0.6).strength(0.9))
      .stop()

    sim.tick(300)

    // 그룹 배경 후광 - 덩어리가 어디에 있는지 먼저 눈에 들어오게
    const halo = g.append('g').attr('class', 'halos')
    groups.forEach((grp) => {
      const pts = nodes.filter((n) => n.group === grp)
      if (pts.length < 2) return
      const gx = d3.mean(pts, (p) => p.x)
      const gy = d3.mean(pts, (p) => p.y)
      const r = Math.max(...pts.map((p) => Math.hypot(p.x - gx, p.y - gy))) + 22
      const color = GROUP_COLORS[grp] || '#94a3b8'
      halo.append('circle')
        .attr('cx', gx).attr('cy', gy).attr('r', r)
        .attr('fill', color).attr('fill-opacity', 0.05)
        .attr('stroke', color).attr('stroke-opacity', 0.16).attr('stroke-width', 1)
      halo.append('text')
        .attr('x', gx).attr('y', gy - r - 7)
        .attr('text-anchor', 'middle')
        .attr('font-size', 11).attr('font-weight', 600)
        .attr('fill', color).attr('fill-opacity', 0.85)
        .text(GROUP_LABEL[grp] || grp)
    })

    // link=실제 인용, tag=주제 인접, bridge=섬을 잇는 보조선
    const EDGE_STYLE = { link: [0.3, 1.1], tag: [0.13, 0.7], bridge: [0.08, 0.6] }
    const g2 = g.append('g')
    const link = g2.attr('fill', 'none').attr('stroke', '#64748b')
      .selectAll('path').data(links).join('path')
      .attr('stroke-opacity', (d) => (EDGE_STYLE[d.kind] || EDGE_STYLE.link)[0])
      .attr('stroke-width', (d) => (EDGE_STYLE[d.kind] || EDGE_STYLE.link)[1])
      .attr('d', (d) => {
        const dx = d.target.x - d.source.x
        const dy = d.target.y - d.source.y
        const dr = Math.hypot(dx, dy) * 1.9        // 살짝 휘어야 겹친 선이 구분된다
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`
      })

    const node = g.append('g')
      .selectAll('circle').data(nodes).join('circle')
      .attr('cx', (d) => d.x).attr('cy', (d) => d.y)
      .attr('r', (d) => 3.5 + Math.min(d.degree, 14) * 0.62)
      .attr('fill', (d) => d.color || GROUP_COLORS[d.group] || '#94a3b8')
      .attr('fill-opacity', 0.9)
      .attr('stroke', '#fff').attr('stroke-width', 1.1)
      .style('cursor', 'pointer')
      .on('mouseenter', function (ev, d) {
        setHover(d)
        d3.select(this).attr('stroke', '#0f172a').attr('stroke-width', 2).attr('fill-opacity', 1)
        const near = new Set([d.id])
        links.forEach((l) => {
          if (l.source.id === d.id) near.add(l.target.id)
          if (l.target.id === d.id) near.add(l.source.id)
        })
        node.attr('opacity', (o) => (near.has(o.id) ? 1 : 0.18))
        link.attr('stroke-opacity', (l) =>
          l.source.id === d.id || l.target.id === d.id ? 0.55 : 0.04)
      })
      .on('mouseleave', function () {
        setHover(null)
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 1.1).attr('fill-opacity', 0.9)
        node.attr('opacity', 1)
        link.attr('stroke-opacity', (l) => (EDGE_STYLE[l.kind] || EDGE_STYLE.link)[0])
      })
      .on('click', (ev, d) => navigate(`/post/${d.id}`))

    node.append('title').text((d) => d.title)

  }, [data, height, navigate])

  if (failed) return null

  return (
    <div ref={wrapRef} className="relative w-full">
      {!data && (
        <div className="flex items-center justify-center text-sm" style={{ height, color: 'var(--text-secondary)' }}>
          그래프를 불러오는 중…
        </div>
      )}
      <svg ref={svgRef} className="w-full" style={{ display: data ? 'block' : 'none' }} />

      {data && (
        <>
          <div className="absolute left-0 top-0 flex flex-wrap gap-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
            {legend.map(([grp, n]) => (
              <span key={grp} className="inline-flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full"
                  style={{ background: GROUP_COLORS[grp] || '#94a3b8' }} />
                {grp} {n}
              </span>
            ))}
          </div>
          <div className="absolute right-0 top-0 text-xs" style={{ color: 'var(--text-secondary)' }}>
            글 {data.total_posts} · 연결 {data.total_links}
          </div>
          {hover && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-0 px-3 py-1.5 rounded-lg text-xs max-w-[80%] truncate"
              style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', color: 'var(--text)' }}>
              {hover.title}
              {hover.categoryName ? ` · ${hover.categoryName}` : ''}
            </div>
          )}
        </>
      )}
    </div>
  )
}
