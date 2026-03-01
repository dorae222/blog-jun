import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { FileText, FolderOpen, BookOpen, Tags, ArrowRight, ChevronRight } from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import TechStack from '../components/portfolio/TechStack'
import Timeline from '../components/portfolio/Timeline'
import AnimatedCounter from '../components/common/AnimatedCounter'
import ScrollReveal from '../components/common/ScrollReveal'
import { getCategoryIcon } from '../utils/categoryIcons'
import { getCategories, getStats, getPosts } from '../api/posts'
import { ACTIVITIES } from '../data/activities'

export default function Home() {
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState({})
  const [recentPosts, setRecentPosts] = useState([])

  useEffect(() => {
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getStats().then(r => setStats(r.data))
    getPosts({ ordering: '-published_at', page_size: 4 })
      .then(r => setRecentPosts(r.data.results || []))
      .catch(() => {})
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <HeroSection />

      {/* Blog Stats */}
      <section className="py-12 px-4 section-gradient-blue">
        <div className="max-w-4xl mx-auto">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-center mb-8" style={{ color: 'var(--text)' }}>Blog</h2>
          </ScrollReveal>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <AnimatedCounter end={stats.total_posts || 0} label="Published Posts" icon={<FileText size={28} />} />
            <AnimatedCounter end={stats.categories || 0} label="Categories" icon={<FolderOpen size={28} />} />
            <AnimatedCounter end={stats.series || 0} label="Series" icon={<BookOpen size={28} />} />
            <AnimatedCounter end={stats.tags || 0} label="Tags" icon={<Tags size={28} />} />
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 px-4 section-gradient-purple">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal>
            <h2 className="text-2xl font-bold text-center mb-10" style={{ color: 'var(--text)' }}>
              Categories
            </h2>
          </ScrollReveal>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {categories.map((cat, i) => (
              <ScrollReveal key={cat.id} delay={i * 0.05}>
                <Link
                  to={`/category/${cat.slug}`}
                  className="block p-5 rounded-xl text-center transition-all hover:shadow-lg hover:-translate-y-1 glass"
                >
                  <div className="flex justify-center mb-2" style={{ color: cat.color || 'var(--text-secondary)' }}>
                    {getCategoryIcon(cat.slug, 28)}
                  </div>
                  <h3 className="font-semibold text-sm" style={{ color: cat.color || 'var(--text)' }}>
                    {cat.name}
                  </h3>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                    {cat.post_count || 0} posts
                  </p>
                </Link>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Posts */}
      {recentPosts.length > 0 && (
        <section className="py-16 px-4 section-gradient-purple">
          <div className="max-w-6xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl font-bold text-center mb-10" style={{ color: 'var(--text)' }}>
                Recent Posts
              </h2>
            </ScrollReveal>
            <div className="grid md:grid-cols-2 gap-4 mb-8">
              {recentPosts.map((post, i) => (
                <ScrollReveal key={post.slug} delay={i * 0.08}>
                  <Link to={`/posts/${post.slug}`}
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
                        {getCategoryIcon(post.category.slug, 12)}
                        <span className="ml-1">{post.category.name}</span>
                      </span>
                    )}
                    <h3 className="font-semibold text-sm mb-auto line-clamp-2 leading-snug"
                      style={{ color: 'var(--text)' }}>
                      {post.title}
                    </h3>
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {post.published_at
                          ? new Date(post.published_at).toLocaleDateString('ko-KR')
                          : ''}
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

      {/* Tech Stack */}
      <div className="section-gradient-cyan">
        <TechStack />
      </div>

      {/* Activities Timeline (정적 데이터) */}
      <Timeline items={ACTIVITIES} />
    </motion.div>
  )
}
