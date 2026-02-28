import { motion } from 'framer-motion'
import { Github, Mail, GraduationCap, Award, Users, Trophy, MapPin } from 'lucide-react'
import ScrollReveal from '../components/common/ScrollReveal'
import TechStack from '../components/portfolio/TechStack'
import TechIcon from '../components/icons/TechIcon'

const ORBIT_TECHS = [
  { name: 'PyTorch', angle: 0 },
  { name: 'AWS', angle: 45 },
  { name: 'Python', angle: 90 },
  { name: 'React', angle: 135 },
  { name: 'Docker', angle: 180 },
  { name: 'HuggingFace', angle: 225 },
  { name: 'Django', angle: 270 },
  { name: 'Kubernetes', angle: 315 },
]

const CERTS_AWS = [
  { name: 'Cloud Practitioner', code: 'CLF-C02', level: 'Foundational' },
  { name: 'AI Practitioner', code: 'AIF-C01', level: 'Foundational' },
  { name: 'Solutions Architect', code: 'SAA-C03', level: 'Associate' },
  { name: 'Machine Learning Engineer', code: 'MLA-C01', level: 'Associate' },
  { name: 'Data Engineer', code: 'DEA-C01', level: 'Associate' },
  { name: 'Machine Learning - Specialty', code: 'MLS-C01', level: 'Specialty' },
]

const CERTS_DATA = [
  { name: 'ADsP', org: 'K-Data' },
  { name: 'SQLD', org: 'K-Data' },
]

const ACTIVITIES = [
  { period: '2025.12 ~ 2026.02', name: 'Likelion NLP 3rd Cohort', desc: 'NLP/AI Bootcamp' },
  { period: '2025.06 ~ 2025.12', name: 'AI Officer Academy 6th Cohort', desc: 'AICA / EST / AWS / NCP' },
  { period: '2024.07 ~ 2024.12', name: 'BizLab', desc: 'Hanyang University' },
  { period: '2023.07 ~ 2024.06', name: 'Tobigs 20th Cohort', desc: 'Big Data Analytics Conference' },
  { period: '2023.03 ~ 2024.02', name: 'HAI', desc: 'Hanyang University AI Club' },
  { period: '2022.10 ~ 2023.03', name: 'Encore Big Data Engineer 17th Cohort', desc: 'PlayData' },
  { period: '2022.07 ~ 2022.09', name: 'Data Youth Campus', desc: 'Ministry of Science and ICT' },
]

const AWARDS = [
  { year: '2025', name: 'AI Officer Academy Online Hackathon Grand Prize', org: 'AICA' },
  { year: '2023', name: 'Korean Dialect Classification - 3rd Place', org: 'Kaggle' },
  { year: '2023', name: 'Busan Data Hackathon Award', org: 'Busan' },
  { year: '2022', name: 'Presidential Citation for Tourism', org: 'Korea Tourism Organization' },
  { year: '2022', name: 'Tourism Data Lab Excellence Award - 2nd', org: 'KTO Data Lab' },
]

export default function About() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Intro with Profile Photo + Orbit Icons */}
      <section className="max-w-5xl mx-auto px-4 pt-16 pb-8">
        <ScrollReveal>
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
                      className="absolute w-9 h-9 rounded-full flex items-center justify-center shadow-md bg-white z-20"
                      style={{
                        border: '1px solid var(--border)',
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
              <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--text)' }}>
                <span className="text-primary-600">Do</span> HyeongJun
              </h1>
              <p className="text-lg font-medium text-primary-600 mb-3">NLP / AI Engineer</p>
              <div
                className="flex items-center gap-2 mb-4 justify-center lg:justify-start"
                style={{ color: 'var(--text-secondary)' }}
              >
                <MapPin size={14} />
                <span className="text-sm">Seoul, South Korea</span>
              </div>
              <p className="text-base max-w-xl mb-6" style={{ color: 'var(--text-secondary)' }}>
                Bridging NLP, cloud infrastructure, and full-stack development. AWS 6x Certified.
                Hanyang University graduate, bridging data science with real-world engineering.
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
                  href="mailto:admin@blog.dorae222.com"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium hover:bg-gray-50 transition-colors"
                  style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
                >
                  <Mail size={18} /> Email
                </a>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </section>

      {/* Education */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
          <div className="flex items-center gap-2 mb-6">
            <GraduationCap size={24} className="text-primary-600" />
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Education</h2>
          </div>
          <div
            className="p-5 rounded-xl border"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
          >
            <h3 className="font-semibold text-lg" style={{ color: 'var(--text)' }}>
              Hanyang University
            </h3>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              B.A. Business Administration + Big Data Science Interdisciplinary Major
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
              2019.03 - 2025.02
            </p>
          </div>
        </ScrollReveal>
      </section>

      {/* Certifications */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
          <div className="flex items-center gap-2 mb-6">
            <Award size={24} className="text-primary-600" />
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Certifications</h2>
          </div>
        </ScrollReveal>

        {/* AWS */}
        <ScrollReveal delay={0.1}>
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <TechIcon name="AWS" size={20} />
              <h3 className="font-semibold" style={{ color: 'var(--text)' }}>Amazon Web Services (6x)</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {CERTS_AWS.map((cert) => (
                <div
                  key={cert.code}
                  className="p-4 rounded-xl border hover:shadow-md transition-all"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{cert.name}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{cert.code}</span>
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{
                        background: cert.level === 'Specialty' ? '#FF990020' : cert.level === 'Associate' ? '#2563eb15' : '#8b5cf615',
                        color: cert.level === 'Specialty' ? '#FF9900' : cert.level === 'Associate' ? '#2563eb' : '#8b5cf6',
                      }}
                    >
                      {cert.level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>

        {/* K-Data */}
        <ScrollReveal delay={0.2}>
          <div>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>K-Data</h3>
            <div className="flex gap-3">
              {CERTS_DATA.map((cert) => (
                <div
                  key={cert.name}
                  className="p-4 rounded-xl border hover:shadow-md transition-all"
                  style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
                >
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{cert.name}</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{cert.org}</p>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>
      </section>

      {/* Activities */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
          <div className="flex items-center gap-2 mb-6">
            <Users size={24} className="text-primary-600" />
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Activities</h2>
          </div>
        </ScrollReveal>

        <div className="space-y-3">
          {ACTIVITIES.map((act, i) => (
            <ScrollReveal key={act.name} delay={i * 0.05}>
              <div
                className="flex items-start gap-4 p-4 rounded-xl border hover:shadow-md transition-all"
                style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
              >
                <span className="text-xs font-mono whitespace-nowrap mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {act.period}
                </span>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{act.name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{act.desc}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Awards */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
          <div className="flex items-center gap-2 mb-6">
            <Trophy size={24} className="text-primary-600" />
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Awards</h2>
          </div>
        </ScrollReveal>

        <div className="space-y-3">
          {AWARDS.map((award, i) => (
            <ScrollReveal key={award.name} delay={i * 0.05}>
              <div
                className="flex items-start gap-4 p-4 rounded-xl border hover:shadow-md transition-all"
                style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
              >
                <span
                  className="text-xs font-bold px-2 py-0.5 rounded-full whitespace-nowrap mt-0.5"
                  style={{ background: '#2563eb15', color: '#2563eb' }}
                >
                  {award.year}
                </span>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{award.name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{award.org}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <TechStack />
    </motion.div>
  )
}
