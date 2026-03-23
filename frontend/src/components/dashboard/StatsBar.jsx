import {
  FileText, CheckCircle, Clock, Eye, AlertTriangle, ImageOff,
} from 'lucide-react'

const STAT_DEFS = [
  { label: '총 포스트', icon: FileText,      accent: '#3b82f6', fn: s => s.total_posts  },
  { label: '발행',       icon: CheckCircle,   accent: '#10b981', fn: s => s.published   },
  { label: '초안',       icon: Clock,         accent: '#f59e0b', fn: s => s.drafts      },
  { label: '총 조회수',  icon: Eye,           accent: '#8b5cf6', fn: s => s.total_views },
  { label: '감사 이슈',  icon: AlertTriangle, accent: '#ef4444', fn: null },
  { label: '이미지 없음', icon: ImageOff,     accent: '#f97316', fn: null },
]

export default function StatsBar({ stats, auditTotalIssues, missingImageCount }) {
  if (!stats) return null

  // 동적 fn 주입 (auditSummary, missingImageCount는 외부 상태)
  const defs = STAT_DEFS.map(d => {
    if (d.label === '감사 이슈') return { ...d, fn: () => auditTotalIssues }
    if (d.label === '이미지 없음') return { ...d, fn: () => missingImageCount }
    return d
  })

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {defs.map(({ label, icon: Icon, accent, fn }) => (
        <div key={label} className="relative p-4 rounded-xl overflow-hidden"
          style={{ background: 'var(--card-bg)', border: '1px solid var(--border)',
                   borderLeft: `4px solid ${accent}` }}>
          <Icon size={32} className="absolute right-3 top-3"
            style={{ color: accent, opacity: 0.12 }} />
          <p className="text-2xl font-bold" style={{ color: accent }}>
            {(fn(stats) ?? 0).toLocaleString()}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{label}</p>
        </div>
      ))}
    </div>
  )
}
