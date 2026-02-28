import ScrollReveal from '../common/ScrollReveal'

const STACKS = [
  { category: 'Cloud', items: ['AWS', 'Docker', 'Kubernetes', 'Terraform'], color: '#FF9900' },
  { category: 'AI/ML', items: ['PyTorch', 'TensorFlow', 'LangChain', 'OpenAI'], color: '#FF6F00' },
  { category: 'Backend', items: ['Python', 'Django', 'FastAPI', 'Node.js'], color: '#3776AB' },
  { category: 'Data', items: ['PostgreSQL', 'Redis', 'Spark', 'Airflow'], color: '#336791' },
  { category: 'Frontend', items: ['React', 'TypeScript', 'Tailwind CSS'], color: '#61DAFB' },
  { category: 'DevOps', items: ['GitHub Actions', 'Linux', 'Nginx', 'Grafana'], color: '#2088FF' },
]

export default function TechStack() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal>
          <h2 className="text-3xl font-bold text-center mb-12" style={{ color: 'var(--text)' }}>
            Tech Stack
          </h2>
        </ScrollReveal>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {STACKS.map((stack, i) => (
            <ScrollReveal key={stack.category} delay={i * 0.1}>
              <div
                className="p-5 rounded-xl border transition-all hover:shadow-lg hover:-translate-y-1"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
              >
                <h3
                  className="text-sm font-bold mb-3 uppercase tracking-wider"
                  style={{ color: stack.color }}
                >
                  {stack.category}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {stack.items.map((item) => (
                    <span
                      key={item}
                      className="text-xs px-2.5 py-1 rounded-full"
                      style={{ background: stack.color + '15', color: stack.color }}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}
