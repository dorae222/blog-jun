import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye } from 'lucide-react'

export default function FeedCard({ item }) {
  const imageUrl = item.cover_image_url || item.figure_url
  const categoryName = item.category?.name
  const categoryColor = item.category?.color || '#6366f1'

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
    <Link
      to={`/post/${item.slug}`}
      className="group block rounded-xl overflow-hidden border transition-shadow hover:shadow-lg"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
    >
      {/* 이미지 영역 */}
      <div className="relative aspect-[16/10] overflow-hidden"
        style={{ background: imageUrl ? undefined : `linear-gradient(135deg, ${categoryColor}20, ${categoryColor}08)` }}>
        {imageUrl ? (
          <img src={imageUrl} alt={item.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-2xl sm:text-4xl opacity-20" style={{ color: categoryColor }}>
              {categoryName?.[0] || '?'}
            </span>
          </div>
        )}
      </div>

      {/* 텍스트 영역 */}
      <div className="p-3 sm:p-4">
        <h3 className="font-semibold text-sm line-clamp-2 mb-1.5 group-hover:text-primary-600 transition-colors"
          style={{ color: 'var(--text)' }}>
          {item.title}
        </h3>

        {item.summary && (
          <p className="text-xs line-clamp-2 mb-3" style={{ color: 'var(--text-secondary)' }}>
            {item.summary}
          </p>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {categoryName && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                style={{ background: `${categoryColor}15`, color: categoryColor }}>
                {categoryName}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-[11px]" style={{ color: 'var(--text-secondary)' }}>
            <Eye size={11} />
            <span>{item.view_count || 0}</span>
          </div>
        </div>

        {/* 태그 */}
        {item.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {item.tags.slice(0, 3).map((tag) => (
              <span key={tag.id} className="text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
    </motion.div>
  )
}
