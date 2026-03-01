import { useState, useEffect, useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import ScrollReveal from '../common/ScrollReveal'
import TiltCard from '../effects/TiltCard'

const USERNAME = 'dorae222'

/* ─── 언어 색상 맵 ─────────────────────────────────────── */
const LANG_COLORS = {
  Python:     '#3572A5',
  JavaScript: '#f7df1e',
  TypeScript: '#3178c6',
  HTML:       '#e34c26',
  CSS:        '#563d7c',
  Shell:      '#89e051',
  Go:         '#00ADD8',
  Rust:       '#dea584',
  Java:       '#b07219',
  Kotlin:     '#A97BFF',
  Vue:        '#41b883',
  Dockerfile: '#0db7ed',
}
const getLangColor = (name) => LANG_COLORS[name] || '#6366f1'

/* ─── 기여도 히트맵 색상 (인디고) ──────────────────────── */
const HEAT = ['#eef2ff', '#c7d2fe', '#818cf8', '#4f46e5', '#312e81']
const getHeatColor = (count, max) => {
  if (count === 0) return HEAT[0]
  return HEAT[Math.min(4, Math.ceil((count / Math.max(max, 1)) * 4))]
}

/* ─── count-up 훅 ──────────────────────────────────────── */
function useCountUp(target, inView, delayMs = 0) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!inView || !target) return
    let rafId
    let startTs = null
    const duration = 1500
    const step = (ts) => {
      if (!startTs) startTs = ts + delayMs
      const t = Math.min(Math.max(0, ts - startTs) / duration, 1)
      setCount(Math.round((1 - (1 - t) ** 3) * target))
      if (t < 1) rafId = requestAnimationFrame(step)
    }
    rafId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafId)
  }, [inView, target, delayMs])
  return count
}

/* ─── 애니메이션 통계 배지 ─────────────────────────────── */
function StatBadge({ icon, label, value, gradient, delay = 0 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  const count = useCountUp(value, inView, delay * 200)

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
      whileHover={{ y: -5, scale: 1.04 }}
      className="rounded-2xl p-5 relative overflow-hidden cursor-default select-none"
      style={{ background: gradient }}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-3xl font-extrabold leading-none" style={{ color: 'white' }}>
        {count.toLocaleString()}+
      </div>
      <div className="mt-1.5 text-sm font-medium" style={{ color: 'rgba(255,255,255,0.75)' }}>
        {label}
      </div>
      {/* 장식 원 */}
      <div className="absolute -right-8 -bottom-8 rounded-full"
        style={{ width: 80, height: 80, background: 'rgba(255,255,255,0.1)' }} />
      <div className="absolute -right-3 -top-3 rounded-full"
        style={{ width: 40, height: 40, background: 'rgba(255,255,255,0.07)' }} />
    </motion.div>
  )
}

/* ─── 기여도 히트맵 (20주 × 7일) ──────────────────────── */
const HEATMAP_WEEKS = 20

function ContribHeatmap({ data = {} }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })

  const today = new Date()
  const weeks = Array.from({ length: HEATMAP_WEEKS }, (_, wi) =>
    Array.from({ length: 7 }, (_, di) => {
      const d = new Date(today)
      d.setDate(today.getDate() - (HEATMAP_WEEKS - 1 - wi) * 7 - (6 - di))
      const key = d.toISOString().slice(0, 10)
      return { date: key, count: data[key] || 0 }
    })
  )

  const maxCount = Math.max(...weeks.flat().map(c => c.count), 1)
  const totalEvents = weeks.flat().reduce((s, c) => s + c.count, 0)

  return (
    <div ref={ref} className="p-5 select-none">
      {/* 요약 */}
      <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
        최근 {HEATMAP_WEEKS}주간 공개 이벤트 <strong style={{ color: 'var(--color-primary-500)' }}>{totalEvents}건</strong>
      </p>

      {/* 그리드 */}
      <div className="flex gap-[3px] overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((day, di) => {
              const color = getHeatColor(day.count, maxCount)
              return (
                <motion.div
                  key={di}
                  title={`${day.date}: ${day.count}건`}
                  initial={{ opacity: 0, scale: 0.3 }}
                  animate={inView ? { opacity: 1, scale: 1 } : {}}
                  transition={{
                    delay: wi * 0.02 + di * 0.004,
                    duration: 0.35,
                    type: 'spring',
                    stiffness: 400,
                    damping: 18,
                  }}
                  whileHover={{ scale: 1.9, zIndex: 10 }}
                  style={{
                    width: 11, height: 11,
                    borderRadius: 2,
                    background: color,
                    flexShrink: 0,
                    cursor: 'pointer',
                    boxShadow: day.count > 0
                      ? `1px 1px 0 rgba(0,0,0,0.08), 0 0 ${Math.min(day.count * 2, 8)}px ${color}90`
                      : '1px 1px 0 rgba(0,0,0,0.04)',
                  }}
                />
              )
            })}
          </div>
        ))}
      </div>

      {/* 범례 */}
      <div className="flex items-center gap-1 mt-3 justify-end">
        <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Less</span>
        {HEAT.map((c, i) => (
          <div key={i} style={{ width: 10, height: 10, borderRadius: 2, background: c }} />
        ))}
        <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>More</span>
      </div>
    </div>
  )
}

