"""
20.AI 카테고리 계층 구조를 생성하는 관리 명령어 (5개 서브카테고리).
사용법:
    python manage.py seed_ai_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


AI_CHILDREN = [
    {
        "code": "20.AI.01",
        "name": "Model Architecture",
        "slug": "model-architecture",
        "icon": "🏗️",
        "color": "#6366F1",
        "description": "transformer, nlp, llm, vision, multimodal, ssm",
    },
    {
        "code": "20.AI.02",
        "name": "Efficient AI",
        "slug": "efficient-ai",
        "icon": "⚡",
        "color": "#F59E0B",
        "description": "moe, scaling, efficiency",
    },
    {
        "code": "20.AI.03",
        "name": "Alignment & RLHF",
        "slug": "alignment-rlhf",
        "icon": "🎯",
        "color": "#10B981",
        "description": "alignment, finetuning",
    },
    {
        "code": "20.AI.04",
        "name": "RAG & Knowledge",
        "slug": "rag-knowledge",
        "icon": "🔍",
        "color": "#3B82F6",
        "description": "rag, retrieval",
    },
    {
        "code": "20.AI.05",
        "name": "Core Techniques",
        "slug": "core-techniques",
        "icon": "🔬",
        "color": "#8B5CF6",
        "description": "technique, foundations",
    },
    {
        "code": "20.AI.06",
        "name": "Prompting & ICL",
        "slug": "prompting-icl",
        "icon": "💬",
        "color": "#EC4899",
        "description": "prompting, in-context learning, instruction tuning",
    },
    {
        "code": "20.AI.07",
        "name": "Benchmark & Evaluation",
        "slug": "benchmark-eval",
        "icon": "📊",
        "color": "#14B8A6",
        "description": "benchmark, evaluation, leaderboard",
    },
    {
        "code": "20.AI.08",
        "name": "Agents & Tools",
        "slug": "agents-tools",
        "icon": "🛠️",
        "color": "#F97316",
        "description": "agents, tool use, planning",
    },
    {
        "code": "20.AI.09",
        "name": "Data & Security",
        "slug": "data-security",
        "icon": "🔒",
        "color": "#6B7280",
        "description": "data, privacy, security, membership inference",
    },
]


class Command(BaseCommand):
    help = "20.AI 카테고리와 9개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 upsert
        parent, created = Category.objects.update_or_create(
            code="20.AI",
            defaults={
                "name": "AI/ML",
                "slug": "ai-ml",
                "icon": "🤖",
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

        self.stdout.write(self.style.SUCCESS("\nAI 카테고리 시딩 완료! (9개 구조)"))
