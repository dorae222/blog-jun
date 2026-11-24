import { useEffect, useRef } from 'react'

const FOCUSABLE = [
  'a[href]', 'button:not([disabled])', 'textarea:not([disabled])', 'input:not([disabled])',
  'select:not([disabled])', '[tabindex]:not([tabindex="-1"])',
].join(',')

/**
 * 모달 안에서 Tab 포커스가 밖으로 새지 않게 하고, ESC로 닫는다.
 * 닫히면 열기 전에 포커스가 있던 요소(보통 여는 버튼)로 포커스를 돌려준다.
 */
export default function useFocusTrap(containerRef, active, onEscape) {
  const escRef = useRef(onEscape)
  useEffect(() => { escRef.current = onEscape }, [onEscape])

  useEffect(() => {
    if (!active) return
    const prev = document.activeElement
    const node = containerRef.current

    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        escRef.current?.()
        return
      }
      if (e.key !== 'Tab' || !node) return
      const items = [...node.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null)
      if (!items.length) { e.preventDefault(); return }
      const first = items[0]
      const last = items[items.length - 1]
      if (e.shiftKey && (document.activeElement === first || !node.contains(document.activeElement))) {
        e.preventDefault(); last.focus()
      } else if (!e.shiftKey && (document.activeElement === last || !node.contains(document.activeElement))) {
        e.preventDefault(); first.focus()
      }
    }
    document.addEventListener('keydown', onKey, true)
    return () => {
      document.removeEventListener('keydown', onKey, true)
      if (prev && typeof prev.focus === 'function' && document.contains(prev)) prev.focus()
    }
  }, [active, containerRef])
}
