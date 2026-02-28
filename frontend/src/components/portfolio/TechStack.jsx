import ScrollReveal from '../common/ScrollReveal'
import TechIcon from '../icons/TechIcon'

const STACKS = [
  {
    category: 'AI / NLP',
    description: 'Building intelligent systems with deep learning and NLP',
    items: ['PyTorch', 'HuggingFace', 'LangChain', 'OpenAI', 'TensorFlow'],
    color: '#FF6F00',
  },
  {
    category: 'Cloud & Infra',
    description: 'Designing scalable cloud-native architectures',
    items: ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'Linux'],
    color: '#FF9900',
  },
  {
    category: 'Backend',
    description: 'Crafting reliable APIs and server-side logic',
    items: ['Python', 'Django', 'FastAPI', 'Node.js'],
    color: '#3776AB',
  },
  {
    category: 'Data',
    description: 'Managing and processing data at scale',
    items: ['PostgreSQL', 'Redis', 'Spark', 'Airflow'],
    color: '#336791',
  },
  {
    category: 'Frontend',
    description: 'Creating responsive and interactive user interfaces',
    items: ['React', 'TypeScript', 'TailwindCSS', 'Vite'],
    color: '#61DAFB',
  },
  {
    category: 'DevOps',
    description: 'Automating deployment and monitoring pipelines',
    items: ['GitHub Actions', 'Nginx', 'Grafana', 'Cloudflare'],
    color: '#2088FF',
  },
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {STACKS.map((stack, i) => (
            <ScrollReveal key={stack.category} delay={i * 0.1}>
              <div
                className="p-5 rounded-xl border transition-all hover:shadow-lg hover:-translate-y-1 relative overflow-hidden"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
              >
                {/* Accent bar */}
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 rounded-l-xl"
                  style={{ background: stack.color }}
                />

                <div className="pl-3">
                  <h3
                    className="text-sm font-bold mb-1 uppercase tracking-wider"
                    style={{ color: stack.color }}
                  >
                    {stack.category}
                  </h3>
                  <p className="text-xs mb-4" style={{ color: 'var(--text-secondary)' }}>
                    {stack.description}
                  </p>

                  <div className="flex flex-wrap gap-3">
                    {stack.items.map((item) => (
                      <div
                        key={item}
                        className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg transition-transform hover:scale-105"
                        style={{ background: stack.color + '12', color: 'var(--text)' }}
                      >
                        <TechIcon name={item} size={16} />
                        <span className="font-medium">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}
