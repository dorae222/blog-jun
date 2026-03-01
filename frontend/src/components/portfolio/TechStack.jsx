import ScrollReveal from '../common/ScrollReveal'
import TechIcon from '../icons/TechIcon'

const STACKS = [
  {
    category: 'AI / NLP',
    description: 'Building intelligent systems with deep learning and NLP',
    items: ['PyTorch', 'TensorFlow', 'HuggingFace', 'OpenAI', 'LangChain', 'LangGraph', 'LangSmith'],
    color: '#FF6F00',
  },
  {
    category: 'Data Science',
    description: 'Analyzing and modeling data for insights',
    items: ['NumPy', 'Pandas', 'Scikit-Learn', 'R'],
    color: '#4DABF7',
  },
  {
    category: 'Data Engineering',
    description: 'Processing and managing data pipelines at scale',
    items: ['Hadoop', 'Spark', 'Hive', 'Pig'],
    color: '#E25A1C',
  },
  {
    category: 'Backend',
    description: 'Crafting reliable APIs and server-side logic',
    items: ['Python', 'Django', 'FastAPI', 'Flask', 'Spring Boot'],
    color: '#3776AB',
  },
  {
    category: 'Frontend & Design',
    description: 'Creating responsive and interactive user interfaces',
    items: ['React', 'TypeScript', 'TailwindCSS', 'Vite', 'Figma'],
    color: '#61DAFB',
  },
  {
    category: 'Database',
    description: 'Managing and optimizing data storage',
    items: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis'],
    color: '#336791',
  },
  {
    category: 'Cloud & DevOps',
    description: 'Automating deployment and cloud infrastructure',
    items: ['AWS', 'Docker', 'Linux', 'GitHub Actions', 'Nginx', 'Cloudflare'],
    color: '#FF9900',
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
              <div className="p-5 rounded-xl glass transition-all hover:shadow-lg hover:-translate-y-1">
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
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}
