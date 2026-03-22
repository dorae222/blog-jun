"""
새로운 Cloud 시리즈 컨텐츠(docker/, lxd/, devops/)를 DB에 임포트.
frontmatter를 파싱하여 Post 레코드 생성, 서브카테고리 자동 할당.

사용법:
    python manage.py import_cloud_content --dry-run
    python manage.py import_cloud_content
    python manage.py import_cloud_content --category docker
"""
import re
from datetime import datetime, timezone
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from blog.models import Category, Post, Tag


# 컨텐츠 디렉토리 → 서브카테고리 slug 매핑
DIR_TO_CATEGORY = {
    'docker': 'docker',
    'lxd': 'lxd',
    'devops': 'devops',
}

CONTENT_BASE = Path('/app/content')


def _parse_frontmatter(text):
    """YAML frontmatter 파싱 (간단한 key: value 형식)"""
    fm = {}
    content = text
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            yaml_block = text[3:end].strip()
            content = text[end + 3:].strip()
            for line in yaml_block.splitlines():
                line = line.strip()
                if ':' not in line:
                    continue
                key, _, val = line.partition(':')
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # 배열 형태: ["tag1", "tag2"] 또는 [tag1, tag2]
                if val.startswith('[') and val.endswith(']'):
                    inner = val[1:-1]
                    items = [
                        v.strip().strip('"').strip("'")
                        for v in inner.split(',')
                        if v.strip()
                    ]
                    fm[key] = items
                else:
                    fm[key] = val
    return fm, content


def _get_or_create_tag(name):
    """태그 가져오거나 생성"""
    slug = slugify(name, allow_unicode=True)
    tag, _ = Tag.objects.get_or_create(
        slug=slug,
        defaults={'name': name}
    )
    return tag


class Command(BaseCommand):
    help = "docker/, lxd/, devops/ 컨텐츠를 DB에 임포트합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 저장 없이 미리보기',
        )
        parser.add_argument(
            '--category',
            choices=list(DIR_TO_CATEGORY.keys()),
            help='특정 카테고리만 임포트 (기본: 전체)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_cat = options.get('category')
        prefix = "[DRY-RUN] " if dry_run else ""

        # 기본 author (superuser 또는 첫 번째 유저)
        try:
            author = User.objects.filter(is_superuser=True).first()
            if not author:
                author = User.objects.first()
            if not author:
                self.stderr.write("유저가 없습니다. createsuperuser를 먼저 실행하세요.")
                return
        except Exception as e:
            self.stderr.write(f"유저 로드 실패: {e}")
            return

        self.stdout.write(f"\n{prefix}import_cloud_content 시작 (author: {author.username})")
        self.stdout.write("=" * 60)

        created_total = 0
        skipped_total = 0

        dirs_to_process = (
            {only_cat: DIR_TO_CATEGORY[only_cat]}
            if only_cat
            else DIR_TO_CATEGORY
        )

        for dir_name, cat_slug in dirs_to_process.items():
            content_dir = CONTENT_BASE / dir_name
            if not content_dir.exists():
                self.stdout.write(f"  [SKIP] {content_dir} 없음")
                continue

            # 서브카테고리 가져오기
            try:
                category = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                self.stderr.write(
                    f"  [ERROR] 카테고리 slug='{cat_slug}' 없음. "
                    f"seed_cloud_categories를 먼저 실행하세요."
                )
                continue

            md_files = sorted(content_dir.glob('*.md'))
            self.stdout.write(f"\n[{dir_name}] → {cat_slug}: {len(md_files)}개 파일")

            created = 0
            skipped = 0

            for md_file in md_files:
                raw = md_file.read_text(encoding='utf-8')
                fm, body = _parse_frontmatter(raw)

                title = fm.get('title', md_file.stem)
                slug = fm.get('slug', slugify(title, allow_unicode=True))
                tags_raw = fm.get('tags', [])
                status = fm.get('status', 'published')
                post_type = fm.get('post_type', 'article')
                quality_score = float(fm.get('quality_score', 8.0))
                created_at_str = fm.get('created_at', '')

                # 중복 slug 체크
                if Post.objects.filter(slug=slug).exists():
                    self.stdout.write(f"  [SKIP] 이미 존재: {slug}")
                    skipped += 1
                    continue

                # summary: 본문 첫 단락 (최대 300자)
                summary = re.sub(r'^#+\s+.*', '', body, flags=re.MULTILINE)
                summary = re.sub(r'\s+', ' ', summary).strip()[:300]

                # published_at
                published_at = None
                if created_at_str:
                    try:
                        published_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        )
                    except (ValueError, TypeError):
                        published_at = datetime.now(timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)

                if dry_run:
                    self.stdout.write(
                        f"  {prefix}[CREATE] {slug} ({cat_slug}) — {title}"
                    )
                    created += 1
                    continue

                post = Post.objects.create(
                    title=title,
                    slug=slug,
                    content=body,
                    summary=summary,
                    category=category,
                    author=author,
                    status=status,
                    post_type=post_type,
                    quality_score=quality_score,
                    source_path=str(md_file),
                    published_at=published_at,
                )

                # 태그 처리
                for tag_name in tags_raw:
                    if tag_name.strip():
                        tag = _get_or_create_tag(tag_name.strip())
                        post.tags.add(tag)

                self.stdout.write(f"  [CREATE] {slug} ({cat_slug})")
                created += 1

            self.stdout.write(
                f"  → 생성: {created}개, 건너뜀: {skipped}개"
            )
            created_total += created
            skipped_total += skipped

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}완료: 총 생성 {created_total}개, 건너뜀 {skipped_total}개"
        ))
