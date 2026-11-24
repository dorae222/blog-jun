import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * 본문 헤딩 목차.
 * - 원본 마크다운이 아니라 **렌더된 DOM의 헤딩**을 읽는다. rehype-slug가 만든 id를 그대로
 *   쓰므로 클릭 이동이 항상 맞고, 콜아웃 안에 들어간 헤딩도 빠짐없이 잡힌다.
 * - 스크롤을 따라 현재 위치를 추적하고, 목차가 길면 목차 자체가 따라 움직인다.
 * - 왼쪽 게이지가 읽은 만큼 차오른다(상단 진행바는 중복이라 제거했다).
 * 부모에 overflow:hidden이 있으면 sticky가 죽으므로 PostView는 overflow-x:clip을 쓴다.
 */
export default function TableOfContents({ content, onNavigate, containerSelector = '.prose' }) {
  const [headings, setHeadings] = useState([])
  const [activeId, setActiveId] = useState('')
  const navRef = useRef(null)
  const itemRefs = useRef({})

  // 렌더가 끝난 뒤 DOM에서 헤딩을 수집한다(본문이 바뀌면 다시).
  useEffect(() => {
    let raf = 0
    let tries = 0

    const collect = () => {
      const root = document.querySelector(containerSelector) || document.querySelector('article')
      if (!root) return false
      const found = [...root.querySelectorAll('h1, h2, h3')]
        .filter((el) => el.id && el.textContent.trim())
        .map((el) => ({
          id: el.id,
          text: el.textContent.trim(),
          level: Number(el.tagName[1]),
        }))
      if (found.length) {
        setHeadings(found)
        return true
      }
      return false
    }

    const tick = () => {
      if (collect() || tries++ > 40) return
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [content, containerSelector])

  // 화면 상단을 지난 마지막 헤딩이 현재 위치
  useEffect(() => {
    if (!headings.length) return
    let ticking = false

    const update = () => {
      ticking = false
      const OFFSET = 120
      let current = ''
      for (const { id } of headings) {
        const el = document.getElementById(id)
        if (!el) continue
        if (el.getBoundingClientRect().top <= OFFSET) current = id
        else break
      }
      if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
        current = headings[headings.length - 1].id
      }
      setActiveId((prev) => (prev === current ? prev : current))
    }

    const onScroll = () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update) }
    }

    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
    }
  }, [headings])

  // 활성 항목이 목차 밖으로 나가면 목차를 그만큼만 굴린다
  useEffect(() => {
    const nav = navRef.current
    const item = itemRefs.current[activeId]
    if (!nav || !item) return
    const navBox = nav.getBoundingClientRect()
    const itemBox = item.getBoundingClientRect()
    if (itemBox.top < navBox.top + 8) {
      nav.scrollBy({ top: itemBox.top - navBox.top - 48, behavior: 'smooth' })
    } else if (itemBox.bottom > navBox.bottom - 8) {
      nav.scrollBy({ top: itemBox.bottom - navBox.bottom + 48, behavior: 'smooth' })
    }
  }, [activeId])

  const go = useCallback((id) => {
    const el = document.getElementById(id)
    if (!el) return
    const top = el.getBoundingClientRect().top + window.scrollY - 88
    window.scrollTo({ top, behavior: 'smooth' })
    setActiveId(id)
    onNavigate?.()
  }, [onNavigate])

  if (headings.length < 2) return null

  const activeIndex = headings.findIndex((h) => h.id === activeId)
  const progress = activeIndex < 0 ? 0 : ((activeIndex + 1) / headings.length) * 100

  return (
    <nav
      ref={navRef}
      className="sticky top-24 overflow-y-auto overscroll-contain pr-1"
      style={{ maxHeight: 'calc(100vh - 8rem)', scrollbarWidth: 'thin' }}
    >
      <h4 className="text-xs font-semibold mb-3 tracking-wide uppercase"
        style={{ color: 'var(--text-secondary)' }}>
        목차
      </h4>

      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-[2px] rounded"
          style={{ background: 'var(--border)' }} />
        <div className="absolute left-0 top-0 w-[2px] rounded transition-all duration-300"
          style={{ height: `${progress}%`, background: 'var(--color-primary-500, #3b82f6)' }} />

        <ul className="space-y-0.5 text-sm">
          {headings.map(({ id, text, level }) => {
            const active = activeId === id
            return (
              <li key={id} style={{ paddingLeft: `${(level - 1) * 12 + 14}px` }}>
                <a
                  href={`#${id}`}
                  ref={(el) => { itemRefs.current[id] = el }}
                  onClick={(e) => { e.preventDefault(); go(id) }}
                  className="block py-1.5 leading-snug transition-colors hover:text-primary-600"
                  style={{
                    color: active ? 'var(--color-primary-500, #3b82f6)' : 'var(--text-secondary)',
                    fontWeight: active ? 600 : 400,
                    fontSize: level === 1 ? '0.875rem' : level === 2 ? '0.83rem' : '0.8rem',
                  }}
                >
                  {text}
                </a>
              </li>
            )
          })}
        </ul>
      </div>
    </nav>
  )
}
