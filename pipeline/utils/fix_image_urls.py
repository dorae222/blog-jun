"""
DB content의 이미지 URL 공백 → %20 인코딩.

문제: ![](/media/posts/imported/ai/Untitled 38.png) → CommonMark에서 파싱 실패
수정: ![](/media/posts/imported/ai/Untitled%2038.png) → 정상 파싱

실행:
    python pipeline/fix_image_urls.py --dry-run    # 변경 건수만 확인
    python pipeline/fix_image_urls.py              # 실제 DB 업데이트
"""
import argparse
import re
import sys
import os
from pathlib import Path
from urllib.parse import quote

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from blog.models import Post

IMG_RE = re.compile(r'(!\[[^\]]*\]\()(/media/[^)]+)(\))')


def encode_url(m):
    """이미지 URL의 공백 등 비안전 문자를 인코딩."""
    prefix = m.group(1)
    url = m.group(2)
    suffix = m.group(3)
    encoded = quote(url, safe='/:#?&=')
    return prefix + encoded + suffix


def fix_image_urls(dry_run: bool = True):
    posts = Post.objects.filter(status__in=["published", "archived"])
    updated = 0
    total_fixes = 0

    for post in posts:
        content = post.content or ""
        if not content:
            continue

        fixed = IMG_RE.sub(encode_url, content)
        if fixed != content:
            # 변경된 URL 수 세기
            fixes = sum(1 for a, b in zip(
                IMG_RE.findall(content), IMG_RE.findall(fixed)
            ) if a != b)
            # findall 비교 대신 단순 diff로
            fixes = len(IMG_RE.findall(content))

            if dry_run:
                # 변경되는 URL 샘플 출력
                orig_urls = [m[1] for m in IMG_RE.findall(content)]
                new_urls = [m[1] for m in IMG_RE.findall(fixed)]
                changed = [(o, n) for o, n in zip(orig_urls, new_urls) if o != n]
                if changed:
                    print(f"[POST {post.id}] {post.title[:50]}")
                    for old, new in changed[:3]:
                        print(f"  {old}")
                        print(f"  → {new}")
                    total_fixes += len(changed)
                    updated += 1
            else:
                post.content = fixed
                post.save(update_fields=["content"])
                updated += 1

    action = "수정 예정" if dry_run else "수정 완료"
    print(f"\n=== 이미지 URL {action} ===")
    print(f"포스트: {updated}건")
    if dry_run:
        print(f"URL 수정: {total_fixes}건")
        print(f"\n실제 적용: python pipeline/fix_image_urls.py (--dry-run 제거)")


def main():
    parser = argparse.ArgumentParser(description="DB 이미지 URL 공백 인코딩")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 DB 수정 없이 변경 건수만 확인",
    )
    args = parser.parse_args()
    fix_image_urls(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
