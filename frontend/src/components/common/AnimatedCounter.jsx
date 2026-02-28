import { useEffect, useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'

export default function AnimatedCounter({ end, duration = 2, label, icon }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!inView) return
    let start = 0
    const step = end / (duration * 60)
    const timer = setInterval(() => {
      start += step
      if (start >= end) {
        setCount(end)
        clearInterval(timer)
      } else {
        setCount(Math.floor(start))
      }
    }, 1000 / 60)
    return () => clearInterval(timer)
  }, [inView, end, duration])

  return (
    <motion.div
      ref={ref}
      className="text-center p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5 }}
    >
      {icon && <div className="flex justify-center mb-2 text-primary-600">{icon}</div>}
      <div className="text-4xl font-bold text-primary-600">{count.toLocaleString()}</div>
      <div className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{label}</div>
    </motion.div>
  )
}
