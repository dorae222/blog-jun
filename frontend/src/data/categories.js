// 카테고리 단일 소스 — LeftSidebar, CategoryTabs, Home, PostView에서 공유
export const CATEGORY_TREE = [
  {
    key: 'ai', label: 'AI', color: '#FF6F00',
    desc: 'LLM, SSM, Diffusion 등 AI 아키텍처',
    path: '/posts/ai',
    subs: [
      { key: 'llm', label: 'LLM' },
      { key: 'ssm', label: 'SSM' },
      { key: 'diffusion', label: 'Diffusion' },
      { key: 'vision', label: 'Vision' },
      { key: 'multimodal', label: 'Multimodal' },
      { key: 'agent', label: 'Agent' },
      { key: 'technique', label: 'Technique' },
      { key: 'efficiency', label: 'Efficiency' },
      { key: 'reasoning', label: 'Reasoning' },
      { key: 'training', label: 'Training' },
      { key: 'rag', label: 'RAG' },
      { key: 'code', label: 'Code' },
      { key: 'tool', label: 'Tool' },
    ],
  },
  {
    key: 'ml', label: 'ML', color: '#10B981',
    desc: '회귀, 분류, 앙상블, MLOps 등',
    path: '/posts/ml',
    subs: [
      { key: 'fundamentals', label: '기초' },
      { key: 'math-foundations', label: '수학' },
      { key: 'preprocessing', label: '전처리' },
      { key: 'supervised-regression', label: '회귀' },
      { key: 'supervised-classification', label: '분류' },
      { key: 'ensemble', label: '앙상블' },
      { key: 'unsupervised', label: '비지도' },
      { key: 'model-evaluation', label: '평가' },
      { key: 'causal-inference', label: '인과추론' },
      { key: 'advanced-algorithms', label: '심화' },
      { key: 'applications', label: '응용' },
      { key: 'mlops', label: 'MLOps' },
    ],
  },
  {
    key: 'cloud', label: 'Cloud', color: '#FF9900',
    desc: 'AWS, Docker, DevOps 인프라',
    path: '/posts/cloud',
    subs: [
      { key: 'aws-compute', label: 'Compute' },
      { key: 'aws-storage', label: 'Storage' },
      { key: 'aws-database', label: 'Database' },
      { key: 'aws-networking', label: 'Network' },
      { key: 'aws-security', label: 'Security' },
      { key: 'aws-analytics', label: 'Analytics' },
      { key: 'aws-ai-ml', label: 'AI/ML' },
      { key: 'aws-devtools', label: 'DevTools' },
      { key: 'aws-management', label: 'Mgmt' },
      { key: 'aws-integration', label: 'Integration' },
      { key: 'docker', label: 'Docker' },
      { key: 'lxd', label: 'LXD' },
      { key: 'devops', label: 'DevOps' },
    ],
  },
  {
    key: 'data', label: 'Data Engineering', color: '#336791',
    desc: 'Hadoop, Spark, Pipeline',
    path: '/posts/data',
    subs: [
      { key: 'big-data', label: 'Big Data' },
      { key: 'database', label: 'Database' },
      { key: 'pipeline', label: 'Pipeline' },
    ],
  },
]

// CategoryTabs용 파생
export const MAIN_TABS = [
  { key: null, label: '전체', path: '/posts' },
  ...CATEGORY_TREE.map(c => ({ key: c.key, label: c.label, path: c.path })),
]

export const SUB_TABS = Object.fromEntries(
  CATEGORY_TREE.map(c => [c.key, [{ key: null, label: '전체' }, ...c.subs]])
)

// PostView 브레드크럼용 역매핑 (DB slug → route key)
export const CATEGORY_ROUTE_MAP = {
  'ai-ml': 'ai',
  cloud: 'cloud',
  'data-engineering': 'data',
  ml: 'ml',
}
