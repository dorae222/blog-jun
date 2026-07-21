import { useEffect, useState, lazy, Suspense } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ChevronRight, Eye } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'

// 3D 카테고리 봇 씬 — three 번들이 크므로 홈에서만 lazy-load
const CategoryBots3D = lazy(() => import('../components/home/CategoryBots3D'))
import ScrollReveal from '../components/common/ScrollReveal'
import { getStats, getFeed } from '../api/posts'
import { CATEGORY_TREE } from '../data/categories'

export default function Home() {
  const [stats, setStats] = useState({})
  const [categoryCounts, setCategoryCounts] = useState({})
  const [recentPosts, setRecentPosts] = useState([])
  const [popularPosts, setPopularPosts] = useState([])
  const [postsTab, setPostsTab] = useState('recent')
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    getStats().then((r) => setStats(r.data)).catch(() => setError(true))
    // 카테고리별 포스트 카운트 (Domain Board 스탯) — 1회만 조회
    getFeed({ page_size: 1, include_counts: 'true', sort: 'latest' })
      .then((r) => setCategoryCounts(r.data.categories || {}))
      .catch(() => {})
    fetchPosts(null)
  }, [])

  function fetchPosts(categoryKey) {
    const params = { page_size: 6 }
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

      {/* Category Bots — 3D 마스코트 (hover 반응 + 클릭 탐색) */}
      <section className="py-12 md:py-16 px-4 section-gradient-blue">
        <div className="max-w-6xl mx-auto">
          <Suspense fallback={<div className="rounded-3xl border" style={{ height: 'clamp(440px, 60vh, 560px)', borderColor: 'var(--border)', background: 'var(--card-bg)' }} />}>
            <CategoryBots3D counts={categoryCounts} />
          </Suspense>
        </div>
      </section>

      {/* Posts (Category filter + Recent/Popular tabs) */}
      {error ? (
        <section className="py-12 md:py-16 px-4 section-gradient-purple">
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
        <section className="py-12 md:py-16 px-4 section-gradient-purple">
          <div className="max-w-6xl mx-auto">
            {/* Category filter pills */}
            <ScrollReveal>
              <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
                <button
                  onClick={() => handleCategoryChange(null)}
                  className="text-sm px-4 py-1.5 rounded-full font-medium transition-colors"
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
                    className="text-sm px-4 py-1.5 rounded-full font-medium transition-colors"
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
            </ScrollReveal>

            {/* Recent / Popular tabs */}
            <ScrollReveal>
              <div className="flex items-center justify-center gap-4 mb-10">
                <button
                  onClick={() => setPostsTab('recent')}
                  className="text-lg font-bold transition-colors"
                  style={{
                    color: postsTab === 'recent' ? 'var(--text)' : 'var(--text-secondary)',
                    borderBottom: postsTab === 'recent' ? '2px solid var(--text)' : '2px solid transparent',
                    paddingBottom: '4px',
                  }}
                >
                  최신
                </button>
                <button
                  onClick={() => setPostsTab('popular')}
                  className="text-lg font-bold transition-colors"
                  style={{
                    color: postsTab === 'popular' ? 'var(--text)' : 'var(--text-secondary)',
                    borderBottom: postsTab === 'popular' ? '2px solid var(--text)' : '2px solid transparent',
                    paddingBottom: '4px',
                  }}
                >
                  인기
                </button>
              </div>
            </ScrollReveal>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {(postsTab === 'recent' ? recentPosts : popularPosts).map((post, i) => (
                <ScrollReveal key={post.slug} delay={i * 0.06}>
                  <Link to={`/post/${post.slug}`}
                    className="flex flex-col p-5 rounded-xl glass transition-all hover:-translate-y-1"
                    style={{ minHeight: 120 }}>
                    {post.category && (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold
                        px-2.5 py-0.5 rounded-full mb-3 self-start"
                        style={{
                          background: `${post.category.color || '#6366f1'}12`,
                          color: post.category.color || '#6366f1',
                          border: `1px solid ${post.category.color || '#6366f1'}25`,
                        }}>
                        {post.category.name}
                      </span>
                    )}
                    <h3 className="font-semibold text-sm mb-auto line-clamp-2 leading-snug"
                      style={{ color: 'var(--text)' }}>
                      {post.title}
                    </h3>
                    <div className="flex items-center gap-3 mt-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      <span>
                        {post.published_at
                          ? new Date(post.published_at).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' })
                          : ''}
                      </span>
                      {post.reading_time && <span>{post.reading_time}min</span>}
                      <span className="flex items-center gap-0.5">
                        <Eye size={10} /> {post.view_count || 0}
                      </span>
                    </div>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
            <ScrollReveal delay={0.4}>
              <div className="text-center">
                <Link to={allPostsPath}
                  className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-lg border
                    text-sm font-medium transition-colors hover:bg-white"
                  style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                  모든 글 보기 <ChevronRight size={14} />
                </Link>
              </div>
            </ScrollReveal>
          </div>
        </section>
      )}
    </motion.div>
    </>
  )
}
