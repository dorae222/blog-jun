"""
20.AI 카테고리 계층 구조를 생성하는 관리 명령어.
사용법:
    python manage.py seed_ai_categories
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from blog.models import Category


AI_CHILDREN = [
    {"code": "20.AI.01", "name": "Model Architecture"},
    {"code": "20.AI.02", "name": "Efficiency"},
    {"code": "20.AI.03", "name": "Sparse Model & Scaling"},
    {"code": "20.AI.04", "name": "Retrieval-Augmented Methods"},
    {"code": "20.AI.05", "name": "Prompting & In-Context Learning"},
    {"code": "20.AI.06", "name": "Benchmark & Evaluation"},
    {"code": "20.AI.07", "name": "Tools & RL"},
    {"code": "20.AI.08", "name": "Data & Security"},
    {"code": "20.AI.09", "name": "Foundations"},
]


class Command(BaseCommand):
    help = "20.AI 카테고리와 하위 카테고리를 생성합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 생성
        parent, created = Category.objects.get_or_create(
            code="20.AI",
            defaults={
                "name": "AI/ML",
                "slug": "ai-ml",
                "icon": "\U0001f916",
                "color": "#FF6F00",
                "order": 20,
            },
        )
        status = "생성" if created else "이미 존재"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.code}) - {status}")

        # 하위 카테고리 생성
        for idx, child_data in enumerate(AI_CHILDREN):
            child, created = Category.objects.get_or_create(
                code=child_data["code"],
                defaults={
                    "name": child_data["name"],
                    "slug": slugify(child_data["name"], allow_unicode=True),
                    "parent": parent,
                    "order": idx + 1,
                },
            )
            status = "생성" if created else "이미 존재"
            self.stdout.write(f"  {child.code} - {child.name}: {status}")

        self.stdout.write(self.style.SUCCESS("\nAI 카테고리 시딩 완료!"))
