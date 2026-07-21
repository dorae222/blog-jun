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
  kubernetes:     { cdn: 'si', slug: 'kubernetes',    color: '#326CE5' },
  navercloud:     { cdn: 'local', src: '/assets/brand/ncloud-favicon.png', color: '#03C75A' },
  pytorch:        { cdn: 'si', slug: 'pytorch',       color: '#EE4C2C' },
  tensorflow:     { cdn: 'si', slug: 'tensorflow',    color: '#FF6F00' },
  huggingface:    { cdn: 'si', slug: 'huggingface',   color: '#FFD21E' },
  langchain:      { cdn: 'si', slug: 'langchain',     color: '#1C3C3C' },
  openai:         { cdn: 'svg', color: '#412991', path: 'M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z' },
  postgresql:     { cdn: 'devicon', slug: 'postgresql/postgresql-original',  color: '#4169E1' },
  redis:          { cdn: 'svg', color: '#FF4438', path: 'M10.5 2.661l.54.997-1.797.644 2.409.218.748 1.246.467-1.121 2.077-.208-1.61-.613.426-1.017-1.578.519zm6.905 2.077L13.76 6.182l3.292 1.298.353-.146 3.293-1.298zm-10.51.312a2.97 1.153 0 0 0-2.97 1.152 2.97 1.153 0 0 0 2.97 1.153 2.97 1.153 0 0 0 2.97-1.153 2.97 1.153 0 0 0-2.97-1.152zM24 6.805s-8.983 4.278-10.395 4.953c-1.226.561-1.901.561-3.261.094C8.318 11.022 0 7.241 0 7.241v1.038c0 .24.332.499.966.8 1.277.613 8.34 3.677 9.45 4.206 1.112.53 1.9.54 3.313-.197 1.412-.738 8.049-3.905 9.326-4.57.654-.342.945-.602.945-.84zm-10.042.602L8.39 8.26l3.884 1.61zM24 10.637s-8.983 4.279-10.395 4.954c-1.226.56-1.901.56-3.261.093C8.318 14.854 0 11.074 0 11.074v1.038c0 .238.332.498.966.8 1.277.612 8.34 3.676 9.45 4.205 1.112.53 1.9.54 3.313-.197 1.412-.737 8.049-3.905 9.326-4.57.654-.332.945-.602.945-.84zm0 3.842l-10.395 4.954c-1.226.56-1.901.56-3.261.094C8.318 18.696 0 14.916 0 14.916v1.038c0 .239.332.499.966.8 1.277.613 8.34 3.676 9.45 4.206 1.112.53 1.9.54 3.313-.198 1.412-.737 8.049-3.904 9.326-4.569.654-.343.945-.613.945-.841z' },
  mysql:          { cdn: 'devicon', slug: 'mysql/mysql-original',             color: '#4479A1' },
  mongodb:        { cdn: 'devicon', slug: 'mongodb/mongodb-original',         color: '#47A248' },
  spark:          { cdn: 'devicon', slug: 'apachespark/apachespark-original', color: '#E25A1C' },
  hadoop:         { cdn: 'si', slug: 'apachehadoop',  color: '#0A5A73' },
  hive:           { cdn: 'si', slug: 'apachehive',    color: '#8A5A00' },
  typescript:     { cdn: 'si', slug: 'typescript',    color: '#3178C6' },
  tailwindcss:    { cdn: 'si', slug: 'tailwindcss',   color: '#06B6D4' },
  vite:           { cdn: 'svg', color: '#646CFF', path: 'm8.286 10.578.512-8.657a.306.306 0 0 1 .247-.282L17.377.006a.306.306 0 0 1 .353.385l-1.558 5.403a.306.306 0 0 0 .352.385l2.388-.46a.306.306 0 0 1 .332.438l-6.79 13.55-.123.19a.294.294 0 0 1-.252.14c-.177 0-.35-.152-.305-.369l1.095-5.301a.306.306 0 0 0-.388-.355l-1.433.435a.306.306 0 0 1-.389-.354l.69-3.375a.306.306 0 0 0-.37-.36l-2.32.536a.306.306 0 0 1-.374-.316zm14.976-7.926L17.284 3.74l-.544 1.887 2.077-.4a.8.8 0 0 1 .84.369.8.8 0 0 1 .034.783L12.9 19.93l-.013.025-.015.023-.122.19a.801.801 0 0 1-.672.37.826.826 0 0 1-.634-.302.8.8 0 0 1-.16-.67l1.029-4.981-1.12.34a.81.81 0 0 1-.86-.262.802.802 0 0 1-.165-.67l.63-3.08-2.027.468a.808.808 0 0 1-.768-.233.81.81 0 0 1-.217-.6l.389-6.57-7.44-1.33a.612.612 0 0 0-.64.906L11.58 23.691a.612.612 0 0 0 1.066-.004l11.26-20.135a.612.612 0 0 0-.644-.9z' },
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
  helm:           { cdn: 'si', slug: 'helm',         color: '#0F1689' },
  argocd:         { cdn: 'si', slug: 'argo',         color: '#EF7B4D' },
}

function getIconUrl(icon) {
  if (icon.cdn === 'local') {
    return icon.src
  }
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
      width={icon.wide ? Math.round(size * 1.8) : size}
      height={icon.wide ? Math.round(size * 0.85) : size}
      className={className}
      loading="lazy"
      style={{ objectFit: 'contain' }}
      onError={() => setBroken(true)}
    />
  )
}

export function getTechColor(name) {
  const key = name.toLowerCase().replace(/[\s./]/g, '')
  return ICONS[key]?.color || '#64748b'
}
