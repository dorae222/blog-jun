"""
vault PDF → media 복사 + post.pdf_file 업데이트.

60.Project 카테고리 포스트와 vault PDF 파일명을 키워드 매칭으로 연결.
매핑된 PDF를 서버 media/posts/pdfs/에 복사하고 post.pdf_file 필드 업데이트.

실행:
    python pipeline/pdf_import.py --dry-run    # 매핑 목록만 출력
    python pipeline/pdf_import.py --execute    # 실제 복사 + DB 업데이트

도커 실행:
    docker compose -f docker-compose.prod.yml run --rm \\
      -v /opt/blog-jun/pipeline:/app/pipeline \\
      -v /Users/dorae222/Documents/Obsidian/hyeongjun:/vault:ro \\
      -e PYTHONPATH=/app \\
      backend python /app/pipeline/pdf_import.py --dry-run
"""
import argparse
import shutil
import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.conf import settings
from blog.models import Post

# vault 마운트 경로 (도커 내부) 또는 로컬 경로
VAULT_DIR = Path(os.environ.get("VAULT_DIR", "/vault"))
PDF_DIR = VAULT_DIR / "90.Settings" / "94.Project-Attachments"

# 서버 미디어 경로
MEDIA_PDF_DIR = Path(settings.MEDIA_ROOT) / "posts" / "pdfs"


def find_candidate_pdfs() -> list[Path]:
    """PDF_DIR에서 모든 PDF 파일 목록 반환."""
    if not PDF_DIR.exists():
        print(f"[경고] PDF 디렉토리 없음: {PDF_DIR}")
        return []
    return sorted(PDF_DIR.glob("*.pdf"))


def score_match(source_path: str, pdf_stem: str) -> int:
    """source_path 파일명과 PDF 파일명 간 키워드 매칭 점수."""
    title_words = Path(source_path).stem.lower().replace("-", " ").replace("_", " ").split()
    pdf_words = pdf_stem.lower().replace("-", " ").replace("_", " ")
    return sum(1 for w in title_words if len(w) >= 3 and w in pdf_words)


def build_mapping(posts: list, pdfs: list[Path]) -> list[tuple]:
    """
    (post, pdf_path) 매핑 리스트 반환.
    각 포스트에 대해 최고 점수 PDF와 매핑 (score >= 1인 경우만).
    """
    mappings = []
    for post in posts:
        source = post.source_path or ""
        if not source.startswith("60.Project"):
            continue

        best_pdf: Path | None = None
        best_score = 0
        for pdf in pdfs:
            score = score_match(source, pdf.stem)
            if score > best_score:
                best_score = score
                best_pdf = pdf

        if best_pdf and best_score >= 1:
            mappings.append((post, best_pdf, best_score))

    mappings.sort(key=lambda x: -x[2])
    return mappings


def run(execute: bool):
    pdfs = find_candidate_pdfs()
    if not pdfs:
        print("처리할 PDF 파일이 없습니다.")
        return

    posts = Post.objects.filter(
        status="published",
        source_path__startswith="60.Project",
    ).only("id", "title", "source_path", "pdf_file")

    mappings = build_mapping(list(posts), pdfs)

    print(f"\n=== PDF Import {'[DRY-RUN]' if not execute else '[EXECUTE]'} ===")
    print(f"PDF 파일: {len(pdfs)}개")
    print(f"60.Project 포스트: {posts.count()}건")
    print(f"매핑 성공: {len(mappings)}건\n")

    for post, pdf_path, score in mappings:
        dest_name = f"{post.id}_{pdf_path.name}"
        print(f"  [score={score}] {post.title[:50]:<50} ← {pdf_path.name}")
        if execute:
            # 미디어 디렉토리 생성
            MEDIA_PDF_DIR.mkdir(parents=True, exist_ok=True)
            dest = MEDIA_PDF_DIR / dest_name
            shutil.copy2(pdf_path, dest)

            # DB 업데이트 (FileField에 상대 경로 저장)
            relative_path = f"posts/pdfs/{dest_name}"
            post.pdf_file = relative_path
            post.save(update_fields=["pdf_file"])

    if not execute:
        print("\n[DRY-RUN] 실제 변경 없음. --execute 플래그로 재실행하세요.")
    else:
        print(f"\n{len(mappings)}개 PDF 복사 + DB 업데이트 완료.")


def main():
    parser = argparse.ArgumentParser(description="vault PDF → media 복사 + DB 업데이트")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="매핑 목록만 출력 (실제 변경 없음)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 복사 + DB 업데이트",
    )
    args = parser.parse_args()

    if not args.execute:
        run(execute=False)
    else:
        run(execute=True)


if __name__ == "__main__":
    main()
