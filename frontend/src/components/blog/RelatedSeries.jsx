import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Layers } from 'lucide-react'
import { OptimizedImage } from '../../utils/mediaVariants'
import { getSeries } from '../../api/posts'

/**
 * 글 끝에 붙는 관련 시리즈 추천.
 *
 * 글 하나를 다 읽은 독자가 다음으로 갈 곳은 낱개의 글보다 시리즈다. 한 편으로 끝나는
 * 주제가 드물기 때문이다. 위쪽 「이어서 읽기」가 앞뒤 편과 링크를 다루고, 여기서는
 * 한 단계 위인 **묶음**을 보여 준다.
 *
 * 목록은 한 번만 받아 모듈에 쥐고 있는다. 시리즈가 118개인데 글마다 다시 받으면
 * 본문을 여닫는 동안 같은 응답을 계속 가져오게 된다.
 */
let cached = null

function load() {
  if (!cached) {
    cached = getSeries()
      .then((r) => (r.data?.results ?? r.data ?? []).filter((s) => (s.post_count || 0) > 0))
      .catch(() => {
        cached = null           // 실패는 캐시하지 않는다. 다음 글에서 다시 시도한다
        return []
      })
  }
  return cached
}

export default function RelatedSeries({ series, categoryName, categoryGroup, limit = 4 }) {
  const [all, setAll] = useState([])

  useEffect(() => {
    let alive = true
    load().then((list) => { if (alive) setAll(list) })
    return () => { alive = false }
  }, [])

  const own = useMemo(
    () => (series?.slug ? all.find((s) => s.slug === series.slug) : null),
    [all, series?.slug])

  // 가까운 것부터: 같은 소분류 > 같은 대분류 > 편수가 많은 것
  const related = useMemo(() => {
    const cat = categoryName || own?.category_name
    const grp = categoryGroup || own?.category_group
    return all
      .filter((s) => s.slug !== series?.slug && (s.post_count || 0) > 1)
      .map((s) => ({
        s,
        score: (s.category_name && s.category_name === cat ? 4 : 0)
             + (s.category_group && s.category_group === grp ? 2 : 0),
      }))
      .sort((a, b) => b.score - a.score
        || (b.s.post_count || 0) - (a.s.post_count || 0))
      .filter((x) => x.score > 0)          // 아무 관련 없는 시리즈를 채우지 않는다
      .slice(0, limit)
      .map((x) => x.s)
  }, [all, series?.slug, categoryName, categoryGroup, own, limit])

  if (!own && related.length === 0) return null

  return (
    <section className="mt-10 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--text)' }}>
        <Layers size={18} /> 관련 시리즈
      </h2>

      {own && (
        <Link
          to={`/series?s=${own.slug}`}
          className="group flex gap-4 p-4 mb-3 rounded-xl border transition-shadow hover:shadow-md"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
        >
          {own.cover_image_url && (
            <div className="w-24 h-16 shrink-0 rounded-lg overflow-hidden" style={{ background: 'var(--bg)' }}>
              <OptimizedImage src={own.cover_image_url} alt={own.name} loading="lazy"
                sizes="96px" className="w-full h-full object-cover" />
            </div>
          )}
          <div className="min-w-0">
            <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              이 글이 속한 시리즈 · {own.post_count}편
            </span>
            <p className="text-sm font-semibold mt-1 group-hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text)' }}>
              {own.name}
            </p>
            {own.description && (
              <p className="text-xs mt-1 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                {own.description}
              </p>
            )}
          </div>
        </Link>
      )}

      {related.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {related.map((s) => (
            <Link
              key={s.slug}
              to={`/series?s=${s.slug}`}
              className="group flex gap-3 p-3 rounded-xl border transition-shadow hover:shadow-md"
              style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            >
              {s.cover_image_url && (
                <div className="w-16 h-12 shrink-0 rounded-md overflow-hidden" style={{ background: 'var(--bg)' }}>
                  <OptimizedImage src={s.cover_image_url} alt={s.name} loading="lazy"
                    sizes="64px" className="w-full h-full object-cover" />
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium line-clamp-2 group-hover:text-primary-600 transition-colors"
                  style={{ color: 'var(--text)' }}>
                  {s.name}
                </p>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {s.category_name ? `${s.category_name} · ` : ''}{s.post_count}편
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}
