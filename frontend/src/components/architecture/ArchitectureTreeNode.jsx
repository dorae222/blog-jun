import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { motion } from 'framer-motion'
import { Lock, Unlock } from 'lucide-react'

const BRANCH_COLORS = {
  encoder_only: { ring: '#60a5fa', glow: '#3b82f640' },
  encoder_decoder: { ring: '#34d399', glow: '#10b98140' },
  decoder_only: { ring: '#a78bfa', glow: '#8b5cf640' },
  ssm: { ring: '#22d3ee', glow: '#06b6d440' },
  diffusion: { ring: '#fbbf24', glow: '#f59e0b40' },
  vision: { ring: '#f472b6', glow: '#ec489940' },
  multimodal: { ring: '#fb7185', glow: '#f4363640' },
  agent: { ring: '#a3e635', glow: '#84cc1640' },
}

const CATEGORY_LABELS = {
  llm: 'LLM',
  ssm: 'SSM',
  diffusion: 'Diffusion',
  vision: 'Vision',
  multimodal: 'Multimodal',
  agent: 'Agent',
  technique: 'Technique',
}

function ArchitectureTreeNode({ data, selected }) {
  const colors = BRANCH_COLORS[data.branch_type] || BRANCH_COLORS.decoder_only
  const year = data.release_date?.slice(0, 4) || ''

  return (
    <>
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !border-0" style={{ background: colors.ring }} />
      <motion.div
        whileHover={{ scale: 1.08 }}
        transition={{ type: 'spring', stiffness: 400, damping: 20 }}
        className="relative cursor-pointer select-none"
        style={{
          background: 'rgba(15, 23, 42, 0.85)',
          border: `2px solid ${selected ? '#fff' : colors.ring}`,
          borderRadius: '9999px',
          padding: '6px 16px',
          boxShadow: selected
            ? `0 0 20px ${colors.ring}, 0 0 40px ${colors.glow}`
            : `0 0 8px ${colors.glow}`,
          backdropFilter: 'blur(8px)',
          minWidth: 80,
          textAlign: 'center',
        }}
      >
        {/* 카테고리 도트 */}
        <div
          className="absolute -top-1 -left-1 w-3 h-3 rounded-full border-2"
          style={{ background: colors.ring, borderColor: 'rgba(15, 23, 42, 0.9)' }}
        />

        {/* Open/Closed source 아이콘 */}
        <div className="absolute -top-1 -right-1">
          {data.is_open_source ? (
            <Unlock size={10} style={{ color: '#4ade80' }} />
          ) : (
            <Lock size={10} style={{ color: '#f87171' }} />
          )}
        </div>

        <div className="text-white text-xs font-bold leading-tight whitespace-nowrap">
          {data.name}
        </div>
        <div className="text-gray-400 text-[10px] leading-tight">
          {data.organization?.split('/')[0]?.trim()}
          {year && ` · ${year}`}
        </div>
      </motion.div>
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !border-0" style={{ background: colors.ring }} />
    </>
  )
}

export default memo(ArchitectureTreeNode)
