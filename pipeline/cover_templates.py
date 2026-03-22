#!/usr/bin/env python3
"""
커버 이미지 SVG 템플릿 — paper_cover, category_gradient, architecture_diagram.

모든 SVG는 viewBox="0 0 1792 1024" (16:9 비율).
svg_utils.py의 svg_to_png() 재사용.
"""
import html
import textwrap

# ── AI 카테고리 목록 (paper_cover 전략 대상) ──
AI_CATEGORIES = {'llm', 'ssm', 'diffusion', 'multimodal', 'agent', 'technique', 'vision', 'paper_review'}

# ── 카테고리별 그라디언트/아이콘 설정 ──
CATEGORY_STYLES = {
    'cloud':      {'from': '#3B82F6', 'to': '#06B6D4', 'icon': 'M425 400c0-88.4 71.6-160 160-160a160 160 0 0 1 155 120h5c66.3 0 120 53.7 120 120s-53.7 120-120 120H385c-55.2 0-100-44.8-100-100a100 100 0 0 1 140-100z'},
    'dev':        {'from': '#8B5CF6', 'to': '#6366F1', 'icon': 'M320 200l-160 280 160 280h160l-160-280 160-280H320zm352 0l160 280-160 280h160l160-280-160-280H672z'},
    'foundation': {'from': '#F59E0B', 'to': '#EF4444', 'icon': 'M496 128L96 352v64l400 224 400-224v-64L496 128zm0 64l320 180v0L496 552 176 372l320-180z'},
    'project':    {'from': '#10B981', 'to': '#059669', 'icon': 'M128 192h544v64H128v-64zm0 160h544v64H128v-64zm0 160h352v64H128v-64z'},
    'program':    {'from': '#EC4899', 'to': '#F43F5E', 'icon': 'M192 128v544h416V128H192zm48 48h320v448H240V176zm80 64l80 120-80 120h48l80-120-80-120h-48z'},
    'data':       {'from': '#14B8A6', 'to': '#0EA5E9', 'icon': 'M496 128c-176 0-320 48-320 108v328c0 60 144 108 320 108s320-48 320-108V236c0-60-144-108-320-108z'},
    'ai-ml':      {'from': '#7C3AED', 'to': '#2563EB', 'icon': 'M496 160a80 80 0 1 0 0 160 80 80 0 0 0 0-160zm-200 280a60 60 0 1 0 0 120 60 60 0 0 0 0-120zm400 0a60 60 0 1 0 0 120 60 60 0 0 0 0-120z'},
}

# paper_cover 색상 팔레트
PAPER_BG_FROM = '#1a1a2e'
PAPER_BG_TO = '#16213e'
PAPER_ACCENT = '#e94560'
PAPER_TEXT = '#eaeaea'

# 한글 지원 폰트 스택 (macOS + Linux Docker)
FONT_TITLE = "'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif"
FONT_BODY = "'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', Arial, sans-serif"
FONT_MONO = "'D2Coding', 'Noto Sans KR', monospace"


def _escape(text: str) -> str:
    """SVG 텍스트용 HTML 이스케이프."""
    return html.escape(str(text), quote=True)


def _wrap_title(title: str, max_chars: int = 45) -> list[str]:
    """제목을 여러 줄로 분리."""
    return textwrap.wrap(title, width=max_chars) or [title]


def _wrap_text(text: str, max_chars: int = 70, max_lines: int = 4) -> list[str]:
    """텍스트를 여러 줄로 분리 (최대 줄 수 제한)."""
    lines = textwrap.wrap(text, width=max_chars)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max_chars - 3] + '...'
    return lines or ['']


