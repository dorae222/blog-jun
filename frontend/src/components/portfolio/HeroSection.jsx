import { motion } from 'framer-motion'
import { Github, Mail, Linkedin, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import TypeWriter from '../common/TypeWriter'
import AnimatedCounter from '../common/AnimatedCounter'
import AuroraBackground from '../home/AuroraBackground'
import CodeEditorHero from '../home/CodeEditorHero'
import useMagnetic from '../../hooks/useMagnetic'

// 마그네틱 CTA — 래퍼 motion.div가 커서 쪽으로 살짝 끌려오고, 내부에 실제 버튼(Link/a)을 둔다.
function MagneticButton({ to, href, primary = false, className = '', children, ...rest }) {
  const { ref, style } = useMagnetic()
  const base = primary
    ? 'inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors'
    : 'inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border text-sm font-medium transition-colors hover:bg-gray-50'
  const innerStyle = primary ? undefined : { borderColor: 'var(--border)', color: 'var(--text)' }

  return (
    <motion.div ref={ref} style={{ ...style, display: 'inline-flex' }}>
      {to ? (
        <Link to={to} className={`${base} ${className}`} style={innerStyle} {...rest}>
          {children}
        </Link>
      ) : (
        <a href={href} className={`${base} ${className}`} style={innerStyle} {...rest}>
          {children}
        </a>
      )}
    </motion.div>
  )
}

export default function HeroSection({ stats = {} }) {
  return (
    <section className="relative overflow-hidden flex items-center min-h-[72vh] pt-10 pb-16 md:pt-16 md:pb-20">
      <AuroraBackground />

      <div className="relative z-10 max-w-6xl mx-auto px-4 w-full">
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-14 items-center">
          {/* 텍스트 컬럼 */}
          <div className="text-center lg:text-left">
            <motion.p
              className="text-sm font-medium tracking-wide uppercase mb-3 text-primary-600"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              Welcome to my blog
            </motion.p>

            <motion.h1
              className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 leading-tight tracking-tight"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
            >
              <span style={{ color: 'var(--text)' }}>Do </span>
              <span className="bg-gradient-to-r from-primary-600 via-primary-500 to-accent bg-clip-text text-transparent">
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
                  'AIOps Engineer',
                  'Cloud & On-Prem Infrastructure',
                  'Full-Stack Developer',
                ]}
              />
            </motion.div>

            <motion.p
              className="text-base max-w-lg mx-auto lg:mx-0 mb-8 leading-relaxed"
              style={{ color: 'var(--text-secondary)' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.8 }}
            >
              Building NLP &amp; LLM systems across cloud and on-prem,{' '}
              <br className="hidden sm:block" />
              and full-stack products - then writing about them here.
            </motion.p>

            {/* Stats */}
            {(stats.total_posts || stats.categories || stats.tags) && (
              <motion.div
                className="flex items-center justify-center lg:justify-start gap-6 mb-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7, duration: 0.6 }}
              >
                <AnimatedCounter end={stats.total_posts || 0} label="Posts" duration={1.5} />
                <AnimatedCounter end={stats.categories || 0} label="Categories" duration={1.5} />
                <AnimatedCounter end={stats.tags || 0} label="Tags" duration={1.5} />
              </motion.div>
            )}

            {/* CTA */}
            <motion.div
              className="flex flex-wrap items-center gap-3 justify-center lg:justify-start"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.6 }}
            >
              <MagneticButton to="/about" primary>
                About Me <ArrowRight size={16} />
              </MagneticButton>
              <MagneticButton
                href="https://github.com/dorae222"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github size={18} /> GitHub
              </MagneticButton>
              <MagneticButton
                href="https://www.linkedin.com/in/hyeongjun-do-5519321aa/"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Linkedin size={18} /> LinkedIn
              </MagneticButton>
              <MagneticButton href="mailto:dhj9842@gmail.com">
                <Mail size={18} /> Email
              </MagneticButton>
            </motion.div>
          </div>

          {/* 코드 에디터 컬럼 */}
          <motion.div
            className="w-full min-w-0"
            initial={{ opacity: 0, y: 30, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.25, ease: 'easeOut' }}
          >
            <CodeEditorHero />
          </motion.div>
        </div>
      </div>
    </section>
  )
}
