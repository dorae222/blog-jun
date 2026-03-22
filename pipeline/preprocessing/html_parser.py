"""
Notion HTML → Markdown 파서.
BeautifulSoup4 기반 재귀적 요소 변환.
21가지 HTML 패턴 처리 (html_analysis.md 참조).

입력: data/catalog.json + HTML 파일들
출력: data/parsed/*.md + data/parse_report.json + data/discovered_images.json
"""
import html
import json
import re
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
PARSED_DIR = DATA_DIR / "parsed"
REPORT_FILE = DATA_DIR / "parse_report.json"
IMAGES_FILE = DATA_DIR / "discovered_images.json"

# Notion 아이콘 URL 패턴 — 제거 대상
NOTION_ICON_PATTERN = re.compile(r'https://www\.notion\.so/icons/')


class NotionHTMLParser:
    """Notion HTML을 마크다운으로 변환하는 재귀 파서."""

    def __init__(self, html_file: Path):
        self.html_file = html_file
        self.html_dir = html_file.parent
        self.images: list[dict] = []
        self.warnings: list[str] = []

    def parse(self) -> tuple[str, dict]:
        """HTML 파일을 파싱하여 마크다운 + 메타데이터 반환."""
        content = self.html_file.read_text(encoding='utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        # 제목 추출
        title_el = soup.find('h1', class_='page-title')
        title = title_el.get_text(strip=True) if title_el else self.html_file.stem

        # page-body만 변환
        body = soup.find('div', class_='page-body')
        if not body:
            return "", {"title": title, "warnings": ["page-body 없음"]}

        md = self._convert_children(body, depth=0)
        md = self._postprocess(md)

        meta = {
            "title": title,
            "image_count": len(self.images),
            "warnings": self.warnings,
        }
        return md, meta

    def _convert_children(self, element: Tag, depth: int = 0) -> str:
        """자식 요소들을 순차적으로 마크다운 변환."""
        parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child)
                # 의미 없는 공백만 있는 텍스트는 건너뛰기
                if text.strip():
                    parts.append(text)
                elif text == '\n':
                    pass  # 줄바꿈만 있는 경우 무시
                else:
                    parts.append(text)
            elif isinstance(child, Tag):
                result = self._convert_element(child, depth)
                if result is not None:
                    parts.append(result)
        return ''.join(parts)

    def _convert_element(self, el: Tag, depth: int = 0) -> str | None:
        """단일 HTML 요소를 마크다운으로 변환. 우선순위 순서로 처리."""

        # 1. 코드 블록
        if el.name == 'pre' and 'code' in el.get('class', []):
            return self._convert_code_block(el)

        # 2. figure 요소들 (이미지, 북마크, callout, link-to-page)
        if el.name == 'figure':
            classes = el.get('class', [])
            if 'image' in classes:
                return self._convert_image(el)
            if 'bookmark' in classes:
                return self._convert_bookmark(el)
            if 'link-to-page' in classes:
                return ''  # Notion 내부 링크 제거
            if any('callout' in c for c in classes):
                return self._convert_callout(el)
            # source div (PDF 등)
            source = el.find('div', class_='source')
            if source:
                return self._convert_source(source)
            return self._convert_children(el, depth)

        # 3. details/summary (toggle)
        if el.name == 'details':
            return self._convert_toggle(el, depth)

        # 4. toggle 리스트 래퍼
        if el.name == 'ul' and 'toggle' in el.get('class', []):
            return self._convert_children(el, depth)

        # 5. Properties 테이블 — 본문에서 제거 (메타데이터로만 추출)
        if el.name == 'table' and 'properties' in el.get('class', []):
            return ''

        # 6. 일반 테이블
        if el.name == 'table':
            return self._convert_table(el)

        # 7. Column 레이아웃
        if el.name == 'div' and 'column-list' in el.get('class', []):
            return self._convert_columns(el, depth)

        # 8. to-do 리스트
        if el.name == 'ul' and 'to-do-list' in el.get('class', []):
            return self._convert_todo_list(el, depth, indent=0)

        # 9. 순서 없는 리스트
        if el.name == 'ul':
            return self._convert_ul(el, depth, indent=0)

        # 10. 순서 있는 리스트
        if el.name == 'ol':
            return self._convert_ol(el, depth, indent=0)

        # 11. KaTeX 수식
        if el.name == 'span' and 'katex' in el.get('class', []):
            return self._convert_katex(el)

        # 12. 수식 블록 (figure로 감싼 katex)
        if el.name == 'div' and el.find('span', class_='katex'):
            return self._convert_katex_block(el)

        # 13. 헤딩
        if el.name in ('h1', 'h2', 'h3'):
            level = int(el.name[1])
            text = self._inline_text(el)
            return f"\n{'#' * level} {text}\n\n"

        # 14. blockquote
        if el.name == 'blockquote':
            return self._convert_blockquote(el, depth)

        # 15. hr
        if el.name == 'hr':
            return '\n---\n\n'

        # 16. 인라인 서식
        if el.name in ('strong', 'b'):
            text = self._inline_text(el)
            return f'**{text}**' if text.strip() else text
        if el.name in ('em', 'i'):
            text = self._inline_text(el)
            return f'*{text}*' if text.strip() else text
        if el.name == 'code' and not self._is_inside_pre(el):
            text = el.get_text()
            return f'`{text}`' if text.strip() else text
        if el.name == 's':
            text = self._inline_text(el)
            return f'~~{text}~~' if text.strip() else text
        if el.name == 'u':
            text = self._inline_text(el)
            return f'<u>{text}</u>' if text.strip() else text
        if el.name == 'mark':
            text = self._inline_text(el)
            return f'**{text}**' if text.strip() else text
        if el.name == 'a':
            return self._convert_link(el)

        # 17. br
        if el.name == 'br':
            return '\n'

        # 18. p 태그
        if el.name == 'p':
            text = self._convert_children(el, depth)
            return f'{text}\n\n' if text.strip() else '\n'

        # 19. display:contents div — unwrap
        if el.name == 'div':
            style = el.get('style', '')
            classes = el.get('class', [])
            if 'display:contents' in style.replace(' ', ''):
                return self._convert_children(el, depth)
            if 'indented' in classes:
                return self._convert_children(el, depth)
            if 'column' in classes:
                return self._convert_children(el, depth)
            # 일반 div → children 처리
            return self._convert_children(el, depth)

        # 20. span → 단순 텍스트 또는 children
        if el.name == 'span':
            classes = el.get('class', [])
            if 'icon' in classes:
                # 아이콘 span → 이모지만 추출
                return el.get_text(strip=True)
            if 'katex' in classes:
                return self._convert_katex(el)
            return self._convert_children(el, depth)

        # 21. li 태그 (리스트 외부에서 단독으로 나올 때)
        if el.name == 'li':
            return self._convert_children(el, depth)

        # 기타 태그 → children 재귀
        if el.name in ('article', 'header', 'section', 'nav', 'main', 'aside',
                        'thead', 'tbody', 'tr', 'td', 'th', 'label',
                        'style', 'script', 'link', 'meta', 'head', 'title'):
            if el.name in ('style', 'script', 'link', 'meta', 'head', 'title'):
                return ''  # 메타/스타일 요소 제거
            return self._convert_children(el, depth)

        # 알려지지 않은 태그 → children 처리
        return self._convert_children(el, depth)

    # ─── 개별 변환기 ───

    def _convert_code_block(self, el: Tag) -> str:
        """코드 블록 변환."""
        code_el = el.find('code')
        if not code_el:
            return ''

        # 언어 추출
        lang = ''
        classes = code_el.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                lang = cls[9:].lower()
                if lang == 'plain text':
                    lang = 'text'
                break

        # 코드 내용 (HTML 엔티티 디코딩)
        code_text = html.unescape(code_el.get_text())

        # 선행/후행 빈 줄 제거
        code_text = code_text.strip('\n')

        return f'\n```{lang}\n{code_text}\n```\n\n'

    def _convert_image(self, el: Tag) -> str:
        """이미지 figure 변환."""
        img = el.find('img')
        if not img:
            return ''

        src = img.get('src', '')
        if not src:
            return ''

        # Notion 아이콘 제거
        if NOTION_ICON_PATTERN.match(src):
            return ''

        # figcaption → alt text
        caption = el.find('figcaption')
        alt = caption.get_text(strip=True) if caption else ''

        # URL 디코딩 (상대 경로인 경우)
        if not src.startswith('http'):
            decoded_src = urllib.parse.unquote(src)
            # 이미지 목록에 추가
            self.images.append({
                "original_ref": src,
                "decoded_path": decoded_src,
                "html_dir": str(self.html_dir),
                "alt": alt,
            })
        else:
            decoded_src = src
            # 외부 이미지도 기록 (Notion static URL 다운로드 시도용)
            if 'notion-static.com' in src or 'notion.so' in src:
                self.images.append({
                    "original_ref": src,
                    "decoded_path": src,
                    "html_dir": str(self.html_dir),
                    "alt": alt,
                    "external": True,
                })

        return f'\n![{alt}]({decoded_src})\n\n'

    def _convert_bookmark(self, el: Tag) -> str:
        """북마크 링크 변환."""
        a = el.find('a')
        if not a:
            return ''

        href = a.get('href', '')
        # 내부 HTML 링크 제거
        if href.endswith('.html'):
            return ''

        title_el = el.find('div', class_='bookmark-title')
        title = title_el.get_text(strip=True) if title_el else href

        desc_el = el.find('div', class_='bookmark-description')
        desc = desc_el.get_text(strip=True) if desc_el else ''

        result = f'\n[{title}]({href})\n'
        if desc:
            result += f'{desc}\n'
        return result + '\n'

    def _convert_callout(self, el: Tag) -> str:
        """Callout/알림 박스 변환."""
        # 이모지 아이콘
        icon_div = el.find('div', style=lambda s: s and 'font-size' in s)
        icon = ''
        if icon_div:
            icon_span = icon_div.find('span', class_='icon')
            if icon_span:
                icon = icon_span.get_text(strip=True) + ' '

        # 내용 div
        content_div = el.find('div', style=lambda s: s and 'width:100%' in s.replace(' ', ''))
        if not content_div:
            # 대체: 두 번째 div
            divs = el.find_all('div', recursive=False)
            content_div = divs[1] if len(divs) > 1 else el

        # 제목 (strong 태그)
        title_el = content_div.find('strong', recursive=False) if content_div else None
        title = ''
        if title_el:
            title = title_el.get_text(strip=True)
            title_el.decompose()

        # 내용
        inner = self._convert_children(content_div, 0) if content_div else ''

        # 블록쿼트 형식
        lines = []
        if title:
            lines.append(f'> **{icon}{title}**')
        elif icon:
            lines.append(f'> {icon.strip()}')

        for line in inner.strip().split('\n'):
            lines.append(f'> {line}')

        return '\n' + '\n'.join(lines) + '\n\n'

    def _convert_toggle(self, el: Tag, depth: int) -> str:
        """Toggle/details 변환 → 헤딩."""
        summary = el.find('summary')
        if not summary:
            return self._convert_children(el, depth)

        # font-size로 헤딩 레벨 결정
        style = summary.get('style', '')
        if '1.5em' in style or '1.875em' in style:
            level = 2
        elif '1.25em' in style:
            level = 3
        else:
            level = 3  # 기본 H3

        # depth 기반 조정 (중첩 toggle)
        level = min(level + depth, 6)

        title = self._inline_text(summary)
        result = f"\n{'#' * level} {title}\n\n"

        # summary 이후의 내용
        for child in el.children:
            if child == summary or (isinstance(child, NavigableString) and not str(child).strip()):
                continue
            if isinstance(child, Tag):
                result += self._convert_element(child, depth + 1)

        return result

    def _convert_table(self, el: Tag) -> str:
        """테이블 변환."""
        rows = el.find_all('tr')
        if not rows:
            return ''

        table_data = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            cell_texts = []
            for cell in cells:
                text = self._inline_text(cell)
                # 셀 내 줄바꿈 → 공백
                text = text.replace('\n', ' ').strip()
                # 파이프 이스케이프
                text = text.replace('|', '\\|')
                cell_texts.append(text)
            table_data.append(cell_texts)

        if not table_data:
            return ''

        # 열 수 통일
        max_cols = max(len(row) for row in table_data)
        for row in table_data:
            while len(row) < max_cols:
                row.append('')

        # 마크다운 테이블 생성
        lines = []
        # 헤더 (첫 행)
        header = table_data[0]
        lines.append('| ' + ' | '.join(header) + ' |')
        lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        # 본문
        for row in table_data[1:]:
            lines.append('| ' + ' | '.join(row) + ' |')

        return '\n' + '\n'.join(lines) + '\n\n'

    def _convert_columns(self, el: Tag, depth: int) -> str:
        """컬럼 레이아웃 → 순차 평탄화."""
        result = ''
        for col in el.find_all('div', class_='column', recursive=False):
            col_content = self._convert_children(col, depth)
            if col_content.strip():
                result += col_content
        return result

    def _convert_ul(self, el: Tag, depth: int, indent: int) -> str:
        """순서 없는 리스트."""
        result = ''
        for li in el.find_all('li', recursive=False):
            prefix = '  ' * indent + '- '
            # li 내부에서 텍스트와 하위 리스트 분리
            text_parts = []
            sub_lists = []

            for child in li.children:
                if isinstance(child, Tag):
                    if child.name in ('ul', 'ol'):
                        sub_lists.append(child)
                    elif child.name == 'div' and child.find(['ul', 'ol'], recursive=False):
                        # display:contents div 안의 리스트
                        for inner in child.children:
                            if isinstance(inner, Tag) and inner.name in ('ul', 'ol'):
                                sub_lists.append(inner)
                            elif isinstance(inner, Tag):
                                text_parts.append(self._convert_element(inner, depth))
                            elif isinstance(inner, NavigableString) and str(inner).strip():
                                text_parts.append(str(inner))
                    else:
                        text_parts.append(self._convert_element(child, depth))
                elif isinstance(child, NavigableString):
                    text = str(child)
                    if text.strip():
                        text_parts.append(text)

            item_text = ''.join(text_parts).strip()
            # 블록 수준 요소 내 줄바꿈 정리
            item_text = re.sub(r'\n{2,}', '\n', item_text)
            result += prefix + item_text + '\n'

            for sub in sub_lists:
                if sub.name == 'ul' and 'to-do-list' in sub.get('class', []):
                    result += self._convert_todo_list(sub, depth, indent + 1)
                elif sub.name == 'ul':
                    result += self._convert_ul(sub, depth, indent + 1)
                elif sub.name == 'ol':
                    result += self._convert_ol(sub, depth, indent + 1)

        if indent == 0:
            result = '\n' + result + '\n'
        return result

    def _convert_ol(self, el: Tag, depth: int, indent: int) -> str:
        """순서 있는 리스트."""
        result = ''
        for idx, li in enumerate(el.find_all('li', recursive=False), 1):
            prefix = '  ' * indent + f'{idx}. '
            text_parts = []
            sub_lists = []

            for child in li.children:
                if isinstance(child, Tag):
                    if child.name in ('ul', 'ol'):
                        sub_lists.append(child)
                    elif child.name == 'div' and child.find(['ul', 'ol'], recursive=False):
                        for inner in child.children:
                            if isinstance(inner, Tag) and inner.name in ('ul', 'ol'):
                                sub_lists.append(inner)
                            elif isinstance(inner, Tag):
                                text_parts.append(self._convert_element(inner, depth))
                            elif isinstance(inner, NavigableString) and str(inner).strip():
                                text_parts.append(str(inner))
                    else:
                        text_parts.append(self._convert_element(child, depth))
                elif isinstance(child, NavigableString):
                    text = str(child)
                    if text.strip():
                        text_parts.append(text)

            item_text = ''.join(text_parts).strip()
            item_text = re.sub(r'\n{2,}', '\n', item_text)
            result += prefix + item_text + '\n'

            for sub in sub_lists:
                if sub.name == 'ul':
                    result += self._convert_ul(sub, depth, indent + 1)
                elif sub.name == 'ol':
                    result += self._convert_ol(sub, depth, indent + 1)

        if indent == 0:
            result = '\n' + result + '\n'
        return result

    def _convert_todo_list(self, el: Tag, depth: int, indent: int) -> str:
        """체크박스 리스트."""
        result = ''
        for li in el.find_all('li', recursive=False):
            checkbox = li.find('div', class_='checkbox')
            checked = 'checkbox-on' in checkbox.get('class', []) if checkbox else False
            marker = '- [x] ' if checked else '- [ ] '

            prefix = '  ' * indent + marker
            text = li.find('span')
            text_content = self._inline_text(text) if text else li.get_text(strip=True)
            result += prefix + text_content + '\n'

        if indent == 0:
            result = '\n' + result + '\n'
        return result

    def _convert_katex(self, el: Tag) -> str:
        """인라인 KaTeX → $LaTeX$."""
        annotation = el.find('annotation', encoding='application/x-tex')
        if annotation:
            latex = annotation.get_text()
            return f'${latex}$'
        # annotation 없으면 텍스트 추출
        return el.get_text(strip=True)

    def _convert_katex_block(self, el: Tag) -> str:
        """블록 KaTeX → $$LaTeX$$."""
        annotation = el.find('annotation', encoding='application/x-tex')
        if annotation:
            latex = annotation.get_text()
            return f'\n$${latex}$$\n\n'
        return ''

    def _convert_blockquote(self, el: Tag, depth: int) -> str:
        """인용문 변환."""
        inner = self._convert_children(el, depth)
        lines = inner.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines)
        return f'\n{quoted}\n\n'

    def _convert_link(self, el: Tag) -> str:
        """링크 변환."""
        href = el.get('href', '')
        text = self._inline_text(el)

        # 빈 링크 무시
        if not href or not text.strip():
            return text

        # 내부 HTML 링크 → 텍스트만
        if href.endswith('.html'):
            return text

        return f'[{text}]({href})'

    def _convert_source(self, el: Tag) -> str:
        """source div (PDF 등 파일 첨부) 변환."""
        a = el.find('a')
        if a:
            href = a.get('href', '')
            text = a.get_text(strip=True)
            if href.lower().endswith(('.mp4', '.mov', '.avi')):
                return f'\n[Video: {text}]\n\n'
            return f'\n[{text}]({href})\n\n'
        return ''

    # ─── 유틸리티 ───

    def _inline_text(self, el: Tag | None) -> str:
        """인라인 텍스트 변환 (재귀적으로 자식 처리)."""
        if el is None:
            return ''

        parts = []
        for child in el.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ('strong', 'b'):
                    inner = self._inline_text(child)
                    parts.append(f'**{inner}**' if inner.strip() else inner)
                elif child.name in ('em', 'i'):
                    inner = self._inline_text(child)
                    parts.append(f'*{inner}*' if inner.strip() else inner)
                elif child.name == 'code':
                    parts.append(f'`{child.get_text()}`')
                elif child.name == 's':
                    inner = self._inline_text(child)
                    parts.append(f'~~{inner}~~')
                elif child.name == 'mark':
                    inner = self._inline_text(child)
                    parts.append(f'**{inner}**')
                elif child.name == 'a':
                    href = child.get('href', '')
                    inner = self._inline_text(child)
                    if href and not href.endswith('.html'):
                        parts.append(f'[{inner}]({href})')
                    else:
                        parts.append(inner)
                elif child.name == 'br':
                    parts.append('\n')
                elif child.name == 'span':
                    if 'katex' in child.get('class', []):
                        parts.append(self._convert_katex(child))
                    else:
                        parts.append(self._inline_text(child))
                elif child.name == 'img':
                    # 인라인 이미지 (아이콘 등)
                    src = child.get('src', '')
                    if not NOTION_ICON_PATTERN.match(src):
                        alt = child.get('alt', '')
                        parts.append(f'![{alt}]({src})')
                else:
                    parts.append(self._inline_text(child))

        return ''.join(parts)

    def _is_inside_pre(self, el: Tag) -> bool:
        """pre 태그 안에 있는지 확인."""
        parent = el.parent
        while parent:
            if parent.name == 'pre':
                return True
            parent = parent.parent
        return False

    def _postprocess(self, md: str) -> str:
        """후처리: 과도한 빈 줄 제거, 정리."""
        # HTML 엔티티 디코딩
        md = html.unescape(md)
        # 과도한 빈 줄 제거 (3+ → 2)
        md = re.sub(r'\n{3,}', '\n\n', md)
        # 헤딩 전 빈 줄 보장
        md = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', md)
        # 선행/후행 공백 제거
        md = md.strip()
        return md + '\n'


