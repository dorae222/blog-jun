import { useEffect, useState } from 'react'

export default function GradientCursor() {
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const move = (e) => {
      setPos({ x: e.clientX, y: e.clientY })
      setVisible(true)
    }
    const leave = () => setVisible(false)

    window.addEventListener('mousemove', move)
    window.addEventListener('mouseleave', leave)
    return () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseleave', leave)
    }
  }, [])

  if (!visible) return null

  return (
    <div
      className="fixed pointer-events-none z-50 mix-blend-screen"
      style={{
        left: pos.x - 150,
        top: pos.y - 150,
        width: 300,
        height: 300,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.15), rgba(59,130,246,0.1), transparent 70%)',
        transition: 'left 0.1s ease, top 0.1s ease',
      }}
    />
  )
}
