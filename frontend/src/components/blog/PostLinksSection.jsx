import { Link } from 'react-router-dom'
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react'

export default function PostLinksSection({ outgoingLinks, incomingLinks }) {
  if (!outgoingLinks?.length && !incomingLinks?.length) return null

  return (
    <div className="mt-8 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Outgoing links */}
        {outgoingLinks?.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
              <ArrowUpRight size={14} className="text-primary-600" />
              References ({outgoingLinks.length})
            </h3>
            <ul className="space-y-1.5">
              {outgoingLinks.map((link, i) => (
                <li key={i}>
                  <Link
                    to={`/post/${link.slug}`}
                    className="text-sm text-primary-600 hover:underline"
                  >
                    {link.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Incoming links (backlinks) */}
        {incomingLinks?.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
              <ArrowDownLeft size={14} className="text-primary-600" />
              Backlinks ({incomingLinks.length})
            </h3>
            <ul className="space-y-1.5">
              {incomingLinks.map((link, i) => (
                <li key={i}>
                  <Link
                    to={`/post/${link.slug}`}
                    className="text-sm text-primary-600 hover:underline"
                  >
                    {link.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
