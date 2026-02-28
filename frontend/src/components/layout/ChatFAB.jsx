import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, X } from 'lucide-react'
import ChatModal from '../chatbot/ChatModal'

export default function ChatFAB() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <motion.button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 left-6 z-40 w-14 h-14 rounded-full bg-accent text-white shadow-lg flex items-center justify-center"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {open ? <X size={24} /> : <MessageSquare size={24} />}
      </motion.button>

      <AnimatePresence>
        {open && <ChatModal onClose={() => setOpen(false)} />}
      </AnimatePresence>
    </>
  )
}
