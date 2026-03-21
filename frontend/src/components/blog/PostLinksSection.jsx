import { Link } from 'react-router-dom'
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react'

function LinkCard({ link, direction }) {
  const Icon = direction === 'out' ? ArrowUpRight : ArrowDownLeft

  return (
    <Link
      to={`/post/${link.slug}`}
      className="flex items-start gap-2.5 p-3 rounded-lg border transition-all
        hover:shadow-sm hover:-translate-y-0.5"
      style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
    >
      <Icon size={14} className="text-primary-600 mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
          {link.title}
        </p>
        {link.category_name && (
          <span
            className="text-[10px] font-medium px-1.5 py-0.5 rounded mt-1 inline-block"
            style={{ background: `${link.category_color || '#6366f1'}15`, color: link.category_color || '#6366f1' }}
          >
            {link.category_name}
          </span>
        )}
      </div>
    </Link>
  )
}

export default function PostLinksSection({ outgoingLinks, incomingLinks }) {
  if (!outgoingLinks?.length && !incomingLinks?.length) return null

  return (
    <div className="mt-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Outgoing links */}
        {outgoingLinks?.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
              <ArrowUpRight size={14} className="text-primary-600" />
              References ({outgoingLinks.length})
            </h3>
            <div className="space-y-2">
              {outgoingLinks.map((link, i) => (
                <LinkCard key={i} link={link} direction="out" />
              ))}
            </div>
          </div>
        )}

        {/* Incoming links (backlinks) */}
        {incomingLinks?.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
              <ArrowDownLeft size={14} className="text-primary-600" />
              Backlinks ({incomingLinks.length})
            </h3>
            <div className="space-y-2">
              {incomingLinks.map((link, i) => (
                <LinkCard key={i} link={link} direction="in" />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
