import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronDown, User, Search } from 'lucide-react'
import useAuth from '../../hooks/useAuth'

export default function Header() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()
  const userMenuRef = useRef(null)
  const searchInputRef = useRef(null)

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  useEffect(() => {
    if (searchOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [searchOpen])

  const closeMobile = () => setMobileOpen(false)

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/posts?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
      setSearchOpen(false)
      closeMobile()
    }
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
            to="/posts"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            Posts
          </Link>

          <Link
            to="/architectures/tree"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            Architecture
          </Link>

          <Link
            to="/about"
            className="text-sm font-medium hover:text-primary-600 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            About
          </Link>

          {/* 검색 */}
          <div className="relative">
            {searchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center">
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="검색..."
                  className="w-40 text-sm px-3 py-1 rounded-lg border outline-none focus:border-primary-400"
                  style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
                  onBlur={() => {
                    if (!searchQuery) setSearchOpen(false)
                  }}
                />
              </form>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="p-1.5 rounded-lg hover:text-primary-600 transition-colors"
                style={{ color: 'var(--text-secondary)' }}
                aria-label="Search"
              >
                <Search size={16} />
              </button>
            )}
          </div>
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border transition-colors hover:bg-gray-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <User size={14} />
                {user.username || 'User'}
                <ChevronDown size={12} className={`transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
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
                    <Link to="/dashboard" onClick={() => setUserMenuOpen(false)}
                      className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                      style={{ color: 'var(--text-secondary)' }}>Dashboard</Link>
                    <Link to="/editor" onClick={() => setUserMenuOpen(false)}
                      className="block px-4 py-2.5 text-sm hover:text-primary-600 transition-colors"
                      style={{ color: 'var(--text-secondary)' }}>새 글 작성</Link>
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
            className="md:hidden p-2"
            aria-label="검색"
            onClick={() => setSearchOpen(!searchOpen)}
          >
            <Search size={20} />
          </button>
          <button
            className="md:hidden p-2"
            aria-label="메뉴 열기"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile 검색바 */}
      <AnimatePresence>
        {searchOpen && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="md:hidden overflow-hidden border-t"
            style={{ borderColor: 'var(--border)' }}
          >
            <form onSubmit={handleSearch} className="px-4 py-2">
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색..."
                className="w-full text-sm px-3 py-2 rounded-lg border outline-none focus:border-primary-400"
                style={{ borderColor: 'var(--border)', background: 'var(--card-bg)' }}
              />
            </form>
          </motion.div>
        )}
      </AnimatePresence>

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
                className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                Posts
              </Link>
              <Link to="/architectures/tree" onClick={closeMobile}
                className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                Architecture
              </Link>
              <Link to="/about" onClick={closeMobile}
                className="block py-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                About
              </Link>
              {user && (
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
    </header>
  )
}
