"""Django ORM 헬퍼 — 임포트 스크립트 공통 패턴 추출."""
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Django 부트스트랩 (pipeline에서 직접 실행 시)
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / 'backend'
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


def ensure_django():
    """Django가 초기화되어 있지 않으면 setup() 호출."""
    import django
    if not django.apps.apps.ready:
        django.setup()


def get_or_create_tags(tag_names: list[str]):
    """태그 목록을 받아 Tag 객체 리스트 반환 (없으면 생성)."""
    ensure_django()
    from django.utils.text import slugify
    from blog.models import Tag

    tags = []
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
        slug = slugify(name, allow_unicode=True)[:50]
        if not slug:
            continue
        tag, _ = Tag.objects.get_or_create(
            slug=slug,
            defaults={'name': name[:100]},
        )
        tags.append(tag)
    return tags


def make_unique_slug(title: str, model_class=None) -> str:
    """제목에서 유니크 slug 생성. 충돌 시 -2, -3 등 접미사."""
    ensure_django()
    from django.utils.text import slugify
    if model_class is None:
        from blog.models import Post
        model_class = Post

    base = slugify(title, allow_unicode=True)[:200]
    if not base:
        base = 'untitled'
    slug = base
    counter = 2
    while model_class.objects.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


def safe_datetime(ts) -> datetime | None:
    """다양한 형식의 타임스탬프를 datetime으로 변환."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d'):
        try:
            return datetime.strptime(str(ts), fmt)
        except ValueError:
            continue
    return None


def get_default_author():
    """기본 작성자 (admin 또는 첫 번째 사용자) 반환."""
    ensure_django()
    from django.contrib.auth.models import User
    return User.objects.filter(is_superuser=True).first() or User.objects.first()


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """마크다운 frontmatter 파싱. (메타데이터 dict, 본문) 반환."""
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    meta = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            meta[key.strip()] = val.strip()
    return meta, parts[2].lstrip('\n')
