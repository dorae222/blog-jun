import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'

import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import ScrollToTop from './components/layout/ScrollToTop'
import ChatFAB from './components/layout/ChatFAB'

import Home from './pages/Home'
import PostView from './pages/PostView'
import CategoryPage from './pages/CategoryPage'
import SeriesPage from './pages/SeriesPage'
import SearchPage from './pages/SearchPage'
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
            <Route path="/post/:slug" element={<PostView />} />
            <Route path="/category/:slug" element={<CategoryPage />} />
            <Route path="/series/:slug" element={<SeriesPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/editor" element={<Editor />} />
            <Route path="/editor/:slug" element={<Editor />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
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
