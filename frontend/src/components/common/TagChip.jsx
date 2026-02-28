import { Link } from 'react-router-dom'

export default function TagChip({ tag, size = 'sm' }) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  }

  return (
    <Link
      to={`/search?tag=${tag.slug}`}
      className={`inline-block rounded-full font-medium transition-all hover:scale-105 hover:shadow-sm ${sizeClasses[size]}`}
      style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
    >
      #{tag.name}
    </Link>
  )
}
