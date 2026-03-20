import { useState, useEffect } from 'react'
import { ExternalLink } from 'lucide-react'

export default function BookmarkEmbed({ url }) {
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!url) return
    // Try to extract basic info from URL
    try {
      const u = new URL(url)
      const domain = u.hostname.replace('www.', '')
      let title = url
      let description = ''

      // arxiv
      if (domain === 'arxiv.org') {
        const id = u.pathname.split('/').pop()
        title = `arXiv: ${id}`
        description = 'View paper on arXiv'
      }
      // github
      else if (domain === 'github.com') {
        const parts = u.pathname.split('/').filter(Boolean)
        title = parts.length >= 2 ? `${parts[0]}/${parts[1]}` : u.pathname
        description = 'GitHub Repository'
      }
      // openai
      else if (domain.includes('openai.com')) {
        title = 'OpenAI'
        description = u.pathname.replace(/\//g, ' ').trim() || 'OpenAI Research'
      }
      // huggingface
      else if (domain.includes('huggingface.co')) {
        title = 'Hugging Face'
        description = u.pathname.replace(/\//g, ' ').trim() || 'Model Hub'
      }
      // generic
      else {
        title = domain
        description = u.pathname.length > 1 ? u.pathname : ''
      }

      setMeta({ title, description, domain, favicon: `https://www.google.com/s2/favicons?domain=${domain}&sz=32` })
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

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border overflow-hidden transition-shadow hover:shadow-md"
      style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}
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
        <ExternalLink size={14} className="flex-shrink-0 mt-1" style={{ color: 'var(--text-secondary)' }} />
      </div>
    </a>
  )
}
