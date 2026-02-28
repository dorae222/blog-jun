import { motion } from 'framer-motion'
import ScrollReveal from '../components/common/ScrollReveal'
import TechStack from '../components/portfolio/TechStack'

export default function About() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <section className="max-w-4xl mx-auto px-4 py-16">
        <ScrollReveal>
          <h1 className="text-4xl font-bold mb-6" style={{ color: 'var(--text)' }}>About Me</h1>
        </ScrollReveal>

        <ScrollReveal delay={0.1}>
          <div className="prose prose-lg max-w-none" style={{ color: 'var(--text-secondary)' }}>
            <p>
              Cloud & AI/ML Engineer with a passion for building scalable systems
              and exploring cutting-edge machine learning technologies.
            </p>
            <p>
              Currently focused on AWS cloud infrastructure, MLOps pipelines,
              and full-stack development with Django and React.
            </p>
          </div>
        </ScrollReveal>

        {/* Certifications */}
        <ScrollReveal delay={0.2}>
          <div className="mt-12">
            <h2 className="text-2xl font-bold mb-6" style={{ color: 'var(--text)' }}>Certifications</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                'AWS Solutions Architect',
                'AWS Developer Associate',
                'AWS Data Engineer',
              ].map((cert, i) => (
                <div
                  key={cert}
                  className="p-4 rounded-xl border text-center hover:shadow-md transition-all"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <div className="text-2xl mb-2">🏆</div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{cert}</p>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>
      </section>

      <TechStack />
    </motion.div>
  )
}
