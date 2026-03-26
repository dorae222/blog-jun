// Architecture 카테고리 색상 팔레트
// HSB 색상환 균등 배치 원칙 — 채도/명도 통일
export const CATEGORY_COLORS = {
  llm: '#4F8CF7',       // Azure
  ssm: '#34B89A',       // Teal
  diffusion: '#E8913A', // Burnt Orange
  vision: '#2DABC1',    // Cyan
  multimodal: '#9F6CD4',// Soft Violet
  agent: '#E05C5C',     // Coral Red
  technique: '#8895A7', // Blue Gray
}

// 엣지 관계 스타일 — Slate 계열 중립 톤 (노드 색상과 분리)
export const EDGE_STYLES = {
  evolved_from:   { stroke: '#64748B', dasharray: null,    width: 2.5, label: 'evolved',   opacity: 0.6 },
  inspired_by:    { stroke: '#94A3B8', dasharray: '8,4',   width: 1.8, label: 'inspired',  opacity: 0.45 },
  variant_of:     { stroke: '#94A3B8', dasharray: '4,4',   width: 1.4, label: 'variant',   opacity: 0.4 },
  technique_used: { stroke: '#CBD5E1', dasharray: '2,4',   width: 1.0, label: 'technique', opacity: 0.3 },
}

// 카테고리 필터 목록 (ArchitectureTreePage용)
export const CATEGORIES = [
  { key: 'all', label: 'All', color: '#8895A7' },
  { key: 'llm', label: 'LLM', color: '#4F8CF7' },
  { key: 'ssm', label: 'SSM', color: '#34B89A' },
  { key: 'diffusion', label: 'Diffusion', color: '#E8913A' },
  { key: 'vision', label: 'Vision', color: '#2DABC1' },
  { key: 'multimodal', label: 'Multimodal', color: '#9F6CD4' },
  { key: 'agent', label: 'Agent', color: '#E05C5C' },
  { key: 'technique', label: 'Technique', color: '#8895A7' },
]