/* ─── 언어 분포 바 ─────────────────────────────────────── */
function LangBars({ langs, total }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-30px' })

  return (
    <div ref={ref} className="p-5">
      {/* 언어 태그 */}
      <div className="flex flex-wrap gap-2 mb-5">
        {langs.map(([name], i) => (
          <span
            key={i}
            className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full"
            style={{
              background: `${getLangColor(name)}18`,
              color: getLangColor(name),
              border: `1px solid ${getLangColor(name)}40`,
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: getLangColor(name), display: 'inline-block' }} />
            {name}
          </span>
        ))}
      </div>

      {/* 진행 막대 */}
      <div className="space-y-3">
        {langs.map(([name, count], i) => {
          const pct = ((count / total) * 100).toFixed(1)
          return (
            <div key={name}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>{name}</span>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{pct}%</span>
              </div>
              <div className="rounded-full overflow-hidden" style={{ height: 6, background: '#e0e7ff' }}>
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={inView ? { width: `${pct}%`, opacity: 1 } : {}}
                  transition={{ delay: i * 0.1 + 0.3, duration: 0.9, ease: 'easeOut' }}
                  style={{
                    height: '100%',
                    background: getLangColor(name),
                    borderRadius: 9999,
                    boxShadow: `0 0 8px ${getLangColor(name)}60`,
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ─── 외부 SVG 카드 (streak, activity graph) ───────────── */
function SvgCard({ src, alt, delay = 0, glowColor, accent = '#6366f1', skeletonH = 170 }) {
  const [loaded, setLoaded] = useState(false)
  const [broken, setBroken] = useState(false)
  if (broken) return null
  return (
    <ScrollReveal delay={delay}>
      <TiltCard glowColor={glowColor} className="overflow-hidden">
        <div style={{ height: 3, background: `linear-gradient(90deg, ${accent}, transparent)` }} />
        {!loaded && (
          <div className="animate-pulse" style={{ background: '#eef2ff', height: skeletonH }} />
        )}
        <img
          src={src} alt={alt} loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setBroken(true)}
          className={`w-full block transition-opacity duration-700 ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
        />
      </TiltCard>
    </ScrollReveal>
  )
}

/* ─── 섹션 그룹 레이블 ─────────────────────────────────── */
function GroupLabel({ icon, label, delay = 0 }) {
  return (
    <ScrollReveal delay={delay}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-base select-none">{icon}</span>
        <span className="text-xs font-bold tracking-[0.2em] uppercase"
          style={{ color: 'var(--color-primary-500)' }}>
          {label}
        </span>
        <span className="flex-1 h-px rounded-full"
          style={{ background: 'linear-gradient(90deg, var(--color-primary-300), transparent)' }} />
      </div>
    </ScrollReveal>
  )
}

/* ─── 메인 컴포넌트 ────────────────────────────────────── */
export default function GitHubStats() {
  const [user, setUser]     = useState(null)
  const [repos, setRepos]   = useState([])
  const [events, setEvents] = useState([])

  useEffect(() => {
    const h = { Accept: 'application/vnd.github+json' }
    fetch(`https://api.github.com/users/${USERNAME}`, { headers: h })
      .then(r => r.json()).then(d => d?.login && setUser(d)).catch(() => {})
    fetch(`https://api.github.com/users/${USERNAME}/repos?per_page=100&sort=pushed`, { headers: h })
      .then(r => r.json()).then(d => Array.isArray(d) && setRepos(d)).catch(() => {})
    fetch(`https://api.github.com/users/${USERNAME}/events?per_page=100`, { headers: h })
      .then(r => r.json()).then(d => Array.isArray(d) && setEvents(d)).catch(() => {})
  }, [])

  /* 파생 통계 */
  const totalStars = repos.reduce((s, r) => s + (r.stargazers_count || 0), 0)
  const totalForks = repos.reduce((s, r) => s + (r.forks_count || 0), 0)

  /* 언어 분포 */
  const langMap = {}
  repos.forEach(r => r.language && (langMap[r.language] = (langMap[r.language] || 0) + 1))
  const topLangs  = Object.entries(langMap).sort((a, b) => b[1] - a[1]).slice(0, 7)
  const langTotal = topLangs.reduce((s, [, c]) => s + c, 0)

  /* 이벤트 → 기여도 맵 */
  const contribMap = {}
  events.forEach(e => {
    const date = e.created_at?.slice(0, 10)
    if (date) contribMap[date] = (contribMap[date] || 0) + 1
  })

  const streakUrl = `https://streak-stats.demolab.com?user=${USERNAME}&theme=default&hide_border=true`
  const graphUrl  = `https://github-readme-activity-graph.vercel.app/graph?username=${USERNAME}&theme=github&hide_border=true&area=true&color=3b82f6&line=6366f1&point=8b5cf6`

  return (
    <section className="py-20 px-4 section-gradient-blue">
      <div className="max-w-5xl mx-auto">

        {/* 헤딩 */}
        <ScrollReveal>
          <div className="text-center mb-14">
            <p className="text-[10px] font-extrabold tracking-[0.4em] uppercase mb-3"
              style={{ color: 'var(--color-primary-400)' }}>
              Open Source
            </p>
            <h2 className="relative inline-block text-4xl font-extrabold tracking-tight"
              style={{ color: 'var(--text)' }}>
              GitHub Activity
              <span className="absolute -bottom-2 left-0 right-0 h-[3px] rounded-full"
                style={{ background: 'linear-gradient(90deg, var(--color-primary-500), #8b5cf6, transparent)' }} />
            </h2>
            <p className="mt-5 text-sm" style={{ color: 'var(--text-secondary)' }}>
              실시간 GitHub 활동 대시보드
            </p>
          </div>
        </ScrollReveal>

        {/* 통계 배지 (4개) */}
        <div className="mb-10">
          <GroupLabel icon="📊" label="Overview" delay={0.05} />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatBadge icon="📦" label="Repositories" value={user?.public_repos ?? 0}
              gradient="linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)" delay={0.1} />
            <StatBadge icon="⭐" label="Total Stars" value={totalStars}
              gradient="linear-gradient(135deg,#f59e0b 0%,#f97316 100%)" delay={0.2} />
            <StatBadge icon="👥" label="Followers" value={user?.followers ?? 0}
              gradient="linear-gradient(135deg,#10b981 0%,#06b6d4 100%)" delay={0.3} />
            <StatBadge icon="🍴" label="Forks" value={totalForks}
              gradient="linear-gradient(135deg,#ef4444 0%,#ec4899 100%)" delay={0.4} />
          </div>
        </div>

        {/* 기여도 히트맵 */}
        <div className="mb-8">
          <GroupLabel icon="🌱" label="Contribution Activity" delay={0.2} />
          <ScrollReveal delay={0.25}>
            <TiltCard glowColor="rgba(99,102,241,0.3)" className="overflow-hidden">
              <div style={{ height: 3, background: 'linear-gradient(90deg,#6366f1,transparent)' }} />
              <ContribHeatmap data={contribMap} />
            </TiltCard>
          </ScrollReveal>
        </div>

        {/* 언어 분포 */}
        {topLangs.length > 0 && (
          <div className="mb-8">
            <GroupLabel icon="💻" label="Language Distribution" delay={0.3} />
            <ScrollReveal delay={0.35}>
              <TiltCard glowColor="rgba(16,185,129,0.3)" className="overflow-hidden">
                <div style={{ height: 3, background: 'linear-gradient(90deg,#10b981,transparent)' }} />
                <LangBars langs={topLangs} total={langTotal} />
              </TiltCard>
            </ScrollReveal>
          </div>
        )}

        {/* Streak SVG */}
        <div className="mb-8">
          <GroupLabel icon="🔥" label="Streak" delay={0.4} />
          <SvgCard src={streakUrl} alt="GitHub Streak" delay={0.45}
            glowColor="rgba(239,68,68,0.35)" accent="#ef4444" />
        </div>

        {/* Activity Graph SVG */}
        <div>
          <GroupLabel icon="📈" label="Contribution Graph" delay={0.5} />
          <SvgCard src={graphUrl} alt="Contribution Graph" delay={0.55}
            glowColor="rgba(59,130,246,0.35)" accent="#3b82f6" skeletonH={200} />
        </div>

      </div>
    </section>
  )
}
