import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3, Activity, Code2, Trophy,
  BookOpen, ExternalLink, Star, GitFork,
  Target, Calendar, Zap, Package, Users,
} from 'lucide-react'
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

/* ─── 기여도 히트맵 색상 ────────────────────────────────── */
const HEAT = ['#eef2ff', '#c7d2fe', '#818cf8', '#4f46e5', '#312e81']
const getHeatColor = (count, max) => {
  if (count === 0) return HEAT[0]
  return HEAT[Math.min(4, Math.ceil((count / Math.max(max, 1)) * 4))]
}

/* ─── count-up 훅 ─────────────────────────────────────── */
function useCountUp(target, delayMs = 0) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!target) return
    let rafId
    let startTs = null
    const duration = 1400
    const timer = setTimeout(() => {
      const step = (ts) => {
        if (!startTs) startTs = ts
        const t = Math.min((ts - startTs) / duration, 1)
        setCount(Math.round((1 - (1 - t) ** 3) * target))
        if (t < 1) rafId = requestAnimationFrame(step)
      }
      rafId = requestAnimationFrame(step)
    }, delayMs)
    return () => { clearTimeout(timer); cancelAnimationFrame(rafId) }
  }, [target, delayMs])
  return count
}

/* ─── 통계 배지 ─────────────────────────────────────────── */
function StatBadge({ icon: Icon, label, value, gradient, delay = 0 }) {
  const count = useCountUp(value, delay * 150)
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
      whileHover={{ y: -5, scale: 1.04 }}
      className="rounded-2xl p-5 relative overflow-hidden cursor-default select-none"
      style={{ background: gradient }}
    >
      <Icon size={24} className="mb-2" style={{ color: 'rgba(255,255,255,0.9)' }} />
      <div className="text-3xl font-extrabold leading-none" style={{ color: 'white' }}>
        {count.toLocaleString()}+
      </div>
      <div className="mt-1.5 text-sm font-medium" style={{ color: 'rgba(255,255,255,0.75)' }}>
        {label}
      </div>
      <div className="absolute -right-8 -bottom-8 rounded-full"
        style={{ width: 80, height: 80, background: 'rgba(255,255,255,0.1)' }} />
      <div className="absolute -right-3 -top-3 rounded-full"
        style={{ width: 40, height: 40, background: 'rgba(255,255,255,0.07)' }} />
    </motion.div>
  )
}

/* ─── 이벤트 유형 한국어 맵 ─────────────────────────────── */
const TYPE_KO = {
  PushEvent:          '푸시',
  PullRequestEvent:   'PR',
  IssuesEvent:        '이슈',
  WatchEvent:         '스타',
  ForkEvent:          '포크',
  CreateEvent:        '생성',
  DeleteEvent:        '삭제',
  IssueCommentEvent:  '댓글',
  CommitCommentEvent: '댓글',
  ReleaseEvent:       '릴리즈',
}

/* ─── 기여도 히트맵 (20주 × 7일) ──────────────────────── */
const HEATMAP_WEEKS = 20

