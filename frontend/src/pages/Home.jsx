import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ChevronRight, Eye, ArrowRight } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import ArchitectureGraph from '../components/architecture/ArchitectureGraph'
import ScrollReveal from '../components/common/ScrollReveal'
import { getStats, getPosts, getArchitectureStats, getArchitectureTree } from '../api/posts'
import { CATEGORY_TREE } from '../data/categories'
import { CATEGORY_COLORS } from '../data/architectureConstants'

export default function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({})
  const [recentPosts, setRecentPosts] = useState([])
  const [popularPosts, setPopularPosts] = useState([])
  const [postsTab, setPostsTab] = useState('recent')
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [error, setError] = useState(false)

  // Architecture graph
  const [archStats, setArchStats] = useState(null)
  const [treeNodes, setTreeNodes] = useState([])
  const [treeEdges, setTreeEdges] = useState([])
  const [selectedArchNode, setSelectedArchNode] = useState(null)

  useEffect(() => {
    getStats().then((r) => setStats(r.data)).catch(() => setError(true))
    fetchPosts(null)
    getArchitectureStats().then((r) => setArchStats(r.data)).catch(() => {})
    getArchitectureTree()
      .then((r) => {
        setTreeNodes(r.data.nodes || [])
        setTreeEdges(r.data.edges || [])
      })
      .catch(() => {})
  }, [])

  function fetchPosts(categoryKey) {
    const params = { page_size: 6 }
    if (categoryKey) {
      const cat = CATEGORY_TREE.find(c => c.key === categoryKey)
      if (cat) params.category = cat.key
    }
    getPosts({ ...params, ordering: '-published_at' })
      .then((r) => setRecentPosts(r.data.results || []))
      .catch(() => setError(true))
    getPosts({ ...params, ordering: '-view_count' })
      .then((r) => setPopularPosts(r.data.results || []))
      .catch(() => setError(true))
  }

  function handleCategoryChange(key) {
    setSelectedCategory(key)
    setPostsTab('recent')
    fetchPosts(key)
  }

  const handleArchNodeClick = useCallback((node) => {
    setSelectedArchNode(node)
  }, [])

  const handleArchNodeDoubleClick = useCallback((node) => {
    if (node?.related_post_slug) {
      navigate(`/post/${node.related_post_slug}`)
    }
  }, [navigate])

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

      {/* Architecture Graph Preview */}
      {treeNodes.length > 0 && (
        <section className="py-12 md:py-16 px-4 section-gradient-blue">
          <div className="max-w-5xl mx-auto">
            <ScrollReveal>
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text)' }}>
                  Architecture Lineage
                </h2>
                {archStats && (
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {archStats.total_entries} models · {archStats.total_relations} connections
                  </p>
                )}
              </div>
            </ScrollReveal>

            {/* Graph container */}
            <div
              className="relative h-[350px] md:h-[500px] rounded-xl overflow-hidden border mb-6"
              style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
            >
              <ArchitectureGraph
                nodes={treeNodes}
                edges={treeEdges}
                onNodeClick={handleArchNodeClick}
                onNodeDoubleClick={handleArchNodeDoubleClick}
                selectedSlug={selectedArchNode?.slug}
                searchQuery=""
              />

              {/* Selected node mini-card overlay */}
              <AnimatePresence>
                {selectedArchNode && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 8 }}
                    transition={{ duration: 0.2 }}
                    className="absolute bottom-3 right-3 p-3 rounded-xl border text-sm z-30"
                    style={{
                      background: 'var(--card-bg)',
                      borderColor: 'var(--border)',
                      backdropFilter: 'blur(8px)',
                      maxWidth: 240,
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ background: CATEGORY_COLORS[selectedArchNode.architecture_category] || '#8895A7' }}
                      />
                      <span className="font-semibold truncate" style={{ color: 'var(--text)' }}>
                        {selectedArchNode.name}
                      </span>
                    </div>
                    <p className="text-xs mb-2 truncate" style={{ color: 'var(--text-secondary)' }}>
                      {selectedArchNode.organization}
                      {selectedArchNode.release_date && ` · ${selectedArchNode.release_date.slice(0, 4)}`}
                    </p>
                    <Link
                      to={`/architectures/tree?selected=${selectedArchNode.slug}`}
                      className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:underline"
                    >
                      트리에서 보기 <ArrowRight size={12} />
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <ScrollReveal delay={0.2}>
              <div className="text-center">
                <Link
                  to="/architectures/tree"
                  className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-lg border text-sm font-medium transition-colors hover:bg-gray-50"
                  style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
                >
                  전체 트리 탐색 <ArrowRight size={14} />
                </Link>
              </div>
            </ScrollReveal>
          </div>
        </section>
      )}

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
