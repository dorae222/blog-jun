import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function NotFound() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="flex items-center justify-center min-h-[60vh] px-4"
    >
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4" style={{ color: 'var(--text-secondary)' }}>404</h1>
        <p className="text-lg mb-6" style={{ color: 'var(--text-secondary)' }}>
          페이지를 찾을 수 없습니다
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          홈으로 돌아가기
        </Link>
      </div>
    </motion.div>
  )
}
