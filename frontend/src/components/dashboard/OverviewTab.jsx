import { ImageOff } from 'lucide-react'
import CARD_COLORS, { COVERAGE_MAP, getCardStyle } from '../../data/cardColors'

export default function OverviewTab({ stats, onShowMissingImages }) {
  if (!stats?.image_coverage) return null

  const { image_coverage, image_coverage_by_category = [] } = stats
  const coveragePct = image_coverage.total_published > 0
    ? Math.round((image_coverage.with_any_image / image_coverage.total_published) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* 이미지 커버리지 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
          <p className="text-xs uppercase tracking-wide mb-1" style={{ color: 'var(--text-secondary)' }}>총 발행</p>
          <p className="text-3xl font-bold" style={{ color: 'var(--text)' }}>
            {image_coverage.total_published}
          </p>
        </div>
        <div className="p-5 rounded-xl" style={getCardStyle(COVERAGE_MAP.with_image, { topAccent: true })}>
          <p className="text-xs uppercase tracking-wide mb-1" style={{ color: 'var(--text-secondary)' }}>이미지 있음</p>
          <p className="text-3xl font-bold" style={{ color: CARD_COLORS[COVERAGE_MAP.with_image].hex }}>
            {image_coverage.with_any_image}
          </p>
        </div>
        <div className="p-5 rounded-xl" style={getCardStyle(COVERAGE_MAP.missing_image, { topAccent: true })}>
          <p className="text-xs uppercase tracking-wide mb-1" style={{ color: 'var(--text-secondary)' }}>이미지 없음</p>
          <p className="text-3xl font-bold" style={{ color: CARD_COLORS[COVERAGE_MAP.missing_image].hex }}>
            {image_coverage.missing_image}
          </p>
        </div>
        <div className="p-5 rounded-xl" style={getCardStyle(COVERAGE_MAP.coverage, { topAccent: true })}>
          <p className="text-xs uppercase tracking-wide mb-1" style={{ color: 'var(--text-secondary)' }}>커버리지</p>
          <p className="text-3xl font-bold" style={{ color: CARD_COLORS[COVERAGE_MAP.coverage].hex }}>
            {coveragePct}%
          </p>
        </div>
      </div>

      {/* 프로그레스 바 */}
      <div className="p-4 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>전체 이미지 커버리지</span>
          <span className="text-sm font-bold" style={{ color: '#3b82f6' }}>
            {image_coverage.with_any_image} / {image_coverage.total_published}
          </span>
        </div>
        <div className="w-full h-3 rounded-full overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
          <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all"
            style={{ width: `${image_coverage.total_published > 0
              ? (image_coverage.with_any_image / image_coverage.total_published) * 100
              : 0}%` }} />
        </div>
        <div className="flex flex-wrap gap-3 sm:gap-4 mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500" /> 커버 이미지: {image_coverage.with_cover_image}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Arch figure 포함: {image_coverage.with_any_image}
          </span>
        </div>
      </div>

      {/* 빠른 액션 */}
      <button
        onClick={onShowMissingImages}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-orange-50 transition-colors"
        style={{ borderColor: '#f97316', color: '#f97316' }}>
        <ImageOff size={16} /> 이미지 없는 포스트 보기 &rarr;
      </button>

      {/* 카테고리별 이미지 커버리지 */}
      <div className="sm:hidden space-y-2">
        {image_coverage_by_category.map(cat => {
          const missing = cat.total - cat.with_cover
          const pct = cat.total > 0 ? Math.round((cat.with_cover / cat.total) * 100) : 0
          return (
            <div key={cat.category__slug || 'none'} className="rounded-xl border p-3"
              style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold truncate" style={{ color: 'var(--text)' }}>
                    {cat.category__name || '(없음)'}
                  </p>
                  <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                    총 {cat.total} · 커버 있음 {cat.with_cover} · 없음 {missing}
                  </p>
                </div>
                <span className="shrink-0 text-sm font-bold" style={{ color: pct >= 50 ? '#10b981' : '#f97316' }}>
                  {pct}%
                </span>
              </div>
              <div className="mt-3 h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
                <div className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, background: pct >= 50 ? '#10b981' : '#f97316' }} />
              </div>
            </div>
          )
        })}
      </div>
      <div className="hidden sm:block rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>카테고리</th>
              <th className="px-4 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>총 포스트</th>
              <th className="px-4 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>커버 있음</th>
              <th className="px-4 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>없음</th>
              <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>커버리지</th>
            </tr>
          </thead>
          <tbody>
            {image_coverage_by_category.map(cat => {
              const missing = cat.total - cat.with_cover
              const pct = cat.total > 0 ? Math.round((cat.with_cover / cat.total) * 100) : 0
              return (
                <tr key={cat.category__slug || 'none'} className="border-t" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-4 py-2 font-medium" style={{ color: 'var(--text)' }}>
                    {cat.category__name || '(없음)'}
                  </td>
                  <td className="px-4 py-2 text-right" style={{ color: 'var(--text)' }}>{cat.total}</td>
                  <td className="px-4 py-2 text-right" style={{ color: '#10b981' }}>{cat.with_cover}</td>
                  <td className="px-4 py-2 text-right" style={{ color: missing > 0 ? '#f97316' : 'var(--text-secondary)' }}>
                    {missing}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-secondary)' }}>
                        <div className="h-full rounded-full transition-all"
                          style={{ width: `${pct}%`, background: pct >= 50 ? '#10b981' : '#f97316' }} />
                      </div>
                      <span className="text-xs font-medium" style={{ color: pct >= 50 ? '#10b981' : '#f97316' }}>
                        {pct}%
                      </span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
