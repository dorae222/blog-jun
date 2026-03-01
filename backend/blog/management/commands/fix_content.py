"""
포스트 콘텐츠 자동 수정 커맨드

사용법:
  python manage.py fix_content --fix=html --dry-run
  python manage.py fix_content --fix=html
  python manage.py fix_content --fix=jupyter --category=ai-ml
  python manage.py fix_content --fix=meta
"""
import re
from django.core.management.base import BaseCommand
from blog.models import Post


def fix_html_tags(content):
    """HTML 태그를 마크다운으로 변환 또는 제거"""
    # <u>text</u> → text (밑줄 마크다운 없음, 그냥 제거)
    content = re.sub(r'<u>(.*?)</u>', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
    # <br> → 빈 줄
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    # <b>text</b> / <strong>text</strong> → **text**
    content = re.sub(r'<(?:b|strong)>(.*?)</(?:b|strong)>', r'**\1**', content, flags=re.DOTALL | re.IGNORECASE)
    # <i>text</i> / <em>text</em> → *text*
    content = re.sub(r'<(?:i|em)>(.*?)</(?:i|em)>', r'*\1*', content, flags=re.DOTALL | re.IGNORECASE)
    # <span ...>text</span> → text
    content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
    # 나머지 안전한 인라인 태그 제거
    content = re.sub(r'<(?:p|div|font)[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</(?:p|div|font)>', '\n', content, flags=re.IGNORECASE)
    return content


def fix_jupyter(content):
    """Jupyter 잔재를 마크다운 코드블록으로 변환하거나 제거"""
    # attachment: 줄 제거
    content = re.sub(r'^attachment:[^\n]*\n?', '', content, flags=re.MULTILINE)
    # In [N]: / Out[N]: 패턴을 코드 접두사 제거
    content = re.sub(r'^In\s*\[\d+\]:\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^Out\s*\[\d+\]:\s*', '', content, flags=re.MULTILINE)
    # %%python 등 셀 매직 제거
    content = re.sub(r'^%%\w+\n?', '', content, flags=re.MULTILINE)
    return content


def fix_meta_remnants(content):
    """메타데이터 잔재 제거"""
    META_RE = re.compile(
        r'^(Category|Quality grade|Created|Updated|Tags|Type|Status|Priority):\s*.+\n?',
        re.MULTILINE | re.IGNORECASE
    )
    return META_RE.sub('', content)


def fix_wiki_links(content):
    """위키링크를 일반 텍스트로 변환
    [[링크|표시텍스트]] → 표시텍스트
    [[링크]] → 링크
    """
    content = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', content)
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    return content


def fix_dupe_title(content, title):
    """content 첫 줄의 h1이 post.title과 동일하면 제거"""
    lines = content.split('\n')
    if lines and re.match(r'^#\s+', lines[0]):
        h1_text = re.sub(r'^#\s+', '', lines[0]).strip()
        if h1_text == title.strip():
            return '\n'.join(lines[1:]).lstrip('\n')
    return content


# content만 받는 fix 함수
FIX_FUNCS = {
    'html': fix_html_tags,
    'jupyter': fix_jupyter,
    'meta': fix_meta_remnants,
    'wikilink': fix_wiki_links,
}

# title도 함께 받아야 하는 fix 함수 (post 객체 전달 방식)
FIX_FUNCS_WITH_TITLE = {
    'dupe_title': fix_dupe_title,
}


class Command(BaseCommand):
    help = '포스트 콘텐츠를 자동 수정합니다.'

    def add_arguments(self, parser):
        all_choices = list(FIX_FUNCS.keys()) + list(FIX_FUNCS_WITH_TITLE.keys())
        parser.add_argument(
            '--fix',
            required=True,
            choices=all_choices,
            help='수정 유형: html | jupyter | meta | wikilink | dupe_title',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 영향 범위만 출력',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='특정 카테고리 slug만 처리',
        )

    def handle(self, *args, **options):
        fix_key = options['fix']
        dry_run = options['dry_run']
        needs_title = fix_key in FIX_FUNCS_WITH_TITLE

        fix_func = FIX_FUNCS_WITH_TITLE[fix_key] if needs_title else FIX_FUNCS[fix_key]

        qs = Post.objects.all()
        if options['category']:
            qs = qs.filter(category__slug=options['category'])

        modified = 0
        for post in qs.iterator(chunk_size=200):
            original = post.content or ''
            fixed = fix_func(original, post.title) if needs_title else fix_func(original)
            if fixed != original:
                modified += 1
                if dry_run:
                    self.stdout.write(f'  [dry-run] {post.slug}')
                else:
                    post.content = fixed
                    post.save(update_fields=['content'])

        mode = '[dry-run] ' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}완료: {modified}개 포스트 수정됨 (fix={fix_key})'
            )
        )
