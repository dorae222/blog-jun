import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Layers } from 'lucide-react'
import { OptimizedImage } from '../../utils/mediaVariants'

/**
 * 시리즈 카드 가로 슬라이드.
 * 홈과 시리즈 탭이 같은 것을 쓰므로 여기 하나만 고치면 둘 다 바뀐다.
 *
 * 렌더 개수를 제한하는 이유: 시리즈가 100개를 넘어가면서 홈 한 장에
 * 카드 91개와 이미지 99개가 한꺼번에 올라갔다. 모바일에서 특히 무겁다.
 * 화면 밖 카드는 오른쪽 끝에 닿을 때 더 붙인다.
 */
export default function SeriesRail({ items, rank = false, initial = 12, step = 12 }) {
  const railRef = useRef(null)
  const [edge, setEdge] = useState({ left: false, right: true })
  const [limit, setLimit] = useState(initial)

  const shown = items.slice(0, limit)

  function syncEdges() {
    const el = railRef.current
    if (!el) return
    const atRight = el.scrollLeft + el.clientWidth >= el.scrollWidth - 8
    setEdge({ left: el.scrollLeft > 8, right: !atRight })
    if (atRight && limit < items.length) setLimit((n) => n + step)
  }

  useEffect(() => {
    setLimit(initial)
    const el = railRef.current
    if (el) el.scrollTo({ left: 0 })
  }, [items, initial])

  useEffect(() => {
    syncEdges()
    const el = railRef.current
    if (!el) return
    el.addEventListener('scroll', syncEdges, { passive: true })
    window.addEventListener('resize', syncEdges)
    return () => {
      el.removeEventListener('scroll', syncEdges)
      window.removeEventListener('resize', syncEdges)
    }
  }, [shown.length, items.length])

  function nudge(dir) {
    const el = railRef.current
    if (!el) return
    el.scrollBy({ left: dir * Math.round(el.clientWidth * 0.85), behavior: 'smooth' })
  }

  if (!items.length) return null

  const arrow = { background: 'var(--card-bg)', borderColor: 'var(--border)', color: 'var(--text)' }

  return (
    <div className="relative">
      <button
        onClick={() => nudge(-1)} aria-label="이전"
        className="hidden md:flex absolute -left-4 top-[38%] z-10 w-9 h-9 rounded-full border
          items-center justify-center shadow-md transition-opacity"
        style={{ ...arrow, opacity: edge.left ? 1 : 0, pointerEvents: edge.left ? 'auto' : 'none' }}
      >
        <ChevronLeft size={17} />
      </button>
      <button
        onClick={() => nudge(1)} aria-label="다음"
        className="hidden md:flex absolute -right-4 top-[38%] z-10 w-9 h-9 rounded-full border
          items-center justify-center shadow-md transition-opacity"
        style={{ ...arrow, opacity: edge.right ? 1 : 0, pointerEvents: edge.right ? 'auto' : 'none' }}
      >
        <ChevronRight size={17} />
      </button>

      <div
        ref={railRef}
        className="flex gap-3 sm:gap-4 overflow-x-auto no-scrollbar pb-1"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {shown.map((s, i) => (
          <Link
            key={s.slug}
            to={`/series?s=${s.slug}`}
            className="group shrink-0 rounded-xl overflow-hidden border transition-shadow hover:shadow-lg
              w-[190px] sm:w-[236px]"
            style={{
              scrollSnapAlign: 'start',
              background: 'var(--card-bg)', borderColor: 'var(--border)',
            }}
          >
            <div className="relative aspect-[16/10] overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
              {s.cover_image_url ? (
                <OptimizedImage
                  src={s.cover_image_url} alt={s.name} loading="lazy" sizes="(max-width: 640px) 190px, 240px"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : null}
              {rank && (
                <span className="absolute left-2 bottom-1 text-[38px] font-black leading-none select-none"
                  style={{ color: 'rgba(255,255,255,0.9)', textShadow: '0 2px 10px rgba(0,0,0,0.55)' }}>
                  {i + 1}
                </span>
              )}
              <span className="absolute right-2 top-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                style={{ background: 'rgba(0,0,0,0.58)', color: '#fff' }}>
                <Layers size={10} /> {s.post_count}편
              </span>
            </div>
            <div className="p-3">
              <h3 className="text-[13px] sm:text-sm font-semibold line-clamp-2 leading-snug
                group-hover:text-primary-600 transition-colors"
                style={{ color: 'var(--text)' }}>
                {s.name}
              </h3>
              {s.category_name && (
                <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>{s.category_name}</p>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
