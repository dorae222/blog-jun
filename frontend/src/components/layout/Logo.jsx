// HJ Tech 로고 — 그라디언트 모노그램 뱃지 + 워드마크 (favicon과 동일 언어)
export default function Logo({ badgeSize = 32, showWordmark = true }) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg width={badgeSize} height={badgeSize} viewBox="0 0 40 40" aria-label="HJ Tech" role="img">
        <defs>
          <linearGradient id="hjLogoGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4F8DF9" />
            <stop offset="0.55" stopColor="#6D5AE6" />
            <stop offset="1" stopColor="#8B3DF0" />
          </linearGradient>
        </defs>
        <rect x="1.5" y="1.5" width="37" height="37" rx="11" fill="url(#hjLogoGrad)" />
        <rect x="1.5" y="1.5" width="37" height="18.5" rx="11" fill="#ffffff" opacity="0.1" />
        <text
          x="20" y="21.5" textAnchor="middle" dominantBaseline="central"
          fill="#ffffff" fontSize="16.5" fontWeight="800" letterSpacing="-0.5"
          fontFamily="Inter, system-ui, sans-serif"
        >HJ</text>
      </svg>
      {showWordmark && (
        <span className="text-xl font-bold tracking-tight" style={{ color: 'var(--text)' }}>
          HJ<span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}> Tech</span>
        </span>
      )}
    </span>
  )
}
