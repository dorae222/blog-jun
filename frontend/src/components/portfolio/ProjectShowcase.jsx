import ScrollReveal from '../common/ScrollReveal'
import TiltCard from '../effects/TiltCard'
import { getCategoryIcon } from '../../utils/categoryIcons'
import { Link } from 'react-router-dom'

const ACCENT_COLORS = [
  { bg: '#2563eb15', ring: '#2563eb40' },
  { bg: '#8b5cf615', ring: '#8b5cf640' },
  { bg: '#05966915', ring: '#05966940' },
  { bg: '#FF990015', ring: '#FF990040' },
]

export default function ProjectShowcase({ projects = [] }) {
  return (
    <section className="py-16 px-4" style={{ background: 'var(--bg-secondary)' }}>
      <div className="max-w-6xl mx-auto">
        <ScrollReveal>
          <h2 className="text-3xl font-bold text-center mb-12" style={{ color: 'var(--text)' }}>
            Projects
          </h2>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-6">
          {projects.map((project, i) => {
            const accent = ACCENT_COLORS[i % ACCENT_COLORS.length]
            return (
              <ScrollReveal key={project.id} delay={i * 0.1} variant="scale-up">
                <TiltCard glowColor="rgba(139,92,246,0.2)">
                  <Link to={`/post/${project.slug}`} className="block p-6">
                    <div className="flex items-start gap-4">
                      {/* Circular avatar icon */}
                      <div
                        className="w-14 h-14 rounded-full flex items-center justify-center shrink-0 shadow-sm"
                        style={{
                          background: accent.bg,
                          border: `2px solid ${accent.ring}`,
                        }}
                      >
                        {getCategoryIcon(project.category?.slug, 24) || (
                          <span className="text-lg font-bold" style={{ color: accent.ring }}>
                            {project.title?.charAt(0) || 'P'}
                          </span>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold mb-1 line-clamp-1" style={{ color: 'var(--text)' }}>
                          {project.title}
                        </h3>
                        <p className="text-sm mb-3 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
                          {project.summary}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {project.tags?.slice(0, 4).map((tag) => (
                            <span
                              key={tag.id}
                              className="text-xs px-2 py-0.5 rounded-full"
                              style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                            >
                              #{tag.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Link>
                </TiltCard>
              </ScrollReveal>
            )
          })}
        </div>
      </div>
    </section>
  )
}
