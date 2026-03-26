#!/usr/bin/env python3
"""arXiv URL로 논문 디렉토리를 자동 생성하는 스크립트.

arXiv API에서 메타데이터를 가져오고, content.json / content.md / figure_reference.json을
생성한 뒤, scrape_arxiv_figures.py를 호출하여 figure를 크롤링합니다.

사용법:
  python pipeline/add_paper.py --url https://arxiv.org/abs/2512.08296
  python pipeline/add_paper.py --url https://arxiv.org/abs/2512.08296 --category agent
  python pipeline/add_paper.py --urls-file papers.txt  # 배치 모드 (한 줄에 하나씩)
"""
import argparse
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests

# ── 경로 설정 ──────────────────────────────────────────────────────────
PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers_written"
SCRAPE_SCRIPT = PIPELINE_DIR / "scrape_arxiv_figures.py"

# ── 상수 ───────────────────────────────────────────────────────────────
ARXIV_API_URL = "http://export.arxiv.org/api/query"
RATE_LIMIT = 3  # seconds — arXiv API 정책 준수
REQUEST_TIMEOUT = 30  # seconds

# ── arXiv 카테고리 → 블로그 카테고리 매핑 ─────────────────────────────
CATEGORY_MAP = {
    # NLP / Transformer → llm
    "cs.CL": ("llm", "nlp"),
    "cs.NE": ("llm", "transformer"),
    # Vision
    "cs.CV": ("vision", ""),
    # Agent
    "cs.AI": ("agent", ""),
    "cs.MA": ("agent", ""),
    # Technique (기본)
    "cs.LG": ("technique", ""),
    "stat.ML": ("technique", ""),
    "eess.SP": ("technique", ""),
    "eess.AS": ("technique", ""),
}
DEFAULT_CATEGORY = ("technique", "")


# ── 색상 출력 ──────────────────────────────────────────────────────────
class Color:
    """터미널 색상 코드. 비-TTY 환경에서는 무색."""

    _enabled = sys.stdout.isatty()

    RESET = "\033[0m" if _enabled else ""
    BOLD = "\033[1m" if _enabled else ""
    GREEN = "\033[32m" if _enabled else ""
    YELLOW = "\033[33m" if _enabled else ""
    RED = "\033[31m" if _enabled else ""
    CYAN = "\033[36m" if _enabled else ""
    DIM = "\033[2m" if _enabled else ""


def info(msg: str) -> None:
    print(f"{Color.GREEN}[INFO]{Color.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{Color.YELLOW}[WARN]{Color.RESET} {msg}")


def error(msg: str) -> None:
    print(f"{Color.RED}[ERROR]{Color.RESET} {msg}")


def header(msg: str) -> None:
    print(f"\n{Color.BOLD}{Color.CYAN}{'=' * 60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{msg}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'=' * 60}{Color.RESET}")


# ── arXiv ID 추출 ─────────────────────────────────────────────────────
def extract_arxiv_id(url: str) -> Optional[str]:
    """arXiv URL에서 논문 ID를 추출한다.

    지원 형식:
      - https://arxiv.org/abs/2512.08296
      - https://arxiv.org/abs/2512.08296v2
      - https://arxiv.org/pdf/2512.08296
      - http://arxiv.org/abs/hep-th/9802150

    Returns:
        arXiv ID 문자열 (버전 번호 제거) 또는 None
    """
    url = url.strip()
    if not url:
        return None

    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?',
        r'arxiv\.org/(?:abs|pdf)/([\w\-]+/\d{7})(?:v\d+)?',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ── Slug 생성 ──────────────────────────────────────────────────────────
def generate_slug(title: str, max_length: int = 100) -> str:
    """논문 제목에서 URL-safe slug를 생성한다.

    Django의 slugify와 유사하지만, 외부 의존성 없이 동작.
    """
    # 소문자 변환
    slug = title.lower()
    # 특수문자를 공백으로
    slug = re.sub(r'[^\w\s-]', ' ', slug)
    # 연속 공백 → 단일 하이픈
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    # 연속 하이픈 제거
    slug = re.sub(r'-{2,}', '-', slug)
    # 길이 제한 (단어 경계에서 자르기)
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]
    return slug


