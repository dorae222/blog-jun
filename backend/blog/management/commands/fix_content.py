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


_CODE_RE = re.compile(r'(```[\s\S]*?```|`[^`\n]+`)')


def _inner_text(html):
    """HTML 태그 제거 후 텍스트 추출 (기본 엔티티 변환 포함)"""
    text = re.sub(r'<[^>]+>', '', html)
    for entity, char in [('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                         ('&nbsp;', ' '), ('&quot;', '"')]:
        text = text.replace(entity, char)
    return text.strip()


def _convert_html_table(table_html):
    """HTML 테이블 → 마크다운 테이블
    rowspan/colspan 있는 복잡한 테이블은 파이프 구분 텍스트로 변환
    """
    rows_html = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
    if not rows_html:
        return _inner_text(table_html)

    has_complex = bool(re.search(r'(rowspan|colspan)\s*=', table_html, re.IGNORECASE))

    parsed = []
    for row_html in rows_html:
        splits = list(re.finditer(r'<t[dh][^>]*>', row_html, re.IGNORECASE))
        if not splits:
            continue
        cells = []
        for j, m in enumerate(splits):
            end = splits[j + 1].start() if j + 1 < len(splits) else len(row_html)
            raw = re.sub(r'</t[dh]>', '', row_html[m.end():end], flags=re.IGNORECASE)
            cells.append(_inner_text(raw))
        if any(cells):
            parsed.append(cells)

    if not parsed:
        return _inner_text(table_html)

    if has_complex:
        # rowspan/colspan → 파이프 구분 텍스트 (마크다운 테이블 구조 포기)
        return '\n'.join(' | '.join(row) for row in parsed)

    # 단순 테이블 → 마크다운
    col_count = max(len(r) for r in parsed)
    lines = ['| ' + ' | '.join(parsed[0]) + ' |',
             '| ' + ' | '.join(['---'] * col_count) + ' |']
    for row in parsed[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


def _convert_html_list(list_html, ordered=False):
    """HTML ul/ol → 마크다운 리스트 (닫는 태그 없는 경우도 처리)"""
    items = re.findall(
        r'<li[^>]*>(.*?)(?:</li>|(?=<li|</[uo]l>))',
        list_html, re.IGNORECASE | re.DOTALL
    )
    if not items:
        return _inner_text(list_html)
    result = []
    for i, item_html in enumerate(items):
        text = _inner_text(item_html)
        if text:
            result.append(f'{i + 1}. {text}' if ordered else f'- {text}')
    return '\n'.join(result)


def _convert_tables(text):
    """<table> 블록 변환 — 닫는 </table> 없는 경우(잘린 pandas HTML)도 처리"""
    result = []
    pos = 0
    for m in re.finditer(r'<table[^>]*>', text, re.IGNORECASE):
        if m.start() < pos:
            continue  # 이전 테이블 범위 안에 중첩된 태그 건너뜀
        result.append(text[pos:m.start()])
        close = re.search(r'</table>', text[m.start():], re.IGNORECASE)
        end = m.start() + close.end() if close else len(text)
        result.append(_convert_html_table(text[m.start():end]))
        pos = end
    result.append(text[pos:])
    return ''.join(result)


def _process_html(text):
    """코드블록 외부 영역의 HTML 태그를 마크다운으로 변환"""
    # <style> 블록 제거 (pandas DataFrame CSS 등)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # <thead>/<tbody>/<tfoot> 래퍼 태그 제거 (내용 유지)
    text = re.sub(r'</?(?:thead|tbody|tfoot)[^>]*>', '', text, flags=re.IGNORECASE)
    # 테이블 (</table> 없는 경우도 처리)
    text = _convert_tables(text)
    # 리스트
    text = re.sub(r'<ul[^>]*>.*?</ul>',
                  lambda m: _convert_html_list(m.group(0), ordered=False),
                  text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<ol[^>]*>.*?</ol>',
                  lambda m: _convert_html_list(m.group(0), ordered=True),
                  text, flags=re.IGNORECASE | re.DOTALL)
    # 헤딩 h1~h6
    for lvl in range(1, 7):
        hashes = '#' * lvl
        text = re.sub(
            rf'<h{lvl}[^>]*>(.*?)</h{lvl}>',
            lambda m, h=hashes: f'{h} {_inner_text(m.group(1))}',
            text, flags=re.IGNORECASE | re.DOTALL
        )
    # <hr> → ---
    text = re.sub(r'<hr\s*/?>', '\n---\n', text, flags=re.IGNORECASE)
    # 인라인 태그
    text = re.sub(r'<u>(.*?)</u>', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<(?:b|strong)>(.*?)</(?:b|strong)>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<(?:i|em)>(.*?)</(?:i|em)>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<(?:p|div|font)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|font)>', '\n', text, flags=re.IGNORECASE)
    return text


def fix_html_tags(content):
    """HTML 태그를 마크다운으로 변환 (코드블록 내용은 보호)"""
    parts = _CODE_RE.split(content)
    return ''.join(part if i % 2 == 1 else _process_html(part)
                   for i, part in enumerate(parts))


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
