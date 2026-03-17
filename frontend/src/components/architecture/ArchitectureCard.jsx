import { motion } from 'framer-motion'
import { ExternalLink, Cpu, Layers } from 'lucide-react'

const TYPE_COLORS = {
  dense: { bg: '#3B82F620', text: '#3B82F6', label: 'Dense' },
  sparse_moe: { bg: '#8B5CF620', text: '#8B5CF6', label: 'MoE' },
  sparse_hybrid: { bg: '#F59E0B20', text: '#F59E0B', label: 'Hybrid' },
}

export default function ArchitectureCard({ entry }) {
  const typeStyle = TYPE_COLORS[entry.decoder_type] || TYPE_COLORS.dense

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border overflow-hidden hover:shadow-lg transition-shadow"
      style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
    >
      {/* Figure / Placeholder */}
      <div
        className="h-40 flex items-center justify-center"
        style={{ background: 'var(--bg-secondary)' }}
      >
        {entry.figure_url ? (
          <img src={entry.figure_url} alt={entry.name} className="w-full h-full object-contain p-4" />
        ) : (
          <Cpu size={48} style={{ color: 'var(--text-secondary)', opacity: 0.3 }} />
        )}
      </div>

      <div className="p-5 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-bold text-lg" style={{ color: 'var(--text)' }}>
              {entry.name}
            </h3>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              {entry.organization}
              {entry.release_date && ` \u00B7 ${entry.release_date.slice(0, 4)}`}
            </p>
          </div>
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
            style={{ backgroundColor: typeStyle.bg, color: typeStyle.text }}
          >
            {typeStyle.label}
          </span>
        </div>

        {/* Specs */}
        <div className="flex flex-wrap gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
          {entry.param_scale && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--bg-secondary)' }}>
              {entry.param_scale}
            </span>
          )}
          {entry.context_length && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--bg-secondary)' }}>
              {entry.context_length}
            </span>
          )}
          {entry.attention_type && (
            <span className="px-2 py-0.5 rounded-full" style={{ background: 'var(--bg-secondary)' }}>
              {entry.attention_type}
            </span>
          )}
        </div>

        {/* Concepts */}
        {entry.concepts?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {entry.concepts.map((c) => (
              <span
                key={c.id}
                className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ backgroundColor: c.color + '20', color: c.color }}
              >
                {c.abbreviation || c.name}
              </span>
            ))}
          </div>
        )}

        {/* Key Detail */}
        {entry.key_detail && (
          <p className="text-sm line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
            {entry.key_detail}
          </p>
        )}

        {/* Links */}
        <div className="flex items-center gap-3 pt-1">
          {entry.paper_url && (
            <a
              href={entry.paper_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs flex items-center gap-1 text-primary-600 hover:underline"
            >
              <ExternalLink size={12} /> Paper
            </a>
          )}
          {entry.license_type && (
            <span className="text-xs flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
              <Layers size={12} /> {entry.license_type}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}
