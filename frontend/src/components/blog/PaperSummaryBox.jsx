import { ExternalLink, BookOpen } from 'lucide-react'

export default function PaperSummaryBox({ post }) {
  const arch = post.architecture_entries?.[0]

  return (
    <div
      className="rounded-xl border p-5 mb-8"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
    >
      <div className="flex items-center gap-2 mb-3">
        <BookOpen size={16} className="text-primary-600" />
        <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          {post.post_type === 'paper_review' ? 'Paper Summary' : 'Architecture Info'}
        </span>
      </div>

      {post.summary && (
        <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>
          {post.summary}
        </p>
      )}

      {arch && (
        <div className="flex flex-wrap gap-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
          {arch.organization && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--card-bg)' }}>
              {arch.organization}
            </span>
          )}
          {arch.param_scale && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--card-bg)' }}>
              {arch.param_scale}
            </span>
          )}
          {arch.decoder_type && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--card-bg)' }}>
              {arch.decoder_type}
            </span>
          )}
          {arch.paper_url && (
            <a
              href={arch.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-primary-600 hover:underline"
            >
              <ExternalLink size={12} /> Paper Link
            </a>
          )}
        </div>
      )}
    </div>
  )
}
