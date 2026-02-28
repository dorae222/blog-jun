import { Link } from 'react-router-dom'
import TiltCard from '../effects/TiltCard'

export default function PostCard({ post }) {
  const typeColors = {
    article: 'bg-blue-100 text-blue-700',
    paper_review: 'bg-purple-100 text-purple-700',
    tutorial: 'bg-green-100 text-green-700',
    til: 'bg-yellow-100 text-yellow-700',
    project: 'bg-orange-100 text-orange-700',
    activity_log: 'bg-pink-100 text-pink-700',
  }

  return (
    <TiltCard>
      <Link to={`/post/${post.slug}`} className="block p-6">
        <div className="flex items-center gap-2 mb-3">
          {post.category && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: post.category.color + '20',
                color: post.category.color,
              }}
            >
              {post.category.icon} {post.category.name}
            </span>
          )}
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${typeColors[post.post_type] || ''}`}>
            {post.post_type?.replace('_', ' ')}
          </span>
        </div>

        <h3 className="text-lg font-semibold mb-2 line-clamp-2" style={{ color: 'var(--text)' }}>
          {post.title}
        </h3>

        {post.summary && (
          <p className="text-sm mb-3 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
            {post.summary}
          </p>
        )}

        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
          <div className="flex items-center gap-3">
            <span>{post.reading_time} min read</span>
            <span>{post.view_count} views</span>
          </div>
          <span>
            {post.published_at
              ? new Date(post.published_at).toLocaleDateString('ko-KR')
              : new Date(post.created_at).toLocaleDateString('ko-KR')}
          </span>
        </div>

        {post.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {post.tags.slice(0, 4).map((tag) => (
              <span
                key={tag.id}
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
              >
                #{tag.name}
              </span>
            ))}
          </div>
        )}
      </Link>
    </TiltCard>
  )
}
