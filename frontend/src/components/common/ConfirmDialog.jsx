import { useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

export default function ConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title = '확인',
  message,
  confirmLabel = '확인',
  variant = 'default',
}) {
  useEffect(() => {
    if (!isOpen) return
    const handleEsc = (e) => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onCancel])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="alertdialog"
          aria-modal="true"
          aria-describedby="confirm-dialog-message"
        >
          <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
          <motion.div
            className="relative max-w-sm w-full rounded-2xl p-6 shadow-2xl border"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <h3 className="text-base font-semibold mb-2" style={{ color: 'var(--text)' }}>{title}</h3>
            <p id="confirm-dialog-message" className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
              {message}
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={onCancel}
                className="px-4 py-2 text-sm rounded-lg border transition-colors hover:bg-gray-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
              >
                취소
              </button>
              <button
                onClick={onConfirm}
                className={`px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors ${
                  variant === 'danger'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-primary-600 hover:bg-primary-700'
                }`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
