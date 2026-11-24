import { lazy, Suspense, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, X } from 'lucide-react'

// 패널(마크다운 렌더러 포함)은 처음 열 때 불러온다. 첫 화면 번들을 키우지 않으려고.
const ChatModal = lazy(() => import('../chatbot/ChatModal'))

// 관리·작성 화면에서는 숨긴다(작성 중 화면을 가리지 않게).
const HIDDEN_PREFIXES = ['/editor', '/dashboard', '/notes', '/login', '/auth']

export default function ChatFAB() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  const btnRef = useRef(null)

  if (import.meta.env.VITE_CHAT_DISABLED === '1') return null
  if (HIDDEN_PREFIXES.some((p) => pathname.startsWith(p))) return null

  return (
    <>
      <motion.button
        ref={btnRef}
        onClick={() => setOpen((v) => !v)}
        className={`fixed bottom-6 left-6 z-40 w-14 h-14 rounded-full bg-accent text-white shadow-lg flex items-center justify-center ${open ? 'hidden sm:flex' : ''}`}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        aria-label={open ? '챗봇 닫기' : '챗봇 열기'}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        {open ? <X size={24} /> : <MessageSquare size={24} />}
      </motion.button>

      <AnimatePresence>
        {open && (
          <Suspense fallback={null}>
            <ChatModal onClose={() => setOpen(false)} />
          </Suspense>
        )}
      </AnimatePresence>
    </>
  )
}
