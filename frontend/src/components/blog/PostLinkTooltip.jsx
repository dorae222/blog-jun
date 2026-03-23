import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'

export default function PostLinkTooltip({ href, linkData, children }) {
  const [show, setShow] = useState(false)
  const timeoutRef = useRef(null)

  const handleEnter = () => {
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setShow(true), 300)
  }

  const handleLeave = () => {
    clearTimeout(timeoutRef.current)
    setShow(false)
  }

  if (!linkData) {
    return <Link to={href} className="text-primary-600 hover:underline">{children}</Link>
  }

  return (
    <span className="relative inline" onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      <Link to={href} className="text-primary-600 hover:underline">
        {children}
      </Link>
      {show && (
        <div
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 rounded-xl border shadow-lg z-50 pointer-events-none"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
        >
          <div className="flex gap-3">
            {linkData.cover_image_url && (
              <img
                src={linkData.cover_image_url}
                alt=""
                className="w-16 h-10 rounded object-cover shrink-0"
              />
            )}
            <div className="min-w-0">
              <p className="text-sm font-semibold line-clamp-1" style={{ color: 'var(--text)' }}>
                {linkData.title}
              </p>
              {linkData.summary && (
                <p className="text-xs line-clamp-2 mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {linkData.summary}
                </p>
              )}
              {linkData.category_name && (
                <span
                  className="text-[10px] font-medium px-1.5 py-0.5 rounded mt-1 inline-block"
                  style={{
                    background: `${linkData.category_color || '#6366f1'}15`,
                    color: linkData.category_color || '#6366f1',
                  }}
                >
                  {linkData.category_name}
                </span>
              )}
            </div>
          </div>
          {/* Arrow */}
          <div
            className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 -mt-1"
            style={{
              background: 'var(--card-bg)',
              borderRight: '1px solid var(--border)',
              borderBottom: '1px solid var(--border)',
            }}
          />
        </div>
      )}
    </span>
  )
}
