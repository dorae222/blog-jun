import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

const BTN =
  'flex items-center justify-center w-8 h-8 rounded-lg transition-colors hover:bg-gray-100 dark:hover:bg-gray-700'

export default function GraphZoomControls({ onZoomIn, onZoomOut, onFitAll }) {
  return (
    <div
      className="absolute top-3 right-3 z-20 flex flex-col gap-1 rounded-xl p-1"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
        backdropFilter: 'blur(8px)',
        opacity: 0.92,
      }}
    >
      <button onClick={onZoomIn} className={BTN} title="Zoom in" style={{ color: 'var(--text-secondary)' }}>
        <ZoomIn size={16} />
      </button>
      <button onClick={onZoomOut} className={BTN} title="Zoom out" style={{ color: 'var(--text-secondary)' }}>
        <ZoomOut size={16} />
      </button>
      <div className="border-t mx-1" style={{ borderColor: 'var(--border)' }} />
      <button onClick={onFitAll} className={BTN} title="Fit all" style={{ color: 'var(--text-secondary)' }}>
        <Maximize2 size={16} />
      </button>
    </div>
  )
}
