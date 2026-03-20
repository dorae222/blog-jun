import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, X, ArrowRight } from 'lucide-react'

const BRANCH_COLORS = {
  encoder_only: '#4ade80',
  encoder_decoder: '#86efac',
  decoder_only: '#93c5fd',
  ssm: '#22d3ee',
  diffusion: '#c084fc',
  vision: '#f472b6',
  multimodal: '#fb923c',
  agent: '#a3e635',
}

export default function TreeNodePopup({ node, position, onClose }) {
  const navigate = useNavigate()
  if (!node) return null

  const data = node
  const color = BRANCH_COLORS[data.branch_type] || '#93c5fd'
  const year = data.release_date?.slice(0, 4) || ''

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.15 }}
        className="fixed z-50 w-80 rounded-xl overflow-hidden shadow-2xl"
        style={{
          left: position?.x ?? '50%',
          top: position?.y ?? '50%',
          transform: 'translate(-50%, -100%) translateY(-16px)',
          background: 'rgba(255, 255, 255, 0.98)',
          border: `1px solid ${color}40`,
          backdropFilter: 'blur(16px)',
        }}
      >
        {/* Header */}
        <div className="p-4 pb-3" style={{ borderBottom: `1px solid ${color}20` }}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-slate-800 font-bold text-base">{data.name}</h3>
              <p className="text-slate-500 text-xs mt-0.5">
                {data.organization} {year && `· ${year}`}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-slate-100 transition-colors"
            >
              <X size={16} className="text-slate-400" />
            </button>
          </div>

          {/* Spec pills */}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {data.param_scale && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                {data.param_scale}
              </span>
            )}
            {data.context_length && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                {data.context_length}
              </span>
            )}
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ background: `${color}20`, color }}
            >
              {data.architecture_category?.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Figure preview */}
        {data.figure_url && (
          <div className="px-4 py-2">
            <img
              src={data.figure_url}
              alt={data.name}
              className="w-full h-32 object-contain rounded-lg bg-slate-50"
            />
          </div>
        )}

        {/* Actions */}
        <div className="px-4 py-3 flex items-center gap-2">
          <button
            onClick={() => navigate(`/architectures/${data.slug}`)}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-colors text-white"
            style={{ background: color }}
          >
            자세히 보기 <ArrowRight size={14} />
          </button>
          {data.paper_url && (
            <a
              href={data.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <ExternalLink size={16} className="text-slate-400" />
            </a>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
