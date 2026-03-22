"""
40.ML 카테고리 계층 구조를 생성하는 관리 명령어 (12개 서브카테고리).
사용법:
    python manage.py seed_ml_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


ML_CHILDREN = [
    {
        "code": "40.ML.01",
        "name": "기초 & 개론",
        "slug": "fundamentals",
        "icon": "BookOpen",
        "color": "#10B981",
    },
    {
        "code": "40.ML.02",
        "name": "수학 기초",
        "slug": "math-foundations",
        "icon": "Calculator",
        "color": "#6366F1",
    },
    {
        "code": "40.ML.03",
        "name": "데이터 전처리",
        "slug": "preprocessing",
        "icon": "Filter",
        "color": "#F59E0B",
    },
    {
        "code": "40.ML.04",
        "name": "지도학습 - 회귀",
        "slug": "supervised-regression",
        "icon": "TrendingUp",
        "color": "#3B82F6",
    },
    {
        "code": "40.ML.05",
        "name": "지도학습 - 분류",
        "slug": "supervised-classification",
        "icon": "Tag",
        "color": "#8B5CF6",
    },
    {
        "code": "40.ML.06",
        "name": "앙상블",
        "slug": "ensemble",
        "icon": "Layers",
        "color": "#F97316",
    },
    {
        "code": "40.ML.07",
        "name": "비지도학습",
        "slug": "unsupervised",
        "icon": "Grid",
        "color": "#EC4899",
    },
    {
        "code": "40.ML.08",
        "name": "모델 평가",
        "slug": "model-evaluation",
        "icon": "BarChart",
        "color": "#14B8A6",
    },
    {
        "code": "40.ML.09",
        "name": "인과추론",
        "slug": "causal-inference",
        "icon": "GitBranch",
        "color": "#EF4444",
    },
    {
        "code": "40.ML.10",
        "name": "심화 알고리즘",
        "slug": "advanced-algorithms",
        "icon": "Cpu",
        "color": "#6B7280",
    },
    {
        "code": "40.ML.11",
        "name": "응용 도메인",
        "slug": "applications",
        "icon": "Globe",
        "color": "#0EA5E9",
    },
    {
        "code": "40.ML.12",
        "name": "MLOps",
        "slug": "mlops",
        "icon": "Settings",
        "color": "#84CC16",
    },
]


class Command(BaseCommand):
    help = "40.ML 카테고리와 12개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 upsert
        parent, created = Category.objects.update_or_create(
            slug="ml",
            defaults={
                "name": "ML",
                "code": "40.ML",
                "icon": "Brain",
                "color": "#10B981",
                "order": 40,
            },
        )
        status = "생성" if created else "업데이트"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.slug}) - {status}")

        # 하위 카테고리 upsert
        for idx, child_data in enumerate(ML_CHILDREN):
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

        self.stdout.write(self.style.SUCCESS("\nML 카테고리 시딩 완료! (12개 서브카테고리)"))