# ── arXiv API 호출 ─────────────────────────────────────────────────────
def fetch_arxiv_metadata(arxiv_id: str) -> Optional[dict]:
    """arXiv API에서 논문 메타데이터를 가져온다.

    Returns:
        {
            "title": str,
            "authors": str,
            "year": int,
            "abstract": str,
            "categories": list[str],
            "arxiv_id": str,
            "arxiv_url": str,
        }
        또는 실패 시 None
    """
    params = {"id_list": arxiv_id}

    try:
        resp = requests.get(ARXIV_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        error(f"arXiv API 요청 실패: {e}")
        return None

    # XML 파싱
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        error(f"XML 파싱 실패: {e}")
        return None

    # Atom 네임스페이스
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    # entry 찾기
    entry = root.find("atom:entry", ns)
    if entry is None:
        error(f"arXiv 응답에서 entry를 찾을 수 없음 (ID: {arxiv_id})")
        return None

    # 에러 응답 체크 (존재하지 않는 논문)
    id_elem = entry.find("atom:id", ns)
    if id_elem is not None and "api/errors" in (id_elem.text or ""):
        error(f"논문을 찾을 수 없음: {arxiv_id}")
        return None

    # 제목
    title_elem = entry.find("atom:title", ns)
    title = ""
    if title_elem is not None and title_elem.text:
        # 줄바꿈과 연속 공백 정리
        title = re.sub(r'\s+', ' ', title_elem.text).strip()

    # 저자
    author_elems = entry.findall("atom:author/atom:name", ns)
    authors_list = [a.text.strip() for a in author_elems if a.text]
    # 3명 이상이면 "First Author et al." 형식
    if len(authors_list) > 3:
        authors = f"{authors_list[0]} et al."
    else:
        authors = ", ".join(authors_list)

    # 발행 연도
    published_elem = entry.find("atom:published", ns)
    year = 2024  # 기본값
    if published_elem is not None and published_elem.text:
        year_match = re.match(r'(\d{4})', published_elem.text)
        if year_match:
            year = int(year_match.group(1))

    # 초록
    summary_elem = entry.find("atom:summary", ns)
    abstract = ""
    if summary_elem is not None and summary_elem.text:
        abstract = re.sub(r'\s+', ' ', summary_elem.text).strip()

    # 카테고리
    category_elems = entry.findall("atom:category", ns)
    categories = [c.get("term", "") for c in category_elems if c.get("term")]

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "categories": categories,
        "arxiv_id": arxiv_id,
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
    }


# ── 카테고리 매핑 ──────────────────────────────────────────────────────
def map_category(
    arxiv_categories: list[str],
    override_category: Optional[str] = None,
) -> tuple[str, str]:
    """arXiv 카테고리를 블로그 카테고리로 매핑한다.

    Args:
        arxiv_categories: arXiv 카테고리 목록 (예: ["cs.CL", "cs.AI"])
        override_category: 사용자 지정 카테고리 (우선)

    Returns:
        (category, sub_category) 튜플
    """
    if override_category:
        return (override_category, "")

    for cat in arxiv_categories:
        if cat in CATEGORY_MAP:
            return CATEGORY_MAP[cat]

    return DEFAULT_CATEGORY


def generate_tags(arxiv_categories: list[str], title: str) -> list[str]:
    """arXiv 카테고리와 제목에서 태그를 생성한다."""
    tags = []

    # 카테고리 기반 태그
    category_tag_map = {
        "cs.CL": ["nlp"],
        "cs.NE": ["neural-architecture"],
        "cs.CV": ["computer-vision"],
        "cs.AI": ["artificial-intelligence"],
        "cs.MA": ["multi-agent"],
        "cs.LG": ["machine-learning"],
        "cs.IR": ["information-retrieval"],
        "cs.RO": ["robotics"],
        "cs.SE": ["software-engineering"],
        "stat.ML": ["statistical-learning"],
        "eess.SP": ["signal-processing"],
        "eess.AS": ["audio-speech"],
    }
    for cat in arxiv_categories:
        if cat in category_tag_map:
            tags.extend(category_tag_map[cat])

    # 제목에서 키워드 추출 (일반적인 ML/DL 키워드)
    title_lower = title.lower()
    keyword_tags = {
        "transformer": "transformer",
        "attention": "attention",
        "diffusion": "diffusion",
        "language model": "language-model",
        "reinforcement learning": "reinforcement-learning",
        "graph neural": "graph-neural-network",
        "contrastive": "contrastive-learning",
        "self-supervised": "self-supervised",
        "generative": "generative-model",
        "retrieval": "retrieval",
        "multimodal": "multimodal",
        "vision": "vision",
        "llm": "llm",
        "agent": "agent",
        "reasoning": "reasoning",
        "alignment": "alignment",
        "fine-tun": "fine-tuning",
        "pretraining": "pretraining",
        "pre-training": "pretraining",
        "efficient": "efficiency",
        "scaling": "scaling",
        "instruction": "instruction-tuning",
        "reward model": "reward-model",
        "mamba": "ssm",
        "state space": "ssm",
    }
    for keyword, tag in keyword_tags.items():
        if keyword in title_lower and tag not in tags:
            tags.append(tag)

    # 중복 제거 & 정렬
    return sorted(set(tags))


