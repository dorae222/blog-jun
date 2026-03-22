"""
이미지 핸들러: Notion HTML 내보내기의 이미지를 블로그 media 디렉토리로 복사.
- URL 디코딩된 경로 해석
- Untitled.png 충돌 해결 (MD5 해시)
- parsed/*.md 이미지 경로 → 블로그 URL 치환
- 외부 Notion static URL 다운로드 시도

입력: data/discovered_images.json + data/catalog.json + 실제 이미지 파일
출력: data/image_map.json + backend/media/posts/imported/{subdir}/
"""
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
IMAGES_FILE = DATA_DIR / "discovered_images.json"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"
PARSED_DIR = DATA_DIR / "parsed"

MEDIA_DIR = Path(__file__).resolve().parent.parent / "backend" / "media" / "posts" / "imported"

# 카테고리 코드 → 이미지 하위 디렉토리
CATEGORY_SUBDIR = {
    "20.AI": "ai",
    "30.Data": "data",
    "40.DEV": "dev",
    "60.Project": "project",
}


def get_subdir(category: str) -> str:
    """카테고리 코드에서 이미지 서브디렉토리 결정."""
    return CATEGORY_SUBDIR.get(category, "etc")


def safe_filename(name: str, src_path: str) -> str:
    """파일명 충돌 방지. Untitled.png 등은 MD5 해시 접미사 추가."""
    stem = Path(name).stem
    suffix = Path(name).suffix

    # Untitled 또는 일반적인 충돌 이름
    if stem.lower() in ('untitled', 'image', 'screenshot', 'img'):
        # 소스 경로 기반 MD5
        hash_str = hashlib.md5(src_path.encode()).hexdigest()[:8]
        return f"{stem}_{hash_str}{suffix}"

    # 파일명에 안전하지 않은 문자 치환
    safe = stem.replace(' ', '_')
    safe = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in safe)
    return f"{safe}{suffix}"


def resolve_local_image(html_dir: str, decoded_path: str) -> Path | None:
    """HTML 디렉토리 기준으로 로컬 이미지 경로 해석."""
    html_dir_path = Path(html_dir)

    # URL 디코딩 (이중 인코딩 가능)
    decoded = urllib.parse.unquote(decoded_path)
    decoded = urllib.parse.unquote(decoded)  # 이중 디코딩

    # 절대 경로인 경우
    abs_path = html_dir_path / decoded
    if abs_path.exists():
        return abs_path

    # 상위 디렉토리에서 찾기
    parent_path = html_dir_path.parent / decoded
    if parent_path.exists():
        return parent_path

    # 파일명만으로 검색 (같은 디렉토리 트리 내)
    filename = Path(decoded).name
    for f in html_dir_path.rglob(filename):
        return f

    # 부모 디렉토리에서도 검색
    for f in html_dir_path.parent.rglob(filename):
        return f

    return None


def download_external_image(url: str, dest: Path) -> bool:
    """외부 URL에서 이미지 다운로드 시도."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(dest, 'wb') as f:
                f.write(response.read())
        return True
    except Exception:
        return False


def process_images():
    """이미지 처리 메인 함수."""
    if not IMAGES_FILE.exists():
        print("⚠️  discovered_images.json 없음. html_parser.py를 먼저 실행하세요.")
        return

    with open(IMAGES_FILE) as f:
        images = json.load(f)

    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    # catalog에서 카테고리 정보 가져오기
    title_to_cat = {}
    for item in catalog:
        title_to_cat[item["title"]] = item.get("parent_code", "")

    stats = Counter()
    image_map = {}  # original_ref → blog URL
    used_filenames: dict[str, set[str]] = {}  # subdir → set of filenames

    for img in images:
        original_ref = img["original_ref"]
        decoded_path = img["decoded_path"]
        html_dir = img["html_dir"]
        category = img.get("category", "")
        is_external = img.get("external", False)

        subdir = get_subdir(category)
        dest_dir = MEDIA_DIR / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        if subdir not in used_filenames:
            used_filenames[subdir] = set()

        if is_external:
            # 외부 URL 다운로드 시도
            filename = safe_filename(Path(urllib.parse.urlparse(decoded_path).path).name or "image.png",
                                     decoded_path)

            # 파일명 충돌 방지
            while filename in used_filenames[subdir]:
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                hash_str = hashlib.md5(decoded_path.encode()).hexdigest()[:8]
                filename = f"{stem}_{hash_str}{suffix}"

            dest_path = dest_dir / filename

            if download_external_image(decoded_path, dest_path):
                blog_url = f"/media/posts/imported/{subdir}/{filename}"
                image_map[original_ref] = blog_url
                used_filenames[subdir].add(filename)
                stats["external_downloaded"] += 1
            else:
                # 다운로드 실패 → 원본 URL 유지
                image_map[original_ref] = decoded_path
                stats["external_failed"] += 1
        else:
            # 로컬 이미지
            src_path = resolve_local_image(html_dir, decoded_path)
            if not src_path:
                stats["local_not_found"] += 1
                continue

            filename = safe_filename(src_path.name, str(src_path))

            # 파일명 충돌 방지
            while filename in used_filenames[subdir]:
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                hash_str = hashlib.md5(str(src_path).encode()).hexdigest()[:8]
                filename = f"{stem}_{hash_str}{suffix}"

            dest_path = dest_dir / filename

            if not dest_path.exists():
                shutil.copy2(src_path, dest_path)
                stats["local_copied"] += 1
            else:
                stats["local_exists"] += 1

            blog_url = f"/media/posts/imported/{subdir}/{filename}"
            image_map[original_ref] = blog_url
            used_filenames[subdir].add(filename)

    # image_map 저장
    with open(IMAGE_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump({"ref_map": image_map, "stats": dict(stats)}, f, ensure_ascii=False, indent=2)

    # parsed/*.md 파일의 이미지 경로 치환
    updated_files = 0
    for md_file in PARSED_DIR.glob("*.md"):
        content = md_file.read_text(encoding='utf-8')
        modified = False

        for original_ref, blog_url in image_map.items():
            # URL 디코딩된 경로도 치환
            decoded_ref = urllib.parse.unquote(original_ref)
            decoded_ref2 = urllib.parse.unquote(decoded_ref)

            for ref in [original_ref, decoded_ref, decoded_ref2]:
                if ref in content:
                    content = content.replace(ref, blog_url)
                    modified = True

        if modified:
            md_file.write_text(content, encoding='utf-8')
            updated_files += 1

    print(f"\n=== Image Handler Results ===")
    print(f"Total images: {len(images)}")
    for key, val in stats.most_common():
        print(f"  {key}: {val}")
    print(f"Image map entries: {len(image_map)}")
    print(f"Updated markdown files: {updated_files}")
    print(f"Image map saved to: {IMAGE_MAP_FILE}")


if __name__ == "__main__":
    process_images()