def parse_all():
    """catalog.json의 모든 항목을 파싱."""
    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    report = []
    all_images = []
    success = 0
    errors = 0

    for item in catalog:
        html_path = Path(item["html_path"])
        if not html_path.exists():
            print(f"⚠️  파일 없음: {html_path}")
            errors += 1
            continue

        parser = NotionHTMLParser(html_path)
        try:
            md, meta = parser.parse()
        except Exception as e:
            print(f"❌ 파싱 실패: {item['title']}: {e}")
            errors += 1
            report.append({"path": item["path"], "error": str(e)})
            continue

        if not md.strip():
            print(f"⚠️  빈 결과: {item['title']}")
            continue

        # 파일명 생성: 카테고리__제목.md (안전한 파일명)
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', item["title"])[:80]
        safe_cat = re.sub(r'[\\/:*?"<>|]', '_', item.get("subcategory", "general"))
        filename = f"{safe_cat}__{safe_title}.md"
        out_path = PARSED_DIR / filename

        out_path.write_text(md, encoding='utf-8')

        # catalog에 parsed 경로 추가
        item["parsed_path"] = str(out_path)
        item["parsed_title"] = meta["title"]

        # 이미지 수집
        for img in parser.images:
            img["source_title"] = item["title"]
            img["category"] = item.get("parent_code", "")
        all_images.extend(parser.images)

        report.append({
            "path": item["path"],
            "title": meta["title"],
            "parsed_file": filename,
            "chars": len(md),
            "image_count": meta["image_count"],
            "warnings": meta["warnings"],
        })
        success += 1

    # catalog 업데이트 (parsed_path 추가)
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # 리포트 저장
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 이미지 목록 저장
    with open(IMAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_images, f, ensure_ascii=False, indent=2)

    print(f"\n=== Parse Results ===")
    print(f"Success: {success}")
    print(f"Errors: {errors}")
    print(f"Total images discovered: {len(all_images)}")
    print(f"Parsed files: {PARSED_DIR}")
    print(f"Report: {REPORT_FILE}")
    print(f"Image list: {IMAGES_FILE}")


if __name__ == "__main__":
    parse_all()
