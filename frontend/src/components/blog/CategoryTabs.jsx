import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

const MAIN_TABS = [
  { key: null, label: '전체', path: '/posts' },
  { key: 'ai', label: 'AI', path: '/posts/ai' },
  { key: 'ml', label: 'ML', path: '/posts/ml' },
  { key: 'cloud', label: 'Cloud', path: '/posts/cloud' },
  { key: 'data', label: 'Data Engineering', path: '/posts/data' },
]

const SUB_TABS = {
  ai: [
    { key: null, label: '전체' },
    { key: 'llm', label: 'LLM' },
    { key: 'ssm', label: 'SSM' },
    { key: 'diffusion', label: 'Diffusion' },
    { key: 'vision', label: 'Vision' },
    { key: 'multimodal', label: 'Multimodal' },
    { key: 'agent', label: 'Agent' },
    { key: 'technique', label: 'Technique' },
  ],
  ml: [
    { key: null, label: '전체' },
    { key: 'fundamentals', label: '기초' },
    { key: 'math-foundations', label: '수학' },
    { key: 'preprocessing', label: '전처리' },
    { key: 'supervised-regression', label: '회귀' },
    { key: 'supervised-classification', label: '분류' },
    { key: 'ensemble', label: '앙상블' },
    { key: 'unsupervised', label: '비지도' },
    { key: 'model-evaluation', label: '평가' },
    { key: 'causal-inference', label: '인과추론' },
    { key: 'advanced-algorithms', label: '심화' },
    { key: 'applications', label: '응용' },
    { key: 'mlops', label: 'MLOps' },
  ],
  cloud: [
    { key: null, label: '전체' },
    { key: 'aws', label: 'AWS' },
    { key: 'docker', label: 'Docker' },
    { key: 'lxd', label: 'LXD' },
    { key: 'devops', label: 'DevOps' },
  ],
  data: [
    { key: null, label: '전체' },
    { key: 'hadoop', label: 'Hadoop' },
    { key: 'spark', label: 'Spark' },
    { key: 'database', label: 'Database' },
    { key: 'pipeline', label: 'Pipeline' },
  ],
}

export default function CategoryTabs({ category, sub, counts }) {
  const navigate = useNavigate()
  const subs = category ? SUB_TABS[category] || [] : []

  return (
    <div>
      {/* 메인 카테고리 탭 */}
      <div className="relative flex items-center gap-1 overflow-x-auto pb-px border-b scroll-snap-x"
        style={{ borderColor: 'var(--border)', scrollSnapType: 'x mandatory' }}>
        {MAIN_TABS.map((tab) => {
          const active = tab.key === (category || null)
          const count = tab.key ? counts?.[tab.key]?.count : null
          return (
            <button
              key={tab.key || 'all'}
              onClick={() => navigate(tab.path)}
              className="relative px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors shrink-0"
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
        <div className="flex items-center gap-1 overflow-x-auto py-2"
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
                className="px-3 py-1 text-xs font-medium rounded-full whitespace-nowrap transition-colors shrink-0"
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
      )}
    </div>
  )
}
