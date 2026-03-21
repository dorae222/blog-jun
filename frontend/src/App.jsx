import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'

import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ScrollToTop from './components/layout/ScrollToTop'
import ChatFAB from './components/layout/ChatFAB'

import Home from './pages/Home'
import PostView from './pages/PostView'
import PostsPage from './pages/PostsPage'
import About from './pages/About'
import Editor from './pages/Editor'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'

export default function App() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      <Header />
      <main className="flex-1">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/posts" element={<PostsPage />} />
            <Route path="/posts/:category" element={<PostsPage />} />
            <Route path="/posts/:category/:sub" element={<PostsPage />} />
            <Route path="/post/:slug" element={<PostView />} />
            <Route path="/about" element={<About />} />
            <Route path="/editor" element={<Editor />} />
            <Route path="/editor/:slug" element={<Editor />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
            {/* 레거시 경로 리다이렉트 */}
            <Route path="/explore" element={<Navigate to="/posts" replace />} />
            <Route path="/search" element={<Navigate to="/posts" replace />} />
            <Route path="/architectures" element={<Navigate to="/posts/ai" replace />} />
            <Route path="/architectures/tree" element={<Navigate to="/posts/ai" replace />} />
            <Route path="/architectures/:slug" element={<Navigate to="/posts/ai" replace />} />
            <Route path="/papers" element={<Navigate to="/posts" replace />} />
            <Route path="/category/:slug" element={<Navigate to="/posts" replace />} />
            <Route path="/series/:slug" element={<Navigate to="/posts" replace />} />
          </Routes>
        </AnimatePresence>
      </main>
      <Footer />
      <ScrollToTop />
      <ChatFAB />
      <Toaster position="bottom-right" />
    </div>
  )
}
