"""
Process images from Obsidian vault for blog use.
- Build image index from vault
- Resolve 4 types of image references (wikilink, markdown, jupyter, external)
- Copy only referenced images with category-based subdirectories
- Handle Untitled.png ambiguity via category proximity + modification time
- Generate image_map.json for preprocessor path conversion
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from urllib.parse import unquote

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "hyeongjun"
MEDIA_DIR = Path(__file__).resolve().parent.parent / "backend" / "media" / "posts" / "imported"
DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"}

# Attachment 폴더 → 블로그 서브디렉토리 매핑
ATTACHMENT_DIR_MAP = {
    "92.AWS-Attachments": "aws",
    "93.AI-Attachments": "ai",
    "94.Project-Attachments": "project",
    "95.Program-Attachments": "program",
    "97.Dev-Attachments": "dev",
    "98.Foundation-Attachments": "foundation",
}

# 소스 마크다운 카테고리 → 우선 탐색할 Attachment 폴더
CATEGORY_TO_ATTACHMENT = {
    "10.Cloud": "92.AWS-Attachments",
    "20.AI": "93.AI-Attachments",
    "30.Data": "97.Dev-Attachments",
    "40.DEV": "97.Dev-Attachments",
    "50.Foundation": "98.Foundation-Attachments",
    "60.Project": "94.Project-Attachments",
    "70.Program": "95.Program-Attachments",
}


def build_image_index() -> dict[str, list[Path]]:
    """vault 전체 이미지 인덱스: filename → [full_paths]

    90.Settings(첨부파일) 우선 탐색 후, vault 전체에서 추가 이미지 수집.
    한글 파일명 포함.
    """
    index = {}
    seen_paths = set()

    # 1. 90.Settings (Attachment 폴더) — 우선 탐색
    settings_dir = VAULT_ROOT / "90.Settings"
    if settings_dir.exists():
        for img_file in settings_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in IMAGE_EXTENSIONS:
                name = img_file.name
                if name not in index:
                    index[name] = []
                index[name].append(img_file)
                seen_paths.add(img_file)

    # 2. vault 전체 탐색 (90.Settings 외 폴더의 인라인 이미지 포함)
    exclude_dirs = {".obsidian", ".trash", "node_modules", ".git"}
    for img_file in VAULT_ROOT.rglob("*"):
        if img_file.is_file() and img_file.suffix.lower() in IMAGE_EXTENSIONS:
            # 제외 디렉토리 스킵
            if any(part in exclude_dirs for part in img_file.parts):
                continue
            if img_file in seen_paths:
                continue
            name = img_file.name
            if name not in index:
                index[name] = []
            index[name].append(img_file)
            seen_paths.add(img_file)

    return index


def get_blog_subdir(image_path: Path) -> str:
    """이미지 경로에서 블로그 서브디렉토리 결정."""
    rel = str(image_path.relative_to(VAULT_ROOT)) if image_path.is_relative_to(VAULT_ROOT) else str(image_path)
    for attach_dir, subdir in ATTACHMENT_DIR_MAP.items():
        if attach_dir in rel:
            return subdir
    return "etc"


def short_hash(path: Path) -> str:
    """파일 경로 기반 짧은 해시 (충돌 방지용)."""
    return hashlib.md5(str(path).encode()).hexdigest()[:8]


def resolve_wikilink(ref: str, source_path: str, index: dict[str, list[Path]],
                     warnings: list[dict]) -> Path | None:
    """![[path]] 스타일 참조를 실제 파일 경로로 resolve.

    ref: 경로 문자열 (예: "90.Settings/93.AI-Attachments/DL-Basic/img.png")
    source_path: 소스 마크다운의 상대 경로 (예: "20.AI/DL/Basic.md")
    """
    ref = unquote(ref).strip()

    # data: URI, base64, 너무 긴 참조 → 무시
    if ref.startswith("data:") or len(ref) > 500:
        return None

    # 전체 경로가 주어진 경우 (90.Settings/... 포함)
    full_path = VAULT_ROOT / ref
    if full_path.exists() and full_path.is_file():
        return full_path

    # 파일명만으로 인덱스 검색
    filename = Path(ref).name
    candidates = index.get(filename, [])

    if not candidates:
        warnings.append({"ref": ref, "source": source_path, "reason": "not_found"})
        return None

    if len(candidates) == 1:
        return candidates[0]

    # 복수 매치: 소스 카테고리 기반 우선순위
    source_top = source_path.split("/")[0] if "/" in source_path else ""
    preferred_attach = CATEGORY_TO_ATTACHMENT.get(source_top, "")

    if preferred_attach:
        preferred = [c for c in candidates if preferred_attach in str(c)]
        if len(preferred) == 1:
            return preferred[0]
        if preferred:
            candidates = preferred

    # 수정일 기준 가장 최근 파일
    try:
        best = max(candidates, key=lambda p: p.stat().st_mtime)
    except OSError:
        best = candidates[0]

    warnings.append({
        "ref": ref,
        "source": source_path,
        "reason": "ambiguous",
        "candidates": len(candidates),
        "resolved": str(best.relative_to(VAULT_ROOT)),
    })
    return best


def resolve_markdown_ref(ref: str, source_path: str, index: dict[str, list[Path]],
                         warnings: list[dict]) -> Path | None:
    """![alt](relative/path) 스타일 참조를 실제 파일 경로로 resolve."""
    ref = unquote(ref).strip()

    # data: URI, base64 인코딩 이미지 → resolve 불가
    if ref.startswith("data:") or len(ref) > 500:
        return None

    # 상대 경로 해석
    source_dir = (VAULT_ROOT / source_path).parent
    try:
        resolved = (source_dir / ref).resolve()
        if resolved.exists() and resolved.is_file():
            return resolved
    except (OSError, ValueError):
        # 경로가 너무 길거나 잘못된 경우
        return None

    # 상대 경로 실패 시 파일명으로 인덱스 검색
    filename = Path(ref).name
    return resolve_wikilink(filename, source_path, index, warnings)


def resolve_image_ref(ref_info: dict, source_path: str, index: dict[str, list[Path]],
                      warnings: list[dict]) -> Path | None:
    """이미지 참조를 실제 파일 경로로 resolve."""
    ref_type = ref_info["type"]
    ref = ref_info["ref"]

    if ref_type == "wikilink":
        return resolve_wikilink(ref, source_path, index, warnings)
    elif ref_type == "markdown":
        return resolve_markdown_ref(ref, source_path, index, warnings)
    elif ref_type == "jupyter":
        # Jupyter attachment:는 임베디드 → resolve 불가
        return None
    elif ref_type == "external":
        # 외부 URL → 복사 불필요
        return None

    return None


def copy_referenced_images(catalog: list[dict], index: dict[str, list[Path]]) -> dict:
    """참조된 이미지만 복사하고 매핑 테이블 생성.

    Returns:
        image_map: { "원본 vault 상대경로": "/media/posts/imported/subdir/filename" }
    """
    image_map = {}
    stats = {"copied": 0, "skipped_exists": 0, "skipped_external": 0,
             "skipped_jupyter": 0, "not_found": 0, "ambiguous": 0}
    warnings = []
    dest_names = {}  # 서브디렉토리/파일명 → 원본경로 (충돌 감지)

    for entry in catalog:
        source_path = entry["path"]
        for ref_info in entry.get("image_refs", []):
            if ref_info["type"] == "external":
                stats["skipped_external"] += 1
                continue
            if ref_info["type"] == "jupyter":
                stats["skipped_jupyter"] += 1
                continue

            resolved = resolve_image_ref(ref_info, source_path, index, warnings)
            if resolved is None:
                stats["not_found"] += 1
                continue

            # 이미 매핑된 이미지는 스킵
            vault_rel = str(resolved.relative_to(VAULT_ROOT))
            if vault_rel in image_map:
                continue

            # 블로그 서브디렉토리 결정
            subdir = get_blog_subdir(resolved)
            dest_dir = MEDIA_DIR / subdir
            dest_dir.mkdir(parents=True, exist_ok=True)

            # 파일명 충돌 처리
            dest_name = resolved.name
            dest_key = f"{subdir}/{dest_name}"

            if dest_key in dest_names and dest_names[dest_key] != vault_rel:
                # 충돌: 해시 접미사 추가
                stem = resolved.stem
                suffix = resolved.suffix
                h = short_hash(resolved)
                dest_name = f"{stem}_{h}{suffix}"
                dest_key = f"{subdir}/{dest_name}"

            dest_names[dest_key] = vault_rel
            dest_path = dest_dir / dest_name

            # 복사
            if not dest_path.exists():
                shutil.copy2(resolved, dest_path)
                stats["copied"] += 1
            else:
                stats["skipped_exists"] += 1

            blog_url = f"/media/posts/imported/{subdir}/{dest_name}"
            image_map[vault_rel] = blog_url

    # 경고 통계
    stats["ambiguous"] = sum(1 for w in warnings if w["reason"] == "ambiguous")

    return image_map, stats, warnings


def build_ref_to_url_map(image_map: dict) -> dict:
    """원본 참조 문자열 → 블로그 URL 역매핑.

    image_map은 vault 상대경로 기준이지만, 마크다운에서 참조하는 문자열은
    다양한 형태이므로 여러 키로 매핑을 구축.
    """
    ref_map = {}
    for vault_rel, blog_url in image_map.items():
        # vault 상대경로 자체
        ref_map[vault_rel] = blog_url
        # 파일명만
        filename = Path(vault_rel).name
        if filename not in ref_map:
            ref_map[filename] = blog_url
        # 90.Settings/ 제외한 경로
        if vault_rel.startswith("90.Settings/"):
            short = vault_rel[len("90.Settings/"):]
            ref_map[short] = blog_url
    return ref_map


def process_images():
    """메인 이미지 처리 로직."""
    print("=== Image Processor ===")

    # 카탈로그 로드
    if not CATALOG_FILE.exists():
        print("Error: Run scanner.py first!")
        return

    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    # 이미지 인덱스 빌드
    print("Building image index...")
    index = build_image_index()
    total_images = sum(len(paths) for paths in index.values())
    print(f"  Found {len(index)} unique filenames ({total_images} total files)")

    # 참조된 이미지만 복사
    print("Copying referenced images...")
    image_map, stats, warnings = copy_referenced_images(catalog, index)

    # 참조 → URL 역매핑 빌드
    ref_map = build_ref_to_url_map(image_map)

    # image_map 저장 (preprocessor가 사용)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    map_output = {
        "image_map": image_map,
        "ref_map": ref_map,
    }
    with open(IMAGE_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(map_output, f, ensure_ascii=False, indent=2)

    # 고아 이미지 통계
    referenced_files = set(image_map.keys())
    all_vault_images = set()
    settings_dir = VAULT_ROOT / "90.Settings"
    if settings_dir.exists():
        for img in settings_dir.rglob("*"):
            if img.is_file() and img.suffix.lower() in IMAGE_EXTENSIONS:
                all_vault_images.add(str(img.relative_to(VAULT_ROOT)))
    orphan_count = len(all_vault_images - referenced_files)

    # 통계 출력
    print(f"\n=== Image Processing Results ===")
    print(f"Copied: {stats['copied']}")
    print(f"Already existed: {stats['skipped_exists']}")
    print(f"External URLs (kept as-is): {stats['skipped_external']}")
    print(f"Jupyter attachments (removed): {stats['skipped_jupyter']}")
    print(f"Not found: {stats['not_found']}")
    print(f"Ambiguous (resolved with heuristic): {stats['ambiguous']}")
    print(f"Orphan images (not copied): {orphan_count}")
    print(f"Total mapped: {len(image_map)}")
    print(f"\nImage map saved to {IMAGE_MAP_FILE}")

    # 서브디렉토리별 통계
    subdir_counts = {}
    for url in image_map.values():
        parts = url.split("/")
        if len(parts) >= 5:
            sd = parts[4]  # /media/posts/imported/{subdir}/...
            subdir_counts[sd] = subdir_counts.get(sd, 0) + 1
    print(f"\nBy subdirectory:")
    for sd, count in sorted(subdir_counts.items()):
        print(f"  {sd}/: {count}")

    # 경고 저장
    if warnings:
        warn_file = DATA_DIR / "image_warnings.json"
        with open(warn_file, "w", encoding="utf-8") as f:
            json.dump(warnings, f, ensure_ascii=False, indent=2)
        print(f"\n{len(warnings)} warnings saved to {warn_file}")

    return image_map, stats, warnings


if __name__ == "__main__":
    process_images()
