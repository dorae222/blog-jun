import { Link } from 'react-router-dom'
import { getCategoryIcon } from '../../utils/categoryIcons'

export default function Sidebar({ categories = [], series = [] }) {
  return (
    <aside className="w-64 shrink-0 hidden lg:block">
      <div className="sticky top-24 space-y-8">
        {/* Categories */}
        {categories.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
              Categories
            </h3>
            <ul className="space-y-1">
              {categories.map((cat) => (
                <li key={cat.id}>
                  <Link
                    to={`/category/${cat.slug}`}
                    className="flex items-center justify-between py-1.5 px-2 rounded-lg text-sm hover:bg-gray-50  transition-colors"
                    style={{ color: 'var(--text)' }}
                  >
                    <span className="inline-flex items-center gap-1.5">{getCategoryIcon(cat.slug, 14)} {cat.name}</span>
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{cat.post_count}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Series */}
        {series.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
              Series
            </h3>
            <ul className="space-y-1">
              {series.map((s) => (
                <li key={s.id}>
                  <Link
                    to={`/series/${s.slug}`}
                    className="block py-1.5 px-2 rounded-lg text-sm hover:bg-gray-50  transition-colors"
                    style={{ color: 'var(--text)' }}
                  >
                    {s.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  )
}
