import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ChatModal from '../chatbot/ChatModal'

export default function ChatFAB() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <motion.button
        onClick={() => setOpen(!open)}
        className="fixed bottom-[calc(1rem+env(safe-area-inset-bottom))] left-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white shadow-lg sm:bottom-6 sm:left-6 sm:h-14 sm:w-14"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {open ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </motion.button>

      <AnimatePresence>
        {open && <ChatModal onClose={() => setOpen(false)} />}
      </AnimatePresence>
    </>
  )
}
