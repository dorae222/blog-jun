import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import PostCard from '../components/blog/PostCard'
import SearchBar from '../components/common/SearchBar'
import { searchPosts, getPosts, getCategories, getTags } from '../api/posts'

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const q = searchParams.get('q') || ''
  const tag = searchParams.get('tag') || ''
  const postType = searchParams.get('type') || ''

  const [posts, setPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState({ type: postType })

  useEffect(() => {
    getCategories().then(r => setCategories(r.data.results || r.data || []))
    getTags().then(r => setTags(r.data.results || r.data || []))
  }, [])

  useEffect(() => {
    setLoading(true)
    if (q) {
      searchPosts(q).then(r => setPosts(r.data)).finally(() => setLoading(false))
    } else {
      const params = { status: 'published' }
      if (filter.type) params.post_type = filter.type
      getPosts(params).then(r => setPosts(r.data.results || [])).finally(() => setLoading(false))
    }
  }, [q, filter.type])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-6xl mx-auto px-4 py-12"
    >
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4" style={{ color: 'var(--text)' }}>
          {q ? `Search: "${q}"` : 'All Posts'}
        </h1>
        <SearchBar className="max-w-xl" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-8">
        {['', 'article', 'tutorial', 'paper_review', 'til', 'project', 'activity_log'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter({ type })}
            className={`text-sm px-3 py-1.5 rounded-full border transition-all ${
              filter.type === type ? 'bg-primary-600 text-white border-primary-600' : ''
            }`}
            style={filter.type !== type ? { borderColor: 'var(--border)', color: 'var(--text-secondary)' } : {}}
          >
            {type ? type.replace('_', ' ') : 'All'}
          </button>
        ))}
      </div>

      {/* Tag Cloud */}
      {tags.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2">
          {tags.slice(0, 30).map((t) => (
            <a
              key={t.id}
              href={`/search?tag=${t.slug}`}
              className="text-xs px-2.5 py-1 rounded-full transition-all hover:scale-105"
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-secondary)',
                fontSize: `${Math.max(0.7, Math.min(1.1, 0.7 + (t.post_count || 0) * 0.05))}rem`,
              }}
            >
              #{t.name} ({t.post_count})
            </a>
          ))}
        </div>
      )}

      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 rounded-2xl animate-pulse" style={{ background: 'var(--bg-secondary)' }} />
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
          {posts.length === 0 && (
            <p className="col-span-full text-center py-12" style={{ color: 'var(--text-secondary)' }}>
              No posts found.
            </p>
          )}
        </div>
      )}
    </motion.div>
  )
}
