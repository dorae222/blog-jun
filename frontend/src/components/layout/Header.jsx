import { Link, useNavigate } from 'react-router-dom'
import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronDown } from 'lucide-react'
import useAuth from '../../hooks/useAuth'

const dropdownVariants = {
  hidden: { opacity: 0, y: -8, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, y: -8, scale: 0.97, transition: { duration: 0.1 } },
}

// Posts 드롭다운 아이템
const postsDropdown = [
  { to: '/papers', label: '📄 Papers' },
  { to: '/architecture', label: '🏗️ Architecture' },
  { to: '/category/ai-ml', label: '🤖 AI' },
  { to: '/category/data-engineering', label: '📊 Data Engineering' },
]

export default function Header() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobilePostsOpen, setMobilePostsOpen] = useState(false)
  const [postsHover, setPostsHover] = useState(false)
  const postsTimer = useRef(null)
  const navigate = useNavigate()

  const handlePostsEnter = () => {
    clearTimeout(postsTimer.current)
    setPostsHover(true)
  }
  const handlePostsLeave = () => {
    postsTimer.current = setTimeout(() => setPostsHover(false), 120)
  }

  return (
    <header className="sticky top-0 z-40 glass-nav">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold tracking-tight">
          <span className="text-primary-600">HJ</span>
          <span style={{ color: 'var(--text)' }}> Tech</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            to="/"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            Home
          </Link>

          {/* Posts 드롭다운 */}
          <div
            className="relative"
            onMouseEnter={handlePostsEnter}
            onMouseLeave={handlePostsLeave}
          >
            <button
              className="flex items-center gap-1 text-sm font-medium hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              Posts
              <ChevronDown size={14} className={`transition-transform ${postsHover ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
              {postsHover && (
                <motion.div
                  variants={dropdownVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="absolute top-full left-0 mt-1 w-52 rounded-xl border shadow-lg overflow-visible"
                  style={{
                    background: 'var(--bg)',
                    borderColor: 'var(--border)',
                  }}
                >
                  {postsDropdown.map((item) => (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setPostsHover(false)}
                      className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {item.label}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <Link
            to="/about"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            About
          </Link>

          {user && (
            <>
              <Link to="/dashboard" className="text-sm font-medium hover:text-primary-600 transition-colors" style={{ color: 'var(--text-secondary)' }}>
                Dashboard
              </Link>
              <Link to="/editor" className="text-sm font-medium hover:text-primary-600 transition-colors" style={{ color: 'var(--text-secondary)' }}>
                Write
              </Link>
            </>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <button
              onClick={() => { logout(); navigate('/') }}
              className="text-sm px-3 py-1.5 rounded-lg border transition-colors hover:bg-gray-50"
              style={{ borderColor: 'var(--border)' }}
            >
              Logout
            </button>
          ) : (
            <Link
              to="/login"
              className="text-sm px-3 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              Login
            </Link>
          )}

          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.nav
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="md:hidden overflow-hidden border-t"
            style={{ borderColor: 'var(--border)' }}
          >
            <div className="px-4 py-3 space-y-1">
              <Link
                to="/"
                onClick={() => setMobileOpen(false)}
                className="block py-2 text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                Home
              </Link>

              {/* Posts 아코디언 */}
              <div>
                <button
                  onClick={() => setMobilePostsOpen(!mobilePostsOpen)}
                  className="flex items-center justify-between w-full py-2 text-sm"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  Posts
                  <ChevronDown
                    size={14}
                    className={`transition-transform ${mobilePostsOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                <AnimatePresence>
                  {mobilePostsOpen && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      className="overflow-hidden pl-4"
                    >
                      {postsDropdown.map((item) => (
                        <Link
                          key={item.to}
                          to={item.to}
                          onClick={() => setMobileOpen(false)}
                          className="block py-2 text-sm"
                          style={{ color: 'var(--text-secondary)' }}
                        >
                          {item.label}
                        </Link>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <Link
                to="/about"
                onClick={() => setMobileOpen(false)}
                className="block py-2 text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                About
              </Link>

              {user && (
                <>
                  <Link
                    to="/dashboard"
                    onClick={() => setMobileOpen(false)}
                    className="block py-2 text-sm"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/editor"
                    onClick={() => setMobileOpen(false)}
                    className="block py-2 text-sm"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    Write
                  </Link>
                </>
              )}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
