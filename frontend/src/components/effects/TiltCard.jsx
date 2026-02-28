import { useRef, useState } from 'react'
import { motion } from 'framer-motion'

export default function TiltCard({ children, className = '', glowColor = 'rgba(59,130,246,0.3)' }) {
  const ref = useRef(null)
  const [transform, setTransform] = useState('')
  const [glowPos, setGlowPos] = useState({ x: 50, y: 50 })

  const handleMouseMove = (e) => {
    const rect = ref.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    const rotateX = (y - 0.5) * -10
    const rotateY = (x - 0.5) * 10
    setTransform(`perspective(600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`)
    setGlowPos({ x: x * 100, y: y * 100 })
  }

  const handleMouseLeave = () => {
    setTransform('')
    setGlowPos({ x: 50, y: 50 })
  }

  return (
    <motion.div
      ref={ref}
      className={`relative overflow-hidden rounded-2xl transition-shadow duration-300 ${className}`}
      style={{
        transform,
        transition: transform ? 'none' : 'transform 0.5s ease',
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileHover={{ boxShadow: `0 20px 40px -12px ${glowColor}` }}
    >
      <div
        className="absolute inset-0 pointer-events-none opacity-0 hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `radial-gradient(circle at ${glowPos.x}% ${glowPos.y}%, ${glowColor}, transparent 60%)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </motion.div>
  )
}
