import useTheme from '../../hooks/useTheme'
import { motion } from 'framer-motion'

export default function ThemeToggle() {
  const { dark, toggle } = useTheme()

  return (
    <button
      onClick={toggle}
      className="relative w-14 h-7 rounded-full transition-colors"
      style={{ background: dark ? '#334155' : '#e2e8f0' }}
      aria-label="Toggle theme"
    >
      <motion.div
        className="absolute top-0.5 w-6 h-6 rounded-full bg-white shadow flex items-center justify-center text-sm"
        animate={{ left: dark ? '30px' : '2px' }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        {dark ? '🌙' : '☀️'}
      </motion.div>
    </button>
  )
}
