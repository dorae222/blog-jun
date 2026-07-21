import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { lazy, Suspense, useEffect } from 'react'

import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ScrollToTop from './components/layout/ScrollToTop'
import ErrorBoundary from './components/common/ErrorBoundary'
import useAuth from './hooks/useAuth'

import Home from './pages/Home'
import PostView from './pages/PostView'
import PostsPage from './pages/PostsPage'
import About from './pages/About'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import NotFound from './pages/NotFound'

const Editor = lazy(() => import('./pages/Editor'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const ArchitectureTreePage = lazy(() => import('./pages/ArchitectureTreePage'))
const SiteIndexPage = lazy(() => import('./pages/SiteIndexPage'))

export default function App() {
  const location = useLocation()
  const initAuth = useAuth((s) => s.init)

  useEffect(() => {
    initAuth()
  }, [initAuth])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:rounded-lg focus:bg-primary-600 focus:text-white focus:text-sm">
        본문으로 건너뛰기
      </a>
      <Header />
      <main id="main-content" className="flex-1">
        <ErrorBoundary>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/posts" element={<PostsPage />} />
            <Route path="/posts/:category" element={<PostsPage />} />
            <Route path="/posts/:category/:sub" element={<PostsPage />} />
            <Route path="/post/:slug" element={<PostView />} />
            <Route path="/about" element={<About />} />
            <Route path="/editor" element={<Suspense fallback={<div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>}><Editor /></Suspense>} />
            <Route path="/editor/:slug" element={<Suspense fallback={<div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>}><Editor /></Suspense>} />
            <Route path="/dashboard" element={<Suspense fallback={<div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>}><Dashboard /></Suspense>} />
            <Route path="/login" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/architectures/tree" element={<Suspense fallback={<div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>}><ArchitectureTreePage /></Suspense>} />
            <Route path="/explore/index" element={<Suspense fallback={<div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>}><SiteIndexPage /></Suspense>} />
            {/* 레거시 경로 리다이렉트 */}
            <Route path="/explore" element={<Navigate to="/posts" replace />} />
            <Route path="/search" element={<Navigate to="/posts" replace />} />
            <Route path="/architectures" element={<Navigate to="/architectures/tree" replace />} />
            <Route path="/architectures/:slug" element={<Navigate to="/architectures/tree" replace />} />
            <Route path="/papers" element={<Navigate to="/posts" replace />} />
            <Route path="/category/:slug" element={<Navigate to="/posts" replace />} />
            <Route path="/series/:slug" element={<Navigate to="/posts" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AnimatePresence>
        </ErrorBoundary>
      </main>
      <Footer />
      <ScrollToTop />
      <Toaster position="bottom-right" />
    </div>
  )
}
