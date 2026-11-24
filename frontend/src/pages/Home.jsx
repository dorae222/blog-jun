import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ChevronRight, Eye } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import SeriesShowcase from '../components/home/SeriesShowcase'
import ScrollReveal from '../components/common/ScrollReveal'
import { OptimizedImage } from '../utils/mediaVariants'
import InlineMath from '../components/common/InlineMath'
import { getStats, getFeed } from '../api/posts'
import useCategories from '../hooks/useCategories'

export default function Home() {
  const CATEGORY_TREE = useCategories()
  const [stats, setStats] = useState({})
  const [categoryCounts, setCategoryCounts] = useState({})
  const [recentPosts, setRecentPosts] = useState([])
  const [popularPosts, setPopularPosts] = useState([])
  const [postsTab, setPostsTab] = useState('recent')
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [error, setError] = useState(false)

  // 좁은 화면에서는 목록을 절반만 그린다. 데이터도 그만큼만 받는다.
  const [isNarrow, setIsNarrow] = useState(
    typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 640px)')
    const on = (e) => setIsNarrow(e.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  useEffect(() => {
    getStats().then((r) => setStats(r.data)).catch(() => setError(true))
    // 카테고리별 포스트 카운트 (Domain Board 스탯) - 1회만 조회
    getFeed({ page_size: 1, include_counts: 'true', sort: 'latest' })
      .then((r) => setCategoryCounts(r.data.categories || {}))
      .catch(() => {})
    fetchPosts(null)
  }, [])

  function fetchPosts(categoryKey, narrow = isNarrow) {
    const params = { page_size: narrow ? 4 : 8 }   // 데스크톱 4열x2행, 모바일 4장
    if (categoryKey) params.category = categoryKey
    getFeed({ ...params, sort: 'latest' })
      .then((r) => setRecentPosts(r.data.results || []))
      .catch(() => setError(true))
    getFeed({ ...params, sort: 'popular' })
      .then((r) => setPopularPosts(r.data.results || []))
      .catch(() => setError(true))
  }

  function handleCategoryChange(key) {
    setSelectedCategory(key)
    setPostsTab('recent')
    fetchPosts(key)
  }

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'HJ Tech Blog',
    url: 'https://blog.dorae222.com',
    description: 'AI, 클라우드, 데이터 엔지니어링 기술 블로그',
    author: { '@type': 'Person', name: 'HyeongJun' },
  }

  const allPostsPath = selectedCategory
    ? CATEGORY_TREE.find(c => c.key === selectedCategory)?.path || '/posts'
    : '/posts'

  return (
    <>
    <Helmet>
      <title>HJ Tech Blog</title>
      <meta name="description" content="AI, 클라우드, 데이터 엔지니어링 기술 블로그. 논문 리뷰, 튜토리얼, 프로젝트 기록을 공유합니다." />
      <link rel="canonical" href="https://blog.dorae222.com" />
      <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
    </Helmet>
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <HeroSection stats={stats} />

      {/* 연재 시리즈 - 무엇부터 읽을지 */}
      <section className="py-12 md:py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-baseline justify-between mb-6">
            <div>
              <p className="text-xs font-semibold tracking-widest mb-1" style={{ color: 'var(--text-secondary)' }}>
                SERIES
              </p>
              <h2 className="text-2xl md:text-3xl font-bold" style={{ color: 'var(--text)' }}>
                연재 시리즈
              </h2>
            </div>
            <Link to="/series" className="text-sm hover:text-primary-600 transition-colors inline-flex items-center gap-1"
              style={{ color: 'var(--text-secondary)' }}>
              전체 시리즈 <ChevronRight size={14} />
            </Link>
          </div>
          <SeriesShowcase />
        </div>
      </section>

      {/* Posts (Category filter + Recent/Popular tabs) */}
      {error ? (
        <section className="py-12 md:py-16 px-4">
          <div className="max-w-6xl mx-auto text-center">
            <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
              게시글을 불러오는 중 오류가 발생했습니다.
            </p>
            <button
              onClick={() => { setError(false); window.location.reload() }}
              className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-lg border
                text-sm font-medium transition-colors hover:bg-white"
              style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
            >
              다시 시도
            </button>
          </div>
        </section>
      ) : (recentPosts.length > 0 || popularPosts.length > 0) && (
        <section className="py-12 md:py-16 px-4">
          <div className="max-w-6xl mx-auto">
            {/* 시리즈 섹션과 같은 좌측 헤더 - 페이지 리듬을 맞춘다 */}
            <div className="flex items-baseline justify-between mb-4">
              <div>
                <p className="text-xs font-semibold tracking-widest mb-1" style={{ color: 'var(--text-secondary)' }}>
                  POSTS
                </p>
                <h2 className="text-2xl md:text-3xl font-bold" style={{ color: 'var(--text)' }}>
                  전체 포스트
                </h2>
              </div>
              <Link to={allPostsPath} className="text-sm hover:text-primary-600 transition-colors inline-flex items-center gap-1"
                style={{ color: 'var(--text-secondary)' }}>
                모든 글 <ChevronRight size={14} />
              </Link>
            </div>

            {/* 최신 / 인기 */}
            <div className="flex items-center gap-4 mb-4">
              {[['recent', '최신'], ['popular', '인기']].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setPostsTab(key)}
                  className="text-base font-bold transition-colors pb-1"
                  style={{
                    color: postsTab === key ? 'var(--text)' : 'var(--text-secondary)',
                    borderBottom: postsTab === key ? '2px solid var(--text)' : '2px solid transparent',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* 카테고리 좁히기 */}
            <div className="flex items-center gap-1 mb-5 overflow-x-auto no-scrollbar">
              <button
                onClick={() => handleCategoryChange(null)}
                className="shrink-0 text-sm px-3.5 py-1.5 rounded-full font-medium transition-colors"
                style={{
                  background: !selectedCategory ? 'var(--text)' : 'transparent',
                  color: !selectedCategory ? 'var(--bg)' : 'var(--text-secondary)',
                  border: `1px solid ${!selectedCategory ? 'var(--text)' : 'var(--border)'}`,
                }}
              >
                전체
              </button>
              {CATEGORY_TREE.map(cat => (
                <button
                  key={cat.key}
                  onClick={() => handleCategoryChange(cat.key)}
                  className="shrink-0 text-sm px-3.5 py-1.5 rounded-full font-medium transition-colors"
                  style={{
                    background: selectedCategory === cat.key ? cat.color + '20' : 'transparent',
                    color: selectedCategory === cat.key ? cat.color : 'var(--text-secondary)',
                    border: `1px solid ${selectedCategory === cat.key ? cat.color + '40' : 'var(--border)'}`,
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {(postsTab === 'recent' ? recentPosts : popularPosts).map((post, i) => (
                <ScrollReveal key={post.slug} delay={Math.min(i, 6) * 0.05}>
                  <Link to={`/post/${post.slug}`}
                    className="group block rounded-xl overflow-hidden border transition-shadow hover:shadow-lg h-full"
                    style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
                    <div className="relative aspect-[16/10] overflow-hidden"
                      style={{ background: 'var(--bg-secondary)' }}>
                      {post.cover_image_url && (
                        <OptimizedImage
                          src={post.cover_image_url} alt={post.title} loading="lazy"
                          sizes="(max-width: 768px) 100vw, 25vw"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      )}
                      {post.category && (
                        <span className="absolute left-2 top-2 px-2 py-0.5 rounded-full text-[11px] font-medium"
                          style={{ background: 'rgba(0,0,0,0.55)', color: '#fff' }}>
                          {post.category.name}
                        </span>
                      )}
                    </div>
                    <div className="p-3">
                      <h3 className="text-sm font-semibold line-clamp-2 leading-snug group-hover:text-primary-600 transition-colors"
                        style={{ color: 'var(--text)' }}>
                        <InlineMath text={post.title} />
                      </h3>
                      {/* 날짜·읽는시간·조회수는 카드로 바뀌어도 남긴다 */}
                      <div className="flex items-center gap-2.5 mt-2 text-[11px]"
                        style={{ color: 'var(--text-secondary)' }}>
                        <span>
                          {post.published_at
                            ? new Date(post.published_at).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' })
                            : ''}
                        </span>
                        {post.reading_time ? <span>{post.reading_time}min</span> : null}
                        <span className="flex items-center gap-0.5">
                          <Eye size={10} /> {post.view_count || 0}
                        </span>
                      </div>
                    </div>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>
      )}
    </motion.div>
    </>
  )
}
