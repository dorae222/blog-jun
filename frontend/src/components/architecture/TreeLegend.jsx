import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

// 그래프 왼쪽 아래 접이식 범례.
// 계보 배치일 때는 노드 색이 가지(레인)를 뜻하고, 힘 기반일 때는 카테고리를 뜻한다.
// 색이 뜻하는 바가 모드마다 다르므로 범례도 그에 맞춰 갈아 끼운다.
export default function TreeLegend({
  lanes,
  laneColors,
  laneLabels,
  categoryColors,
  edgeStyles,
  showOpenSource = false,
}) {
  const [open, setOpen] = useState(false)
  const swatches = lanes?.length
    ? lanes.map(lane => ({ key: lane, color: laneColors[lane], label: laneLabels[lane] || lane }))
    : Object.entries(categoryColors).map(([cat, color]) => ({ key: cat, color, label: cat.toUpperCase() }))

  return (
    <div
      className="absolute bottom-3 left-3 rounded-xl text-xs"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
        opacity: 0.92,
        backdropFilter: 'blur(8px)',
        maxWidth: 'min(420px, calc(100% - 24px))',
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-2 w-full font-semibold"
        style={{ color: 'var(--text)' }}
      >
        Legend
        {open ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
      </button>
      {open && (
        <div className="px-3 pb-2.5 space-y-2.5">
          <div className="flex flex-wrap gap-x-3 gap-y-1.5">
            {swatches.map(s => (
              <span key={s.key} className="flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
                <span style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
              </span>
            ))}
          </div>
          {showOpenSource && (
            <div className="flex flex-wrap gap-x-3 gap-y-1.5">
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14">
                  <circle cx="7" cy="7" r="5" fill="var(--text-secondary)" fillOpacity="0.85"
                    stroke="var(--text-secondary)" strokeWidth="1.5" />
                </svg>
                <span style={{ color: 'var(--text-secondary)' }}>공개 가중치</span>
              </span>
              <span className="flex items-center gap-1.5">
                <svg width="14" height="14">
                  <circle cx="7" cy="7" r="5" fill="var(--text-secondary)" fillOpacity="0.85"
                    stroke="var(--text-secondary)" strokeWidth="1.5" strokeDasharray="3,2.5" />
                </svg>
                <span style={{ color: 'var(--text-secondary)' }}>비공개 (점선 테두리)</span>
              </span>
            </div>
          )}
          <div className="flex flex-wrap gap-x-3 gap-y-1.5">
            {Object.entries(edgeStyles).map(([type, style]) => (
              <span key={type} className="flex items-center gap-1.5">
                <svg width="22" height="8">
                  <line x1="0" y1="4" x2="22" y2="4" stroke={style.stroke} strokeWidth={style.width}
                    strokeDasharray={style.dasharray || undefined} opacity={style.opacity} />
                </svg>
                <span style={{ color: 'var(--text-secondary)' }}>{style.labelKo || style.label}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
