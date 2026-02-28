import { useEffect, useState } from 'react'

export default function ReadingProgress() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const onScroll = () => {
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      setProgress(docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="fixed top-16 left-0 right-0 z-30 h-1 bg-transparent">
      <div
        className="h-full bg-gradient-to-r from-primary-500 to-accent transition-all duration-150"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}
