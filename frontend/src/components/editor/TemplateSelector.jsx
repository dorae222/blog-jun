import { motion } from 'framer-motion'

export default function TemplateSelector({ templates, onSelect, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="w-full max-w-lg rounded-2xl p-6 max-h-[80vh] overflow-y-auto"
        style={{ background: 'var(--card-bg)' }}
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--text)' }}>Choose a Template</h3>
        <div className="space-y-3">
          {templates.map(tmpl => (
            <button
              key={tmpl.id}
              onClick={() => onSelect(tmpl)}
              className="w-full text-left p-4 rounded-xl border hover:shadow-md transition-all hover:-translate-y-0.5"
              style={{ borderColor: 'var(--border)', background: 'var(--bg)' }}
            >
              <h4 className="font-semibold" style={{ color: 'var(--text)' }}>{tmpl.name}</h4>
              <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{tmpl.description}</p>
              <span className="text-xs mt-2 inline-block px-2 py-0.5 rounded-full bg-primary-100 text-primary-700">
                {tmpl.post_type?.replace('_', ' ')}
              </span>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
