import { useSearchParams } from 'react-router-dom'
import SearchPage from './SearchPage'
import PaperList from './PaperList'
import ArchitectureGallery from './ArchitectureGallery'

const TABS = [
  { key: 'posts', label: '📝 Posts' },
  { key: 'papers', label: '📄 Papers' },
  { key: 'architecture', label: '🏗️ Architecture' },
]

export default function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'posts'

  const setTab = (key) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('tab', key)
      if (key !== 'posts') {
        ;['q', 'type', 'category', 'page', 'view', 'sort'].forEach((k) => next.delete(k))
      }
      return next
    })

  return (
    <div>
      {/* 탭 바 */}
      <div className="max-w-7xl mx-auto px-4 pt-8">
        <div className="flex gap-1 border-b" style={{ borderColor: 'var(--border)' }}>
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === key
                  ? 'border-primary-600'
                  : 'border-transparent hover:text-primary-600'
              }`}
              style={{ color: tab === key ? 'var(--color-primary-600)' : 'var(--text-secondary)' }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 탭 콘텐츠 (각 컴포넌트 자체 패딩 유지) */}
      {tab === 'posts' && <SearchPage />}
      {tab === 'papers' && <PaperList />}
      {tab === 'architecture' && <ArchitectureGallery />}
    </div>
  )
}
