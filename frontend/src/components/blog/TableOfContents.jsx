import { useEffect, useState } from 'react'

export default function TableOfContents({ content }) {
  const [headings, setHeadings] = useState([])
  const [activeId, setActiveId] = useState('')

  useEffect(() => {
    const matches = content.match(/^#{1,3}\s.+$/gm) || []
    const parsed = matches.map((h, i) => {
      const level = h.match(/^#+/)[0].length
      const text = h.replace(/^#+\s/, '')
      const id = text.toLowerCase().replace(/[^a-z0-9가-힣]+/g, '-').replace(/^-|-$/g, '')
      return { id, text, level }
    })
    setHeadings(parsed)
  }, [content])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        })
      },
      { rootMargin: '-80px 0px -80% 0px' }
    )

    headings.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [headings])

  if (headings.length < 2) return null

  return (
    <nav className="sticky top-24 hidden xl:block">
      <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
        Table of Contents
      </h4>
      <ul className="space-y-1 text-sm border-l-2" style={{ borderColor: 'var(--border)' }}>
        {headings.map(({ id, text, level }) => (
          <li key={id} style={{ paddingLeft: `${(level - 1) * 12 + 12}px` }}>
            <a
              href={`#${id}`}
              onClick={(e) => {
                e.preventDefault()
                document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
              }}
              className={`block py-1 transition-colors ${
                activeId === id
                  ? 'text-primary-600 font-medium border-l-2 -ml-[2px] border-primary-600 pl-3'
                  : 'hover:text-primary-600'
              }`}
              style={activeId !== id ? { color: 'var(--text-secondary)' } : {}}
            >
              {text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
