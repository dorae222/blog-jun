"""
Scan Notion HTML exports and build catalog.json for blog processing.
Handles two source directories:
  - 디렉토리1 (개인 페이지 & 공유된 페이지): 포트폴리오/프로젝트 (21 HTML)
  - 디렉토리2 (개인 페이지 & 공유된 페이지 2): 지식베이스 (113 HTML)
"""
import json
import re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

# 두 Notion HTML 내보내기 디렉토리
DOWNLOADS = Path("/Users/dorae222/Downloads")
SOURCE_DIRS = [
    DOWNLOADS / "개인 페이지 & 공유된 페이지",   # dir1: 포트폴리오
    DOWNLOADS / "개인 페이지 & 공유된 페이지 2",  # dir2: 지식베이스
]
OUTPUT_FILE = Path(__file__).parent / "data" / "catalog.json"

# 32자 hex page ID 패턴 (Notion 내보내기 파일명 끝에 붙는 UUID)
RE_PAGE_ID = re.compile(r'\s+[0-9a-f]{32}$')

# 스킵 대상: 인덱스 페이지 (하위 링크만 있는 페이지)
SKIP_TITLES = {
    "[My Page]", "포트폴리오", "[ML & DL]", "[ Deep Learning ]",
    "[ Machine Learning ]", "[Big Data Solution]", "[Front+Back]",
    "[Etc]", "[ Certificate ]", "Paper Review",
    "[ TimeSeries Analysis ]", "Statistical Analysis",
}

# Certificate 카테고리 전체 제외
SKIP_PATHS = {"[ Certificate ]"}

# 부모 카테고리 매핑
PARENT_CATEGORY_MAP = {
    "20.AI":      ("AI/ML",            "🤖", "#FF6F00"),
    "30.Data":    ("Data Engineering",  "📊", "#336791"),
    "40.DEV":     ("Development",       "💻", "#3776AB"),
    "60.Project": ("Projects",          "🚀", "#059669"),
}

# Notion 폴더(경로) → (parent_code, subcategory_name)
# 폴더 경로의 각 부분을 매칭
FOLDER_CATEGORY_MAP = {
    # dir1: 포트폴리오 하위 (폴더)
    "교외 AI 프로젝트":         ("60.Project", "AI Projects"),
    "비즈니스 관련 교내 프로젝트": ("60.Project", "Business Projects"),
    "Related With Data":       ("60.Project", "Data Projects"),
    # dir2: [ML & DL] 하위 (폴더)
    "[ Deep Learning ]":       ("20.AI", "Deep Learning"),
    "Paper Review":            ("20.AI", "Paper Review"),
    # dir2: [Front+Back] 하위 (폴더)
    "Servlet & JSP":           ("40.DEV", "Backend"),
    "[MongoDB]":               ("40.DEV", "Database"),
    # dir2: 학기/방학 (폴더)
    "2023_summer":             ("60.Project", "2023 Summer"),
    "2023_6th semester":       ("60.Project", "2023 Semester"),
}

# 컨테이너 폴더 → parent_code (하위 페이지의 기본 카테고리)
CONTAINER_FOLDER_MAP = {
    "[Big Data Solution]": "30.Data",
    "[Front+Back]":        "40.DEV",
    "[Etc]":               "40.DEV",
    "[ML & DL]":           "20.AI",
    "포트폴리오":           "60.Project",
}

# 페이지 제목 → (parent_code, subcategory_name)
# 폴더 매칭 실패 시 제목으로 매칭
TITLE_CATEGORY_MAP = {
    # [Big Data Solution] 하위 페이지
    "[Hadoop]":                ("30.Data", "Hadoop"),
    "[Spark]":                 ("30.Data", "Spark"),
    "[HIVE]":                  ("30.Data", "Hive"),
    "[Pig]":                   ("30.Data", "Pig"),
    "[SQOOP]":                 ("30.Data", "SQOOP"),
    "[Setting]":               ("30.Data", "Setting"),
    "[What is Big Data ]":     ("30.Data", "Big Data Intro"),
    "[하둡완전분산모드]":         ("30.Data", "Hadoop"),
    "Error":                   ("30.Data", "Troubleshooting"),
    "[빅데이터 수집 및 시각화]":  ("30.Data", "Data Visualization"),
    # [Front+Back] 하위 페이지
    "Django":                  ("40.DEV", "Backend"),
    "Django 기초":              ("40.DEV", "Backend"),
    "Cookie↔Token & Session↔JWT": ("40.DEV", "Backend"),
    # [Etc] 하위 페이지
    "LINUX_UBUNTU":            ("40.DEV", "Linux"),
    "Git":                     ("40.DEV", "Git"),
    "Figma":                   ("40.DEV", "Design"),
}


