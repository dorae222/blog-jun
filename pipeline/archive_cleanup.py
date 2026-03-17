"""
불필요 콘텐츠 진단 + 아카이브.

아카이브 기준 (하나라도 해당):
1. content 길이 < 400자 (짧은 스텁)
2. 전체 줄의 60% 이상이 HTTP(s) URL만 있음 (링크 덤프)
3. source_path가 catalog.json의 skip=True 항목에 해당
4. content에 위키링크([[...]]) 또는 제목(# ...)만 있고 본문 없음

실행:
    python pipeline/archive_cleanup.py            # dry-run (기본)
    python pipeline/archive_cleanup.py --execute  # 실제 archived 처리
"""
import argparse
import json
import re
import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from blog.models import Post

DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"

URL_ONLY_RE = re.compile(r"^\s*https?://\S+\s*$")
WIKILINK_RE = re.compile(r"\[\[.*?\]\]")
HEADING_RE = re.compile(r"^#+\s+\S")


def load_skip_paths() -> set:
    """catalog.json에서 skip=True 항목의 source_path 집합 반환."""
    if not CATALOG_FILE.exists():
        return set()
    with open(CATALOG_FILE, encoding="utf-8") as f:
        catalog = json.load(f)
    return {item["path"] for item in catalog if item.get("skip", False)}


def is_link_dump(content: str) -> bool:
    """전체 줄의 60% 이상이 URL만으로 구성된 줄이면 True."""
    lines = [l for l in content.splitlines() if l.strip()]
    if not lines:
        return False
    url_lines = sum(1 for l in lines if URL_ONLY_RE.match(l))
    return url_lines / len(lines) >= 0.6


def is_skeleton_only(content: str) -> bool:
    """위키링크·제목만 있고 실질적 본문이 없으면 True."""
    # 위키링크와 마크다운 제목을 제거한 후 남은 텍스트 길이 확인
    stripped = WIKILINK_RE.sub("", content)
    # 제목 줄 제거
    stripped = "\n".join(
        l for l in stripped.splitlines()
        if not HEADING_RE.match(l)
    )
    return len(stripped.strip()) < 80


def classify_post(post: Post, skip_paths: set) -> tuple[bool, str]:
    """
    (should_archive: bool, reason: str) 반환.
    False이면 reason은 빈 문자열.
    """
    content = post.content or ""
    stripped = content.strip()

    # 기준 1: 너무 짧음
    if len(stripped) < 400:
        return True, f"콘텐츠 길이 {len(stripped)}자 (<400자 스텁)"

    # 기준 2: 링크 덤프
    if is_link_dump(content):
        return True, "URL 링크 덤프 (60% 이상 URL만)"

    # 기준 3: catalog skip 항목
    if post.source_path and post.source_path in skip_paths:
        return True, f"catalog.json skip=True: {post.source_path}"

    # 기준 4: 위키링크/제목만 있는 뼈대
    if is_skeleton_only(content):
        return True, "위키링크·제목만 있는 빈 뼈대"

    return False, ""


def run(execute: bool):
    skip_paths = load_skip_paths()
    posts = Post.objects.filter(status="published").only(
        "id", "title", "content", "source_path", "status"
    )

    to_archive: list[tuple[Post, str]] = []
    for post in posts:
        should_archive, reason = classify_post(post, skip_paths)
        if should_archive:
            to_archive.append((post, reason))

    print(f"\n=== Archive Cleanup {'[DRY-RUN]' if not execute else '[EXECUTE]'} ===")
    print(f"Published 포스트 전체: {posts.count()}건")
    print(f"아카이브 대상: {len(to_archive)}건\n")

    for post, reason in to_archive:
        print(f"  [{post.id:5d}] {post.title[:60]:<60}  | {reason}")

    if not execute:
        print("\n[DRY-RUN] 실제 변경 없음. --execute 플래그로 재실행하면 archived 처리됩니다.")
        return

    ids = [post.id for post, _ in to_archive]
    updated = Post.objects.filter(id__in=ids).update(status="archived")
    print(f"\n{updated}건 archived 처리 완료.")


def main():
    parser = argparse.ArgumentParser(description="불필요 콘텐츠 아카이브")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제로 archived 처리 (없으면 dry-run)",
    )
    args = parser.parse_args()
    run(execute=args.execute)


if __name__ == "__main__":
    main()
