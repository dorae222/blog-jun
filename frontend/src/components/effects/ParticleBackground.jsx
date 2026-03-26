import { useEffect, useRef } from 'react'

export default function ParticleBackground({ count = 50 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animId
    let particles = []

    // Mobile: reduce particle count
    const isMobile = window.innerWidth < 768
    const actualCount = isMobile ? Math.min(count, 25) : count

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio
      canvas.height = canvas.offsetHeight * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }

    const createParticles = () => {
      particles = Array.from({ length: actualCount }, () => ({
        x: Math.random() * canvas.offsetWidth,
        y: Math.random() * canvas.offsetHeight,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        r: Math.random() * 2 + 1,
        opacity: Math.random() * 0.5 + 0.1,
      }))
    }

    const handleResize = () => { resize(); createParticles() }

    let frameCount = 0
    const draw = () => {
      frameCount++
      // Mobile: skip every other frame
      if (isMobile && frameCount % 2 !== 0) {
        animId = requestAnimationFrame(draw)
        return
      }

      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      ctx.clearRect(0, 0, w, h)

      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0 || p.x > w) p.vx *= -1
        if (p.y < 0 || p.y > h) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(59, 130, 246, ${p.opacity})`
        ctx.fill()
      })

      // Grid-based neighbor lookup for connections
      const cellSize = 120
      const grid = {}
      for (let i = 0; i < particles.length; i++) {
        const cx = Math.floor(particles[i].x / cellSize)
        const cy = Math.floor(particles[i].y / cellSize)
        const key = `${cx},${cy}`
        if (!grid[key]) grid[key] = []
        grid[key].push(i)
      }

      for (const key in grid) {
        const [cx, cy] = key.split(',').map(Number)
        const neighbors = []
        for (let dx = -1; dx <= 1; dx++) {
          for (let dy = -1; dy <= 1; dy++) {
            const nk = `${cx + dx},${cy + dy}`
            if (grid[nk]) neighbors.push(...grid[nk])
          }
        }
        for (const i of grid[key]) {
          for (const j of neighbors) {
            if (j <= i) continue
            const ddx = particles[i].x - particles[j].x
            const ddy = particles[i].y - particles[j].y
            const dist = Math.sqrt(ddx * ddx + ddy * ddy)
            if (dist < 120) {
              ctx.beginPath()
              ctx.moveTo(particles[i].x, particles[i].y)
              ctx.lineTo(particles[j].x, particles[j].y)
              ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - dist / 120)})`
              ctx.stroke()
            }
          }
        }
      }

      animId = requestAnimationFrame(draw)
    }

    resize()
    createParticles()
    draw()
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', handleResize)
    }
  }, [count])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 0.6 }}
    />
  )
}
