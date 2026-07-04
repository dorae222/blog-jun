import { motion } from 'framer-motion'
import { Helmet } from 'react-helmet-async'
import { Github, Mail, Linkedin, GraduationCap, Award, MapPin } from 'lucide-react'
import TechStack from '../components/portfolio/TechStack'
import Timeline from '../components/portfolio/Timeline'
import TechIcon from '../components/icons/TechIcon'
import { ACTIVITIES } from '../data/activities'

const ORBIT_TECHS = [
  { name: 'PyTorch', angle: 0 },
  { name: 'Naver Cloud', angle: 36 },
  { name: 'AWS', angle: 72 },
  { name: 'Kubernetes', angle: 108 },
  { name: 'Python', angle: 144 },
  { name: 'React', angle: 180 },
  { name: 'Docker', angle: 216 },
  { name: 'HuggingFace', angle: 252 },
  { name: 'Django', angle: 288 },
  { name: 'FastAPI', angle: 324 },
]

const CERTS_AWS = [
  { name: 'Machine Learning - Specialty', code: 'MLS-C01', level: 'Specialty' },
  { name: 'Machine Learning Engineer', code: 'MLA-C01', level: 'Associate' },
  { name: 'Solutions Architect', code: 'SAA-C03', level: 'Associate' },
  { name: 'Data Engineer', code: 'DEA-C01', level: 'Associate' },
  { name: 'AI Practitioner', code: 'AIF-C01', level: 'Foundational' },
  { name: 'Cloud Practitioner', code: 'CLF-C02', level: 'Foundational' },
]

const LEVEL_COLORS = {
  Specialty: { bg: '#FF990020', color: '#FF9900' },
  Associate: { bg: '#2563eb15', color: '#2563eb' },
  Foundational: { bg: '#10b98115', color: '#10b981' },
}

const CERTS_DATA = [
  { name: 'ADsP', org: 'K-Data' },
  { name: 'SQLD', org: 'K-Data' },
]


export default function About() {
  return (
    <>
    <Helmet>
      <title>About | HJ Tech Blog</title>
      <meta name="description" content="AIOps Engineer 도형준의 기술 블로그. AWS 자격증, 논문 리뷰, 클라우드 인프라 경험을 공유합니다." />
    </Helmet>
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      {/* Intro with Profile Photo + Orbit Icons */}
      <section className="max-w-5xl mx-auto px-4 pt-16 pb-8">
        <div className="flex flex-col lg:flex-row items-center gap-10 lg:gap-14">
          {/* Profile photo with orbiting icons */}
          <motion.div
            className="relative shrink-0"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
          >
            <div className="relative w-56 h-56 md:w-64 md:h-64">
              {/* Photo */}
              <div className="absolute inset-6 md:inset-7 rounded-full overflow-hidden shadow-xl ring-4 ring-white z-10">
                <img
                  src="/profile.jpeg"
                  alt="Do HyeongJun"
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Orbit ring */}
              <div
                className="absolute inset-0 rounded-full"
                style={{ border: '1px dashed var(--border)' }}
              />

              {/* Tech icons */}
              {ORBIT_TECHS.map((tech, i) => {
                const rad = (tech.angle * Math.PI) / 180
                const radius = 112
                const x = Math.cos(rad) * radius
                const y = Math.sin(rad) * radius

                return (
                  <motion.div
                    key={tech.name}
                    className="absolute w-9 h-9 rounded-full flex items-center justify-center shadow-md z-20 glass"
                    style={{
                      left: '50%',
                      top: '50%',
                      marginLeft: -18,
                      marginTop: -18,
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
                    <TechIcon name={tech.name} size={18} />
                  </motion.div>
                )
              })}
            </div>
          </motion.div>

          {/* Text content */}
          <div className="text-center lg:text-left flex-1">
            <h1 className="text-2xl md:text-4xl font-bold mb-2" style={{ color: 'var(--text)' }}>
              <span className="text-primary-600">Do</span> HyeongJun
            </h1>
            <p className="text-lg font-medium text-primary-600 mb-3">AIOps Engineer</p>
            <div
              className="flex items-center gap-2 mb-4 justify-center lg:justify-start"
              style={{ color: 'var(--text-secondary)' }}
            >
              <MapPin size={14} />
              <span className="text-sm">Seoul, South Korea</span>
            </div>
            <p className="text-base max-w-xl mb-6" style={{ color: 'var(--text-secondary)' }}>
              AIOps Engineer로, 자연어처리(NLP), 운영 자동화, 클라우드 인프라, 풀스택 개발을 연결해 실질적인 AI 서비스를 설계하고 구현합니다.
            </p>
            <div className="flex items-center justify-center lg:justify-start gap-4">
              <a
                href="https://github.com/dorae222"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <Github size={18} /> GitHub
              </a>
              <a
                href="https://www.linkedin.com/in/hyeongjun-do-5519321aa/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <Linkedin size={18} /> LinkedIn
              </a>
              <a
                href="mailto:dhj9842@gmail.com"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <Mail size={18} /> Email
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Education */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 mb-6">
          <GraduationCap size={24} className="text-primary-600" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Education</h2>
        </div>
        <div className="p-5 rounded-xl glass">
          <h3 className="font-semibold text-lg" style={{ color: 'var(--text)' }}>
            한양대학교
          </h3>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            경영학부 + 빅데이터융합전공
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
            2019.03 - 2025.02
          </p>
        </div>
      </section>

      {/* Certifications */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 mb-6">
          <Award size={24} className="text-primary-600" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Certifications</h2>
        </div>

        {/* AWS */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <TechIcon name="AWS" size={20} />
            <h3 className="font-semibold" style={{ color: 'var(--text)' }}>Amazon Web Services</h3>
            <a
              href="https://www.credly.com/users/hyeongjun-do"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs px-2 py-0.5 rounded-full border hover:opacity-80 transition-opacity"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            >
              Credly →
            </a>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {CERTS_AWS.map((cert) => (
              <div
                key={cert.code}
                className="p-4 rounded-xl glass hover:shadow-md transition-all"
              >
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{cert.name}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{cert.code}</span>
                  <span
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      background: LEVEL_COLORS[cert.level]?.bg,
                      color: LEVEL_COLORS[cert.level]?.color,
                    }}
                  >
                    {cert.level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* K-Data */}
        <div>
          <h3 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>K-Data</h3>
          <div className="flex gap-3">
            {CERTS_DATA.map((cert) => (
              <div
                key={cert.name}
                className="p-4 rounded-xl glass hover:shadow-md transition-all"
              >
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{cert.name}</p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{cert.org}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline (Activities + Awards + Education + Projects) */}
      <Timeline items={ACTIVITIES} />

      {/* Tech Stack */}
      <TechStack />
    </motion.div>
    </>
  )
}
