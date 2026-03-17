import { useState } from 'react'
import { Video, ExternalLink, X } from 'lucide-react'

/**
 * YouTube / Vimeo URL을 iframe embed로 변환하는 유틸리티
 */
export function parseVideoUrl(url) {
  // YouTube
  const ytMatch = url.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/
  )
  if (ytMatch) {
    return {
      provider: 'youtube',
      id: ytMatch[1],
      embedUrl: `https://www.youtube-nocookie.com/embed/${ytMatch[1]}`,
    }
  }

  // Vimeo
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/)
  if (vimeoMatch) {
    return {
      provider: 'vimeo',
      id: vimeoMatch[1],
      embedUrl: `https://player.vimeo.com/video/${vimeoMatch[1]}`,
    }
  }

  return null
}

export default function EmbedBlock({ onEmbed, onClose }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    const parsed = parseVideoUrl(url.trim())
    if (!parsed) {
      setError('YouTube 또는 Vimeo URL을 입력해주세요')
      return
    }
    setPreview(parsed)
  }

  const handleInsert = () => {
    if (preview) {
      onEmbed(preview)
    }
  }

  return (
    <div
      className="rounded-lg border p-4"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Video size={18} style={{ color: 'var(--text-secondary)' }} />
          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            비디오 임베드
          </span>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-200">
            <X size={16} style={{ color: 'var(--text-secondary)' }} />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={url}
          onChange={e => { setUrl(e.target.value); setError('') }}
          placeholder="YouTube or Vimeo URL..."
          className="flex-1 px-3 py-1.5 rounded border text-sm outline-none"
          style={{
            background: 'var(--bg)',
            borderColor: 'var(--border)',
            color: 'var(--text)',
          }}
        />
        <button
          type="submit"
          className="px-3 py-1.5 rounded text-sm bg-primary-600 text-white hover:bg-primary-700 transition-colors"
        >
          Preview
        </button>
      </form>

      {error && (
        <p className="text-xs mt-2 text-red-500">{error}</p>
      )}

      {preview && (
        <div className="mt-3">
          <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
            <iframe
              src={preview.embedUrl}
              className="absolute inset-0 w-full h-full rounded"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
          <button
            onClick={handleInsert}
            className="mt-2 flex items-center gap-1 px-3 py-1.5 rounded text-sm bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            <ExternalLink size={14} />
            Insert
          </button>
        </div>
      )}
    </div>
  )
}
