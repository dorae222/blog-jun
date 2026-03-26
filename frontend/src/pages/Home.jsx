import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ChevronRight, Eye } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import TechStack from '../components/portfolio/TechStack'
import Timeline from '../components/portfolio/Timeline'
import ScrollReveal from '../components/common/ScrollReveal'
import AnimatedCounter from '../components/common/AnimatedCounter'
import { getCategoryIcon } from '../utils/categoryIcons'
import { getStats, getPosts } from '../api/posts'
import { ACTIVITIES } from '../data/activities'
import { CATEGORY_TREE } from '../data/categories'

export default function Home() {
  const [stats, setStats] = useState({})
  const [recentPosts, setRecentPosts] = useState([])
  const [popularPosts, setPopularPosts] = useState([])
  const [postsTab, setPostsTab] = useState('recent')
  const [error, setError] = useState(false)

  useEffect(() => {
    getStats().then((r) => setStats(r.data)).catch(() => setError(true))
    getPosts({ ordering: '-published_at', page_size: 6 })
      .then((r) => setRecentPosts(r.data.results || []))
      .catch(() => setError(true))
    getPosts({ ordering: '-view_count', page_size: 6 })
      .then((r) => setPopularPosts(r.data.results || []))
      .catch(() => setError(true))
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <HeroSection />

      {/* 카테고리 섹션 */}
      <section className="py-12 md:py-16 px-4 section-gradient-purple">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-center mb-10" style={{ color: 'var(--text)' }}>
              Categories
            </h2>
          </ScrollReveal>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {CATEGORY_TREE.map((cat, i) => (
              <ScrollReveal key={cat.key} delay={i * 0.08}>
                <Link
                  to={cat.path}
                  className="block p-6 rounded-xl text-center transition-all hover:shadow-lg hover:-translate-y-1 glass"
                >
                  <div className="mb-3" style={{ color: cat.color }}>{getCategoryIcon(cat.key, 28)}</div>
                  <h3 className="font-bold text-lg mb-1" style={{ color: cat.color }}>
                    {cat.label}
                  </h3>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {cat.desc}
                  </p>
                </Link>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Blog Stats */}
      <section className="py-12 px-4 section-gradient-blue">
        <div className="max-w-4xl mx-auto text-center">
          <ScrollReveal>
            <div className="flex justify-center gap-8">
              <AnimatedCounter end={stats.total_posts || 0} label="Published Posts" />
              <AnimatedCounter end={stats.categories || 0} label="Categories" />
              <AnimatedCounter end={stats.tags || 0} label="Tags" />
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* Posts (Recent / Popular tabs) */}
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
                <Link to="/posts"
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

      {/* Tech Stack */}
      <div className="section-gradient-cyan">
        <TechStack />
      </div>

      {/* Activities Timeline */}
      <Timeline items={ACTIVITIES} />
    </motion.div>
  )
}