def clean_title(filename: str) -> str:
    """파일명에서 32자 hex page ID 제거 → 깨끗한 제목."""
    stem = Path(filename).stem
    return RE_PAGE_ID.sub('', stem).strip()


def get_quality_grade(body_len: int) -> str:
    """본문 길이 기반 품질 등급."""
    if body_len < 200:
        return "SKIP"
    if body_len < 1000:
        return "C"
    if body_len < 5000:
        return "B"
    return "A"


def resolve_category(rel_parts: list[str], title: str, source_idx: int) -> tuple[str, str, str]:
    """폴더 경로 + 제목에서 카테고리 결정.

    매칭 우선순위: 하위 폴더 > 페이지 제목 > 컨테이너 폴더 > 기본값
    Returns: (parent_code, category_name, subcategory)
    """
    # 1. 하위 폴더 매칭 (가장 구체적)
    for part in rel_parts:
        if part in FOLDER_CATEGORY_MAP:
            parent_code, subcat = FOLDER_CATEGORY_MAP[part]
            cat_info = PARENT_CATEGORY_MAP.get(parent_code, ("Uncategorized", "📁", "#6B7280"))
            return parent_code, cat_info[0], subcat

    # 2. 페이지 제목 매칭 (Big Data Solution, Front+Back 직속 자식 등)
    if title in TITLE_CATEGORY_MAP:
        parent_code, subcat = TITLE_CATEGORY_MAP[title]
        cat_info = PARENT_CATEGORY_MAP.get(parent_code, ("Uncategorized", "📁", "#6B7280"))
        return parent_code, cat_info[0], subcat

    # 3. 컨테이너 폴더 매칭 (부모 카테고리만 결정)
    for part in rel_parts:
        if part in CONTAINER_FOLDER_MAP:
            parent_code = CONTAINER_FOLDER_MAP[part]
            cat_info = PARENT_CATEGORY_MAP.get(parent_code, ("Uncategorized", "📁", "#6B7280"))
            return parent_code, cat_info[0], "General"

    # 4. dir1 최상위는 프로젝트
    if source_idx == 0:
        return "60.Project", "Projects", "General"

    # 5. dir2 기본값
    return "40.DEV", "Development", "General"


def extract_properties(soup: BeautifulSoup) -> dict:
    """디렉토리1 HTML에서 properties 테이블 추출."""
    props = {}
    table = soup.find('table', class_='properties')
    if not table:
        return props

    for row in table.find_all('tr', class_='property-row'):
        th = row.find('th')
        td = row.find('td')
        if not th or not td:
            continue

        key = th.get_text(strip=True)
        # 아이콘 이미지 텍스트 제거
        for img in th.find_all('img'):
            img.decompose()
        key = th.get_text(strip=True)

        # multi_select: 여러 값
        if 'property-row-multi_select' in row.get('class', []):
            values = [span.get_text(strip=True) for span in td.find_all('span', class_='selected-value')]
            props[key] = values
        else:
            props[key] = td.get_text(strip=True)

    return props


def scan_content_flags(soup: BeautifulSoup) -> dict:
    """HTML에서 콘텐츠 특성 플래그 빠르게 감지."""
    body = soup.find('div', class_='page-body')
    if not body:
        return {}

    html_str = str(body)
    return {
        "has_code": bool(body.find('pre', class_='code')),
        "has_images": bool(body.find('figure', class_='image')),
        "has_tables": bool(body.find('table') and not body.find('table', class_='properties')),
        "has_latex": 'katex' in html_str or 'annotation' in html_str,
        "has_callout": bool(body.find('figure', class_=lambda c: c and 'callout' in c)),
        "has_toggle": bool(body.find('details')),
        "has_bookmark": bool(body.find('figure', class_='bookmark')),
        "has_columns": bool(body.find('div', class_='column-list')),
    }


def should_skip(title: str, rel_parts: list[str]) -> bool:
    """스킵 대상 판단."""
    if title in SKIP_TITLES:
        return True
    for part in rel_parts:
        if part in SKIP_PATHS:
            return True
    return False