# ── 디렉토리 존재 확인 ─────────────────────────────────────────────────
def find_existing_paper(slug: str) -> Optional[Path]:
    """slug에 해당하는 기존 논문 디렉토리를 찾는다.

    번호 접두사가 있는 디렉토리(예: 5_llama)도 탐색.
    """
    # 1. 정확한 slug 매치
    plain_dir = PAPERS_DIR / slug
    if plain_dir.exists():
        return plain_dir

    # 2. 번호 접두사 디렉토리 탐색
    for paper_dir in PAPERS_DIR.iterdir():
        if not paper_dir.is_dir():
            continue
        match = re.match(r'^\d+_(.+)$', paper_dir.name)
        if match and match.group(1) == slug:
            return paper_dir

    # 3. content.json의 slug 필드와 비교
    for paper_dir in PAPERS_DIR.iterdir():
        if not paper_dir.is_dir():
            continue
        content_path = paper_dir / "content.json"
        if content_path.exists():
            try:
                data = json.loads(content_path.read_text(encoding="utf-8"))
                if data.get("slug") == slug:
                    return paper_dir
            except (json.JSONDecodeError, OSError):
                continue

    return None


def find_existing_by_arxiv_id(arxiv_id: str) -> Optional[Path]:
    """arxiv_id로 기존 논문 디렉토리를 찾는다."""
    arxiv_url_pattern = f"arxiv.org/abs/{arxiv_id}"
    for paper_dir in PAPERS_DIR.iterdir():
        if not paper_dir.is_dir():
            continue
        content_path = paper_dir / "content.json"
        if content_path.exists():
            try:
                data = json.loads(content_path.read_text(encoding="utf-8"))
                if arxiv_url_pattern in data.get("arxiv_url", ""):
                    return paper_dir
            except (json.JSONDecodeError, OSError):
                continue
    return None


