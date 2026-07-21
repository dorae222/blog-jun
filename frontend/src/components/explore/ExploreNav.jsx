import { Link, useLocation } from 'react-router-dom'
import { List, Network, Map } from 'lucide-react'

// Explore 허브 상단 탭바 — List / Tree / Index 3뷰 전환
const TABS = [
  { key: 'list', label: 'List', to: '/posts', icon: List, match: (p) => p.startsWith('/posts') },
  { key: 'tree', label: 'Tree', to: '/architectures/tree', icon: Network, match: (p) => p.startsWith('/architectures') },
  { key: 'index', label: 'Index', to: '/explore/index', icon: Map, match: (p) => p.startsWith('/explore') },
]

export default function ExploreNav() {
  const { pathname } = useLocation()

  return (
    <nav
      className="flex items-center gap-1 overflow-x-auto scrollbar-hide border-b"
      style={{ borderColor: 'var(--border)' }}
      aria-label="Explore 뷰 전환"
    >
      {TABS.map((tab) => {
        const Icon = tab.icon
        const active = tab.match(pathname)
        return (
          <Link
            key={tab.key}
            to={tab.to}
            aria-current={active ? 'page' : undefined}
            className="relative flex items-center gap-1.5 px-3 sm:px-4 py-2.5 text-xs sm:text-sm whitespace-nowrap transition-colors shrink-0 hover:text-primary-600"
            style={{
              color: active ? 'var(--color-primary-600)' : 'var(--text-secondary)',
              fontWeight: active ? 600 : 500,
            }}
          >
            <Icon size={15} className="shrink-0" />
            {tab.label}
            {active && (
              <span
                className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full"
                style={{ background: 'var(--color-primary-600)' }}
              />
            )}
          </Link>
        )
      })}
    </nav>
  )
}
