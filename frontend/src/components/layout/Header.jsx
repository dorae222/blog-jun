import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronDown } from 'lucide-react'
import useAuth from '../../hooks/useAuth'

const POSTS_MENU = [
  { label: 'Papers',       to: '/search?type=paper_review' },
  { label: 'Architecture', to: '/search?type=architecture' },
  { label: 'Articles',     to: '/search?type=article' },
  { label: 'TIL',          to: '/search?type=til' },
  { label: 'All Posts',    to: '/search' },
]

export default function Header() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobilePostsOpen, setMobilePostsOpen] = useState(false)
  const [desktopDropdownOpen, setDesktopDropdownOpen] = useState(false)
  const navigate = useNavigate()
  const hoverTimeout = useRef(null)

  // 모바일 메뉴 열릴 때 배경 스크롤 잠금
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  const closeMobile = () => {
    setMobileOpen(false)
    setMobilePostsOpen(false)
  }

  const handlePostsMouseEnter = () => {
    clearTimeout(hoverTimeout.current)
    setDesktopDropdownOpen(true)
  }

  const handlePostsMouseLeave = () => {
    hoverTimeout.current = setTimeout(() => setDesktopDropdownOpen(false), 150)
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
            onMouseEnter={handlePostsMouseEnter}
            onMouseLeave={handlePostsMouseLeave}
          >
            <button
              className="flex items-center gap-1 text-sm font-medium hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              Posts
              <ChevronDown
                size={14}
                className={`transition-transform duration-200 ${desktopDropdownOpen ? 'rotate-180' : ''}`}
              />
            </button>

            <AnimatePresence>
              {desktopDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                  className="absolute top-full left-0 mt-2 w-44 rounded-xl shadow-lg glass-nav overflow-hidden"
                  style={{ border: '1px solid var(--border)' }}
                  onMouseEnter={handlePostsMouseEnter}
                  onMouseLeave={handlePostsMouseLeave}
                >
                  {POSTS_MENU.map((item) => (
                    <Link
                      key={item.to}
                      to={item.to}
                      className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                      style={{ color: 'var(--text-secondary)' }}
                      onClick={() => setDesktopDropdownOpen(false)}
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
            aria-label="메뉴 열기"
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
            <div className="px-4 py-3 space-y-1 max-h-[80vh] overflow-y-auto">
              <Link
                to="/"
                onClick={closeMobile}
                className="block py-2 text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                Home
              </Link>

              {/* Posts 아코디언 */}
              <div>
                <button
                  className="flex items-center gap-1 w-full py-2 text-sm text-left"
                  style={{ color: 'var(--text-secondary)' }}
                  onClick={() => setMobilePostsOpen(!mobilePostsOpen)}
                >
                  Posts
                  <ChevronDown
                    size={14}
                    className={`ml-auto transition-transform duration-200 ${mobilePostsOpen ? 'rotate-180' : ''}`}
                  />
                </button>
                <AnimatePresence>
                  {mobilePostsOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden pl-4"
                    >
                      {POSTS_MENU.map((item) => (
                        <Link
                          key={item.to}
                          to={item.to}
                          onClick={closeMobile}
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
                onClick={closeMobile}
                className="block py-2 text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                About
              </Link>

              {user && (
                <>
                  <Link
                    to="/dashboard"
                    onClick={closeMobile}
                    className="block py-2 text-sm"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/editor"
                    onClick={closeMobile}
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
