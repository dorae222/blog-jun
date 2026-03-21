import { Link } from 'react-router-dom'
import { Eye, Pin } from 'lucide-react'

function isNew(item) {
  const date = item.published_at || item.created_at
  if (!date) return false
  return Date.now() - new Date(date).getTime() < 7 * 24 * 60 * 60 * 1000
}

function Row({ item, index, isPinned }) {
  const categoryName = item.category?.name
  const categoryColor = item.category?.color || '#6366f1'

  return (
    <Link
      to={`/post/${item.slug}`}
      className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-gray-50 border-b"
      style={{ borderColor: 'var(--border)' }}
    >
      {/* 번호 또는 핀 */}
      <div className="w-8 text-center shrink-0">
        {isPinned ? (
          <Pin size={14} className="text-primary-600 mx-auto" />
        ) : (
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{index}</span>
        )}
      </div>

      {/* 제목 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium truncate hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text)' }}>
            {item.title}
          </h3>
          {isNew(item) && (
            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-red-500 text-white shrink-0">
              NEW
            </span>
          )}
        </div>
      </div>

      {/* 서브카테고리 (Desktop) */}
      {categoryName && (
        <span className="hidden md:inline-block text-[11px] font-medium px-2 py-0.5 rounded-full shrink-0"
          style={{ background: `${categoryColor}15`, color: categoryColor }}>
          {categoryName}
        </span>
      )}

      {/* 조회수 */}
      <div className="flex items-center gap-1 text-xs shrink-0 w-16 justify-end"
        style={{ color: 'var(--text-secondary)' }}>
        <Eye size={12} />
        <span>{item.view_count || 0}</span>
      </div>
    </Link>
  )
}

export default function BulletinListView({ items, totalCount, pinnedItems = [] }) {
  return (
    <div className="rounded-xl border overflow-hidden"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
      {/* 헤더 (Desktop) */}
      <div className="hidden md:flex items-center gap-3 px-4 py-2 text-xs font-medium border-b"
        style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
        <div className="w-8 text-center">#</div>
        <div className="flex-1">제목</div>
        <div className="w-20 text-center">카테고리</div>
        <div className="w-16 text-right">조회수</div>
      </div>

      {/* 고정글 */}
      {pinnedItems.map((item) => (
        <Row key={item.slug} item={item} isPinned />
      ))}

      {/* 고정글과 일반글 구분선 */}
      {pinnedItems.length > 0 && items.length > 0 && (
        <div className="h-px mx-4" style={{ background: 'var(--border)' }} />
      )}

      {/* 일반 글 */}
      {items.map((item, i) => (
        <Row key={item.slug} item={item} index={totalCount - i} />
      ))}

      {items.length === 0 && pinnedItems.length === 0 && (
        <div className="py-12 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
          게시글이 없습니다.
        </div>
      )}
    </div>
  )
}
