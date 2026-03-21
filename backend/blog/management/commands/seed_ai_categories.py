"""
20.AI 카테고리 계층 구조를 생성하는 관리 명령어 (7개 서브카테고리).
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
        "description": "efficient-ai, alignment, rlhf, rag, prompting, benchmark, evaluation, data, security",
    },
]


class Command(BaseCommand):
    help = "20.AI 카테고리와 7개 하위 카테고리를 생성(upsert)합니다."

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

        self.stdout.write(self.style.SUCCESS("\nAI 카테고리 시딩 완료! (7개 구조)"))
