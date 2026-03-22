"""
ML 포스트를 content.json의 sub_category에 따라 올바른 서브카테고리로 재배정합니다.
사용법:
    python manage.py reassign_ml_posts
    python manage.py reassign_ml_posts --dry-run
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from blog.models import Category, Post


# content.json sub_category → DB Category slug 매핑
SUB_CATEGORY_MAP = {
    "fundamentals": "fundamentals",
    "math-foundations": "math-foundations",
    "data-engineering": "preprocessing",        # slug 충돌 방지
    "supervised-regression": "supervised-regression",
    "supervised-classification": "supervised-classification",
    "ensemble": "ensemble",
    "unsupervised": "unsupervised",
    "evaluation": "model-evaluation",           # 혼재 통일
    "model-evaluation": "model-evaluation",
    "causal-inference": "causal-inference",
    "advanced-algorithms": "advanced-algorithms",
    "applications": "applications",
    "mlops": "mlops",
}

_cmd_file = Path(__file__).resolve()
_candidates = [
    _cmd_file.parents[4] / "pipeline" / "data" / "ml_written",   # 로컬 개발 (blog-jun/)
    Path("/opt/blog-jun/pipeline/data/ml_written"),                # 서버 Docker
]
ML_WRITTEN_DIR = next((p for p in _candidates if p.exists()), _candidates[0])


class Command(BaseCommand):
    help = "ML 포스트를 올바른 서브카테고리에 재배정합니다."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="실제 변경 없이 미리보기")
        parser.add_argument("--data-dir", default=None, help="ml_written 디렉토리 경로 (기본값 자동 감지)")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        ml_dir = Path(options["data_dir"]) if options.get("data_dir") else ML_WRITTEN_DIR

        if not ml_dir.exists():
            self.stderr.write(f"ml_written 디렉토리 없음: {ml_dir}")
            return

        # 서브카테고리 Category 캐시
        cat_cache = {c.slug: c for c in Category.objects.all()}

        updated = 0
        skipped = 0
        errors = 0

        for item_dir in sorted(ml_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            content_json = item_dir / "content.json"
            if not content_json.exists():
                continue

            data = json.load(open(content_json, encoding="utf-8"))
            slug = data.get("slug", "")
            json_sub = data.get("sub_category", "")
            db_sub_slug = SUB_CATEGORY_MAP.get(json_sub)

            if not db_sub_slug:
                self.stderr.write(f"  [WARN] 매핑 없음: {slug} (sub_category={json_sub})")
                errors += 1
                continue

            sub_cat = cat_cache.get(db_sub_slug)
            if not sub_cat:
                self.stderr.write(f"  [WARN] DB에 카테고리 없음: {db_sub_slug} (먼저 seed_ml_categories 실행)")
                errors += 1
                continue

            try:
                post = Post.objects.get(slug=slug)
            except Post.DoesNotExist:
                self.stderr.write(f"  [WARN] Post 없음: {slug}")
                errors += 1
                continue

            if post.category_id == sub_cat.id:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] {slug}: {post.category.slug if post.category else 'None'} → {db_sub_slug}")
            else:
                post.category = sub_cat
                post.save(update_fields=["category"])
                self.stdout.write(f"  [UPDATE] {slug} → {db_sub_slug}")
            updated += 1

        action = "예정" if dry_run else "완료"
        self.stdout.write(self.style.SUCCESS(
            f"\n재배정 {action}: {updated}개, 이미 올바름: {skipped}개, 오류: {errors}개"
        ))
