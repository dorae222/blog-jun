import {
  FileText, CheckCircle, Clock, Eye, AlertTriangle, ImageOff,
} from 'lucide-react'
import CARD_COLORS, { STAT_MAP, getCardStyle } from '../../data/cardColors'

const STAT_DEFS = [
  { label: '총 포스트',  icon: FileText,      colorKey: STAT_MAP.total,     fn: s => s.total_posts  },
  { label: '발행',       icon: CheckCircle,   colorKey: STAT_MAP.published, fn: s => s.published   },
  { label: '초안',       icon: Clock,         colorKey: STAT_MAP.drafts,    fn: s => s.drafts      },
  { label: '총 조회수',  icon: Eye,           colorKey: STAT_MAP.views,     fn: s => s.total_views },
  { label: '감사 이슈',  icon: AlertTriangle, colorKey: STAT_MAP.issues,    fn: null },
  { label: '이미지 없음', icon: ImageOff,     colorKey: STAT_MAP.missing,   fn: null },
]

export default function StatsBar({ stats, auditTotalIssues, missingImageCount }) {
  if (!stats) return null

  const defs = STAT_DEFS.map(d => {
    if (d.label === '감사 이슈') return { ...d, fn: () => auditTotalIssues }
    if (d.label === '이미지 없음') return { ...d, fn: () => missingImageCount }
    return d
  })

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {defs.map(({ label, icon: Icon, colorKey, fn }) => {
        const accent = CARD_COLORS[colorKey].hex
        return (
          <div key={label} className="relative p-4 rounded-xl overflow-hidden"
            style={getCardStyle(colorKey, { topAccent: true })}>
            <Icon size={32} className="absolute right-3 top-3"
              style={{ color: accent, opacity: 0.12 }} />
            <p className="text-2xl font-bold" style={{ color: accent }}>
              {(fn(stats) ?? 0).toLocaleString()}
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{label}</p>
          </div>
        )
      })}
    </div>
  )
}
