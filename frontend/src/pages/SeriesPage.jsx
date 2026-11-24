import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { ChevronRight, ArrowLeft, Eye, Layers } from 'lucide-react'
import { getSeries } from '../api/posts'
import client from '../api/client'
import { OptimizedImage } from '../utils/mediaVariants'
import InlineMath from '../components/common/InlineMath'
import SeriesRail from '../components/home/SeriesRail'

/**
 * 연재 시리즈 목록과 상세.
 * 목록에서는 표지로 시리즈를 고르고, 하나를 고르면 그 시리즈의 글이 편 순서대로 펼쳐진다.
 * 상세에서도 각 편의 표지를 살려 두는데, 글자만 있는 목록은 어느 편이 무엇인지 잘 안 붙기 때문이다.
 */
export default function SeriesPage() {
  const [params, setParams] = useSearchParams()
  const active = params.get('s') || ''
  const [series, setSeries] = useState([])
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    getSeries()
      .then((r) => {
        const list = (r.data?.results ?? r.data ?? []).filter((s) => (s.post_count || 0) > 0)
        list.sort((a, b) => (b.post_count || 0) - (a.post_count || 0))
        if (alive) setSeries(list)
      })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!active) { setPosts([]); return }
    let alive = true
    window.scrollTo({ top: 0 })
    client.get('/posts/', { params: { series__slug: active, page_size: 100, ordering: 'series_order' } })
      .then((r) => {
        const list = r.data?.results ?? r.data ?? []
        list.sort((a, b) => (a.series_order || 0) - (b.series_order || 0))
        if (alive) setPosts(list)
      })
      .catch(() => { if (alive) setPosts([]) })
    return () => { alive = false }
  }, [active])

  const current = useMemo(() => series.find((s) => s.slug === active), [series, active])

  // 큰 카테고리로 묶는다. 100개가 넘는 시리즈를 한 줄로 쭉 늘어놓으면 무엇이 있는지 안 보인다.
  const groups = useMemo(() => {
    const m = new Map()
    series.forEach((s) => {
      const g = s.category_group || s.category_name || '기타'
      if (!m.has(g)) m.set(g, [])
      m.get(g).push(s)
    })
    return [...m.entries()].sort((a, b) => b[1].length - a[1].length)
  }, [series])

  // 같은 카테고리를 먼저, 그다음 편수가 많은 순
  const related = useMemo(() => {
    if (!active) return []
    return series
      .filter((s) => s.slug !== active && (s.post_count || 0) > 1)
      .sort((a, b) => {
        const sameA = a.category_name && a.category_name === current?.category_name ? 1 : 0
        const sameB = b.category_name && b.category_name === current?.category_name ? 1 : 0
        if (sameA !== sameB) return sameB - sameA
        return (b.post_count || 0) - (a.post_count || 0)
      })
      .slice(0, 8)
  }, [series, active, current])

  return (
    <>
      <Helmet>
        <title>{current ? `${current.name} | 연재 시리즈` : '연재 시리즈'} | HJ Tech Blog</title>
        <meta name="description" content={current?.description || '주제별로 이어 읽는 연재 시리즈 모음'} />
      </Helmet>

      <div className="w-full max-w-6xl mx-auto px-4 py-10 md:py-14">
        {!active && (
          <>
            <header className="mb-8">
              <p className="text-xs font-semibold tracking-widest mb-1" style={{ color: 'var(--text-secondary)' }}>
                SERIES
              </p>
              <h1 className="text-3xl md:text-4xl font-bold" style={{ color: 'var(--text)' }}>
                연재 시리즈
              </h1>

            </header>

            {loading ? (
              <div className="space-y-8">
                {Array.from({ length: 3 }).map((_, g) => (
                  <div key={g}>
                    <div className="h-5 w-32 rounded skeleton mb-3" />
                    <div className="flex gap-4 overflow-hidden">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="shrink-0 w-[236px] rounded-xl overflow-hidden border"
                          style={{ borderColor: 'var(--border)' }}>
                          <div className="aspect-[16/10] skeleton" />
                          <div className="p-3 space-y-2">
                            <div className="h-4 rounded skeleton w-3/4" />
                            <div className="h-3 rounded skeleton w-1/3" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-10">
                {groups.map(([group, rows]) => (
                  <section key={group}>
                    <div className="flex items-baseline gap-2 mb-3">
                      <h2 className="text-lg md:text-xl font-bold" style={{ color: 'var(--text)' }}>
                        {group}
                      </h2>
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {rows.length}개 시리즈
                      </span>
                    </div>
                    <SeriesRail items={rows} initial={10} />
                  </section>
                ))}
              </div>
            )}
          </>
        )}

        {active && (
          <>
            <button
              onClick={() => setParams({})}
              className="inline-flex items-center gap-1.5 text-sm mb-6 hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              <ArrowLeft size={15} /> 시리즈 목록
            </button>

            {/* 시리즈 표지를 머리에 세워 어떤 묶음인지 먼저 보이게 한다 */}
            <header className="mb-8 grid gap-6 md:grid-cols-[300px_1fr] items-start">
              {current?.cover_image_url && (
                <div className="rounded-xl overflow-hidden border aspect-[16/10]"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
                  <div className="relative w-full h-full">
                    <OptimizedImage src={current.cover_image_url} alt={current.name}
                      sizes="300px" className="w-full h-full object-cover" />
                  </div>
                </div>
              )}
              <div>
                <p className="text-xs font-semibold tracking-widest mb-1" style={{ color: 'var(--text-secondary)' }}>
                  SERIES
                </p>
                <h1 className="text-2xl md:text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>
                  {current?.name || active}
                </h1>
                {current?.description && (
                  <p className="text-sm mb-3 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                    {current.description}
                  </p>
                )}
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  전 {posts.length}편
                </p>
              </div>
            </header>

            <ol className="space-y-3">
              {posts.map((p, idx) => (
                <li key={p.slug}>
                  <Link
                    to={`/post/${p.slug}`}
                    className="group flex items-start gap-3 sm:gap-4 p-3 rounded-xl border transition-shadow hover:shadow-md"
                    style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                  >
                    <span className="relative shrink-0 w-[104px] sm:w-[168px] rounded-lg overflow-hidden"
                      style={{ background: 'var(--bg-secondary)', aspectRatio: '16 / 10' }}>
                      {p.cover_image_url && (
                        <OptimizedImage src={p.cover_image_url} alt={p.title} loading="lazy" sizes="168px"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      )}
                      <span className="absolute left-1.5 top-1.5 w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-bold"
                        style={{ background: 'rgba(0,0,0,0.62)', color: '#fff' }}>
                        {String(p.series_order || idx + 1).padStart(2, '0')}
                      </span>
                    </span>
                    <span className="min-w-0 flex-1 flex flex-col justify-start py-0.5">
                      <span className="block font-semibold leading-snug group-hover:text-primary-600 transition-colors"
                        style={{ color: 'var(--text)' }}>
                        {p.title}
                      </span>
                      {p.summary && (
                        <span className="block mt-1 text-[13px] sm:text-sm line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                          <InlineMath text={p.summary} />
                        </span>
                      )}
                      <span className="flex items-center gap-3 mt-2 text-[11px]" style={{ color: 'var(--text-secondary)' }}>
                        {p.reading_time ? <span>{p.reading_time}min</span> : null}
                        <span className="flex items-center gap-0.5"><Eye size={10} /> {p.view_count || 0}</span>
                      </span>
                    </span>
                    <ChevronRight size={16} className="shrink-0 self-center opacity-40 group-hover:opacity-100 transition-opacity" />
                  </Link>
                </li>
              ))}
            </ol>

            {related.length > 0 && (
              <section className="mt-14">
                <div className="flex items-baseline justify-between mb-4">
                  <h2 className="text-xl font-bold" style={{ color: 'var(--text)' }}>다른 시리즈</h2>
                  <button onClick={() => setParams({})}
                    className="text-sm hover:text-primary-600 transition-colors inline-flex items-center gap-1"
                    style={{ color: 'var(--text-secondary)' }}>
                    전체 보기 <ChevronRight size={14} />
                  </button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                  {related.map((s) => (
                    <button
                      key={s.slug}
                      onClick={() => setParams({ s: s.slug })}
                      className="group text-left rounded-xl overflow-hidden border transition-shadow hover:shadow-lg"
                      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                    >
                      <div className="relative aspect-[16/10] overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
                        {s.cover_image_url && (
                          <OptimizedImage src={s.cover_image_url} alt={s.name} loading="lazy" sizes="25vw"
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                        )}
                        <span className="absolute right-2 top-2 px-2 py-0.5 rounded-full text-[11px] font-medium"
                          style={{ background: 'rgba(0,0,0,0.58)', color: '#fff' }}>
                          {s.post_count}편
                        </span>
                      </div>
                      <div className="p-3">
                        <h3 className="text-sm font-semibold line-clamp-2 leading-snug group-hover:text-primary-600 transition-colors"
                          style={{ color: 'var(--text)' }}>
                          {s.name}
                        </h3>
                        {s.category_name && (
                          <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>{s.category_name}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </>
  )
}
