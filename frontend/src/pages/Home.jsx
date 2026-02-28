import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

import HeroSection from '../components/portfolio/HeroSection'
import TechStack from '../components/portfolio/TechStack'
import ProjectShowcase from '../components/portfolio/ProjectShowcase'
import Timeline from '../components/portfolio/Timeline'
import PostCard from '../components/blog/PostCard'
import AnimatedCounter from '../components/common/AnimatedCounter'
import ScrollReveal from '../components/common/ScrollReveal'
import { getPosts, getCategories, getStats } from '../api/posts'

export default function Home() {
  const [latestPosts, setLatestPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [projects, setProjects] = useState([])
  const [activities, setActivities] = useState([])
  const [stats, setStats] = useState({})

  useEffect(() => {
    getPosts({ page_size: 6, status: 'published' }).then(r => setLatestPosts(r.data.results || []))
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getPosts({ post_type: 'project', status: 'published' }).then(r => setProjects(r.data.results || []))
    getPosts({ post_type: 'activity_log', status: 'published' }).then(r => setActivities(r.data.results || []))
    getStats().then(r => setStats(r.data))
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <HeroSection />

      {/* Stats */}
      <section className="py-12 px-4" style={{ background: 'var(--bg-secondary)' }}>
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          <AnimatedCounter end={stats.total_posts || 0} label="Published Posts" icon="📝" />
          <AnimatedCounter end={stats.categories || 0} label="Categories" icon="📂" />
          <AnimatedCounter end={stats.series || 0} label="Series" icon="📚" />
          <AnimatedCounter end={stats.tags || 0} label="Tags" icon="🏷️" />
        </div>
      </section>

      {/* Latest Posts */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal>
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-bold" style={{ color: 'var(--text)' }}>Latest Posts</h2>
              <Link to="/search" className="text-sm text-primary-600 hover:underline">View all →</Link>
            </div>
          </ScrollReveal>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {latestPosts.map((post, i) => (
              <ScrollReveal key={post.id} delay={i * 0.1}>
                <PostCard post={post} />
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 px-4" style={{ background: 'var(--bg-secondary)' }}>
        <div className="max-w-6xl mx-auto">
          <ScrollReveal>
            <h2 className="text-3xl font-bold text-center mb-12" style={{ color: 'var(--text)' }}>
              Categories
            </h2>
          </ScrollReveal>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {categories.map((cat, i) => (
              <ScrollReveal key={cat.id} delay={i * 0.05}>
                <Link
                  to={`/category/${cat.slug}`}
                  className="block p-5 rounded-xl border text-center transition-all hover:shadow-lg hover:-translate-y-1 hover:scale-105"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <div className="text-3xl mb-2">{cat.icon || '📁'}</div>
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

      {/* Projects */}
      {projects.length > 0 && <ProjectShowcase projects={projects} />}

      {/* Tech Stack */}
      <TechStack />

      {/* Activities Timeline */}
      {activities.length > 0 && <Timeline items={activities} />}
    </motion.div>
  )
}