def generate_paper_cover_svg(
    title: str,
    summary: str = '',
    category_name: str = '',
    tags: list[str] | None = None,
    date: str = '',
) -> str:
    """PDF 표지 스타일 커버 이미지 SVG 생성.

    다크 학술 배경, 큰 타이틀, 요약, 카테고리/태그 뱃지, 기하학적 장식.
    """
    tags = tags or []
    title_lines = _wrap_title(title, max_chars=40)
    summary_lines = _wrap_text(summary, max_chars=65, max_lines=3) if summary else []

    # 타이틀 y 위치 계산
    title_start_y = 320 if len(title_lines) <= 2 else 280
    title_block = ''
    for i, line in enumerate(title_lines):
        title_block += (
            f'<text x="896" y="{title_start_y + i * 68}" text-anchor="middle" '
            f'font-size="56" font-weight="bold" fill="{PAPER_TEXT}" '
            f'font-family="{FONT_TITLE}">'
            f'{_escape(line)}</text>\n'
        )

    # 요약
    summary_y = title_start_y + len(title_lines) * 68 + 40
    summary_block = ''
    for i, line in enumerate(summary_lines):
        summary_block += (
            f'<text x="896" y="{summary_y + i * 28}" text-anchor="middle" '
            f'font-size="20" fill="#a0a0b8" font-family="{FONT_BODY}">'
            f'{_escape(line)}</text>\n'
        )

    # 카테고리 뱃지
    cat_badge = ''
    if category_name:
        cat_badge = (
            f'<rect x="796" y="160" width="200" height="36" rx="18" fill="{PAPER_ACCENT}" opacity="0.9"/>'
            f'<text x="896" y="184" text-anchor="middle" font-size="16" font-weight="bold" '
            f'fill="white" font-family="{FONT_BODY}">{_escape(category_name.upper())}</text>'
        )

    # 태그 뱃지
    tags_block = ''
    visible_tags = tags[:5]
    if visible_tags:
        total_width = sum(len(t) * 10 + 24 for t in visible_tags) + (len(visible_tags) - 1) * 8
        start_x = 896 - total_width // 2
        tag_y = summary_y + len(summary_lines) * 28 + 40
        cur_x = start_x
        for t in visible_tags:
            w = len(t) * 10 + 24
            tags_block += (
                f'<rect x="{cur_x}" y="{tag_y}" width="{w}" height="28" rx="14" '
                f'fill="white" opacity="0.1"/>'
                f'<text x="{cur_x + w // 2}" y="{tag_y + 19}" text-anchor="middle" '
                f'font-size="13" fill="#8888aa" font-family="{FONT_BODY}">'
                f'#{_escape(t)}</text>'
            )
            cur_x += w + 8

    # 날짜
    date_block = ''
    if date:
        date_block = (
            f'<text x="896" y="920" text-anchor="middle" font-size="16" '
            f'fill="#666680" font-family="{FONT_MONO}">{_escape(date)}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1792 1024">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PAPER_BG_FROM}"/>
      <stop offset="100%" stop-color="{PAPER_BG_TO}"/>
    </linearGradient>
  </defs>

  <!-- 배경 -->
  <rect width="1792" height="1024" fill="url(#bg)"/>

  <!-- 기하학적 장식 -->
  <circle cx="200" cy="200" r="300" fill="white" opacity="0.02"/>
  <circle cx="1600" cy="850" r="250" fill="{PAPER_ACCENT}" opacity="0.04"/>
  <line x1="100" y1="100" x2="300" y2="100" stroke="white" stroke-width="1" opacity="0.08"/>
  <line x1="100" y1="100" x2="100" y2="300" stroke="white" stroke-width="1" opacity="0.08"/>
  <line x1="1492" y1="724" x2="1692" y2="724" stroke="{PAPER_ACCENT}" stroke-width="1" opacity="0.1"/>
  <line x1="1692" y1="724" x2="1692" y2="924" stroke="{PAPER_ACCENT}" stroke-width="1" opacity="0.1"/>
  <rect x="140" y="880" width="60" height="4" rx="2" fill="{PAPER_ACCENT}" opacity="0.3"/>
  <rect x="220" y="880" width="40" height="4" rx="2" fill="white" opacity="0.1"/>

  <!-- 상단 악센트 라인 -->
  <rect x="0" y="0" width="1792" height="4" fill="{PAPER_ACCENT}"/>

  <!-- 콘텐츠 -->
  {cat_badge}
  {title_block}
  {summary_block}
  {tags_block}

  <!-- 하단 구분선 + 날짜 -->
  <line x1="696" y1="870" x2="1096" y2="870" stroke="white" stroke-width="1" opacity="0.1"/>
  {date_block}

  <!-- 하단 악센트 -->
  <rect x="846" y="980" width="100" height="3" rx="1.5" fill="{PAPER_ACCENT}" opacity="0.5"/>
</svg>'''


def generate_category_cover_svg(
    title: str,
    category_slug: str,
    category_color: str = '',
) -> str:
    """카테고리별 그라디언트 + 아이콘 오버레이 커버 이미지 SVG 생성."""
    style = CATEGORY_STYLES.get(category_slug, CATEGORY_STYLES.get('dev'))
    color_from = category_color or style['from']
    color_to = style['to']
    icon_path = style.get('icon', '')

    title_lines = _wrap_title(title, max_chars=38)
    title_block = ''
    title_y = 480 if len(title_lines) <= 2 else 440
    for i, line in enumerate(title_lines):
        title_block += (
            f'<text x="180" y="{title_y + i * 64}" '
            f'font-size="52" font-weight="bold" fill="white" '
            f'font-family="{FONT_BODY}">'
            f'{_escape(line)}</text>\n'
        )

    # 카테고리 라벨
    cat_label = category_slug.upper().replace('-', '/')
    cat_label_block = (
        f'<rect x="180" y="{title_y - 80}" width="{len(cat_label) * 14 + 32}" height="36" rx="18" '
        f'fill="white" opacity="0.2"/>'
        f'<text x="{180 + (len(cat_label) * 14 + 32) // 2}" y="{title_y - 56}" text-anchor="middle" '
        f'font-size="15" font-weight="bold" fill="white" font-family="{FONT_BODY}">'
        f'{_escape(cat_label)}</text>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1792 1024">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color_from}"/>
      <stop offset="100%" stop-color="{color_to}"/>
    </linearGradient>
  </defs>

  <!-- 배경 -->
  <rect width="1792" height="1024" fill="url(#bg)"/>

  <!-- 아이콘 오버레이 -->
  <g transform="translate(1100, 180) scale(1.4)" opacity="0.08" fill="white">
    <path d="{icon_path}"/>
  </g>

  <!-- 장식 원 -->
  <circle cx="1500" cy="800" r="200" fill="white" opacity="0.05"/>
  <circle cx="300" cy="150" r="100" fill="white" opacity="0.04"/>

  <!-- 콘텐츠 -->
  {cat_label_block}
  {title_block}

  <!-- 하단 라인 -->
  <rect x="180" y="{title_y + len(title_lines) * 64 + 20}" width="80" height="4" rx="2" fill="white" opacity="0.5"/>
</svg>'''


def generate_architecture_cover_prompt(
    post_title: str,
    arch_name: str,
    arch_category: str = '',
    key_detail: str = '',
) -> str:
    """아키텍처 다이어그램 커버용 Claude API 프롬프트 생성.

    generate_arch_figures.py의 간소화 버전 (랜드스케이프 16:9).
    """
    return f"""Generate a clean, publication-quality SVG cover image for "{post_title}".

=== CONTEXT ===
Architecture: {arch_name}
Category: {arch_category}
Key Detail: {key_detail}

=== REQUIREMENTS ===
1. viewBox="0 0 1792 1024" (16:9 landscape)
2. Dark blue-gray background (#1e293b → #0f172a gradient)
3. Show a SIMPLIFIED architecture diagram in the center (not full detail)
4. Title "{arch_name}" in large white text at top
5. Category badge in accent color
6. Professional, clean aesthetic — suitable as a blog post cover image
7. Use these colors: blue (#3B82F6) for attention blocks, orange (#F97316) for FFN,
   teal (#14B8A6) for SSM, purple (#8B5CF6) for embeddings
8. Keep it simple — this is a cover image, not a full architecture diagram

Output ONLY the SVG code."""


def classify_strategy(
    category_slug: str,
    post_type: str = '',
    has_arch_entry: bool = False,
) -> str:
    """포스트에 적합한 커버 이미지 생성 전략 분류.

    Returns: 'paper_cover' | 'category_gradient' | 'architecture_diagram'
    """
    # AI 관련 카테고리 → paper_cover
    if category_slug in AI_CATEGORIES or post_type == 'paper_review':
        return 'paper_cover'
    # ArchitectureEntry가 있고 figure가 없는 경우 → architecture_diagram
    if has_arch_entry:
        return 'architecture_diagram'
    # 기본 → category_gradient
    return 'category_gradient'
