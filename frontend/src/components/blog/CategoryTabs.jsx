import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MAIN_TABS, SUB_TABS } from '../../data/categories'

export default function CategoryTabs({ category, sub, counts }) {
  const navigate = useNavigate()
  const subs = category ? SUB_TABS[category] || [] : []

  return (
    <div>
      {/* 메인 카테고리 탭 */}
      <div className="relative flex items-center gap-1 overflow-x-auto pb-px border-b scroll-snap-x"
        style={{ borderColor: 'var(--border)', scrollSnapType: 'x mandatory', WebkitOverflowScrolling: 'touch' }}>
        {MAIN_TABS.map((tab) => {
          const active = tab.key === (category || null)
          const count = tab.key ? counts?.[tab.key]?.count : null
          return (
            <button
              key={tab.key || 'all'}
              onClick={() => navigate(tab.path)}
              className="relative px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium whitespace-nowrap transition-colors shrink-0"
              style={{ color: active ? 'var(--text)' : 'var(--text-secondary)' }}
            >
              {tab.label}
              {count != null && (
                <span className="ml-1.5 text-xs opacity-60">{count}</span>
              )}
              {active && (
                <motion.div
                  layoutId="main-tab-indicator"
                  className="absolute bottom-0 left-2 right-2 h-0.5 bg-primary-600 rounded-full"
                />
              )}
            </button>
          )
        })}
      </div>

      {/* 서브카테고리 탭 */}
      {subs.length > 0 && (
        <div className="relative">
          <div className="flex items-center gap-1 overflow-x-auto py-2 scrollbar-hide"
            style={{ scrollSnapType: 'x mandatory' }}>
            {subs.map((s) => {
              const active = s.key === (sub || null)
              const subCount = s.key ? counts?.[category]?.subs?.[s.key] : null
              return (
                <button
                  key={s.key || 'all'}
                  onClick={() => {
                    const path = s.key ? `/posts/${category}/${s.key}` : `/posts/${category}`
                    navigate(path)
                  }}
                  className="px-3 py-2 sm:py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors shrink-0"
                  style={{
                    background: active ? 'var(--text)' : 'transparent',
                    color: active ? '#fff' : 'var(--text-secondary)',
                  }}
                >
                  {s.label}
                  {subCount != null && (
                    <span className="ml-1 opacity-70">{subCount}</span>
                  )}
                </button>
              )
            })}
          </div>
          <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none"
            style={{ background: 'linear-gradient(to left, var(--bg), transparent)' }} />
        </div>
      )}
    </div>
  )
}
