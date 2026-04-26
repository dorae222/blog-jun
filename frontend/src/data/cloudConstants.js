// Cloud 서비스 도메인별 색상
export const CLOUD_DOMAIN_COLORS = {
  compute: '#FF9900',
  storage: '#3F8624',
  database: '#C925D1',
  networking: '#8C4FFF',
  security: '#DD344C',
  analytics: '#1A73E8',
  ai_ml: '#01A88D',
  devtools: '#C17B9E',
  management: '#E7157B',
  integration: '#F59E0B',
  container: '#2496ED',
  devops: '#0DB7ED',
}

// Cloud 관계 엣지 스타일
export const CLOUD_EDGE_STYLES = {
  integrates_with: { stroke: '#64748B', dasharray: null, width: 2.0, label: 'integrates', opacity: 0.5 },
  depends_on: { stroke: '#EF4444', dasharray: null, width: 2.5, label: 'depends on', opacity: 0.6 },
  alternative_to: { stroke: '#94A3B8', dasharray: '6,4', width: 1.4, label: 'alternative', opacity: 0.35 },
  part_of: { stroke: '#22C55E', dasharray: '4,4', width: 1.8, label: 'part of', opacity: 0.45 },
  evolved_from: { stroke: '#64748B', dasharray: '2,4', width: 1.0, label: 'evolved', opacity: 0.3 },
}

// Cloud 카테고리 필터 탭
export const CLOUD_CATEGORIES = [
  { key: 'all', label: 'All', color: '#8895A7' },
  { key: 'compute', label: 'Compute', color: '#FF9900' },
  { key: 'storage', label: 'Storage', color: '#3F8624' },
  { key: 'database', label: 'Database', color: '#C925D1' },
  { key: 'networking', label: 'Network', color: '#8C4FFF' },
  { key: 'security', label: 'Security', color: '#DD344C' },
  { key: 'analytics', label: 'Analytics', color: '#1A73E8' },
  { key: 'ai_ml', label: 'AI/ML', color: '#01A88D' },
  { key: 'integration', label: 'Integration', color: '#F59E0B' },
  { key: 'management', label: 'Mgmt', color: '#E7157B' },
]

// Cloud 노드 반경 (importance 1-10 -> radius 5.8-22)
export function getCloudNodeRadius(node) {
  const imp = node.importance || 5
  return 4 + imp * 1.8
}
