import { Suspense, lazy } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'

import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ScrollToTop from './components/layout/ScrollToTop'
import ChatFAB from './components/layout/ChatFAB'

const Home = lazy(() => import('./pages/Home'))
const PostView = lazy(() => import('./pages/PostView'))
const CategoryPage = lazy(() => import('./pages/CategoryPage'))
const SeriesPage = lazy(() => import('./pages/SeriesPage'))
const SearchPage = lazy(() => import('./pages/SearchPage'))
const About = lazy(() => import('./pages/About'))
const Editor = lazy(() => import('./pages/Editor'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Login = lazy(() => import('./pages/Login'))

function PageFallback() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <div className="h-6 w-40 animate-pulse rounded" style={{ background: 'var(--bg-secondary)' }} />
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((item) => (
          <div key={item} className="h-40 animate-pulse rounded-lg" style={{ background: 'var(--bg-secondary)' }} />
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      <Header />
      <main className="flex-1">
        <AnimatePresence mode="wait">
          <Suspense fallback={<PageFallback />}>
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<Home />} />
              <Route path="/post/:slug" element={<PostView />} />
              <Route path="/category/:slug" element={<CategoryPage />} />
              <Route path="/series/:slug" element={<SeriesPage />} />
              <Route path="/posts" element={<SearchPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/about" element={<About />} />
              <Route path="/editor" element={<Editor />} />
              <Route path="/editor/:slug" element={<Editor />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/login" element={<Login />} />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </main>
      <Footer />
      <ScrollToTop />
      <ChatFAB />
      <Toaster position="bottom-right" />
    </div>
  )
}
