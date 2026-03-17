"""
Claude Code 직접 콘텐츠 개선 헬퍼 스크립트.

모드 1: --list
    preprocessed 파일을 카테고리 단위로 나열해 Claude Code가 처리할 순서를 파악.

    python pipeline/fixstyle_interactive.py --list --category 20.AI

모드 2: --import-dir (서버에서 Django 환경으로 실행)
    fixstyle/ 디렉토리의 .md 파일을 읽어 DB 반영.

    docker compose -f docker-compose.prod.yml run --rm \\
      -v /opt/blog-jun/pipeline:/app/pipeline \\
      -e PYTHONPATH=/app \\
      backend python /app/pipeline/fixstyle_interactive.py \\
      --import-dir /app/pipeline/data/fixstyle/

파일 네이밍 규칙:
    source_path "20.AI/22. ML/KNN.md"
    → fixstyle 파일: "20.AI__22. ML__KNN.md"
    (슬래시를 더블언더스코어로 치환 — preprocessed와 동일)
"""
import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
FIXSTYLE_DIR = DATA_DIR / "fixstyle"

VAULT_DIR = Path(os.environ.get("VAULT_DIR", "/Users/dorae222/Documents/Obsidian/hyeongjun"))


# ──────────────────────────────────────────────
# 공통 유틸
# ──────────────────────────────────────────────

def path_to_filename(source_path: str) -> str:
    """source_path → fixstyle 파일명 (슬래시 → __)."""
    return source_path.replace("/", "__")


def filename_to_path(filename: str) -> str:
    """fixstyle 파일명 → source_path."""
    if filename.endswith(".md"):
        filename = filename[:-3]
    return filename.replace("__", "/")