# ── 파일 생성 ──────────────────────────────────────────────────────────
def create_content_json(
    paper_dir: Path,
    metadata: dict,
    slug: str,
    category: str,
    sub_category: str,
    tags: list[str],
) -> None:
    """content.json을 생성한다."""
    content = {
        "title": metadata["title"],
        "title_ko": "",
        "slug": slug,
        "category": category,
        "sub_category": sub_category,
        "year": metadata["year"],
        "venue": "",
        "authors": metadata["authors"],
        "arxiv_url": metadata["arxiv_url"],
        "summary": "",
        "tags": tags,
        "related_architecture": "",
    }

    content_path = paper_dir / "content.json"
    content_path.write_text(
        json.dumps(content, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    info(f"content.json 생성: {content_path}")


def create_content_md(paper_dir: Path) -> None:
    """content.md 스텁을 생성한다."""
    stub = """## 개요

## 배경 및 문제

## 핵심 아이디어

## 방법론

## 실험 결과

## 의의 및 한계

## 관련 연구

## 결론
"""
    content_path = paper_dir / "content.md"
    content_path.write_text(stub, encoding="utf-8")
    info(f"content.md 생성: {content_path}")


def create_figure_reference(paper_dir: Path, slug: str) -> None:
    """figure_reference.json을 생성한다."""
    ref = {
        "slug": slug,
        "figures": [],
        "sections": [],
        "existing_refs": [],
        "total_figures": 0,
        "total_existing_refs": 0,
    }

    ref_path = paper_dir / "figure_reference.json"
    ref_path.write_text(
        json.dumps(ref, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    info(f"figure_reference.json 생성: {ref_path}")


def run_figure_scraper(slug: str) -> bool:
    """scrape_arxiv_figures.py를 호출하여 figure를 크롤링한다."""
    if not SCRAPE_SCRIPT.exists():
        warn(f"figure 크롤링 스크립트를 찾을 수 없음: {SCRAPE_SCRIPT}")
        return False

    info(f"figure 크롤링 시작: {slug}")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRAPE_SCRIPT), "--slug", slug],
            cwd=str(PIPELINE_DIR.parent),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            # 크롤링 결과에서 이미지 수 추출
            output = result.stdout
            count_match = re.search(r'총 (\d+)개 이미지 다운로드', output)
            if count_match:
                info(f"figure 크롤링 완료: {count_match.group(1)}개 이미지")
            else:
                info("figure 크롤링 완료")
            return True
        else:
            # 에러 출력
            stderr = result.stderr.strip()
            if stderr:
                warn(f"figure 크롤링 경고: {stderr[:200]}")
            # stdout에서도 에러 메시지 확인
            stdout = result.stdout.strip()
            if "WARN" in stdout or "ERROR" in stdout:
                # arXiv URL을 찾지 못하는 것은 새 논문이라 정상
                warn("figure 크롤링에서 경고 발생 (새 논문이면 정상)")
            return False
    except subprocess.TimeoutExpired:
        warn("figure 크롤링 타임아웃 (120초)")
        return False
    except Exception as e:
        warn(f"figure 크롤링 실행 실패: {e}")
        return False


# ── 메인 처리 ──────────────────────────────────────────────────────────
def process_paper(
    url: str,
    override_category: Optional[str] = None,
) -> dict:
    """단일 논문 URL을 처리한다.

    Returns:
        {"slug": str, "status": str, "title": str, "dir": str}
    """
    result = {"url": url, "slug": "", "status": "pending", "title": "", "dir": ""}

    # 1. arXiv ID 추출
    arxiv_id = extract_arxiv_id(url)
    if not arxiv_id:
        error(f"유효하지 않은 arXiv URL: {url}")
        result["status"] = "invalid_url"
        return result

    info(f"arXiv ID: {arxiv_id}")

    # 2. arXiv ID로 기존 논문 확인
    existing = find_existing_by_arxiv_id(arxiv_id)
    if existing:
        warn(f"이미 존재하는 논문: {existing.name}")
        result["status"] = "already_exists"
        result["dir"] = str(existing)
        # slug 확인
        content_path = existing / "content.json"
        if content_path.exists():
            try:
                data = json.loads(content_path.read_text(encoding="utf-8"))
                result["slug"] = data.get("slug", existing.name)
                result["title"] = data.get("title", "")
            except (json.JSONDecodeError, OSError):
                result["slug"] = existing.name
        return result

    # 3. arXiv API로 메타데이터 가져오기
    info("arXiv API에서 메타데이터 가져오는 중...")
    metadata = fetch_arxiv_metadata(arxiv_id)
    if not metadata:
        result["status"] = "api_error"
        return result

    title = metadata["title"]
    info(f"제목: {title}")
    info(f"저자: {metadata['authors']}")
    info(f"연도: {metadata['year']}")
    info(f"카테고리: {', '.join(metadata['categories'])}")

    # 4. Slug 생성
    slug = generate_slug(title)
    result["slug"] = slug
    result["title"] = title
    info(f"Slug: {slug}")

    # 5. Slug로 기존 디렉토리 확인
    existing = find_existing_paper(slug)
    if existing:
        warn(f"이미 존재하는 디렉토리: {existing.name}")
        result["status"] = "already_exists"
        result["dir"] = str(existing)
        return result

    # 6. 카테고리 매핑
    category, sub_category = map_category(metadata["categories"], override_category)
    info(f"카테고리: {category}" + (f" / {sub_category}" if sub_category else ""))

    # 7. 태그 생성
    tags = generate_tags(metadata["categories"], title)
    if tags:
        info(f"태그: {', '.join(tags)}")

    # 8. 디렉토리 생성
    paper_dir = PAPERS_DIR / slug
    paper_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = paper_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    result["dir"] = str(paper_dir)
    info(f"디렉토리 생성: {paper_dir}")

    # 9. 파일 생성
    create_content_json(paper_dir, metadata, slug, category, sub_category, tags)
    create_figure_reference(paper_dir, slug)

    # 10. Figure 크롤링
    run_figure_scraper(slug)

    # 11. content.md 생성 (figure 크롤링 후)
    create_content_md(paper_dir)

    result["status"] = "created"
    return result


def process_urls(
    urls: list[str],
    override_category: Optional[str] = None,
) -> list[dict]:
    """여러 URL을 순차 처리한다."""
    results = []
    total = len(urls)

    for idx, url in enumerate(urls, 1):
        url = url.strip()
        if not url or url.startswith("#"):
            continue

        header(f"[{idx}/{total}] 논문 추가")
        print(f"  URL: {url}")

        result = process_paper(url, override_category)
        results.append(result)

        # arXiv API 속도 제한
        if idx < total:
            remaining_urls = [u.strip() for u in urls[idx:] if u.strip() and not u.strip().startswith("#")]
            if remaining_urls:
                print(f"\n{Color.DIM}  (arXiv 속도 제한 대기: {RATE_LIMIT}초){Color.RESET}")
                time.sleep(RATE_LIMIT)

    return results


# ── 결과 요약 ──────────────────────────────────────────────────────────
def print_summary(results: list[dict]) -> None:
    """처리 결과를 요약 출력한다."""
    header("처리 결과 요약")

    created = [r for r in results if r["status"] == "created"]
    skipped = [r for r in results if r["status"] == "already_exists"]
    failed = [r for r in results if r["status"] not in ("created", "already_exists")]

    print(f"  전체: {len(results)}건")
    print(f"  {Color.GREEN}생성: {len(created)}건{Color.RESET}")
    if skipped:
        print(f"  {Color.YELLOW}건너뜀 (이미 존재): {len(skipped)}건{Color.RESET}")
    if failed:
        print(f"  {Color.RED}실패: {len(failed)}건{Color.RESET}")

    if created:
        print(f"\n  {Color.GREEN}생성된 논문:{Color.RESET}")
        for r in created:
            print(f"    - {r['slug']}: {r['title']}")
            print(f"      {Color.DIM}{r['dir']}{Color.RESET}")

    if skipped:
        print(f"\n  {Color.YELLOW}건너뛴 논문:{Color.RESET}")
        for r in skipped:
            slug = r.get("slug") or r.get("url", "")
            print(f"    - {slug}")

    if failed:
        print(f"\n  {Color.RED}실패한 논문:{Color.RESET}")
        for r in failed:
            print(f"    - {r['url']}: {r['status']}")


# ── CLI 엔트리포인트 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="arXiv URL로 논문 디렉토리를 자동 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python pipeline/add_paper.py --url https://arxiv.org/abs/2512.08296
  python pipeline/add_paper.py --url https://arxiv.org/abs/2512.08296 --category agent
  python pipeline/add_paper.py --urls-file papers.txt
        """,
    )

    # URL 소스 (상호 배타적)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--url",
        type=str,
        help="단일 arXiv URL (abs 또는 pdf)",
    )
    source.add_argument(
        "--urls-file",
        type=str,
        help="URL 목록 파일 경로 (한 줄에 하나, #으로 주석)",
    )

    # 옵션
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="카테고리 수동 지정 (llm, vision, agent, technique 등). 미지정 시 arXiv 카테고리에서 자동 매핑",
    )

    args = parser.parse_args()

    header("논문 추가 스크립트")

    # URL 목록 준비
    if args.url:
        urls = [args.url]
    else:
        urls_file = Path(args.urls_file)
        if not urls_file.exists():
            error(f"파일을 찾을 수 없음: {args.urls_file}")
            sys.exit(1)
        urls = urls_file.read_text(encoding="utf-8").strip().splitlines()
        valid_urls = [u.strip() for u in urls if u.strip() and not u.strip().startswith("#")]
        info(f"파일에서 {len(valid_urls)}개 URL 로드: {args.urls_file}")

    # PAPERS_DIR 존재 확인
    if not PAPERS_DIR.exists():
        PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        info(f"디렉토리 생성: {PAPERS_DIR}")

    # 처리
    results = process_urls(urls, args.category)

    # 요약
    if results:
        print_summary(results)


if __name__ == "__main__":
    main()
