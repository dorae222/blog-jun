import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronDown, User, Search } from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import SearchModal from '../common/SearchModal'
import Logo from './Logo'

const isMac = typeof navigator !== 'undefined' && navigator.platform?.includes('Mac')

export default function Header() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const userMenuRef = useRef(null)

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  // Cmd+K / Ctrl+K 키보드 단축키
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        // Editor에서는 PostLinkModal용으로 사용하므로 가로채지 않음
        if (location.pathname.startsWith('/editor')) return
        e.preventDefault()
        setSearchModalOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [location.pathname])

  const closeMobile = () => setMobileOpen(false)

  // Explore 허브: Posts(List) / Tree / Index 를 하나로 묶음
  const exploreActive = ['/posts', '/architectures', '/explore'].some((p) =>
    location.pathname.startsWith(p)
  )

  return (
    <header className="sticky top-0 z-40 glass-nav">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="shrink-0" aria-label="HJ Tech 홈">
          <Logo />
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            to="/posts"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{
              color: exploreActive ? 'var(--color-primary-600)' : 'var(--text-secondary)',
              fontWeight: exploreActive ? 600 : 500,
            }}
          >
            Explore
          </Link>

          <Link
            to="/about"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{
              color: location.pathname === '/about' ? 'var(--color-primary-600)' : 'var(--text-secondary)',
              fontWeight: location.pathname === '/about' ? 600 : 500,
            }}
          >
            About
          </Link>

          {/* 검색 버튼 */}
          <button
            onClick={() => setSearchModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm transition-colors hover:bg-gray-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
          >
            <Search size={14} /> 검색
            <kbd className="ml-2 text-[10px] px-1.5 py-0.5 rounded border"
              style={{ borderColor: 'var(--border)' }}>
              {isMac ? '⌘K' : 'Ctrl+K'}
            </kbd>
          </button>
        </nav>

        <div className="flex min-w-0 items-center gap-1 sm:gap-3">
          {user ? (
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex max-w-[3.25rem] sm:max-w-[13rem] items-center gap-1.5 text-sm px-2 sm:px-3 py-1.5 rounded-lg border transition-colors hover:bg-gray-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
                title={user.username || 'User'}
              >
                <User size={14} className="shrink-0" />
                <span className="hidden sm:block truncate">{user.username || 'User'}</span>
                <ChevronDown size={12} className={`shrink-0 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
              </button>
              <AnimatePresence>
                {userMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="absolute right-0 top-full mt-2 w-48 rounded-xl shadow-lg glass-nav overflow-hidden z-50"
                    style={{ border: '1px solid var(--border)' }}
                  >
                    {user.is_staff && (
                      <>
                        <Link to="/dashboard" onClick={() => setUserMenuOpen(false)}
                          className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                          style={{ color: 'var(--text-secondary)' }}>Dashboard</Link>
                        <Link to="/editor" onClick={() => setUserMenuOpen(false)}
                          className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                          style={{ color: 'var(--text-secondary)' }}>새 글 작성</Link>
                      </>
                    )}
                    <div style={{ borderTop: '1px solid var(--border)' }} />
                    <button
                      onClick={() => { logout(); navigate('/'); setUserMenuOpen(false) }}
                      className="block w-full text-left px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors"
                    >
                      Logout
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link
              to="/login"
              className="text-sm px-3 py-1.5 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              Login
            </Link>
          )}

          {/* Mobile: 검색 + 햄버거 */}
          <button
            className="md:hidden p-2 shrink-0"
            aria-label="검색"
            onClick={() => setSearchModalOpen(true)}
          >
            <Search size={20} />
          </button>
          <button
            className="md:hidden p-2 shrink-0"
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
              <Link to="/" onClick={closeMobile}
                className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                Home
              </Link>
              <Link to="/posts" onClick={closeMobile}
                className="block py-2 text-sm"
                style={{ color: exploreActive ? 'var(--color-primary-600)' : 'var(--text-secondary)' }}>
                Explore
              </Link>
              <Link to="/about" onClick={closeMobile}
                className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                About
              </Link>
              {user?.is_staff && (
                <>
                  <Link to="/dashboard" onClick={closeMobile}
                    className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Dashboard
                  </Link>
                  <Link to="/editor" onClick={closeMobile}
                    className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Write
                  </Link>
                </>
              )}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>

      {/* Search Modal */}
      <SearchModal isOpen={searchModalOpen} onClose={() => setSearchModalOpen(false)} />
    </header>
  )
}
