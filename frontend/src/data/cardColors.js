// 카드/callout UI 공유 색상 시스템
// border-left 대신 배경색 틴트 + 컬러 아이콘/타이틀로 타입 구분 (VitePress 스타일)

// ── 기본 팔레트 (10색) ──────────────────────────────────
const CARD_COLORS = {
  blue:    { hex: '#3b82f6', rgb: '59,130,246',   label: 'Note' },
  amber:   { hex: '#f59e0b', rgb: '245,158,11',   label: 'Warning' },
  emerald: { hex: '#10b981', rgb: '16,185,129',   label: 'Tip' },
  red:     { hex: '#ef4444', rgb: '239,68,68',    label: 'Caution' },
  purple:  { hex: '#8b5cf6', rgb: '139,92,246',   label: 'Important' },
  orange:  { hex: '#f97316', rgb: '249,115,22',   label: 'Attention' },
  cyan:    { hex: '#06b6d4', rgb: '6,182,212',    label: 'Definition' },
  rose:    { hex: '#f43f5e', rgb: '244,63,94',    label: 'Experimental' },
  indigo:  { hex: '#6366f1', rgb: '99,102,241',   label: 'Reference' },
  slate:   { hex: '#64748b', rgb: '100,116,139',  label: 'Note' },
}

// ── 용도별 매핑 ─────────────────────────────────────────

// Callout 블록 (:::info, :::warning 등)
const CALLOUT_MAP = {
  info:    'blue',
  warning: 'amber',
  tip:     'emerald',
  danger:  'red',
}

// 대시보드 통계 카드
const STAT_MAP = {
  total:     'blue',
  published: 'emerald',
  drafts:    'amber',
  views:     'purple',
  issues:    'red',
  missing:   'orange',
}

// 포스트 타입 배지
const POST_TYPE_MAP = {
  article:      'blue',
  paper_review: 'purple',
  tutorial:     'emerald',
  til:          'amber',
  project:      'orange',
  activity_log: 'rose',
}

// 포스트 상태 표시
const STATUS_MAP = {
  published: 'emerald',
  draft:     'amber',
  archived:  'slate',
}

// 북마크 도메인 스타일
const DOMAIN_MAP = {
  'github.com':     'slate',
  'arxiv.org':      'red',
  'openai.com':     'purple',
  'huggingface.co': 'amber',
  _default:         'indigo',
}

// 컨텐츠 감사 이슈 배지
const AUDIT_ISSUE_MAP = {
  HTML_TAG:     'orange',
  JUPYTER:      'purple',
  SHORT:        'slate',
  META_REMNANT: 'amber',
  ENCODING:     'red',
}

// 이미지 커버리지 통계
const COVERAGE_MAP = {
  with_image:    'emerald',
  missing_image: 'orange',
  coverage:      'blue',
}

// ── 헬퍼 함수 ───────────────────────────────────────────

// 카드 컨테이너 스타일 생성
function getCardStyle(colorKey, options = {}) {
  const c = CARD_COLORS[colorKey] || CARD_COLORS.blue
  const { bgOpacity = 0.06, borderOpacity = 0.08, topAccent = false } = options

  if (topAccent) {
    return {
      background: `linear-gradient(to bottom, rgba(${c.rgb}, 0.04) 0%, var(--card-bg) 50%)`,
      border: '1px solid var(--border)',
      borderTop: `2px solid ${c.hex}`,
      borderRadius: '12px',
    }
  }

  return {
    background: `rgba(${c.rgb}, ${bgOpacity})`,
    border: `1px solid rgba(${c.rgb}, ${borderOpacity})`,
    borderRadius: '12px',
  }
}

// 배지/pill 스타일 생성
function getBadgeStyle(colorKey) {
  const c = CARD_COLORS[colorKey] || CARD_COLORS.blue
  return {
    background: `rgba(${c.rgb}, 0.1)`,
    color: c.hex,
  }
}

// 타이틀/아이콘 색상
function getTitleColor(colorKey) {
  return (CARD_COLORS[colorKey] || CARD_COLORS.blue).hex
}

// 상태 도트 색상
function getStatusColor(status) {
  const key = STATUS_MAP[status] || 'slate'
  return CARD_COLORS[key].hex
}

export {
  CARD_COLORS,
  CALLOUT_MAP, STAT_MAP, POST_TYPE_MAP, STATUS_MAP,
  DOMAIN_MAP, AUDIT_ISSUE_MAP, COVERAGE_MAP,
  getCardStyle, getBadgeStyle, getTitleColor, getStatusColor,
}
export default CARD_COLORS
