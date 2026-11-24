// Architecture 카테고리 색상 팔레트
// HSB 색상환 균등 배치 원칙 - 채도/명도 통일
export const CATEGORY_COLORS = {
  llm: '#4F8CF7',       // Azure
  ssm: '#34B89A',       // Teal
  diffusion: '#E8913A', // Burnt Orange
  vision: '#2DABC1',    // Cyan
  multimodal: '#9F6CD4',// Soft Violet
  agent: '#E05C5C',     // Coral Red
  technique: '#8895A7', // Blue Gray
}

// 엣지 관계 스타일 - Slate 계열 중립 톤 (노드 색상과 분리)
// 계보에서 굵기가 곧 가까움이다. 발전이 가장 굵고, 영향은 점선, 변형은 얇은 실선,
// 기법 적용만 색을 달리해 계보선과 성격이 다르다는 것을 드러낸다.
export const EDGE_STYLES = {
  evolved_from:   { stroke: '#64748B', dasharray: null,  width: 2.5, label: 'evolved',   labelKo: '발전',      opacity: 0.6 },
  inspired_by:    { stroke: '#94A3B8', dasharray: '8,4', width: 1.8, label: 'inspired',  labelKo: '영향',      opacity: 0.5 },
  variant_of:     { stroke: '#94A3B8', dasharray: null,  width: 1.2, label: 'variant',   labelKo: '변형',      opacity: 0.45 },
  technique_used: { stroke: '#D9A441', dasharray: null,  width: 1.2, label: 'technique', labelKo: '기법 적용', opacity: 0.5 },
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

// 종류 필터. architecture_category로 가른다.
//
// `entry_kind`(model 171 / technique 27 / paper 6)도 API가 세 serializer 모두에서
// 실어 보내고 `?entry_kind=`로 거를 수도 있다. 그런데 그쪽으로 갈아 끼우면 일곱 갈래가
// 세 갈래로 줄어 LLM·Diffusion·Vision을 따로 볼 수 없다. 필터는 카테고리로 두고,
// entry_kind는 노드 모양(모델은 원, 그 밖은 마름모 표식)으로 드러낸다.
export const KIND_FILTER = {
  field: 'architecture_category',
  param: 'category',
  label: '종류',
  options: CATEGORIES,
}

// entry_kind별 표식. 모델이 아닌 노드에만 붙는다.
export const NON_MODEL_KINDS = new Set(['technique', 'paper'])

// 계보 레인의 **대비책**이다. 정본은 `Branch` 테이블이고 API가
// `/api/architectures/tree/`의 `branches`로 색·이름·순서까지 실어 보낸다(backend/blog/views.py).
// 아래 목록을 정본으로 쓰다가 가지 15종 중 여섯(retrieval·rag·vector_index·prompt_opt·
// graph_ml·classic_ml·serving)이 빠진 채 굳었고, 그 가지의 노드 20개(XGBoost·HNSW·
// GraphRAG·SGLang 등)가 카테고리 대비책을 타고 **전부 디코더 레인에 그려졌다.**
// 범례에도 그 가지 칩이 없어 접을 수조차 없었다.
//
// 그래서 지금은 `lanesFromBranches`가 응답에서 레인 설정을 만들고, 이 상수는 응답에
// `branches`가 없을 때만 쓴다.
export const LANE_ORDER = [
  'encoder_only',
  'encoder_decoder',
  'decoder_only',
  'ssm',
  'multimodal',
  'vision',
  'diffusion',
  'agent',
  'other',
]

export const LANE_COLORS = {
  encoder_only: '#dc2626',
  encoder_decoder: '#059669',
  decoder_only: '#2563eb',
  ssm: '#7c3aed',
  multimodal: '#ea580c',
  vision: '#0891b2',
  diffusion: '#db2777',
  agent: '#65a30d',
  other: '#64748b',
}

// 범례 칩에 적는 이름. `Branch.name`은 한글("디코더 전용")인데 이 칩들은 영어로 굳었고
// Encoder·Decoder·RAG·SSM 처럼 영어가 더 적절한 용어라 영어를 정본으로 둔다.
// 여기 없는 가지는 `Branch.name`을 그대로 쓴다(읽히기는 하므로 빈 칩이 되지 않는다).
export const LANE_LABELS = {
  encoder_only: 'Encoder',
  encoder_decoder: 'Enc-Dec',
  decoder_only: 'Decoder',
  ssm: 'SSM',
  multimodal: 'Multimodal',
  vision: 'Vision',
  diffusion: 'Diffusion',
  diffusion_lm: 'Diffusion LM',
  agent: 'Agent',
  retrieval: 'Retrieval',
  rag: 'RAG',
  vector_index: 'Vector Index',
  prompt_opt: 'Prompt Opt',
  graph_ml: 'Graph ML',
  classic_ml: 'Classic ML',
  serving: 'Serving',
  other: 'Other',
}

const LANE_CATEGORY_FALLBACK = {
  llm: 'decoder_only',
  ssm: 'ssm',
  diffusion: 'diffusion',
  multimodal: 'multimodal',
  vision: 'vision',
  agent: 'agent',
  technique: 'other',
}

// `other`는 가지가 아니다. branch_type이 비고 카테고리로도 못 메우는 노드가 서는 자리다.
// `Branch` 테이블에 행이 없으므로 레인 목록 끝에 손으로 붙인다.
const OTHER_LANE = 'other'

// 노드가 선 레인을 정하는 함수를 만든다. 레인 목록을 밖에서 받으므로 도메인마다 다른
// 목록을 쓸 수 있다. `branch_type`이 정본이고, 그 값이 목록에 없으면 카테고리로 메운다.
export function makeLaneOf(laneOrder) {
  const known = new Set(laneOrder)
  return function laneOfNode(node) {
    const branch = (node?.branch_type || '').trim()
    if (known.has(branch)) return branch
    return LANE_CATEGORY_FALLBACK[(node?.architecture_category || '').trim()] || OTHER_LANE
  }
}

// 상수만으로 만든 대비책 설정. API가 `branches`를 안 줄 때 쓴다.
const FALLBACK_LANES = {
  order: LANE_ORDER,
  colors: LANE_COLORS,
  labels: LANE_LABELS,
  laneOf: makeLaneOf(LANE_ORDER),
}

// 트리 응답의 `branches`로 레인 설정을 만든다. 순서와 색은 `Branch` 테이블이 정하고
// 이름만 위의 영어 목록을 앞세운다.
//
// `order`는 `Branch.order` 오름차순이다. 서버가 이미 그 순서로 보내지만 응답 순서에
// 기대지 않는다. 한 번 어긋나면 범례와 트리의 좌우가 서로 달라져 눈으로 찾기 어렵다.
export function lanesFromBranches(branches) {
  if (!Array.isArray(branches) || branches.length === 0) return FALLBACK_LANES
  const sorted = [...branches].sort((a, b) => (a?.order ?? 0) - (b?.order ?? 0))
  const order = []
  const colors = {}
  const labels = {}
  for (const b of sorted) {
    const slug = (b?.slug || '').trim()
    if (!slug || colors[slug]) continue
    order.push(slug)
    colors[slug] = b.color || LANE_COLORS[slug] || '#64748b'
    labels[slug] = LANE_LABELS[slug] || b.name || slug
  }
  if (!order.length) return FALLBACK_LANES
  if (!colors[OTHER_LANE]) {
    order.push(OTHER_LANE)
    colors[OTHER_LANE] = LANE_COLORS[OTHER_LANE]
    labels[OTHER_LANE] = LANE_LABELS[OTHER_LANE]
  }
  return { order, colors, labels, laneOf: makeLaneOf(order) }
}

// 노드가 선 레인. 대비책 목록을 쓰는 판이다. 레인 목록이 손에 있으면
// `lanesFromBranches(...).laneOf`를 쓰는 쪽이 맞다.
export const laneOf = FALLBACK_LANES.laneOf
