import { useState, useEffect } from 'react'
import ScrollReveal from '../common/ScrollReveal'

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

function StatImage({ src, alt, className = '' }) {
  const [broken, setBroken] = useState(false)
  if (broken) return null
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setBroken(true)}
      className={`w-full rounded-xl ${className}`}
    />
  )
}

export default function GitHubStats() {
  const theme = useGitHubTheme()

  const statsUrl = `https://github-readme-stats.vercel.app/api?username=${USERNAME}&show_icons=true&theme=${theme}&hide_border=true&bg_color=00000000`
  const langsUrl = `https://github-readme-stats.vercel.app/api/top-langs/?username=${USERNAME}&layout=compact&theme=${theme}&hide_border=true&bg_color=00000000`
  const streakUrl = `https://streak-stats.demolab.com?user=${USERNAME}&theme=${theme}&hide_border=true`
  const graphUrl = `https://github-readme-activity-graph.vercel.app/graph?username=${USERNAME}&theme=${theme === 'dark' ? 'github-compact' : 'github'}&hide_border=true&area=true`

  return (
    <section className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal>
          <h2 className="text-3xl font-bold text-center mb-12" style={{ color: 'var(--text)' }}>
            GitHub Stats
          </h2>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <ScrollReveal delay={0.1}>
            <div className="p-4 rounded-xl glass flex items-center justify-center min-h-[160px]">
              <StatImage src={statsUrl} alt="GitHub Stats" />
            </div>
          </ScrollReveal>
          <ScrollReveal delay={0.2}>
            <div className="p-4 rounded-xl glass flex items-center justify-center min-h-[160px]">
              <StatImage src={langsUrl} alt="Top Languages" />
            </div>
          </ScrollReveal>
        </div>

        <ScrollReveal delay={0.3}>
          <div className="p-4 rounded-xl glass mb-6 flex items-center justify-center min-h-[160px]">
            <StatImage src={streakUrl} alt="GitHub Streak" />
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.4}>
          <div className="p-4 rounded-xl glass flex items-center justify-center min-h-[160px] overflow-x-auto">
            <StatImage src={graphUrl} alt="Contribution Graph" className="min-w-[600px]" />
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}
