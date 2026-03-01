import { useState, useEffect } from 'react'
import ScrollReveal from '../common/ScrollReveal'
import TiltCard from '../effects/TiltCard'

const USERNAME = 'dorae222'

// 현재 테마 감지 (다크/라이트)
function useGitHubTheme() {
  const [theme, setTheme] = useState(() => {
    const stored = document.documentElement.dataset.theme
    if (stored) return stored === 'dark' ? 'dark' : 'default'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'
  })

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const t = document.documentElement.dataset.theme
      setTheme(t === 'dark' ? 'dark' : 'default')
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (e) => {
      if (!document.documentElement.dataset.theme) {
        setTheme(e.matches ? 'dark' : 'default')
      }
    }
    mq.addEventListener('change', onChange)
    return () => {
      observer.disconnect()
      mq.removeEventListener('change', onChange)
    }
  }, [])

  return theme
}

function StatCard({ src, alt, delay = 0, glowColor = 'rgba(59,130,246,0.3)' }) {
  const [loaded, setLoaded] = useState(false)
  const [broken, setBroken] = useState(false)

  if (broken) return null

  return (
    <ScrollReveal delay={delay}>
      <TiltCard glowColor={glowColor} className="overflow-hidden">
        {!loaded && (
          <div
            className="animate-pulse w-full"
            style={{ background: 'var(--bg-secondary)', height: '170px' }}
          />
        )}
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setBroken(true)}
          className={`w-full block transition-opacity duration-500 ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
        />
      </TiltCard>
    </ScrollReveal>
  )
}

export default function GitHubStats() {
  const theme = useGitHubTheme()
  const isDark = theme === 'dark'

  // bg_color 파라미터 제거 → SVG 자체 배경(흰/다크) 사용
  const statsUrl = `https://github-readme-stats.vercel.app/api?username=${USERNAME}&show_icons=true&theme=${theme}&hide_border=true`
  const langsUrl = `https://github-readme-stats.vercel.app/api/top-langs/?username=${USERNAME}&layout=compact&theme=${theme}&hide_border=true`
  const streakUrl = `https://streak-stats.demolab.com?user=${USERNAME}&theme=${theme}&hide_border=true`
  // 라이트: github, 다크: github-dark (github-compact는 다크 고정이라 라이트에서 어색)
  const graphUrl = `https://github-readme-activity-graph.vercel.app/graph?username=${USERNAME}&theme=${isDark ? 'github-dark' : 'github'}&hide_border=true&area=true`

  return (
    <section className="py-16 px-4 section-gradient-blue">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal>
          <h2
            className="relative text-3xl font-bold text-center mb-12"
            style={{ color: 'var(--text)' }}
          >
            GitHub Stats
            <span
              className="absolute -bottom-2 left-1/2 -translate-x-1/2 h-0.5 w-16 rounded-full"
              style={{ background: 'linear-gradient(90deg, var(--primary-500), var(--primary-300))' }}
            />
          </h2>
        </ScrollReveal>

        {/* 2열 그리드: Stats + Languages */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <StatCard src={statsUrl}  alt="GitHub Stats"   delay={0.1} glowColor="rgba(99,102,241,0.35)" />
          <StatCard src={langsUrl}  alt="Top Languages"  delay={0.2} glowColor="rgba(16,185,129,0.35)" />
        </div>

        {/* Streak: 전폭 */}
        <div className="mb-6">
          <StatCard src={streakUrl} alt="GitHub Streak"  delay={0.3} glowColor="rgba(245,158,11,0.35)" />
        </div>

        {/* Activity Graph: 전폭 */}
        <StatCard src={graphUrl} alt="Contribution Graph" delay={0.4} glowColor="rgba(239,68,68,0.3)" />
      </div>
    </section>
  )
}
