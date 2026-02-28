// CDN-based tech icons — no more broken inline SVG paths
// Primary: cdn.simpleicons.org (returns colored SVG)
// Fallback: devicon CDN or inline SVG for unsupported icons

const ICONS = {
  aws:           { cdn: 'devicon', slug: 'amazonwebservices/amazonwebservices-plain-wordmark', color: '#FF9900' },
  python:        { cdn: 'si', slug: 'python',        color: '#3776AB' },
  django:        { cdn: 'si', slug: 'django',        color: '#092E20' },
  fastapi:       { cdn: 'si', slug: 'fastapi',       color: '#009688' },
  flask:         { cdn: 'si', slug: 'flask',         color: '#000000' },
  react:         { cdn: 'si', slug: 'react',         color: '#61DAFB' },
  docker:        { cdn: 'si', slug: 'docker',        color: '#2496ED' },
  pytorch:       { cdn: 'si', slug: 'pytorch',       color: '#EE4C2C' },
  tensorflow:    { cdn: 'si', slug: 'tensorflow',    color: '#FF6F00' },
  huggingface:   { cdn: 'si', slug: 'huggingface',   color: '#FFD21E' },
  langchain:     { cdn: 'si', slug: 'langchain',     color: '#1C3C3C' },
  openai:        { cdn: 'si', slug: 'openai',        color: '#412991', fallbackSi: true },
  postgresql:    { cdn: 'si', slug: 'postgresql',    color: '#4169E1' },
  redis:         { cdn: 'si', slug: 'redis',         color: '#FF4438' },
  mysql:         { cdn: 'si', slug: 'mysql',         color: '#4479A1' },
  mongodb:       { cdn: 'si', slug: 'mongodb',       color: '#47A248' },
  spark:         { cdn: 'si', slug: 'apachespark',   color: '#E25A1C' },
  hadoop:        { cdn: 'si', slug: 'apachehadoop',  color: '#66CCFF' },
  hive:          { cdn: 'si', slug: 'apachehive',    color: '#FDEE21' },
  typescript:    { cdn: 'si', slug: 'typescript',    color: '#3178C6' },
  tailwindcss:   { cdn: 'si', slug: 'tailwindcss',   color: '#06B6D4' },
  vite:          { cdn: 'si', slug: 'vite',          color: '#646CFF' },
  githubactions: { cdn: 'si', slug: 'githubactions', color: '#2088FF' },
  linux:         { cdn: 'si', slug: 'linux',         color: '#FCC624' },
  nginx:         { cdn: 'si', slug: 'nginx',         color: '#009639' },
  cloudflare:    { cdn: 'si', slug: 'cloudflare',    color: '#F38020' },
  figma:         { cdn: 'si', slug: 'figma',         color: '#F24E1E' },
}

function getIconUrl(icon) {
  const hex = icon.color.replace('#', '')
  if (icon.cdn === 'devicon') {
    return `https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/${icon.slug}.svg`
  }
  // Simple Icons CDN — returns colored SVG
  return `https://cdn.simpleicons.org/${icon.slug}/${hex}`
}

export default function TechIcon({ name, size = 24, className = '' }) {
  const key = name.toLowerCase().replace(/[\s./]/g, '')
  const icon = ICONS[key]

  if (!icon) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded text-xs font-bold ${className}`}
        style={{ width: size, height: size, color: '#64748b' }}
      >
        {name.slice(0, 2)}
      </span>
    )
  }

  return (
    <img
      src={getIconUrl(icon)}
      alt={name}
      width={size}
      height={size}
      className={className}
      loading="lazy"
    />
  )
}

export function getTechColor(name) {
  const key = name.toLowerCase().replace(/[\s./]/g, '')
  return ICONS[key]?.color || '#64748b'
}
