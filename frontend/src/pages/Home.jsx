import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  FileText, FolderOpen, BookOpen, Tags, ArrowRight,
} from 'lucide-react'

import HeroSection from '../components/portfolio/HeroSection'
import TechStack from '../components/portfolio/TechStack'
import ProjectShowcase from '../components/portfolio/ProjectShowcase'
import Timeline from '../components/portfolio/Timeline'
import PostCard from '../components/blog/PostCard'
import AnimatedCounter from '../components/common/AnimatedCounter'
import ScrollReveal from '../components/common/ScrollReveal'
import { getCategoryIcon } from '../utils/categoryIcons'
import { getPosts, getCategories, getStats } from '../api/posts'

export default function Home() {
  const [latestPosts, setLatestPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState({})
  const [projects, setProjects] = useState([])
  const [activities, setActivities] = useState([])

  useEffect(() => {
    getPosts({ page_size: 6, status: 'published' }).then(r => setLatestPosts(r.data.results || []))
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getStats().then(r => setStats(r.data))
    getPosts({ page_size: 4, status: 'published', category: 'project' }).then(r => setProjects(r.data.results || []))
    getPosts({ page_size: 6, status: 'published', category: 'program' }).then(r => setActivities(r.data.results || []))
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

      {/* Latest Posts */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <ScrollReveal>
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Latest Posts</h2>
              <Link to="/search" className="text-sm text-primary-600 hover:underline inline-flex items-center gap-1">
                View all <ArrowRight size={14} />
              </Link>
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

      {/* Tech Stack */}
      <div className="section-gradient-cyan">
        <TechStack />
      </div>

      {/* Projects */}
      {projects.length > 0 && <ProjectShowcase projects={projects} />}

      {/* Activities Timeline */}
      {activities.length > 0 && <Timeline items={activities} />}
    </motion.div>
  )
}
