import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import useAuth from '../../hooks/useAuth'
import useTheme from '../../hooks/useTheme'

export default function Header() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/search', label: 'Posts' },
    { to: '/about', label: 'About' },
  ]

  return (
    <header
      className="sticky top-0 z-40 backdrop-blur-md border-b"
      style={{ background: 'var(--bg)', borderColor: 'var(--border)', opacity: 0.98 }}
    >
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold tracking-tight">
          <span className="text-primary-600">blog</span>
          <span style={{ color: 'var(--text)' }}>-jun</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="text-sm font-medium hover:text-primary-600 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              {l.label}
            </Link>
          ))}
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
          <button
            onClick={toggle}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle theme"
          >
            {dark ? '☀️' : '🌙'}
          </button>

          {user ? (
            <button
              onClick={() => { logout(); navigate('/') }}
              className="text-sm px-3 py-1.5 rounded-lg border transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
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
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen
                ? <path d="M6 18L18 6M6 6l12 12" />
                : <path d="M3 12h18M3 6h18M3 18h18" />
              }
            </svg>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.nav
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="md:hidden overflow-hidden border-t"
            style={{ borderColor: 'var(--border)' }}
          >
            <div className="px-4 py-3 space-y-2">
              {navLinks.map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  onClick={() => setMobileOpen(false)}
                  className="block py-2 text-sm"
                >
                  {l.label}
                </Link>
              ))}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
