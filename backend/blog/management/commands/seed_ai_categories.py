"""
20.AI 카테고리 계층 구조를 생성하는 관리 명령어 (12개 서브카테고리).
사용법:
    python manage.py seed_ai_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


AI_CHILDREN = [
    {
        "code": "20.AI.01",
        "name": "LLM",
        "slug": "llm",
        "icon": "Brain",
        "color": "#6366F1",
        "description": "transformer, nlp, llm",
    },
    {
        "code": "20.AI.02",
        "name": "SSM",
        "slug": "ssm",
        "icon": "Zap",
        "color": "#F59E0B",
        "description": "state space model, mamba, rwkv",
    },
    {
        "code": "20.AI.03",
        "name": "Diffusion",
        "slug": "diffusion",
        "icon": "Sparkles",
        "color": "#EC4899",
        "description": "diffusion, image generation, video generation",
    },
    {
        "code": "20.AI.04",
        "name": "Vision",
        "slug": "vision",
        "icon": "Eye",
        "color": "#10B981",
        "description": "vision transformer, detection, segmentation",
    },
    {
        "code": "20.AI.05",
        "name": "Multimodal",
        "slug": "multimodal",
        "icon": "Layers",
        "color": "#8B5CF6",
        "description": "vision-language, multimodal, omni",
    },
    {
        "code": "20.AI.06",
        "name": "Agent",
        "slug": "agent",
        "icon": "Bot",
        "color": "#F97316",
        "description": "agents, tool use, planning, reasoning",
    },
    {
        "code": "20.AI.07",
        "name": "Technique",
        "slug": "technique",
        "icon": "Wrench",
        "color": "#14B8A6",
        "description": "prompting, ICL, few-shot, SLM, long context, structured output",
    },
    {
        "code": "20.AI.08",
        "name": "Efficiency",
        "slug": "efficiency",
        "icon": "Gauge",
        "color": "#EF4444",
        "description": "양자화, 프루닝, 증류, MFU, 추론 최적화, ONNX, 서빙, NVLink",
    },
    {
        "code": "20.AI.09",
        "name": "Reasoning",
        "slug": "reasoning",
        "icon": "Lightbulb",
        "color": "#FBBF24",
        "description": "CoT, test-time compute, reasoning 모델(o1/R1), evaluation, benchmark",
    },
    {
        "code": "20.AI.10",
        "name": "Training",
        "slug": "training",
        "icon": "GraduationCap",
        "color": "#3B82F6",
        "description": "파인튜닝, RLHF/DPO/IPO, 합성 데이터, distillation, model merging",
    },
    {
        "code": "20.AI.11",
        "name": "RAG",
        "slug": "rag",
        "icon": "Search",
        "color": "#8B5CF6",
        "description": "RAG, GraphRAG, knowledge graph, hybrid search, dense retrieval",
    },
    {
        "code": "20.AI.12",
        "name": "Code",
        "slug": "code",
        "icon": "Code",
        "color": "#06B6D4",
        "description": "코드 생성 모델, CodeLlama, StarCoder, code evaluation",
    },
]


class Command(BaseCommand):
    help = "20.AI 카테고리와 12개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 upsert
        parent, created = Category.objects.update_or_create(
            code="20.AI",
            defaults={
                "name": "AI/ML",
                "slug": "ai-ml",
                "icon": "Brain",
                "color": "#FF6F00",
                "order": 20,
            },
        )
        status = "생성" if created else "업데이트"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.code}) - {status}")

        # 하위 카테고리 upsert
        for idx, child_data in enumerate(AI_CHILDREN):
            child, created = Category.objects.update_or_create(
                code=child_data["code"],
                defaults={
                    "name": child_data["name"],
                    "slug": child_data["slug"],
                    "icon": child_data["icon"],
                    "color": child_data["color"],
                    "parent": parent,
                    "order": idx + 1,
                },
            )
            status = "생성" if created else "업데이트"
            self.stdout.write(f"  {child.code} - {child.name} ({child.slug}): {status}")

        self.stdout.write(self.style.SUCCESS(f"\nAI 카테고리 시딩 완료! ({len(AI_CHILDREN)}개 구조)"))