def load_catalog() -> list[dict]:
    if not CATALOG_FILE.exists():
        print(f"[ERROR] catalog.json 없음: {CATALOG_FILE}")
        sys.exit(1)
    with open(CATALOG_FILE, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# 모드 1: --list
# ──────────────────────────────────────────────

def cmd_list(category: str):
    """카테고리 처리 목록 출력 (done / todo 구분)."""
    catalog = load_catalog()

    # 카테고리 필터링 (prefix 매칭, skip=False)
    items = [
        item for item in catalog
        if item.get("top_category", "").startswith(category)
        and not item.get("skip", False)
    ]

    if not items:
        print(f"[WARN] '{category}' 에 해당하는 항목 없음 (또는 전부 skip=True)")
        return

    # word_count 오름차순 정렬
    items.sort(key=lambda x: x.get("word_count", 0))

    FIXSTYLE_DIR.mkdir(parents=True, exist_ok=True)
    # NFC normalize to handle macOS HFS+ NFD vs Python NFC mismatch
    done_files = {unicodedata.normalize("NFC", f.name) for f in FIXSTYLE_DIR.glob("*.md")}

    done_count = 0
    todo_count = 0
    rows = []

    for item in items:
        source_path = item["path"]
        fname = unicodedata.normalize("NFC", path_to_filename(source_path))
        is_done = fname in done_files

        # preprocessed 파일 존재 여부
        pre_file = PREPROCESSED_DIR / fname
        has_pre = pre_file.exists()

        word_count = item.get("word_count", 0)
        has_latex = "L" if item.get("has_latex") else " "
        has_code = "C" if item.get("has_code") else " "
        has_images = "I" if item.get("has_images") else " "
        flags = f"[{has_latex}{has_code}{has_images}]"  # L=latex C=code I=images

        if is_done:
            done_count += 1
        else:
            todo_count += 1

        rows.append((is_done, word_count, source_path, flags, has_pre))

    total = len(items)
    print(f"\n=== {category} 목록 ({total}건) ===")
    print(f"[ done {done_count:3d} ]  [ todo {todo_count:3d} ]\n")

    for is_done, word_count, source_path, flags, has_pre in rows:
        status = "done" if is_done else "todo"
        pre_tag = "pre" if has_pre else "raw"
        print(f"[{status:4}] [{word_count:5d}자] {flags} ({pre_tag}) {source_path}")

    print(f"\n범례: L=LaTeX C=Code I=Images | pre=preprocessed 있음 raw=vault 원본 사용")


# ──────────────────────────────────────────────
# 모드 2: --import-dir
# ──────────────────────────────────────────────

def _setup_django():
    BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django
    django.setup()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    YAML frontmatter 파싱.
    반환: (meta_dict, content_without_frontmatter)
    frontmatter 없으면 ({}, 원본 텍스트)
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    content = text[end + 4:].lstrip("\n")

    meta = {}
    _last_key = ""
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        # 리스트 항목 (  - value)
        if line.startswith("  - ") and _last_key:
            meta.setdefault(_last_key, [])
            if isinstance(meta[_last_key], list):
                meta[_last_key].append(line[4:].strip())
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            _last_key = k
            if v == "true":
                meta[k] = True
            elif v == "false":
                meta[k] = False
            elif v == "":
                meta[k] = []
            else:
                try:
                    meta[k] = float(v) if "." in v else int(v)
                except ValueError:
                    meta[k] = v

    return meta, content


def parse_frontmatter_yaml(text: str) -> tuple[dict, str]:
    """yaml 라이브러리를 사용한 안전한 파싱 (있으면 사용, 없으면 수동 파싱)."""
    try:
        import yaml
    except ImportError:
        return parse_frontmatter(text)

    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    content = text[end + 4:].lstrip("\n")

    try:
        meta = yaml.safe_load(fm_text) or {}
    except Exception:
        meta = {}

    return meta, content


def cmd_import_dir(import_dir: str):
    """fixstyle/ 디렉토리의 .md 파일을 순회하여 DB 반영."""
    _setup_django()

    from django.utils.text import slugify
    from blog.models import Post, Tag

    fixstyle_path = Path(import_dir)
    if not fixstyle_path.exists():
        print(f"[ERROR] 디렉토리 없음: {fixstyle_path}")
        sys.exit(1)

    md_files = sorted(fixstyle_path.glob("*.md"))
    if not md_files:
        print(f"[WARN] .md 파일 없음: {fixstyle_path}")
        return

    updated = 0
    archived = 0
    skipped = 0
    errors = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        meta, content = parse_frontmatter_yaml(text)

        source_path = meta.get("source_path", "")
        if not source_path:
            # 파일명에서 역산
            source_path = filename_to_path(md_file.stem)

        post = Post.objects.filter(source_path=source_path).first()
        if post is None:
            print(f"[SKIP] 포스트 없음: {source_path}")
            skipped += 1
            continue

        should_archive = meta.get("should_archive", False)
        quality_score = float(meta.get("quality_score", 5.0))

        if should_archive:
            post.status = "archived"
            post.save(update_fields=["status"])
            print(f"[ARCHIVE] {post.id}: {post.title[:50]}")
            archived += 1
            continue

        # 업데이트
        try:
            if meta.get("title"):
                post.title = meta["title"]
            if content.strip():
                post.content = content.strip()
            if meta.get("summary"):
                post.summary = str(meta["summary"])[:500]
            if meta.get("post_type"):
                post.post_type = meta["post_type"]
            post.quality_score = quality_score

            post.save(update_fields=[
                "title", "content", "summary", "post_type", "quality_score", "updated_at"
            ])

            # 태그
            tag_names = meta.get("tags", [])
            if isinstance(tag_names, list) and tag_names:
                tag_objs = []
                for name in tag_names:
                    name = str(name).strip()
                    if not name:
                        continue
                    tag_slug = name.lower().replace(" ", "-")[:100]
                    tag, _ = Tag.objects.get_or_create(
                        slug=tag_slug,
                        defaults={"name": name},
                    )
                    tag_objs.append(tag)
                post.tags.set(tag_objs)

            print(f"[OK] {post.id}: {post.title[:60]} (score={quality_score:.1f})")
            updated += 1

        except Exception as e:
            print(f"[ERROR] {source_path}: {e}")
            errors += 1

    print(f"\n=== Import 완료 ===")
    print(f"Updated:  {updated}")
    print(f"Archived: {archived}")
    print(f"Skipped:  {skipped}")
    print(f"Errors:   {errors}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="fixstyle_interactive — Claude Code 콘텐츠 개선 헬퍼"
    )
    sub = parser.add_subparsers(dest="mode")

    # --list
    p_list = sub.add_parser("list", help="카테고리 처리 목록 출력")
    p_list.add_argument("--category", required=True, help="e.g. 20.AI")

    # --import-dir
    p_import = sub.add_parser("import-dir", help="fixstyle/ 디렉토리 DB 반영")
    p_import.add_argument("--dir", required=True, help="fixstyle 디렉토리 경로")

    # 구 스타일 인자도 지원 (--list --category / --import-dir)
    parser.add_argument("--list", action="store_true", help="목록 출력 모드")
    parser.add_argument("--category", help="카테고리 (--list와 함께)")
    parser.add_argument("--import-dir", dest="import_dir", help="import 디렉토리 경로")

    args = parser.parse_args()

    if args.mode == "list":
        cmd_list(args.category)
    elif args.mode == "import-dir":
        cmd_import_dir(args.dir)
    elif args.list:
        if not args.category:
            parser.error("--list 에는 --category 가 필요합니다")
        cmd_list(args.category)
    elif args.import_dir:
        cmd_import_dir(args.import_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
