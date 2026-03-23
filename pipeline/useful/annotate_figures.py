#!/usr/bin/env python3
"""
Claude API로 ML figure PNG를 분석하여 content.json의 figure 캡션과 주변 설명을 개선합니다.

워크플로우:
1. ml_written content.json에서 figure 참조 추출
2. 해당 PNG 파일을 base64로 인코딩
3. Claude API에 이미지 + 포스트 제목 전송
4. 응답으로 받은 설명을 Figure N. 캡션에 삽입
5. content.json 업데이트

사용법:
    python pipeline/useful/annotate_figures.py --slug regression-metrics
    python pipeline/useful/annotate_figures.py --all
    python pipeline/useful/annotate_figures.py --all --dry-run
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("anthropic 패키지 필요: pip install anthropic")
    sys.exit(1)

MEDIA_DIR = Path("backend/media/figures/outputs")
ML_DIR = Path("pipeline/data/ml_written")


def find_figures_in_content(content: str, slug: str) -> list[dict]:
    """content에서 Figure N 참조를 찾아 PNG 경로와 함께 반환."""
    pattern = re.compile(
        r'\*\*Figure (\d+)\.\*\*\s*(.+?)\n\n'
        r'!\[.*?\]\((/media/figures/outputs/' + re.escape(slug) + r'/([^)]+))\)',
        re.DOTALL,
    )
    figures = []
    for m in pattern.finditer(content):
        fig_num = int(m.group(1))
        current_caption = m.group(2).strip()
        media_path = m.group(3)
        filename = m.group(4)
        png_path = MEDIA_DIR / slug / filename
        figures.append({
            'num': fig_num,
            'current_caption': current_caption,
            'media_path': media_path,
            'filename': filename,
            'png_path': png_path,
            'match_start': m.start(),
            'match_end': m.end(),
            'full_match': m.group(0),
        })
    return figures


def analyze_figure(client: "anthropic.Anthropic", fig_path: Path, post_title: str) -> str:
    """Claude API로 PNG 분석 → 한국어 캡션 생성."""
    if not fig_path.exists():
        return None

    with open(fig_path, 'rb') as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        f"이 그래프는 '{post_title}' 포스트의 ML 시각화입니다. "
                        "20-30 단어로 한국어 캡션을 작성하세요. "
                        "핵심 내용(축, 트렌드, 결론)을 포함하세요. "
                        "캡션만 출력하세요."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text.strip()


def annotate_module(slug: str, client: "anthropic.Anthropic", dry_run: bool = False) -> dict:
    """단일 모듈의 figure 캡션을 개선."""
    module_dir = None
    for d in sorted(ML_DIR.iterdir()):
        if d.is_dir() and (d / "content.json").exists():
            with open(d / "content.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("slug") == slug:
                module_dir = d
                break

    if not module_dir:
        return {"slug": slug, "status": "not_found"}

    with open(module_dir / "content.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    content = data.get("content", "")
    title = data.get("title", slug)
    figures = find_figures_in_content(content, slug)

    if not figures:
        return {"slug": slug, "status": "no_figures"}

    updated = 0
    for fig in reversed(figures):  # 역순으로 치환 (offset 안전)
        if not fig['png_path'].exists():
            print(f"  [SKIP] {fig['filename']} — PNG 없음")
            continue

        new_caption = analyze_figure(client, fig['png_path'], title)
        if not new_caption:
            continue

        if dry_run:
            print(f"  [DRY-RUN] Figure {fig['num']}: {fig['current_caption']}")
            print(f"         → {new_caption}")
        else:
            old_text = fig['full_match']
            new_text = old_text.replace(
                f"**Figure {fig['num']}.** {fig['current_caption']}",
                f"**Figure {fig['num']}.** {new_caption}",
            )
            content = content.replace(old_text, new_text)
            print(f"  [UPDATE] Figure {fig['num']}: {new_caption[:60]}...")
        updated += 1

    if not dry_run and updated > 0:
        data["content"] = content
        with open(module_dir / "content.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return {"slug": slug, "status": "annotated", "figures": len(figures), "updated": updated}


def main():
    parser = argparse.ArgumentParser(description="Claude API로 ML figure 캡션 개선")
    parser.add_argument("--slug", help="단일 모듈 slug")
    parser.add_argument("--all", action="store_true", help="전체 모듈")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 미리보기")
    args = parser.parse_args()

    client = anthropic.Anthropic()

    if args.slug:
        result = annotate_module(args.slug, client, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.all:
        for d in sorted(ML_DIR.iterdir()):
            if d.is_dir() and (d / "content.json").exists():
                with open(d / "content.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                slug = data.get("slug", d.name)
                print(f"\n{slug}:")
                result = annotate_module(slug, client, dry_run=args.dry_run)
                print(f"  → {result.get('status')} ({result.get('updated', 0)}/{result.get('figures', 0)} figures)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
