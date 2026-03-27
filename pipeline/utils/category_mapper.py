"""
통합 카테고리 매퍼 — 5개 import 스크립트의 중복 매핑을 하나로 통합.

사용법:
    from pipeline.utils.category_mapper import CategoryMapper
    mapper = CategoryMapper()
    slug = mapper.resolve('transformer', 'paper_review')  # → 'llm'
    cat = mapper.get_category('llm')  # → Category object
"""


# 소스 카테고리 → DB slug 매핑 (papers에서 사용)
PAPER_CATEGORY_MAP = {
    # LLM
    'transformer': 'llm', 'nlp': 'llm', 'llm': 'llm',
    'llm-architecture': 'llm', 'pretraining': 'llm',
    # Vision / Multimodal / SSM / Diffusion
    'vision': 'vision', 'multimodal': 'multimodal',
    'ssm': 'ssm', 'diffusion': 'diffusion',
    # Efficiency (신규)
    'moe': 'efficiency', 'scaling': 'efficiency',
    'efficiency': 'efficiency', 'efficient-training': 'efficiency',
    # Training (신규)
    'training': 'training', 'alignment': 'training', 'finetuning': 'training', 'data': 'training',
    # RAG (신규)
    'rag': 'rag', 'retrieval': 'rag',
    # Reasoning (신규)
    'reasoning': 'reasoning', 'benchmark': 'reasoning', 'evaluation': 'reasoning',
    # Agent
    'agent': 'agent', 'agents': 'agent', 'tools': 'agent',
    # Technique (나머지)
    'technique': 'technique', 'attention-mechanism': 'technique',
    'prompting': 'technique', 'icl': 'technique',
    'few-shot-learning': 'technique', 'security': 'technique',
    # Code (신규)
    'code': 'code', 'code-generation': 'code',
}

# Colab 카테고리 매핑
COLAB_CATEGORY_MAP = {
    'efficient-ai': 'efficiency',
    'core-techniques': 'technique',
}

# Architecture 카테고리 매핑
ARCH_CATEGORY_MAP = {
    'llm': 'llm', 'vision': 'vision', 'multimodal': 'multimodal',
    'ssm': 'ssm', 'diffusion': 'diffusion', 'agent': 'agent',
}

# Data 카테고리: 기본값 — content.json의 category_slug 사용
# ML 카테고리: 고정 'ml' — content.json의 sub_category로 서브카테고리 결정


class CategoryMapper:
    """import 스크립트에서 카테고리를 DB slug으로 변환."""

    def __init__(self):
        self._category_cache = {}

    def resolve(self, source_category: str, post_type: str = 'article') -> str:
        """소스 카테고리 → DB slug 변환.

        Args:
            source_category: content.json의 category_slug 또는 papers의 category 필드
            post_type: paper_review, tutorial, article 등

        Returns:
            DB Category slug
        """
        if post_type == 'paper_review':
            return PAPER_CATEGORY_MAP.get(source_category, 'technique')

        if post_type == 'architecture':
            return ARCH_CATEGORY_MAP.get(source_category, 'llm')

        if source_category in COLAB_CATEGORY_MAP:
            return COLAB_CATEGORY_MAP[source_category]

        # 직접 매핑 (category_slug이 이미 DB slug인 경우)
        return source_category

    def get_category(self, slug: str):
        """slug으로 Category 객체 조회 (캐시)."""
        if slug not in self._category_cache:
            from blog.models import Category
            self._category_cache[slug] = Category.objects.filter(slug=slug).first()
        return self._category_cache[slug]

    def resolve_with_fallback(self, source_category: str, post_type: str,
                               fallback_slug: str = 'technique'):
        """카테고리 해석 + DB 존재 확인. 없으면 fallback 사용."""
        slug = self.resolve(source_category, post_type)
        cat = self.get_category(slug)
        if cat is None:
            cat = self.get_category(fallback_slug)
        return cat
