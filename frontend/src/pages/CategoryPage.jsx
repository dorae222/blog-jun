import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import PostCard from '../components/blog/PostCard'
import ScrollReveal from '../components/common/ScrollReveal'
import { getPosts } from '../api/posts'

const PAGE_SIZE = 10

export default function CategoryPage() {
  const { slug } = useParams()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  // slug + page를 하나의 state로 관리 → slug 변경 시 page가 원자적으로 1로 리셋됨
  const [fetchParams, setFetchParams] = useState({ slug, page: 1 })

  // slug 변경 시 page를 1로 원자적 리셋 (별도 effect 불필요)
  useEffect(() => {
    setFetchParams({ slug, page: 1 })
  }, [slug])

  // fetchParams 변경 시 단 1회 fetch
  useEffect(() => {
    setLoading(true)
    getPosts({
      category__slug: fetchParams.slug,
      status: 'published',
      page: fetchParams.page,
      page_size: PAGE_SIZE,
    })
      .then(r => {
        setPosts(r.data.results || [])
        setTotal(r.data.count || 0)
      })
      .finally(() => setLoading(false))
  }, [fetchParams])

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const page = fetchParams.page

  const goToPage = (newPage) => setFetchParams({ slug, page: newPage })

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-6xl mx-auto px-4 py-12"
    >
      <h1 className="text-3xl font-bold mb-8 capitalize" style={{ color: 'var(--text)' }}>
        {slug.replace(/-/g, ' ')}
      </h1>

      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-2xl animate-pulse" style={{ background: 'var(--bg-secondary)' }} />
          ))}
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post, i) => (
              <ScrollReveal key={post.id} delay={i * 0.05}>
                <PostCard post={post} />
              </ScrollReveal>
            ))}
            {posts.length === 0 && (
              <p style={{ color: 'var(--text-secondary)' }}>No posts in this category yet.</p>
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-10">
              <button
                onClick={() => goToPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg border text-sm transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                Prev
              </button>
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {page} / {totalPages} 페이지
              </span>
              <button
                onClick={() => goToPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 rounded-lg border text-sm transition-colors disabled:opacity-40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </motion.div>
  )
}
