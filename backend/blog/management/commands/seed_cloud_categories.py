"""
10.Cloud 카테고리 계층 구조를 생성하는 관리 명령어 (4개 서브카테고리).
사용법:
    python manage.py seed_cloud_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


CLOUD_CHILDREN = [
    {
        "code": "10.Cloud.01",
        "name": "AWS",
        "slug": "aws",
        "icon": "aws",
        "color": "#FF9900",
        "description": "amazon web services",
    },
    {
        "code": "10.Cloud.02",
        "name": "Docker",
        "slug": "docker",
        "icon": "docker",
        "color": "#2496ED",
        "description": "docker, container",
    },
    {
        "code": "10.Cloud.03",
        "name": "LXD",
        "slug": "lxd",
        "icon": "lxd",
        "color": "#E95420",
        "description": "lxd, system container",
    },
    {
        "code": "10.Cloud.04",
        "name": "DevOps",
        "slug": "devops",
        "icon": "devops",
        "color": "#0DB7ED",
        "description": "cicd, deployment, monitoring",
    },
]


class Command(BaseCommand):
    help = "10.Cloud 카테고리와 4개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 upsert (slug 기준)
        parent, created = Category.objects.update_or_create(
            slug="cloud",
            defaults={
                "code": "10.Cloud",
                "name": "Cloud",
                "icon": "Cloud",
                "color": "#FF9900",
                "order": 10,
            },
        )
        status = "생성" if created else "업데이트"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.code}) - {status}")

        # 하위 카테고리 upsert (slug 기준, 명시적 get-then-update)
        for idx, child_data in enumerate(CLOUD_CHILDREN):
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

        self.stdout.write(self.style.SUCCESS("\nCloud 카테고리 시딩 완료! (4개 구조)"))
