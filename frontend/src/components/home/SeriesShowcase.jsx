import { useEffect, useMemo, useRef, useState } from 'react'
import { getSeries } from '../../api/posts'
import { rankSeries } from '../../utils/seriesOrder'
import SeriesRail from './SeriesRail'

/**
 * 홈의 연재 시리즈.
 * 카테고리 탭으로 좁히고 가로로 넘겨 본다. 카드 렌더는 SeriesRail이 맡는다.
 *
 * 순서는 편수 고정이 아니라 최신도 기반으로 매번 조금씩 섞는다(rankSeries).
 * 시드를 컴포넌트 수명 동안 붙들고 있어서, 탭을 옮겨 다녀도 같은 방문 안에서는
 * 배열이 흔들리지 않는다.
 */
export default function SeriesShowcase() {
  const [items, setItems] = useState([])
  const [tab, setTab] = useState('전체')
  const railKey = useRef(0)
  const seed = useRef(Math.random())

  useEffect(() => {
    let alive = true
    getSeries()
      .then((r) => {
        const list = (r.data?.results ?? r.data ?? [])
          .filter((s) => (s.post_count || 0) > 1)
        if (alive) setItems(rankSeries(list, seed.current))
      })
      .catch(() => {})
    return () => { alive = false }
  }, [])

  // 큰 카테고리로 묶는다. 하위 카테고리로 나누면 탭이 스무 개가 넘어간다.
  const tabs = useMemo(() => {
    const seen = []
    items.forEach((s) => {
      const c = s.category_group || s.category_name
      if (c && !seen.includes(c)) seen.push(c)
    })
    return ['전체', ...seen]
  }, [items])

  const shown = tab === '전체'
    ? items
    : items.filter((s) => (s.category_group || s.category_name) === tab)

  if (!items.length) return null

  return (
    <div>
      <div className="flex items-center gap-1 mb-4 overflow-x-auto no-scrollbar">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); railKey.current += 1 }}
            className="shrink-0 text-sm px-3.5 py-1.5 rounded-full font-medium transition-colors"
            style={{
              background: tab === t ? 'var(--text)' : 'transparent',
              color: tab === t ? 'var(--bg)' : 'var(--text-secondary)',
              border: `1px solid ${tab === t ? 'var(--text)' : 'var(--border)'}`,
            }}
          >
            {t}
          </button>
        ))}
      </div>
      <SeriesRail key={`${tab}-${railKey.current}`} items={shown} rank initial={10} />
    </div>
  )
}