function ContribHeatmap({ data = {}, events = [] }) {
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
  const activeDays = weeks.flat().filter(c => c.count > 0).length

  const typeCount = {}
  events.forEach(e => { if (e.type) typeCount[e.type] = (typeCount[e.type] || 0) + 1 })
  const topType = Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0]?.[0] || ''
  const avgPerDay = activeDays > 0 ? (totalEvents / activeDays).toFixed(1) : 0

  const highlights = [
    { Icon: Target,   value: TYPE_KO[topType] || '-', label: '주요 활동' },
    { Icon: Calendar, value: `${activeDays}일`,        label: '활동 일수' },
    { Icon: Zap,      value: `${avgPerDay}건`,         label: '일평균 이벤트' },
  ]

  return (
    <div className="p-5 select-none">
      <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>
        최근 공개 이벤트{' '}
        <strong style={{ color: 'var(--color-primary-500)' }}>{totalEvents}건</strong>
      </p>

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
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true, margin: '-20px' }}
                  transition={{
                    delay: wi * 0.015 + di * 0.003,
                    duration: 0.3,
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

      {/* ActivityHighlights */}
      <div className="grid grid-cols-3 gap-0 mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
        {highlights.map(({ Icon, value, label }, i) => (
          <div key={label}
            className={`text-center px-2 py-2 ${i < 2 ? 'border-r' : ''}`}
            style={i < 2 ? { borderColor: 'var(--border)' } : {}}>
            <Icon size={14} style={{ color: 'var(--color-primary-400)', margin: '0 auto 4px' }} />
            <div className="text-xs font-bold" style={{ color: 'var(--text)' }}>{value}</div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── 언어 분포 바 ─────────────────────────────────────── */
function LangBars({ langs, total }) {
  return (
    <div className="p-5">
      {/* 태그 */}
      <div className="flex flex-wrap gap-2 mb-5">
        {langs.map(([name], i) => (
          <span key={i}
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
                  whileInView={{ width: `${pct}%`, opacity: 1 }}
                  viewport={{ once: true, margin: '-20px' }}
                  transition={{ delay: i * 0.1 + 0.2, duration: 0.9, ease: 'easeOut' }}
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

/* ─── 섹션 그룹 레이블 ─────────────────────────────────── */
function GroupLabel({ icon: Icon, label, delay = 0 }) {
  return (
    <ScrollReveal delay={delay}>
      <div className="flex items-center gap-3 mb-3">
        <Icon size={15} style={{ color: 'var(--color-primary-500)', flexShrink: 0 }} />
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

/* ─── RepoCard ──────────────────────────────────────────── */
function RepoCard({ repo, delay = 0 }) {
  const langColor = getLangColor(repo.language)
  const updatedDaysAgo = repo.pushed_at
    ? Math.floor((Date.now() - new Date(repo.pushed_at)) / 86400000)
    : null
  const updatedLabel = updatedDaysAgo === null ? ''
    : updatedDaysAgo === 0 ? 'Updated today'
    : updatedDaysAgo === 1 ? 'Updated yesterday'
    : `Updated ${updatedDaysAgo}d ago`

  return (
    <ScrollReveal delay={delay}>
      <motion.a
        href={repo.html_url}
        target="_blank"
        rel="noopener noreferrer"
        whileHover={{ y: -4 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        className="block rounded-2xl overflow-hidden glass"
        style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
      >
        <div style={{ height: 3, background: repo.language ? langColor : '#6366f1' }} />
        <div className="p-5">
          <div className="flex items-start justify-between gap-2 mb-3">
            <div className="flex items-center gap-2 min-w-0">
              <BookOpen size={14} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
              <span className="font-semibold text-sm truncate" style={{ color: 'var(--text)' }}>
                {repo.name}
              </span>
            </div>
            <ExternalLink size={13} style={{ color: 'var(--text-secondary)', flexShrink: 0, marginTop: 2 }} />
          </div>
          <p className="text-xs leading-relaxed line-clamp-2 mb-4"
            style={{ color: 'var(--text-secondary)', minHeight: '2.5rem' }}>
            {repo.description || 'No description provided.'}
          </p>
          <div style={{ height: 1, background: 'var(--border)', marginBottom: 12 }} />
          <div className="flex items-center gap-3 text-xs flex-wrap"
            style={{ color: 'var(--text-secondary)' }}>
            {repo.language && (
              <span className="flex items-center gap-1.5">
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: langColor, flexShrink: 0 }} />
                <span className="font-medium">{repo.language}</span>
              </span>
            )}
            <span className="flex items-center gap-1"><Star size={11} /> {repo.stargazers_count}</span>
            <span className="flex items-center gap-1"><GitFork size={11} /> {repo.forks_count}</span>
            {updatedLabel && <span className="ml-auto">{updatedLabel}</span>}
          </div>
        </div>
      </motion.a>
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

  const totalStars = repos.reduce((s, r) => s + (r.stargazers_count || 0), 0)
  const totalForks = repos.reduce((s, r) => s + (r.forks_count || 0), 0)

  const langMap = {}
  repos.forEach(r => r.language && (langMap[r.language] = (langMap[r.language] || 0) + 1))
  const topLangs  = Object.entries(langMap).sort((a, b) => b[1] - a[1]).slice(0, 7)
  const langTotal = topLangs.reduce((s, [, c]) => s + c, 0)

  const contribMap = {}
  events.forEach(e => {
    const date = e.created_at?.slice(0, 10)
    if (date) contribMap[date] = (contribMap[date] || 0) + 1
  })

  const topRepos = useMemo(() =>
    [...repos].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 4),
  [repos])

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

        {/* 통계 배지 */}
        <div className="mb-10">
          <GroupLabel icon={BarChart3} label="Overview" delay={0.05} />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatBadge icon={Package} label="Repositories" value={user?.public_repos ?? 0}
              gradient="linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)" delay={0.1} />
            <StatBadge icon={Star} label="Total Stars" value={totalStars}
              gradient="linear-gradient(135deg,#f59e0b 0%,#f97316 100%)" delay={0.2} />
            <StatBadge icon={Users} label="Followers" value={user?.followers ?? 0}
              gradient="linear-gradient(135deg,#10b981 0%,#06b6d4 100%)" delay={0.3} />
            <StatBadge icon={GitFork} label="Forks" value={totalForks}
              gradient="linear-gradient(135deg,#ef4444 0%,#ec4899 100%)" delay={0.4} />
          </div>
        </div>

        {/* 기여도 히트맵 */}
        <div className="mb-8">
          <GroupLabel icon={Activity} label="Contribution Activity" delay={0.2} />
          <ScrollReveal delay={0.25}>
            <TiltCard glowColor="rgba(99,102,241,0.3)" className="overflow-hidden">
              <div style={{ height: 3, background: 'linear-gradient(90deg,#6366f1,transparent)' }} />
              <ContribHeatmap data={contribMap} events={events} />
            </TiltCard>
          </ScrollReveal>
        </div>

        {/* 언어 분포 */}
        {topLangs.length > 0 && (
          <div className="mb-8">
            <GroupLabel icon={Code2} label="Language Distribution" delay={0.3} />
            <ScrollReveal delay={0.35}>
              <TiltCard glowColor="rgba(16,185,129,0.3)" className="overflow-hidden">
                <div style={{ height: 3, background: 'linear-gradient(90deg,#10b981,transparent)' }} />
                <LangBars langs={topLangs} total={langTotal} />
              </TiltCard>
            </ScrollReveal>
          </div>
        )}

        {/* Top Repositories */}
        <div className="mb-8">
          <GroupLabel icon={Trophy} label="Top Repositories" delay={0.4} />
          {topRepos.length > 0
            ? <div className="grid md:grid-cols-2 gap-4">
                {topRepos.map((repo, i) => <RepoCard key={repo.id} repo={repo} delay={0.45 + i * 0.07} />)}
              </div>
            : <div className="grid md:grid-cols-2 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="rounded-2xl overflow-hidden animate-pulse"
                    style={{ background: 'var(--bg-secondary)', height: 160 }} />
                ))}
              </div>
          }
        </div>

      </div>
    </section>
  )
}
