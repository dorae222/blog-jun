import { GitFork, Network } from 'lucide-react'
import { LANE_COLORS, LANE_LABELS } from '../../data/architectureConstants'

// 레인 색과 이름은 트리 응답에서 만들어 내려온다. 기본값은 상수 대비책이다

// 계보 트리 전용 조작 줄. 배치 모드 토글과 가지(레인) 접기·펴기를 한 줄에 둔다.
// 상단 바가 이미 도메인 탭·종류 필터·검색으로 꽉 차서 따로 뺐다.
export default function TreeViewControls({
  layoutMode,
  onLayoutModeChange,
  lanes,
  laneCounts,
  laneColors = LANE_COLORS,
  laneLabels = LANE_LABELS,
  hiddenLanes,
  onToggleLane,
  onResetLanes,
}) {
  const hidden = new Set(hiddenLanes)

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
      <div className="flex items-center border rounded-lg overflow-hidden shrink-0" style={{ borderColor: 'var(--border)' }}>
        <button
          onClick={() => onLayoutModeChange('lineage')}
          className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium transition-colors"
          style={{
            background: layoutMode === 'lineage' ? 'var(--text)' : 'transparent',
            color: layoutMode === 'lineage' ? '#fff' : 'var(--text-secondary)',
          }}
          title="발표 시점과 가지를 따라 고정 배치한다"
        >
          <GitFork size={12} /> 계보
        </button>
        <button
          onClick={() => onLayoutModeChange('force')}
          className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium transition-colors"
          style={{
            background: layoutMode === 'force' ? 'var(--text)' : 'transparent',
            color: layoutMode === 'force' ? '#fff' : 'var(--text-secondary)',
          }}
          title="관계가 가까운 것끼리 뭉치게 한다"
        >
          <Network size={12} /> 관계
        </button>
      </div>

      {layoutMode === 'lineage' && (
        <>
          <span className="w-px h-4 shrink-0" style={{ background: 'var(--border)' }} />
          {lanes.map(lane => {
            const off = hidden.has(lane)
            const color = laneColors[lane]
            return (
              <button
                key={lane}
                onClick={() => onToggleLane(lane)}
                className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full transition-all shrink-0"
                style={{
                  background: off ? 'transparent' : color + '18',
                  color: off ? 'var(--text-secondary)' : color,
                  border: `1px solid ${off ? 'var(--border)' : color + '40'}`,
                  opacity: off ? 0.55 : 1,
                }}
                title={off ? '가지를 펴기' : '가지를 접기'}
              >
                <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ background: off ? 'var(--text-secondary)' : color }} />
                {laneLabels[lane] || lane}
                <span className="tabular-nums" style={{ opacity: 0.7 }}>{laneCounts[lane]}</span>
              </button>
            )
          })}
          {hidden.size > 0 && (
            <button
              onClick={onResetLanes}
              className="text-xs px-2 py-1 rounded-full shrink-0 underline"
              style={{ color: 'var(--text-secondary)' }}
            >
              모두 펴기
            </button>
          )}
        </>
      )}
    </div>
  )
}
