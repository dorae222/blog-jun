"""
포스트 품질 검토 및 아카이브 커맨드

사용법:
  python manage.py review_post_quality --dry-run   # 후보 목록 출력만
  python manage.py review_post_quality             # status='draft'로 변경 + 리포트 생성
  python manage.py review_post_quality --output=/app/archived_posts_report.txt
"""
import re
from datetime import date
from django.core.management.base import BaseCommand
from blog.models import Post

MIN_CHARS = 200
TODO_PATTERN = re.compile(r'\bTODO\b|placeholder|\.\.\.\s*$', re.IGNORECASE | re.MULTILINE)
# 마크다운 제거용: 인라인 코드, 코드블록, 이미지, 링크, 헤더, 강조 등
_MD_STRIP_RE = re.compile(
    r'```[\s\S]*?```'          # 펜스 코드블록
    r'|`[^`]+`'                # 인라인 코드
    r'|!\[[^\]]*\]\([^)]*\)'  # 이미지
    r'|\[[^\]]*\]\([^)]*\)'   # 링크
    r'|^#{1,6}\s+'             # 헤더 마커
    r'|[*_~]+'                 # 강조 마커
    r'|\|[^\n]*'               # 테이블 셀
    r'|^\s*[-*+]\s+'           # 리스트 마커
    r'|^\s*\d+\.\s+',          # 순서 있는 리스트
    re.MULTILINE,
)


def strip_markdown(text):
    """마크다운 문법 제거 후 실제 텍스트만 반환"""
    text = _MD_STRIP_RE.sub(' ', text)
    # 연속 공백/줄바꿈 정리
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def score_post(post):
    """품질 기준 평가 → 이유 목록 반환 (비어있으면 통과)"""
    content = post.content or ''
    reasons = []

    plain = strip_markdown(content)
    if len(plain) < MIN_CHARS:
        reasons.append(f'너무 짧음 ({len(plain)}자)')

    if not re.search(r'^#{1,4}\s', content, re.MULTILINE):
        reasons.append('헤더 없음')

    if TODO_PATTERN.search(content):
        reasons.append('미완성 마커(TODO/placeholder/...)')

    # 제목 ≈ 전체 내용: 본문이 제목과 거의 동일한 경우
    if plain and post.title and plain.strip() == post.title.strip():
        reasons.append('제목 = 전체 내용')

    return reasons


def build_report(archived, merge_candidates, total_reviewed, dry_run):
    today = date.today().isoformat()
    lines = [
        '# 아카이브된 포스트 목록',
        f'생성일: {today} | 검토: {total_reviewed}개 | 아카이브: {len(archived)}개 | 병합후보: {len(merge_candidates)}개',
        f'dry-run: {"예 (실제 변경 없음)" if dry_run else "아니오 (status=draft 변경됨)"}',
        '',
        '## ARCHIVE',
        '| # | 제목 | Slug | 이유 |',
        '|---|------|------|------|',
    ]
    for i, item in enumerate(archived, 1):
        lines.append(f'| {i} | {item["title"]} | {item["slug"]} | {item["reasons"]} |')

    lines += [
        '',
        '## MERGE_CANDIDATE',
        '| # | 제목 | Slug | 메모 |',
        '|---|------|------|------|',
    ]
    for i, item in enumerate(merge_candidates, 1):
        lines.append(f'| {i} | {item["title"]} | {item["slug"]} | {item["reasons"]} |')

    return '\n'.join(lines) + '\n'


class Command(BaseCommand):
    help = 'published 포스트 품질 검토 후 낮은 품질 포스트를 draft로 변경합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='실제 변경 없이 후보 목록만 출력',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='/app/archived_posts_report.txt',
            help='리포트 저장 경로 (기본값: /app/archived_posts_report.txt)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        output_path = options['output']

        qs = Post.objects.filter(status=Post.Status.PUBLISHED).select_related('category')
        total = qs.count()
        self.stdout.write(f'검토 시작: published 포스트 {total}개')

        archived = []
        merge_candidates = []
        to_draft_ids = []

        for post in qs.iterator(chunk_size=200):
            reasons = score_post(post)
            if not reasons:
                continue

            reason_str = ' / '.join(reasons)

            # 헤더 없음만 단독으로 해당하는 경우 병합 후보, 나머지는 아카이브
            if reasons == ['헤더 없음']:
                merge_candidates.append({
                    'title': post.title,
                    'slug': post.slug,
                    'reasons': reason_str,
                })
            else:
                archived.append({
                    'title': post.title,
                    'slug': post.slug,
                    'reasons': reason_str,
                })
                to_draft_ids.append(post.id)

        # dry-run이 아닌 경우 실제 변경
        if not dry_run and to_draft_ids:
            updated = Post.objects.filter(id__in=to_draft_ids).update(status=Post.Status.DRAFT)
            self.stdout.write(self.style.WARNING(f'{updated}개 포스트를 draft로 변경했습니다.'))

        # 리포트 출력
        self.stdout.write('\n--- ARCHIVE 후보 ---')
        for item in archived:
            self.stdout.write(f'  [{item["slug"]}] {item["title"]}')
            self.stdout.write(f'    이유: {item["reasons"]}')

        self.stdout.write('\n--- MERGE_CANDIDATE ---')
        for item in merge_candidates:
            self.stdout.write(f'  [{item["slug"]}] {item["title"]}')
            self.stdout.write(f'    이유: {item["reasons"]}')

        # 리포트 파일 저장
        report = build_report(archived, merge_candidates, total, dry_run)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n완료: {total}개 검토 | 아카이브 {len(archived)}개 | 병합후보 {len(merge_candidates)}개 → {output_path}'
            )
        )
