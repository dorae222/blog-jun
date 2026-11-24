import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import useDialog from '../../hooks/useDialog'
import useFocusTrap from '../../hooks/useFocusTrap'

/** useDialog의 confirmDialog/promptDialog를 그리는 자리. App에 한 번만 둔다. */
export default function DialogHost() {
  const current = useDialog((s) => s.current)
  const close = useDialog((s) => s.close)
  const boxRef = useRef(null)
  const inputRef = useRef(null)
  const okRef = useRef(null)
  const [value, setValue] = useState('')
  const isPrompt = current?.kind === 'prompt'
  const o = current?.options || {}

  const cancel = () => close(isPrompt ? null : false)
  useFocusTrap(boxRef, Boolean(current), cancel)

  useEffect(() => {
    if (!current) return
    setValue(current.options?.defaultValue ?? '')
    const t = setTimeout(() => {
      if (current.kind === 'prompt') { inputRef.current?.focus(); inputRef.current?.select() } else okRef.current?.focus()
    }, 30)
    return () => clearTimeout(t)
  }, [current])

  const submit = (e) => {
    e?.preventDefault()
    if (isPrompt) {
      const v = value.trim()
      if (!v && o.required !== false) return
      close(v)
    } else close(true)
  }

  return (
    <AnimatePresence>
      {current && (
        <motion.div className="fixed inset-0 z-[70] flex items-center justify-center p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-black/40" onClick={cancel} />
          <motion.form ref={boxRef} onSubmit={submit}
            role={isPrompt ? 'dialog' : 'alertdialog'} aria-modal="true" aria-labelledby="app-dialog-title"
            className="relative max-w-sm w-full rounded-2xl p-6 shadow-2xl border"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
            initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} transition={{ duration: 0.15 }}>
            <h3 id="app-dialog-title" className="text-base font-semibold mb-2" style={{ color: 'var(--text)' }}>
              {o.title || (isPrompt ? '입력' : '확인')}
            </h3>
            {o.message && <p className="text-sm mb-4 whitespace-pre-line" style={{ color: 'var(--text-secondary)' }}>{o.message}</p>}
            {isPrompt && (
              <>
                {o.label && <label htmlFor="app-dialog-input" className="block text-xs font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{o.label}</label>}
                <input id="app-dialog-input" ref={inputRef} value={value} onChange={(e) => setValue(e.target.value)}
                  placeholder={o.placeholder || ''} type={o.inputType || 'text'}
                  className="w-full mb-4 text-sm px-3 py-2 rounded-lg border outline-none focus:ring-2 focus:ring-primary-500"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }} />
              </>
            )}
            <div className="flex justify-end gap-2 mt-2">
              <button type="button" onClick={cancel} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                {o.cancelLabel || '취소'}
              </button>
              <button type="submit" ref={okRef} disabled={isPrompt && !value.trim() && o.required !== false}
                className={`px-4 py-2 text-sm font-medium rounded-lg text-white disabled:opacity-40 ${o.variant === 'danger' ? 'bg-red-600 hover:bg-red-700' : 'bg-primary-600 hover:bg-primary-700'}`}>
                {o.confirmLabel || '확인'}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
