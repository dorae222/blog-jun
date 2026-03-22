"""텍스트 유틸리티 — 이모지 제거, 타이틀 래핑 등."""
import re

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "\U00002600-\U000026FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)


def strip_emoji(text: str) -> str:
    """이모지 제거."""
    return EMOJI_PATTERN.sub('', text).strip()


def wrap_title(title: str, max_chars: int = 30) -> list[str]:
    """긴 제목을 SVG용으로 줄바꿈 분할."""
    words = title.split()
    lines = []
    current = ''
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = f'{current} {word}'.strip() if current else word
    if current:
        lines.append(current)
    return lines
