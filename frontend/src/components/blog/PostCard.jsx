import { Link } from 'react-router-dom'
import TiltCard from '../effects/TiltCard'
import { getCategoryIcon } from '../../utils/categoryIcons'

const TYPE_COLORS = {
  article: 'bg-blue-100 text-blue-700',
  paper_review: 'bg-purple-100 text-purple-700',
  tutorial: 'bg-green-100 text-green-700',
  til: 'bg-yellow-100 text-yellow-700',
  project: 'bg-orange-100 text-orange-700',
  activity_log: 'bg-pink-100 text-pink-700',
}

function PostMeta({ post }) {
  const dateStr = post.published_at
    ? new Date(post.published_at).toLocaleDateString('ko-KR')
    : new Date(post.created_at).toLocaleDateString('ko-KR')
  return (
    <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
      <div className="flex items-center gap-3">
        <span>{post.reading_time} min read</span>
        <span>{post.view_count} views</span>
      </div>
      <span>{dateStr}</span>
    </div>
  )
}

function PostBadges({ post }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {post.category && (
        <span
          className="text-xs font-medium px-2 py-0.5 rounded-full"
          style={{ backgroundColor: post.category.color + '20', color: post.category.color }}
        >
          <span className="inline-flex items-center gap-1">
            {getCategoryIcon(post.category.slug, 12)}
            {post.category.name}
          </span>
        </span>
      )}
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TYPE_COLORS[post.post_type] || ''}`}>
        {post.post_type?.replace('_', ' ')}
      </span>
    </div>
  )
}

// Grid 뷰 (기본)
function GridCard({ post }) {
  return (
    <TiltCard>
      <Link to={`/post/${post.slug}`} className="block p-6">
        <div className="mb-3">
          <PostBadges post={post} />
        </div>

        <h3 className="text-lg font-semibold mb-2 line-clamp-2" style={{ color: 'var(--text)' }}>
          {post.title}
        </h3>

        {post.summary && (
          <p className="text-sm mb-3 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
            {post.summary}
          </p>
        )}

        <PostMeta post={post} />

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

// List 뷰 — 가로형 카드
function ListCard({ post }) {
  return (
    <Link
      to={`/post/${post.slug}`}
      className="flex gap-4 p-4 rounded-xl border transition-all hover:shadow-md hover:-translate-y-0.5"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <PostBadges post={post} />
        </div>

        <h3 className="text-base font-semibold mb-1 line-clamp-1" style={{ color: 'var(--text)' }}>
          {post.title}
        </h3>

        {post.summary && (
          <p className="text-sm mb-2 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
            {post.summary}
          </p>
        )}

        <PostMeta post={post} />

        {post.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {post.tags.slice(0, 6).map((tag) => (
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
      </div>
    </Link>
  )
}

export default function PostCard({ post, variant = 'grid' }) {
  if (variant === 'list') return <ListCard post={post} />
  return <GridCard post={post} />
}
