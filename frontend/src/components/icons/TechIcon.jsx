// CDN-based tech icons — no more broken inline SVG paths
// Primary: cdn.simpleicons.org (returns colored SVG)
// Fallback: devicon CDN or inline SVG for unsupported icons
import { useState } from 'react'

const ICONS = {
  aws:            { cdn: 'devicon', slug: 'amazonwebservices/amazonwebservices-plain-wordmark', color: '#FF9900' },
  python:         { cdn: 'si', slug: 'python',        color: '#3776AB' },
  django:         { cdn: 'si', slug: 'django',        color: '#092E20' },
  fastapi:        { cdn: 'si', slug: 'fastapi',       color: '#009688' },
  flask:          { cdn: 'si', slug: 'flask',         color: '#000000' },
  react:          { cdn: 'si', slug: 'react',         color: '#61DAFB' },
  docker:         { cdn: 'si', slug: 'docker',        color: '#2496ED' },
  pytorch:        { cdn: 'si', slug: 'pytorch',       color: '#EE4C2C' },
  tensorflow:     { cdn: 'si', slug: 'tensorflow',    color: '#FF6F00' },
  huggingface:    { cdn: 'si', slug: 'huggingface',   color: '#FFD21E' },
  langchain:      { cdn: 'si', slug: 'langchain',     color: '#1C3C3C' },
  openai:         { cdn: 'svg', color: '#412991', path: 'M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z' },
  postgresql:     { cdn: 'si', slug: 'postgresql',    color: '#4169E1' },
  redis:          { cdn: 'si', slug: 'redis',         color: '#FF4438' },
  mysql:          { cdn: 'si', slug: 'mysql',         color: '#4479A1' },
  mongodb:        { cdn: 'si', slug: 'mongodb',       color: '#47A248' },
  spark:          { cdn: 'si', slug: 'apachespark',   color: '#E25A1C' },
  hadoop:         { cdn: 'si', slug: 'apachehadoop',  color: '#66CCFF' },
  hive:           { cdn: 'si', slug: 'apachehive',    color: '#FDEE21' },
  typescript:     { cdn: 'si', slug: 'typescript',    color: '#3178C6' },
  tailwindcss:    { cdn: 'si', slug: 'tailwindcss',   color: '#06B6D4' },
  vite:           { cdn: 'si', slug: 'vite',          color: '#646CFF' },
  githubactions:  { cdn: 'si', slug: 'githubactions', color: '#2088FF' },
  linux:          { cdn: 'si', slug: 'linux',         color: '#FCC624' },
  nginx:          { cdn: 'si', slug: 'nginx',         color: '#009639' },
  cloudflare:     { cdn: 'si', slug: 'cloudflare',    color: '#F38020' },
  figma:          { cdn: 'si', slug: 'figma',         color: '#F24E1E' },
  // 신규 추가 (8종)
  numpy:          { cdn: 'si', slug: 'numpy',         color: '#013243' },
  pandas:         { cdn: 'si', slug: 'pandas',        color: '#150458' },
  'scikit-learn': { cdn: 'si', slug: 'scikitlearn',   color: '#F7931E' },
  r:              { cdn: 'si', slug: 'r',              color: '#276DC3' },
  springboot:     { cdn: 'si', slug: 'springboot',    color: '#6DB33F' },
  langgraph:      { cdn: 'si', slug: 'langgraph',     color: '#22C55E' },
  langsmith:      { cdn: 'svg', color: '#1C3C3C', path: 'M7.53 15.975a7.53 7.53 0 0 0 2.206-5.325A7.54 7.54 0 0 0 7.53 5.325L2.205 0A7.54 7.54 0 0 0 0 5.325a7.54 7.54 0 0 0 2.205 5.325zm11.144.493a7.54 7.54 0 0 0-5.325-2.206 7.54 7.54 0 0 0-5.325 2.206l5.325 5.325a7.54 7.54 0 0 0 5.325 2.205A7.54 7.54 0 0 0 24 21.793zM2.219 21.78a7.54 7.54 0 0 0 5.325 2.205v-7.53H.014a7.54 7.54 0 0 0 2.205 5.325M20.73 8.595a7.53 7.53 0 0 0-5.327-2.206 7.53 7.53 0 0 0-5.325 2.207l5.325 5.325z' },
  pig:            { cdn: 'svg', color: '#D2A03C', fillRule: 'evenodd', path: 'M12 2L7.5 5.5 4 1.5l3 5C4 8.5 2 10.5 2 13c0 4.5 4.5 8 10 8s10-3.5 10-8c0-2.5-2-4.5-5-6.5l3-5-3.5 4zM7.5 14c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5-2 4.5-4.5 4.5-4.5-2-4.5-4.5zm2-.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zm5 0a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z' },
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
  const [broken, setBroken] = useState(false)
  const key = name.toLowerCase().replace(/[\s./]/g, '')  // 하이픈은 유지
  const icon = ICONS[key]

  if (!icon || broken) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded text-xs font-bold ${className}`}
        style={{ width: size, height: size, color: '#64748b' }}
      >
        {name.slice(0, 2)}
      </span>
    )
  }

  if (icon.cdn === 'svg') {
    return (
      <svg
        viewBox={icon.viewBox || '0 0 24 24'}
        width={size}
        height={size}
        className={className}
        fill={icon.color}
        fillRule={icon.fillRule || undefined}
        aria-label={name}
      >
        <path d={icon.path} />
      </svg>
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
      onError={() => setBroken(true)}
    />
  )
}

export function getTechColor(name) {
  const key = name.toLowerCase().replace(/[\s./]/g, '')
  return ICONS[key]?.color || '#64748b'
}
