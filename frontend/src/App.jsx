import { Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import toast, { Toaster } from 'react-hot-toast'
import { lazy, Suspense, useEffect } from 'react'

import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ScrollToTop from './components/layout/ScrollToTop'
import ErrorBoundary from './components/common/ErrorBoundary'
import StaffRoute from './components/common/StaffRoute'
import ChatFAB from './components/layout/ChatFAB'
import QuickNoteModal from './components/notes/QuickNoteModal'
import DialogHost from './components/common/DialogHost'
import useWorkspaceHotkeys from './hooks/useWorkspaceHotkeys'
import useAuth from './hooks/useAuth'

import Home from './pages/Home'
import PostView from './pages/PostView'
import PostsPage from './pages/PostsPage'
import About from './pages/About'
import SeriesPage from './pages/SeriesPage'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import NotFound from './pages/NotFound'

const Editor = lazy(() => import('./pages/Editor'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const ArchitectureTreePage = lazy(() => import('./pages/ArchitectureTreePage'))
const SiteIndexPage = lazy(() => import('./pages/SiteIndexPage'))
const Notes = lazy(() => import('./pages/Notes'))

const PageLoading = () => (
  <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>Loading...</div>
)

/**
 * 라우트 전환 애니메이션 키. 편집기는 /editor → /editor/:slug 로 주소만 바뀌는 경우가 있어서
 * (새 글을 처음 저장할 때) 같은 키를 줘서 다시 그리지 않는다. 다시 그리면 쓰던 내용이 날아간다.
 */
const routeKey = (pathname) => (pathname.startsWith('/editor') ? '/editor' : pathname)
const isWorkspaceRoute = (pathname) => pathname.startsWith('/editor') || pathname.startsWith('/notes')

/**
 * `/series/<슬러그>`로 들어온 것을 그 시리즈 화면으로 넘긴다.
 *
 * 시리즈 화면은 `?s=<슬러그>`로 어느 시리즈를 펼칠지 정한다. 그런데 예전에는
 * `/series/:slug`가 `/posts`로 리다이렉트돼 있어서, 본문의 시리즈 배지나
 * 사이드바에서 시리즈를 누르면 전체 글 목록으로 튕겼다.
 */
function SeriesSlugRedirect() {
  const { slug } = useParams()
  return <Navigate to={`/series?s=${encodeURIComponent(slug)}`} replace />
}

export default function App() {
  // 서버 요청 한도에 걸리면 조용히 빈 화면이 되지 않도록 알린다.
  useEffect(() => {
    const on = (e) => toast.error(`요청이 많아 잠시 제한되었습니다. ${e.detail || ''}`, { id: 'throttled' })
    window.addEventListener('api:throttled', on)
    return () => window.removeEventListener('api:throttled', on)
  }, [])

  const location = useLocation()
  const initAuth = useAuth((s) => s.init)
  useWorkspaceHotkeys()

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
          <Routes location={location} key={routeKey(location.pathname)}>
            <Route path="/" element={<Home />} />
            <Route path="/posts" element={<PostsPage />} />
            <Route path="/posts/:category" element={<PostsPage />} />
            <Route path="/posts/:category/:sub" element={<PostsPage />} />
            <Route path="/post/:slug" element={<PostView />} />
            <Route path="/series" element={<SeriesPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/editor" element={<StaffRoute><Suspense fallback={<PageLoading />}><Editor /></Suspense></StaffRoute>} />
            <Route path="/editor/:slug" element={<StaffRoute><Suspense fallback={<PageLoading />}><Editor /></Suspense></StaffRoute>} />
            <Route path="/notes" element={<StaffRoute><Suspense fallback={<PageLoading />}><Notes /></Suspense></StaffRoute>} />
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
            <Route path="/series/:slug" element={<SeriesSlugRedirect />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AnimatePresence>
        </ErrorBoundary>
      </main>
      {/* 작성·메모 화면은 앱처럼 화면 높이를 꽉 채우므로 바닥글을 붙이지 않는다 */}
      {!isWorkspaceRoute(location.pathname) && <Footer />}
      <ScrollToTop />
      <ChatFAB />
      <QuickNoteModal />
      <DialogHost />
      <Toaster position="bottom-right" />
    </div>
  )
}
