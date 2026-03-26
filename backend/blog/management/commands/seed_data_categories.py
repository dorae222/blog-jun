"""
30.Data 카테고리 계층 구조를 생성하는 관리 명령어 (4개 서브카테고리).

사용법:
    python manage.py seed_data_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


DATA_CHILDREN = [
    {
        "code": "30.Data.01",
        "name": "Big Data",
        "slug": "big-data",
        "icon": "Database",
        "color": "#66CCFF",
        "description": "Hadoop, Spark, HDFS, MapReduce, Pig, Hive, Sqoop, 빅데이터 개론",
    },
    {
        "code": "30.Data.02",
        "name": "Database",
        "slug": "database",
        "icon": "Database",
        "color": "#4DB33D",
        "description": "MongoDB, PostgreSQL, pgvector, Neo4j, Redis",
    },
    {
        "code": "30.Data.03",
        "name": "Pipeline",
        "slug": "pipeline",
        "icon": "GitBranch",
        "color": "#0EA5E9",
        "description": "빅데이터 수집, 처리, 시각화 파이프라인",
    },
]


class Command(BaseCommand):
    help = "30.Data 카테고리와 4개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        parent, created = Category.objects.update_or_create(
            slug="data-engineering",
            defaults={
                "code": "30.Data",
                "name": "Data Engineering",
                "icon": "Data",
                "color": "#14B8A6",
                "order": 30,
            },
        )
        status = "생성" if created else "업데이트"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.code}) - {status}")

        for idx, child_data in enumerate(DATA_CHILDREN):
            try:
                child = Category.objects.get(slug=child_data["slug"])
                child.code = child_data["code"]
                child.name = child_data["name"]
                child.icon = child_data["icon"]
                child.color = child_data["color"]
                child.parent = parent
                child.order = idx + 1
                child.save()
                created = False
            except Category.DoesNotExist:
                child = Category.objects.create(
                    slug=child_data["slug"],
                    code=child_data["code"],
                    name=child_data["name"],
                    icon=child_data["icon"],
                    color=child_data["color"],
                    parent=parent,
                    order=idx + 1,
                )
                created = True
            status = "생성" if created else "업데이트"
            self.stdout.write(f"  {child.code} - {child.name} ({child.slug}): {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\nData Engineering 카테고리 시딩 완료! ({len(DATA_CHILDREN)}개 서브카테고리)"
        ))