def scan_html_files():
    """두 디렉토리의 HTML 파일을 스캔하여 카탈로그 생성."""
    catalog = []

    for src_idx, src_dir in enumerate(SOURCE_DIRS):
        if not src_dir.exists():
            print(f"⚠️  디렉토리 없음: {src_dir}")
            continue

        for html_file in sorted(src_dir.rglob("*.html")):
            rel_path = html_file.relative_to(src_dir)
            rel_parts = list(rel_path.parts[:-1])  # 폴더 부분만

            title = clean_title(html_file.name)

            # 스킵 판단
            if should_skip(title, rel_parts):
                continue

            # HTML 파싱
            try:
                content = html_file.read_text(encoding='utf-8')
                soup = BeautifulSoup(content, 'html.parser')
            except Exception as e:
                print(f"⚠️  파싱 실패: {html_file.name}: {e}")
                continue

            # page-title에서 제목 추출 (파일명보다 우선)
            page_title = soup.find('h1', class_='page-title')
            if page_title:
                title = page_title.get_text(strip=True)

            # page-body 길이 측정
            body = soup.find('div', class_='page-body')
            body_text = body.get_text(strip=True) if body else ""
            body_len = len(body_text)

            # 품질 등급
            quality = get_quality_grade(body_len)
            if quality == "SKIP":
                continue

            # 카테고리 결정
            parent_code, category_name, subcategory = resolve_category(rel_parts, title, src_idx)

            # 콘텐츠 플래그
            flags = scan_content_flags(soup)

            # properties 메타데이터 (dir1만)
            properties = extract_properties(soup) if src_idx == 0 else {}

            # 이미지 참조 수집
            image_refs = []
            if body:
                for fig in body.find_all('figure', class_='image'):
                    img = fig.find('img')
                    if img and img.get('src'):
                        image_refs.append({
                            "type": "external" if img['src'].startswith('http') else "local",
                            "ref": img['src'],
                        })

            entry = {
                "path": str(rel_path),
                "html_path": str(html_file),
                "source_dir": src_idx,  # 0=포트폴리오, 1=지식베이스
                "title": title,
                "parent_code": parent_code,
                "category_name": category_name,
                "subcategory": subcategory,
                "body_chars": body_len,
                "quality": quality,
                "large": body_len > 50000,
                **flags,
                "properties": properties,
                "image_refs": image_refs,
                "image_count": len(image_refs),
            }

            catalog.append(entry)

    return catalog


def print_stats(catalog: list[dict]):
    """카탈로그 통계 출력."""
    total = len(catalog)
    print(f"\n=== HTML Scan Results ===")
    print(f"Total entries: {total}")

    # 소스 디렉토리별
    for idx in [0, 1]:
        count = sum(1 for e in catalog if e["source_dir"] == idx)
        label = "포트폴리오" if idx == 0 else "지식베이스"
        print(f"  dir{idx+1} ({label}): {count}")

    # 품질 분포
    grade_dist = Counter(e["quality"] for e in catalog)
    print(f"\nQuality distribution:")
    for grade in ["A", "B", "C"]:
        print(f"  {grade}: {grade_dist.get(grade, 0)}")

    # 카테고리 분포
    print(f"\nCategory distribution:")
    cat_dist = Counter(e["category_name"] for e in catalog)
    for cat, count in cat_dist.most_common():
        print(f"  {cat}: {count}")

    # 서브카테고리 분포
    print(f"\nSubcategory distribution:")
    sub_dist = Counter(e["subcategory"] for e in catalog)
    for sub, count in sub_dist.most_common(15):
        print(f"  {sub}: {count}")

    # 콘텐츠 플래그
    print(f"\nContent flags:")
    for flag in ["has_code", "has_images", "has_tables", "has_latex",
                 "has_callout", "has_toggle", "has_bookmark", "has_columns"]:
        count = sum(1 for e in catalog if e.get(flag, False))
        print(f"  {flag}: {count}")

    # 이미지 통계
    total_imgs = sum(e["image_count"] for e in catalog)
    print(f"\nTotal image references: {total_imgs}")

    # Properties 통계
    with_props = sum(1 for e in catalog if e.get("properties"))
    print(f"Entries with properties: {with_props}")


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    catalog = scan_html_files()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print_stats(catalog)
    print(f"\nCatalog saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
