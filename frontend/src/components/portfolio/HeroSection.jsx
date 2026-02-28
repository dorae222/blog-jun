import ParticleBackground from '../effects/ParticleBackground'
import TypeWriter from '../common/TypeWriter'
import GradientCursor from '../effects/GradientCursor'
import { motion } from 'framer-motion'

const TECH_ICONS = [
  { name: 'AWS', color: '#FF9900', angle: 0 },
  { name: 'Python', color: '#3776AB', angle: 45 },
  { name: 'Django', color: '#092E20', angle: 90 },
  { name: 'React', color: '#61DAFB', angle: 135 },
  { name: 'Docker', color: '#2496ED', angle: 180 },
  { name: 'K8s', color: '#326CE5', angle: 225 },
  { name: 'AI/ML', color: '#FF6F00', angle: 270 },
  { name: 'Linux', color: '#FCC624', angle: 315 },
]

export default function HeroSection() {
  return (
    <section className="relative min-h-[80vh] flex items-center justify-center overflow-hidden">
      <ParticleBackground count={40} />
      <GradientCursor />

      <div className="relative z-10 text-center px-4 max-w-3xl mx-auto">
        <motion.h1
          className="text-5xl md:text-6xl font-bold mb-6"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <span style={{ color: 'var(--text)' }}>Hi, I'm </span>
          <span className="text-primary-600">HyeongJun</span>
        </motion.h1>

        <motion.div
          className="text-xl md:text-2xl mb-8 h-8"
          style={{ color: 'var(--text-secondary)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <TypeWriter
            texts={[
              'Cloud & DevOps Engineer',
              'AI/ML Enthusiast',
              'Full-Stack Developer',
              'AWS Solutions Architect',
            ]}
          />
        </motion.div>

        <motion.div
          className="relative w-64 h-64 mx-auto mb-8"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          {TECH_ICONS.map((tech, i) => (
            <motion.div
              key={tech.name}
              className="absolute w-12 h-12 rounded-xl flex items-center justify-center text-xs font-bold shadow-md"
              style={{
                backgroundColor: tech.color + '20',
                color: tech.color,
                border: `2px solid ${tech.color}40`,
              }}
              animate={{
                x: Math.cos((tech.angle * Math.PI) / 180 + Date.now() / 5000) * 100,
                y: Math.sin((tech.angle * Math.PI) / 180 + Date.now() / 5000) * 100,
              }}
              transition={{
                repeat: Infinity,
                duration: 8,
                ease: 'linear',
                delay: i * 0.3,
              }}
              initial={{
                x: Math.cos((tech.angle * Math.PI) / 180) * 100,
                y: Math.sin((tech.angle * Math.PI) / 180) * 100,
                left: '50%',
                top: '50%',
                marginLeft: -24,
                marginTop: -24,
              }}
            >
              {tech.name}
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
