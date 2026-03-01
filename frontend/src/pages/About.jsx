import { motion } from 'framer-motion'
import { Github, Mail, Linkedin, GraduationCap, Award, Users, Trophy, MapPin, Briefcase } from 'lucide-react'
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
  { name: 'FastAPI', angle: 315 },
]

const CERTS_AWS = [
  { name: 'Machine Learning - Specialty', code: 'MLS-C01', level: 'Specialty' },
  { name: 'Machine Learning Engineer', code: 'MLA-C01', level: 'Associate' },
  { name: 'Solutions Architect', code: 'SAA-C03', level: 'Associate' },
  { name: 'Data Engineer', code: 'DEA-C01', level: 'Associate' },
]

const CERTS_DATA = [
  { name: 'ADsP', org: 'K-Data' },
  { name: 'SQLD', org: 'K-Data' },
]

const EXPERIENCE = [
  {
    period: '2023.12 ~ 2024.02',
    company: '원데이원 커뮤니케이션',
    role: '솔루션개발팀 인턴',
    desc: 'AI바우처 정부 사업을 위한 기획 및 개발. 사업계획서 작성, 주재원 대상 챗봇 조사 및 설계, AI 강의 커리큘럼 설계',
  },
]

const ACTIVITIES = [
  { period: '2025.12 ~ now', name: '멋쟁이 사자처럼 NLP 트랙 3기', desc: '금융 학습 컨텐츠 생성 및 챗봇 시스템' },
  { period: '2025.06 ~ 2025.12', name: 'AICA 인공지능사관학교 6기 NLP 트랙', desc: '광주광역시 플리마켓 챗봇 플랫폼' },
  { period: '2023.07 ~ 2024.06', name: '투빅스 (Tobigs)', desc: '학석사 연합 AI 동아리' },
  { period: '2023.03 ~ 2024.02', name: 'HAI', desc: '교내 AI 동아리' },
]

const AWARDS = [
  { year: '2025', name: '인공지능사관학교 온라인 해커톤 1위', org: 'AICA' },
  { year: '2023', name: '교내 한국어 지역 방언 분류 (Kaggle) 3위', org: 'Kaggle' },
  { year: '2022', name: '한국관광공사 표창장 - 사장상', org: '한국관광공사' },
  { year: '2022', name: '한국관광 데이터랩 우수 활용사례 공모전 2위', org: 'KTO Data Lab' },
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
                      className="absolute w-9 h-9 rounded-full flex items-center justify-center shadow-md z-20"
                      style={{
                        background: 'rgba(255,255,255,0.45)',
                        backdropFilter: 'blur(12px) saturate(180%)',
                        WebkitBackdropFilter: 'blur(12px) saturate(180%)',
                        border: '1px solid rgba(255,255,255,0.3)',
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
              <p className="text-lg font-medium text-primary-600 mb-3">NLP 엔지니어</p>
              <div
                className="flex items-center gap-2 mb-4 justify-center lg:justify-start"
                style={{ color: 'var(--text-secondary)' }}
              >
                <MapPin size={14} />
                <span className="text-sm">Seoul, South Korea</span>
              </div>
              <p className="text-base max-w-xl mb-6" style={{ color: 'var(--text-secondary)' }}>
                자연어처리(NLP) 기반 AI 엔지니어로, 클라우드 인프라와 풀스택 개발을 아우르며 실질적인 AI 서비스를 설계하고 구현합니다. AWS Certified.
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
        </ScrollReveal>
      </section>

      {/* Education */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
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
              2019.03 - 2025.02 | GPA 4.0 / 4.5
            </p>
          </div>
        </ScrollReveal>
      </section>

      {/* Experience */}
      <section className="max-w-4xl mx-auto px-4 py-8">
        <ScrollReveal>
          <div className="flex items-center gap-2 mb-6">
            <Briefcase size={24} className="text-primary-600" />
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Experience</h2>
          </div>
        </ScrollReveal>

        <div className="space-y-3">
          {EXPERIENCE.map((exp, i) => (
            <ScrollReveal key={exp.company} delay={i * 0.05}>
              <div className="flex items-start gap-4 p-4 rounded-xl glass hover:shadow-md transition-all">
                <span className="text-xs font-mono whitespace-nowrap mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {exp.period}
                </span>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{exp.company}</p>
                  <p className="text-xs font-medium text-primary-600">{exp.role}</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{exp.desc}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
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
                        background: cert.level === 'Specialty' ? '#FF990020' : '#2563eb15',
                        color: cert.level === 'Specialty' ? '#FF9900' : '#2563eb',
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
                  className="p-4 rounded-xl glass hover:shadow-md transition-all"
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
              <div className="flex items-start gap-4 p-4 rounded-xl glass hover:shadow-md transition-all">
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
              <div className="flex items-start gap-4 p-4 rounded-xl glass hover:shadow-md transition-all">
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
