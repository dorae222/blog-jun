import { useEffect, useRef } from 'react'
import { useMotionValue, useSpring, useReducedMotion } from 'framer-motion'

/**
 * useMagnetic — 커서가 요소 근처에 오면 요소를 커서 쪽으로 살짝 끌어당긴다.
 * 벗어나면 스프링으로 원위치. prefers-reduced-motion이면 리스너를 붙이지 않아 정지.
 *
 * @param {object}  opts
 * @param {number}  opts.strength  끌림 강도(0~1). 커서까지 거리 * strength 만큼 이동.
 * @param {number}  opts.radius    요소 경계 바깥으로 얼마나 넓게 반응할지(px).
 * @returns {{ ref, style }} ref는 감쌀 motion 요소에, style은 그 요소의 style로 전달.
 */
export default function useMagnetic({ strength = 0.35, radius = 70 } = {}) {
  const ref = useRef(null)
  const reduce = useReducedMotion()

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const spring = { stiffness: 220, damping: 16, mass: 0.5 }
  const springX = useSpring(x, spring)
  const springY = useSpring(y, spring)

  useEffect(() => {
    const el = ref.current
    if (reduce || !el) return

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height / 2
      const dx = e.clientX - cx
      const dy = e.clientY - cy
      const zone = radius + Math.max(rect.width, rect.height) / 2

      if (Math.hypot(dx, dy) < zone) {
        x.set(dx * strength)
        y.set(dy * strength)
      } else {
        x.set(0)
        y.set(0)
      }
    }
    const reset = () => { x.set(0); y.set(0) }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseleave', reset)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseleave', reset)
    }
  }, [reduce, strength, radius, x, y])

  return { ref, style: { x: springX, y: springY } }
}
