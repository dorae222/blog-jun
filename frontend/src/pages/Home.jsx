import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, ChevronRight, TrendingUp, Eye } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import TechStack from '../components/portfolio/TechStack'
import Timeline from '../components/portfolio/Timeline'
import ScrollReveal from '../components/common/ScrollReveal'
import AnimatedCounter from '../components/common/AnimatedCounter'
import { getCategoryIcon } from '../utils/categoryIcons'
import { getStats, getPosts } from '../api/posts'
import { ACTIVITIES } from '../data/activities'

const CATEGORIES = [
  {
    key: 'ai', label: 'AI', color: '#FF6F00',
    desc: 'LLM, SSM, Diffusion 등 AI 아키텍처',
    path: '/posts/ai',
  },
  {
    key: 'cloud', label: 'Cloud', color: '#FF9900',
    desc: 'AWS, Docker, DevOps 인프라',
    path: '/posts/cloud',
  },
  {
    key: 'data', label: 'Data Engineering', color: '#336791',
    desc: 'Hadoop, Spark, Pipeline',
    path: '/posts/data',
  },
]

export default function Home() {
  const [stats, setStats] = useState({})
  const [recentPosts, setRecentPosts] = useState([])
  const [popularPosts, setPopularPosts] = useState([])

  useEffect(() => {
    getStats().then((r) => setStats(r.data))
    getPosts({ ordering: '-published_at', page_size: 4 })
      .then((r) => setRecentPosts(r.data.results || []))
      .catch(() => {})
    getPosts({ ordering: '-view_count', page_size: 6 })
      .then((r) => setPopularPosts(r.data.results || []))
      .catch(() => {})
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
          <div className="grid md:grid-cols-3 gap-4">
            {CATEGORIES.map((cat, i) => (
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

      {/* Recent Posts */}
      {recentPosts.length > 0 && (
        <section className="py-12 md:py-16 px-4 section-gradient-purple">
          <div className="max-w-6xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl font-bold text-center mb-10" style={{ color: 'var(--text)' }}>
                Recent Posts
              </h2>
            </ScrollReveal>
            <div className="grid md:grid-cols-2 gap-4 mb-8">
              {recentPosts.map((post, i) => (
                <ScrollReveal key={post.slug} delay={i * 0.08}>
                  <Link to={`/post/${post.slug}`}
                    className="flex flex-col p-5 rounded-xl glass transition-all hover:-translate-y-1"
                    style={{ minHeight: 120 }}>
                    {post.category && (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold
                        px-2.5 py-0.5 rounded-full mb-3 self-start"
                        style={{
                          background: `${post.category.color || '#6366f1'}18`,
                          color: post.category.color || '#6366f1',
                          border: `1px solid ${post.category.color || '#6366f1'}30`,
                        }}>
                        {post.category.name}
                      </span>
                    )}
                    <h3 className="font-semibold text-sm mb-auto line-clamp-2 leading-snug"
                      style={{ color: 'var(--text)' }}>
                      {post.title}
                    </h3>
                    <div className="flex items-center justify-between mt-3">
                      <span className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
                        <Eye size={10} /> {post.view_count || 0}
                      </span>
                      <span className="flex items-center gap-0.5 text-xs font-medium"
                        style={{ color: 'var(--color-primary-500)' }}>
                        읽기 <ArrowRight size={11} />
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

      {/* Popular Posts */}
      {popularPosts.length > 0 && (
        <section className="py-12 md:py-16 px-4">
          <div className="max-w-6xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--text)' }}>
                <TrendingUp size={24} className="inline mr-2 text-primary-600" />
                Popular Posts
              </h2>
              <p className="text-center text-sm mb-10" style={{ color: 'var(--text-secondary)' }}>
                Most viewed posts
              </p>
            </ScrollReveal>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {popularPosts.map((post, i) => (
                <ScrollReveal key={post.slug} delay={i * 0.06}>
                  <Link to={`/post/${post.slug}`}
                    className="flex items-start gap-3 p-4 rounded-xl glass transition-all hover:-translate-y-0.5">
                    <span className="text-2xl font-bold text-primary-600/30 mt-0.5">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm line-clamp-2" style={{ color: 'var(--text)' }}>
                        {post.title}
                      </h3>
                      <div className="flex items-center gap-2 mt-1.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
                        <span className="flex items-center gap-0.5"><Eye size={10} /> {post.view_count}</span>
                        <span>{post.reading_time}min</span>
                      </div>
                    </div>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
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
