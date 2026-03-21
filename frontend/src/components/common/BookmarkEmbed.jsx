import { useState, useEffect } from 'react'
import { ExternalLink, FileText, Github, Bot } from 'lucide-react'

const DOMAIN_STYLES = {
  'github.com':       { accent: '#24292f', Icon: Github,       label: 'GitHub' },
  'huggingface.co':   { accent: '#ffd21e', Icon: null,         label: 'Hugging Face' },
  'arxiv.org':        { accent: '#b31b1b', Icon: FileText,     label: 'arXiv' },
  'openai.com':       { accent: '#412991', Icon: Bot,          label: 'OpenAI' },
}

function getDomainStyle(domain) {
  for (const [key, style] of Object.entries(DOMAIN_STYLES)) {
    if (domain.includes(key)) return style
  }
  return { accent: '#6366f1', Icon: ExternalLink, label: null }
}

export default function BookmarkEmbed({ url }) {
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!url) return
    try {
      const u = new URL(url)
      const domain = u.hostname.replace('www.', '')
      const style = getDomainStyle(domain)
      let title = url
      let description = ''

      if (domain === 'arxiv.org') {
        const id = u.pathname.split('/').pop()
        title = `arXiv: ${id}`
        description = 'Paper'
      } else if (domain === 'github.com') {
        const parts = u.pathname.split('/').filter(Boolean)
        title = parts.length >= 2 ? `${parts[0]}/${parts[1]}` : u.pathname
        description = 'GitHub Repository'
      } else if (domain.includes('openai.com')) {
        title = 'OpenAI'
        description = u.pathname.replace(/\//g, ' ').trim() || 'OpenAI Research'
      } else if (domain.includes('huggingface.co')) {
        const parts = u.pathname.split('/').filter(Boolean)
        title = parts.length >= 2 ? `${parts[0]}/${parts[1]}` : 'Hugging Face'
        description = parts.length >= 2 ? 'Model / Dataset / Space' : 'Model Hub'
      } else {
        title = domain
        description = u.pathname.length > 1 ? u.pathname : ''
      }

      setMeta({
        title, description, domain, style,
        favicon: `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
      })
    } catch {
      setError(true)
    }
  }, [url])

  if (!url) return null

  if (error || !meta) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm text-primary-600 hover:underline"
      >
        <ExternalLink size={14} />
        {url}
      </a>
    )
  }

  const { accent, Icon } = meta.style

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border overflow-hidden transition-all hover:shadow-md hover:-translate-y-0.5 my-4"
      style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)', borderLeft: `3px solid ${accent}` }}
    >
      <div className="flex items-start gap-3 p-4">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
            {meta.title}
          </h4>
          {meta.description && (
            <p className="text-xs mt-1 truncate" style={{ color: 'var(--text-secondary)' }}>
              {meta.description}
            </p>
          )}
          <div className="flex items-center gap-1.5 mt-2">
            {meta.favicon && <img src={meta.favicon} alt="" className="w-4 h-4" />}
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{meta.domain}</span>
          </div>
        </div>
        {Icon ? (
          <Icon size={16} className="flex-shrink-0 mt-1" style={{ color: accent }} />
        ) : (
          <ExternalLink size={14} className="flex-shrink-0 mt-1" style={{ color: 'var(--text-secondary)' }} />
        )}
      </div>
    </a>
  )
}
