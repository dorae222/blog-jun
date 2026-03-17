"""
Playwright로 blog.dorae222.com 포스트 렌더링 검증.

기능:
1. fixstyle_sample_output.jsonl (또는 --url-list로 직접 URL 목록) 읽기
2. blog.dorae222.com/posts/{slug}/ 방문
3. 스크린샷 저장 → data/playwright_screenshots/{post_id}_{slug}.png
4. 콘솔 에러 / KaTeX 에러 / 깨진 이미지 캡처 → data/playwright_errors.json

검증 항목:
- KaTeX 렌더링: .katex-error CSS 클래스 없음
- 이미지: img.complete && img.naturalWidth > 0
- 코드 블록: pre code 하이라이트 클래스 존재

설치:
    pip install playwright
    playwright install chromium

실행:
    python pipeline/playwright_check.py                      # 전체 published 포스트
    python pipeline/playwright_check.py --quick-check        # 홈 + 최신 5건만
    python pipeline/playwright_check.py --post-ids 1,2,3    # ID 목록
    python pipeline/playwright_check.py --input pipeline/data/fixstyle_sample_output.jsonl
"""
import argparse
import json
import sys
import os
import time
from pathlib import Path
from urllib.parse import quote

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from blog.models import Post

DATA_DIR = Path(__file__).parent / "data"
SCREENSHOTS_DIR = DATA_DIR / "playwright_screenshots"
ERRORS_FILE = DATA_DIR / "playwright_errors.json"

BLOG_BASE = "https://blog.dorae222.com"
SCREENSHOT_TIMEOUT = 30_000  # ms
PAGE_LOAD_TIMEOUT = 30_000   # ms


def check_page(page, url: str, post_id: int, slug: str) -> dict:
    """단일 페이지 방문 + 검증. 결과 dict 반환."""
    console_errors = []
    js_errors = []

    page.on("console", lambda msg: console_errors.append({
        "type": msg.type,
        "text": msg.text,
    }) if msg.type == "error" else None)

    page.on("pageerror", lambda err: js_errors.append(str(err)))

    result = {
        "post_id":      post_id,
        "slug":         slug,
        "url":          url,
        "status":       None,
        "katex_errors": 0,
        "broken_images": 0,
        "code_highlighted": False,
        "console_errors": [],
        "js_errors": [],
        "screenshot":   None,
    }

    try:
        response = page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
        result["status"] = response.status if response else None

        # 페이지 렌더링 대기 (KaTeX / 코드 하이라이팅)
        page.wait_for_timeout(2000)

        # KaTeX 에러 확인
        katex_errors = page.locator(".katex-error").count()
        result["katex_errors"] = katex_errors

        # 깨진 이미지 확인
        broken = page.evaluate("""() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.filter(img =>
                !img.complete || img.naturalWidth === 0
            ).length;
        }""")
        result["broken_images"] = broken

        # 코드 블록 하이라이팅 확인
        code_ok = page.evaluate("""() => {
            const codes = document.querySelectorAll('pre code');
            if (!codes.length) return null;  // 코드 블록 없음
            return Array.from(codes).some(c =>
                c.className && c.className.includes('hljs')
            );
        }""")
        result["code_highlighted"] = code_ok

        # 스크린샷
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        safe_slug = slug[:60].replace("/", "_")
        screenshot_path = SCREENSHOTS_DIR / f"{post_id}_{safe_slug}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot"] = str(screenshot_path)

    except Exception as e:
        result["error"] = str(e)

    result["console_errors"] = console_errors[:20]
    result["js_errors"] = js_errors[:10]
    return result


