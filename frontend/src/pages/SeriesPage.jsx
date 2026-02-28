import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'
import ScrollReveal from '../components/common/ScrollReveal'
import { getPosts, getSeriesDetail } from '../api/posts'

export default function SeriesPage() {
  const { slug } = useParams()
  const [series, setSeries] = useState(null)
  const [posts, setPosts] = useState([])

  useEffect(() => {
    getSeriesDetail(slug).then((r) => setSeries(r.data))
    getPosts({ series__slug: slug, status: 'published' }).then((r) => setPosts(r.data.results || []))
  }, [slug])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-4xl mx-auto px-4 py-12"
    >
      {series && (
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>
            <BookOpen size={28} className="inline mr-2 text-primary-600" />{series.name}
          </h1>
          {series.description && (
            <p style={{ color: 'var(--text-secondary)' }}>{series.description}</p>
          )}
          <p className="text-sm mt-2" style={{ color: 'var(--text-secondary)' }}>
            {posts.length} posts in this series
          </p>
        </div>
      )}

      <div className="space-y-4">
        {posts
          .sort((a, b) => (a.series_order || 0) - (b.series_order || 0))
          .map((post, i) => (
            <ScrollReveal key={post.id} delay={i * 0.05}>
              <Link
                to={`/post/${post.slug}`}
                className="flex items-center gap-4 p-4 rounded-xl border transition-all hover:shadow-md hover:-translate-y-0.5"
                style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
              >
                <span className="text-2xl font-bold text-primary-600 w-8 text-center shrink-0">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold truncate" style={{ color: 'var(--text)' }}>{post.title}</h3>
                  <p className="text-sm truncate" style={{ color: 'var(--text-secondary)' }}>{post.summary}</p>
                </div>
                <span className="text-xs shrink-0" style={{ color: 'var(--text-secondary)' }}>
                  {post.reading_time} min
                </span>
              </Link>
            </ScrollReveal>
          ))}
      </div>
    </motion.div>
  )
}
