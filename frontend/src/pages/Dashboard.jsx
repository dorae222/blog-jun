import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import useAuth from '../hooks/useAuth'
import { getDashboardStats, getPosts, deletePost } from '../api/posts'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    getDashboardStats().then(r => setStats(r.data))
    loadPosts()
  }, [user, navigate])

  const loadPosts = (status = '') => {
    const params = {}
    if (status) params.status = status
    getPosts(params).then(r => setPosts(r.data.results || []))
  }

  useEffect(() => { loadPosts(filter) }, [filter])

  const handleDelete = async (slug) => {
    if (!confirm('Delete this post?')) return
    try {
      await deletePost(slug)
      toast.success('Deleted')
      loadPosts(filter)
    } catch {
      toast.error('Delete failed')
    }
  }

  if (!user) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-6xl mx-auto px-4 py-12"
    >
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text)' }}>Dashboard</h1>
        <Link
          to="/editor"
          className="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors text-sm"
        >
          + New Post
        </Link>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Posts', value: stats.total_posts, color: 'text-blue-600' },
            { label: 'Published', value: stats.published, color: 'text-green-600' },
            { label: 'Drafts', value: stats.drafts, color: 'text-yellow-600' },
            { label: 'Total Views', value: stats.total_views, color: 'text-purple-600' },
          ].map(s => (
            <div
              key={s.label}
              className="p-4 rounded-xl border"
              style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            >
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value?.toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 mb-6">
        {['', 'draft', 'published', 'archived'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-sm px-3 py-1.5 rounded-full border transition-all ${
              filter === f ? 'bg-primary-600 text-white border-primary-600' : ''
            }`}
            style={filter !== f ? { borderColor: 'var(--border)', color: 'var(--text-secondary)' } : {}}
          >
            {f || 'All'}
          </button>
        ))}
      </div>

      {/* Posts List */}
      <div className="space-y-3">
        {posts.map(post => (
          <div
            key={post.id}
            className="flex items-center justify-between p-4 rounded-xl border"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  post.status === 'published' ? 'bg-green-100 text-green-700' :
                  post.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {post.status}
                </span>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {post.post_type?.replace('_', ' ')}
                </span>
              </div>
              <h3 className="font-medium truncate" style={{ color: 'var(--text)' }}>{post.title}</h3>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {new Date(post.created_at).toLocaleDateString('ko-KR')} · {post.view_count} views
              </p>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Link
                to={`/editor/${post.slug}`}
                className="text-sm px-3 py-1 rounded border hover:bg-gray-50 dark:hover:bg-gray-800"
                style={{ borderColor: 'var(--border)' }}
              >
                Edit
              </Link>
              <button
                onClick={() => handleDelete(post.slug)}
                className="text-sm px-3 py-1 rounded border text-red-600 hover:bg-red-50"
                style={{ borderColor: 'var(--border)' }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
