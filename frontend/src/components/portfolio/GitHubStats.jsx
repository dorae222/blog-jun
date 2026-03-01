import { useState } from 'react'
import ScrollReveal from '../common/ScrollReveal'
import TiltCard from '../effects/TiltCard'

const USERNAME = 'dorae222'

// 라이트 모드 고정 (사용자 결정)
const T = 'default'
const GRAPH_T = 'github'

// 각 카드별 상단 accent 색상
const ACCENT = {
  stats:   '#6366f1',
  langs:   '#10b981',
  contrib: '#8b5cf6',
  trophy:  '#f59e0b',
  streak:  '#ef4444',
  graph:   '#3b82f6',
}

function StatCard({
  src,
  alt,
  delay = 0,
  glowColor = 'rgba(99,102,241,0.3)',
  accent = '#6366f1',
  skeletonH = 170,
}) {
  const [loaded, setLoaded] = useState(false)
  const [broken, setBroken] = useState(false)

  if (broken) return null

  return (
    <ScrollReveal delay={delay}>
      <TiltCard glowColor={glowColor} className="overflow-hidden">
        {/* 컬러 accent 라인 */}
        <div
          style={{
            height: '3px',
            background: `linear-gradient(90deg, ${accent}, transparent)`,
          }}
        />
        {/* 로딩 스켈레톤 */}
        {!loaded && (
          <div
            className="animate-pulse w-full"
            style={{ background: '#eef2ff', height: `${skeletonH}px` }}
          />
        )}
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setBroken(true)}
          className={`w-full block transition-opacity duration-700 ${
            loaded ? 'opacity-100' : 'opacity-0 h-0'
          }`}
        />
      </TiltCard>
    </ScrollReveal>
  )
}

// 섹션 그룹 레이블
function GroupLabel({ icon, label, delay = 0 }) {
  return (
    <ScrollReveal delay={delay}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-base select-none">{icon}</span>
        <span
          className="text-xs font-bold tracking-[0.2em] uppercase"
          style={{ color: 'var(--color-primary-500)' }}
        >
          {label}
        </span>
        <span
          className="flex-1 h-px rounded-full"
          style={{
            background:
              'linear-gradient(90deg, var(--color-primary-300), transparent)',
          }}
        />
      </div>
    </ScrollReveal>
  )
}

export default function GitHubStats() {
  const statsUrl    = `https://github-readme-stats.vercel.app/api?username=${USERNAME}&show_icons=true&theme=${T}&hide_border=true&count_private=true&include_all_commits=true`
  const langsUrl    = `https://github-readme-stats.vercel.app/api/top-langs/?username=${USERNAME}&layout=compact&theme=${T}&hide_border=true&langs_count=8`
  const streakUrl   = `https://streak-stats.demolab.com?user=${USERNAME}&theme=${T}&hide_border=true&date_format=j%20M%5B%20Y%5D`
  const graphUrl    = `https://github-readme-activity-graph.vercel.app/graph?username=${USERNAME}&theme=${GRAPH_T}&hide_border=true&area=true&color=3b82f6&line=6366f1&point=8b5cf6`
  const trophyUrl   = `https://github-profile-trophy.vercel.app/?username=${USERNAME}&theme=flat&no-frame=true&no-bg=true&margin-w=6&row=1&column=6`
  const contrib3dUrl = `https://github-profile-3d-contrib.vercel.app/api/artful/${USERNAME}.svg`

  return (
    <section className="py-20 px-4 section-gradient-blue">
      <div className="max-w-5xl mx-auto">

        {/* ── 헤딩 ── */}
        <ScrollReveal>
          <div className="text-center mb-14">
            <p
              className="text-[10px] font-extrabold tracking-[0.4em] uppercase mb-3"
              style={{ color: 'var(--color-primary-400)' }}
            >
              Open Source
            </p>
            <h2
              className="relative inline-block text-4xl font-extrabold tracking-tight"
              style={{ color: 'var(--text)' }}
            >
              GitHub Activity
              <span
                className="absolute -bottom-2 left-0 right-0 h-[3px] rounded-full"
                style={{
                  background:
                    'linear-gradient(90deg, var(--color-primary-500), #8b5cf6, transparent)',
                }}
              />
            </h2>
            <p
              className="mt-5 text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              실시간 GitHub 활동 대시보드
            </p>
          </div>
        </ScrollReveal>

        {/* ── Row 1: Stats + Languages ── */}
        <div className="mb-8">
          <GroupLabel icon="📊" label="Overview" delay={0.05} />
          <div className="grid md:grid-cols-2 gap-5">
            <StatCard
              src={statsUrl}
              alt="GitHub Stats"
              delay={0.1}
              glowColor="rgba(99,102,241,0.35)"
              accent={ACCENT.stats}
            />
            <StatCard
              src={langsUrl}
              alt="Top Languages"
              delay={0.18}
              glowColor="rgba(16,185,129,0.35)"
              accent={ACCENT.langs}
            />
          </div>
        </div>

        {/* ── Row 2: 3D Contribution (히어로) ── */}
        <div className="mb-8">
          <GroupLabel icon="🌱" label="3D Contribution Graph" delay={0.22} />
          <StatCard
            src={contrib3dUrl}
            alt="3D Contribution Graph"
            delay={0.27}
            glowColor="rgba(139,92,246,0.35)"
            accent={ACCENT.contrib}
            skeletonH={320}
          />
        </div>

        {/* ── Row 3: Trophies ── */}
        <div className="mb-8">
          <GroupLabel icon="🏆" label="Achievements" delay={0.32} />
          <StatCard
            src={trophyUrl}
            alt="GitHub Trophies"
            delay={0.37}
            glowColor="rgba(245,158,11,0.35)"
            accent={ACCENT.trophy}
            skeletonH={120}
          />
        </div>

        {/* ── Row 4: Streak ── */}
        <div className="mb-8">
          <GroupLabel icon="🔥" label="Streak" delay={0.42} />
          <StatCard
            src={streakUrl}
            alt="GitHub Streak"
            delay={0.47}
            glowColor="rgba(239,68,68,0.35)"
            accent={ACCENT.streak}
          />
        </div>

        {/* ── Row 5: Activity Graph ── */}
        <div>
          <GroupLabel icon="📈" label="Contribution Graph" delay={0.52} />
          <StatCard
            src={graphUrl}
            alt="Contribution Graph"
            delay={0.57}
            glowColor="rgba(59,130,246,0.35)"
            accent={ACCENT.graph}
            skeletonH={200}
          />
        </div>

      </div>
    </section>
  )
}
