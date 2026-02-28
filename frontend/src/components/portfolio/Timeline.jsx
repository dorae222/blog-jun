import ScrollReveal from '../common/ScrollReveal'

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

          {items.map((item, i) => (
            <ScrollReveal
              key={item.id}
              variant={i % 2 === 0 ? 'slide-in-left' : 'slide-in-right'}
              delay={i * 0.1}
            >
              <div className={`relative flex items-start mb-8 ${i % 2 === 0 ? 'md:flex-row-reverse' : ''}`}>
                <div className="absolute left-4 md:left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-primary-600 border-4 z-10" style={{ borderColor: 'var(--bg)' }} />
                <div
                  className={`ml-10 md:ml-0 md:w-5/12 p-4 rounded-xl border ${i % 2 === 0 ? 'md:mr-auto md:mr-8' : 'md:ml-auto md:ml-8'}`}
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <p className="text-xs font-medium text-primary-600 mb-1">
                    {new Date(item.published_at || item.created_at).toLocaleDateString('ko-KR')}
                  </p>
                  <h3 className="font-semibold mb-1" style={{ color: 'var(--text)' }}>{item.title}</h3>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{item.summary}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}
