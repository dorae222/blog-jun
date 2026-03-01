"""
포스트 콘텐츠 감사 커맨드

사용법:
  python manage.py audit_posts --save=/tmp/audit.json
  python manage.py audit_posts --category=ai-ml
"""
import json
import re
from django.core.management.base import BaseCommand
from blog.models import Post


# 감사 패턴 정의
PATTERNS = {
    'HTML_TAG': re.compile(
        r'<(u|br|span|div|p|b|i|em|strong|font|table|tr|td|th|ul|ol|li|hr|h[1-6])'
        r'(\s[^>]*)?>',
        re.IGNORECASE
    ),
    'JUPYTER': re.compile(
        r'(In\s*\[\d+\]:|Out\s*\[\d+\]:|%%\w+|attachment:[^\s]+)',
        re.MULTILINE
    ),
    'META_REMNANT': re.compile(
        r'^(Category:|Quality grade:|Created:|Updated:|Tags:|Type:)\s*.+$',
        re.MULTILINE | re.IGNORECASE
    ),
    'ENCODING': re.compile(r'\x00|[\ufffd\ufffe\uffff]'),
}

SHORT_THRESHOLD = 100


def detect_issues(content):
    issues = []
    if len(content) < SHORT_THRESHOLD:
        issues.append('SHORT')
    for code, pattern in PATTERNS.items():
        if pattern.search(content):
            issues.append(code)
    return issues


class Command(BaseCommand):
    help = '포스트 콘텐츠를 감사하고 이슈를 JSON 파일로 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            type=str,
            default='/tmp/audit.json',
            help='결과를 저장할 JSON 파일 경로 (기본값: /tmp/audit.json)',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='특정 카테고리 slug만 감사',
        )

    def handle(self, *args, **options):
        qs = Post.objects.select_related('category', 'author').all()
        if options['category']:
            qs = qs.filter(category__slug=options['category'])

        total = qs.count()
        self.stdout.write(f'감사 시작: {total}개 포스트')

        results = []
        issue_count = 0

        for post in qs.iterator(chunk_size=200):
            issues = detect_issues(post.content or '')
            if issues:
                issue_count += 1
                results.append({
                    'id': post.id,
                    'slug': post.slug,
                    'title': post.title,
                    'status': post.status,
                    'category': post.category.slug if post.category else None,
                    'content_length': len(post.content or ''),
                    'issues': issues,
                })

        save_path = options['save']
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_audited': total,
                'total_issues': issue_count,
                'results': results,
            }, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'완료: {total}개 중 {issue_count}개 이슈 발견 → {save_path}'
            )
        )
