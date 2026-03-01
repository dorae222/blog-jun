import { ExternalLink } from 'lucide-react'
import ScrollReveal from '../common/ScrollReveal'

// type별 색상·아이콘 설정
const TYPE_STYLES = {
  project:   { color: '#3B82F6', label: 'Project' },
  education: { color: '#10B981', label: 'Education' },
  award:     { color: '#F59E0B', label: 'Award' },
  activity:  { color: '#8B5CF6', label: 'Activity' },
}

export default function Timeline({ items = [] }) {
  return (
    <section className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <ScrollReveal>
          <h2 className="text-3xl font-bold text-center mb-12" style={{ color: 'var(--text)' }}>
            Activities
          </h2>
        </ScrollReveal>

        <div className="relative">
          <div
            className="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5"
            style={{ background: 'var(--border)' }}
          />

          {items.map((item, i) => {
            const typeStyle = TYPE_STYLES[item.type] || TYPE_STYLES.activity
            const dateStr = item.date || (item.published_at
              ? new Date(item.published_at).toLocaleDateString('ko-KR')
              : new Date(item.created_at).toLocaleDateString('ko-KR'))
            const descText = item.description || item.summary

            const card = (
              <div
                className={`ml-10 md:ml-0 md:w-5/12 p-4 rounded-xl border ${i % 2 === 0 ? 'md:mr-auto md:mr-8' : 'md:ml-auto md:ml-8'}`}
                style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
              >
                {/* 날짜 + type 뱃지 */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium" style={{ color: typeStyle.color }}>
                    {dateStr}
                  </span>
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full font-medium"
                    style={{ background: typeStyle.color + '20', color: typeStyle.color }}
                  >
                    {typeStyle.label}
                  </span>
                </div>

                {/* 제목 */}
                {item.link ? (
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold hover:underline mb-1"
                    style={{ color: 'var(--text)' }}
                  >
                    {item.title}
                    <ExternalLink size={12} style={{ color: 'var(--text-secondary)' }} />
                  </a>
                ) : (
                  <h3 className="font-semibold mb-1" style={{ color: 'var(--text)' }}>{item.title}</h3>
                )}

                {/* 설명 */}
                {descText && (
                  <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{descText}</p>
                )}

                {/* 태그 뱃지 */}
                {item.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {item.tags.map(tag => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )

            return (
              <ScrollReveal
                key={item.id}
                variant={i % 2 === 0 ? 'slide-in-left' : 'slide-in-right'}
                delay={i * 0.1}
              >
                <div className={`relative flex items-start mb-8 ${i % 2 === 0 ? 'md:flex-row-reverse' : ''}`}>
                  {/* 타임라인 점 — type 색상 */}
                  <div
                    className="absolute left-4 md:left-1/2 -translate-x-1/2 w-3 h-3 rounded-full border-4 z-10"
                    style={{ background: typeStyle.color, borderColor: 'var(--bg)' }}
                  />
                  {card}
                </div>
              </ScrollReveal>
            )
          })}
        </div>
      </div>
    </section>
  )
}