def run_checks(posts_to_check: list[dict], headless: bool = True) -> list[dict]:
    """posts_to_check: [{"post_id": int, "slug": str}, ...]"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright 미설치. 실행: pip install playwright && playwright install chromium")
        sys.exit(1)

    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        total = len(posts_to_check)
        for i, item in enumerate(posts_to_check, start=1):
            post_id = item["post_id"]
            slug = item["slug"]
            url = f"{BLOG_BASE}/posts/{slug}/"

            print(f"[{i}/{total}] {post_id}: {slug[:60]}")

            result = check_page(page, url, post_id, slug)

            status_icon = "✓" if result.get("status") == 200 else "✗"
            katex_icon = "✗" if result["katex_errors"] > 0 else "✓"
            img_icon = "✗" if result["broken_images"] > 0 else "✓"
            print(
                f"  HTTP={result.get('status')} {status_icon} | "
                f"KaTeX {katex_icon}({result['katex_errors']}) | "
                f"Img {img_icon}({result['broken_images']}) | "
                f"{'screenshot: ' + Path(result['screenshot']).name if result.get('screenshot') else 'no screenshot'}"
            )

            if result["katex_errors"] > 0 or result["broken_images"] > 0:
                print(f"  !! 문제 발견: post_id={post_id}, url={url}")

            results.append(result)
            time.sleep(0.5)  # 서버 부하 방지

        context.close()
        browser.close()

    return results


def posts_from_jsonl(jsonl_path: Path) -> list[dict]:
    """fixstyle 출력 JSONL에서 포스트 목록 추출."""
    posts = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            custom_id = item.get("custom_id", "")
            if item.get("response", {}).get("status_code") != 200:
                continue
            # source_path로 slug 조회
            post = None
            if custom_id.startswith("post-"):
                try:
                    pid = int(custom_id[5:])
                    post = Post.objects.filter(id=pid).first()
                except ValueError:
                    pass
            else:
                post = Post.objects.filter(source_path=custom_id).first()

            if post and post.slug:
                posts.append({"post_id": post.id, "slug": post.slug})
    return posts


def main():
    parser = argparse.ArgumentParser(description="Playwright 렌더링 검증")
    parser.add_argument(
        "--quick-check",
        action="store_true",
        help="빠른 검증: 최신 5건 + 카테고리별 1건",
    )
    parser.add_argument(
        "--post-ids",
        type=str,
        default=None,
        help="검증할 post ID 목록 (콤마 구분, 예: 1,2,3)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="fixstyle 출력 JSONL 파일 경로 (슬러그를 자동으로 조회)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="브라우저 UI 표시 (디버깅용)",
    )
    args = parser.parse_args()

    posts_to_check: list[dict] = []

    if args.post_ids:
        ids = [int(x.strip()) for x in args.post_ids.split(",") if x.strip()]
        for post in Post.objects.filter(id__in=ids).only("id", "slug"):
            if post.slug:
                posts_to_check.append({"post_id": post.id, "slug": post.slug})

    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"파일 없음: {input_path}")
            sys.exit(1)
        posts_to_check = posts_from_jsonl(input_path)

    elif args.quick_check:
        # 최신 5건 + 포스트 타입별 1건
        seen_types = set()
        qs = Post.objects.filter(status="published").order_by("-created_at").only("id", "slug", "post_type")
        for post in qs[:50]:
            if not post.slug:
                continue
            if len(posts_to_check) < 5 or post.post_type not in seen_types:
                posts_to_check.append({"post_id": post.id, "slug": post.slug})
                seen_types.add(post.post_type)
            if len(posts_to_check) >= 15:
                break
    else:
        # 전체 published 포스트
        for post in Post.objects.filter(status="published").only("id", "slug").order_by("id"):
            if post.slug:
                posts_to_check.append({"post_id": post.id, "slug": post.slug})

    if not posts_to_check:
        print("검증할 포스트가 없습니다.")
        sys.exit(0)

    print(f"검증 대상: {len(posts_to_check)}건")
    print(f"Base URL: {BLOG_BASE}")
    print()

    results = run_checks(posts_to_check, headless=not args.no_headless)

    # 에러 파일 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 요약
    total = len(results)
    ok_http = sum(1 for r in results if r.get("status") == 200)
    katex_issues = sum(1 for r in results if r["katex_errors"] > 0)
    broken_imgs = sum(1 for r in results if r["broken_images"] > 0)

    print(f"\n=== Playwright 검증 완료 ===")
    print(f"총: {total}건 | HTTP 200: {ok_http}건")
    print(f"KaTeX 에러: {katex_issues}건 | 깨진 이미지: {broken_imgs}건")
    print(f"스크린샷: {SCREENSHOTS_DIR}/")
    print(f"에러 리포트: {ERRORS_FILE}")

    if katex_issues or broken_imgs:
        print("\n[ 문제 포스트 ]")
        for r in results:
            if r["katex_errors"] > 0 or r["broken_images"] > 0:
                print(
                    f"  post_id={r['post_id']} | katex={r['katex_errors']} | "
                    f"broken_img={r['broken_images']} | {r['url']}"
                )


if __name__ == "__main__":
    main()
