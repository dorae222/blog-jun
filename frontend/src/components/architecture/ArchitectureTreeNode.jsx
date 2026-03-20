import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { motion } from 'framer-motion'

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

const ORG_ICONS = {
  google: '🔵',
  openai: '🟢',
  meta: '🟣',
  anthropic: '🟠',
  microsoft: '🔷',
  nvidia: '🟩',
  deepseek: '🔹',
  alibaba: '🟧',
  mistral: '⬛',
  hugging: '🟡',
  stability: '🟪',
  baidu: '🔴',
  tsinghua: '🔶',
  apple: '⬜',
}

function getOrgIcon(org) {
  if (!org) return ''
  const lower = org.toLowerCase()
  for (const [key, icon] of Object.entries(ORG_ICONS)) {
    if (lower.includes(key)) return icon
  }
  return '🏢'
}

function ArchitectureTreeNode({ data, selected }) {
  const color = BRANCH_COLORS[data.branch_type] || BRANCH_COLORS.decoder_only
  const orgIcon = getOrgIcon(data.organization)
  const isOpen = data.is_open_source

  return (
    <>
      {/* 상단 핸들 (자식으로부터 받는 = target) → 실제로는 parent에서 보내는 source */}
      <Handle
        type="source"
        position={Position.Top}
        className="!w-1.5 !h-1.5 !border-0 !opacity-0"
        style={{ background: color }}
      />

      <motion.div
        whileHover={{ scale: 1.06, y: -2 }}
        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        className="relative cursor-pointer select-none group"
        style={{
          background: isOpen
            ? `${color}12`
            : 'rgba(255,255,255,0.95)',
          border: `1.5px solid ${selected ? color : `${color}60`}`,
          borderRadius: '10px',
          padding: '5px 12px',
          boxShadow: selected
            ? `0 0 0 2px ${color}40, 0 4px 12px ${color}25`
            : `0 1px 4px rgba(0,0,0,0.08)`,
          minWidth: 60,
          textAlign: 'center',
          transition: 'box-shadow 0.2s ease',
        }}
      >
        {/* Open/Closed source 인디케이터 */}
        <div
          className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-sm border"
          style={{
            background: isOpen ? '#d4a574' : '#ffffff',
            borderColor: isOpen ? '#b8956a' : '#cbd5e1',
          }}
        />

        {/* 모델 이름 + 조직 아이콘 */}
        <div className="flex items-center gap-1 justify-center">
          <span
            className="text-[11px] font-bold leading-tight whitespace-nowrap"
            style={{ color: '#1e293b' }}
          >
            {data.name || data.slug}
          </span>
          {orgIcon && (
            <span className="text-[10px] leading-none" title={data.organization}>
              {orgIcon}
            </span>
          )}
        </div>
      </motion.div>

      {/* 하단 핸들 (부모에서 오는 = target) */}
      <Handle
        type="target"
        position={Position.Bottom}
        className="!w-1.5 !h-1.5 !border-0 !opacity-0"
        style={{ background: color }}
      />
    </>
  )
}

export default memo(ArchitectureTreeNode)
