import ParticleBackground from '../effects/ParticleBackground'
import TypeWriter from '../common/TypeWriter'
import GradientCursor from '../effects/GradientCursor'
import TechIcon from '../icons/TechIcon'
import { motion } from 'framer-motion'
import { Github, Mail, Linkedin, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

const ORBIT_TECHS = [
  { name: 'PyTorch', angle: 0 },
  { name: 'AWS', angle: 45 },
  { name: 'Python', angle: 90 },
  { name: 'React', angle: 135 },
  { name: 'Docker', angle: 180 },
  { name: 'HuggingFace', angle: 225 },
  { name: 'Django', angle: 270 },
  { name: 'FastAPI', angle: 315 },
]

export default function HeroSection() {
  return (
    <section className="relative min-h-[85vh] flex items-center overflow-hidden">
      <ParticleBackground count={40} />
      <GradientCursor />

      <div className="relative z-10 max-w-4xl mx-auto px-4 w-full text-center">
        {/* Orbit icons (standalone, no photo) */}
        <motion.div
          className="relative mx-auto mb-10"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
        >
          <div className="relative w-48 h-48 mx-auto">
            {/* Orbit ring */}
            <div
              className="absolute inset-0 rounded-full"
              style={{ border: '1px dashed var(--border)' }}
            />

            {/* Center dot */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-primary-500 opacity-60" />
            </div>

            {/* Tech icons */}
            {ORBIT_TECHS.map((tech, i) => {
              const rad = (tech.angle * Math.PI) / 180
              const radius = 96
              const x = Math.cos(rad) * radius
              const y = Math.sin(rad) * radius

              return (
                <motion.div
                  key={tech.name}
                  className="absolute w-10 h-10 rounded-full flex items-center justify-center shadow-md z-20"
                  style={{
                    background: 'rgba(255,255,255,0.45)',
                    backdropFilter: 'blur(12px) saturate(180%)',
                    WebkitBackdropFilter: 'blur(12px) saturate(180%)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    left: '50%',
                    top: '50%',
                    marginLeft: -20,
                    marginTop: -20,
                  }}
                  animate={{
                    x: [
                      Math.cos(rad) * radius,
                      Math.cos(rad + Math.PI * 2) * radius,
                    ],
                    y: [
                      Math.sin(rad) * radius,
                      Math.sin(rad + Math.PI * 2) * radius,
                    ],
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 24,
                    ease: 'linear',
                    delay: i * 0.3,
                  }}
                  initial={{ x, y }}
                  title={tech.name}
                >
                  <TechIcon name={tech.name} size={20} />
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        {/* Text content - centered */}
        <motion.p
          className="text-sm font-medium tracking-wide uppercase mb-3 text-primary-600"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Welcome to my blog
        </motion.p>

        <motion.h1
          className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 leading-tight"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
        >
          <span style={{ color: 'var(--text)' }}>Do </span>
          <span className="bg-gradient-to-r from-primary-500 to-accent bg-clip-text text-transparent">
            HyeongJun
          </span>
        </motion.h1>

        <motion.div
          className="text-lg md:text-xl mb-6 h-7"
          style={{ color: 'var(--text-secondary)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <TypeWriter
            texts={[
              'NLP / AI Engineer',
              'Cloud & Infrastructure Builder',
              'Full-Stack Developer',
            ]}
          />
        </motion.div>

        <motion.p
          className="text-base max-w-lg mx-auto mb-8 leading-relaxed"
          style={{ color: 'var(--text-secondary)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          Building NLP &amp; LLM systems, cloud-native infrastructure,
          <br />
          and full-stack products — then writing about them here.
        </motion.p>

        {/* CTA */}
        <motion.div
          className="flex flex-wrap items-center gap-3 justify-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <Link
            to="/about"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
          >
            About Me <ArrowRight size={16} />
          </Link>
          <a
            href="https://github.com/dorae222"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border text-sm font-medium transition-colors hover:bg-gray-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            <Github size={18} /> GitHub
          </a>
          <a
            href="https://www.linkedin.com/in/hyeongjun-do-5519321aa/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border text-sm font-medium transition-colors hover:bg-gray-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            <Linkedin size={18} /> LinkedIn
          </a>
          <a
            href="mailto:dhj9842@gmail.com"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border text-sm font-medium transition-colors hover:bg-gray-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            <Mail size={18} /> Email
          </a>
        </motion.div>
      </div>
    </section>
  )
}
