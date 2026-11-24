// 인프라 계열별 색상. `CloudServiceEntry.ServiceDomain` 의 12종과 같아야 한다.
//
// 아래 `INFRA_CATEGORIES` 와 **둘 다 12종이어야 한다.** 색만 있고 칩이 없으면 그 계열
// 노드는 화면에 그려지면서 필터에서 사라진다. AI 쪽 레인에서 똑같이 당했다. 가지 15종
// 가운데 6종이 칩 목록에서 빠져 그 노드 20개를 접을 수도 고를 수도 없었다.
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

// 인프라 관계 엣지 스타일.
//
// **`CloudServiceRelation.RelationType` 의 일곱 종류를 하나도 빼지 않는다.** 모르는
// 종류는 `Object.values(edgeStyles)[0]` 로 떨어져 `integrates_with` 의 흐린 회색이
// 되고, 화살표 마커는 아는 종류만 만들어져 `url(#arrow-runs_on)` 이 빈 참조가 된다.
// 선은 그려지는데 종류를 알 수 없고 범례에도 안 뜬다. 레인에서 똑같이 당했다.
//
// 아래 둘은 **층을 가로지르는 세로선**이다. 나머지는 같은 층 안의 가로선이라
// 세로선 쪽을 진하고 굵게 둬서 눈으로 갈린다.
export const CLOUD_EDGE_STYLES = {
  integrates_with: { stroke: '#64748B', dasharray: null, width: 2.0, label: 'integrates', opacity: 0.5 },
  runs_on: { stroke: '#2563EB', dasharray: null, width: 2.8, label: 'runs on', opacity: 0.75 },
  managed_version_of: { stroke: '#D97706', dasharray: null, width: 2.6, label: 'managed version of', opacity: 0.7 },
  depends_on: { stroke: '#EF4444', dasharray: null, width: 2.5, label: 'depends on', opacity: 0.6 },
  alternative_to: { stroke: '#94A3B8', dasharray: '6,4', width: 1.4, label: 'alternative', opacity: 0.35 },
  part_of: { stroke: '#22C55E', dasharray: '4,4', width: 1.8, label: 'part of', opacity: 0.45 },
  evolved_from: { stroke: '#64748B', dasharray: '2,4', width: 1.0, label: 'evolved', opacity: 0.3 },
}

// 인프라 계열 필터 칩. `CLOUD_DOMAIN_COLORS` 의 12종을 하나도 빼지 않는다.
export const INFRA_CATEGORIES = [
  { key: 'all', label: 'All', color: '#8895A7' },
  { key: 'compute', label: 'Compute', color: '#FF9900' },
  { key: 'container', label: 'Container', color: '#2496ED' },
  { key: 'storage', label: 'Storage', color: '#3F8624' },
  { key: 'database', label: 'Database', color: '#C925D1' },
  { key: 'networking', label: 'Network', color: '#8C4FFF' },
  { key: 'security', label: 'Security', color: '#DD344C' },
  { key: 'analytics', label: 'Analytics', color: '#1A73E8' },
  { key: 'ai_ml', label: 'AI/ML', color: '#01A88D' },
  { key: 'devops', label: 'DevOps', color: '#0DB7ED' },
  { key: 'devtools', label: 'DevTools', color: '#C17B9E' },
  { key: 'integration', label: 'Integration', color: '#F59E0B' },
  { key: 'management', label: 'Mgmt', color: '#E7157B' },
]

// 예전 이름. 도메인 키를 cloud 에서 infra 로 옮기는 동안 남겨 둔다
export const CLOUD_CATEGORIES = INFRA_CATEGORIES

// ---------------------------------------------------------------- 계보 축
//
// 인프라 트리의 세로축은 연도가 아니라 **추상화 층**이다. 인프라 기술의 값은 언제
// 나왔느냐가 아니라 어느 층에 서느냐에 있다. EC2(2006)와 Fargate(2017)를 연도로
// 세우면 둘 다 컴퓨트라는 것만 보이고, 층으로 세우면 가상화 위에 서버리스가 얹힌
// 관계가 보인다.
//
// 아래 상수는 **대비책**이다. 정본은 `CloudServiceEntry.Layer` 이고 API 가
// `/api/cloud-services/tree/` 의 `layers` 로 보낸다. 같은 목록을 두 곳에 적어 두면
// 한쪽만 늘어난다. 이 저장소에서 이미 두 번 그랬다.
export const LAYER_ORDER = [
  'concept', 'serverless', 'managed', 'orchestration',
  'container', 'virtualization', 'physical',
]

export const LAYER_LABELS = {
  concept: '개념·규격',
  serverless: '서버리스',
  managed: '관리형',
  orchestration: '오케스트레이션',
  container: '컨테이너',
  virtualization: '가상화',
  physical: '물리·OS',
}

// 층이 빈 노드가 서는 자리. 층이 아니라 층 밖이다
export const LAYER_NONE = '(미분류)'

// 트리 응답의 `layers` 로 축 설정을 만든다. `order` 가 작을수록 위다
export function layersFromPayload(layers) {
  if (!Array.isArray(layers) || layers.length === 0) {
    return { order: LAYER_ORDER, labels: LAYER_LABELS }
  }
  const sorted = [...layers].sort((a, b) => (a?.order ?? 0) - (b?.order ?? 0))
  const order = []
  const labels = {}
  for (const l of sorted) {
    const slug = (l?.slug || '').trim()
    if (!slug || labels[slug]) continue
    order.push(slug)
    labels[slug] = LAYER_LABELS[slug] || l.name || slug
  }
  return order.length ? { order, labels } : { order: LAYER_ORDER, labels: LAYER_LABELS }
}

// 노드가 선 층. 비면 `LAYER_NONE` 이다. 모르는 것을 관리형 같은 그럴듯한 층에
// 넣지 않는다. 비어 있다는 사실이 화면에 보여야 채워진다.
export function layerOf(node) {
  const v = (node?.layer || '').trim()
  return v || LAYER_NONE
}

// 인프라 트리의 레인은 계열(service_domain)이다. AI 트리의 가지와 같은 자리다.
export function infraLanesFromPayload(domains) {
  const base = Array.isArray(domains) && domains.length
    ? [...domains].sort((a, b) => (a?.order ?? 0) - (b?.order ?? 0)).map(d => d.slug)
    : INFRA_CATEGORIES.filter(c => c.key !== 'all').map(c => c.key)
  const order = []
  const colors = {}
  const labels = {}
  const byKey = Object.fromEntries(INFRA_CATEGORIES.map(c => [c.key, c]))
  for (const slug of base) {
    if (!slug || colors[slug]) continue
    order.push(slug)
    colors[slug] = CLOUD_DOMAIN_COLORS[slug] || '#64748b'
    labels[slug] = byKey[slug]?.label || slug
  }
  return { order, colors, labels, laneOf: node => {
    const d = (node?.service_domain || '').trim()
    return colors[d] ? d : (order[0] || 'compute')
  } }
}

// 인프라 노드 반경 (importance 1-10 -> radius 5.8-22)
export function getCloudNodeRadius(node) {
  const imp = node.importance || 5
  return 4 + imp * 1.8
}
