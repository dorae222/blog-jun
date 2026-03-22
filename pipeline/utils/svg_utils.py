#!/usr/bin/env python3
"""
공통 SVG 유틸리티 — LLM 응답에서 SVG 추출, PNG 변환, 검증.

generate_arch_figures.py, batch_generate_figures.py, generate_figures_vllm.py에서 공유.
"""
import re
from pathlib import Path

import cairosvg

DEFAULT_OUTPUT_WIDTH = 1920


def extract_svg(text: str) -> str | None:
    """응답 텍스트에서 SVG 코드 추출."""
    # ```svg ... ``` 블록
    match = re.search(r'```(?:svg|xml)?\s*\n(.*?)```', text, re.DOTALL)
    if match:
        svg = match.group(1).strip()
        if svg.startswith('<svg'):
            return svg

    # <svg ... </svg> 직접 매칭
    match = re.search(r'(<svg[\s\S]*?</svg>)', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None


def sanitize_svg(svg_str: str) -> str:
    """SVG 정리 — 불필요한 태그/속성 제거, 렌더링 버그 수정."""
    # XML 선언 제거 (cairosvg가 처리)
    svg_str = re.sub(r'<\?xml[^?]*\?>', '', svg_str).strip()
    # 불필요한 주석 제거
    svg_str = re.sub(r'<!--[\s\S]*?-->', '', svg_str)
    # stroke-width="0" + marker → cairo INVALID_MATRIX 방지: stroke-width를 2로 변경
    svg_str = re.sub(
        r'stroke-width="0"(\s+marker-(?:end|start|mid)=)',
        r'stroke-width="2"\1',
        svg_str,
    )
    return svg_str


def svg_to_png(svg_str: str, output_path: Path | str,
               output_width: int = DEFAULT_OUTPUT_WIDTH,
               background_color: str = 'white') -> bool:
    """SVG 문자열을 PNG 파일로 변환. 성공 시 True 반환."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        cairosvg.svg2png(
            bytestring=svg_str.encode('utf-8'),
            write_to=str(output_path),
            output_width=output_width,
            background_color=background_color,
        )
        return True
    except Exception:
        return False


def validate_png(path: Path | str, min_size_kb: float = 10) -> bool:
    """PNG 파일 크기/존재 검증."""
    path = Path(path)
    if not path.exists():
        return False
    size_kb = path.stat().st_size / 1024
    return size_kb >= min_size_kb


def save_svg(svg_str: str, output_path: Path | str) -> None:
    """SVG 문자열을 파일로 저장."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_str, encoding='utf-8')
