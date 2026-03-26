"""
published 전체 포스트 → gpt-5-mini Batch API 재처리 JSONL 준비.

주요 기능:
- 모델: text_only → gpt-5-mini, heavy_multimodal → gpt-4.1-mini
- 입력: DB content + 원본 Notion/Obsidian .md (SOURCE_MAP + vault fallback)
- 전처리: preprocessor.preprocess_content() 재사용
- 프롬프트: 1인칭 경험 기록 + bullet 구조 유지 + XML 마커 + 출력 금지 규칙
- pre-filter: should_skip_pre() — stub/과제 제거, 기술 주제 키워드 예외
- 멀티모달: --multimodal 시 이미지 base64 + PDF 페이지 이미지 포함, tier별 JSONL 분할
- MAX_CONTENT_CHARS=50000 (gpt-5-mini 400K context 기준)

실행:
    python pipeline/batch_fixstyle.py
    python pipeline/batch_fixstyle.py --sample pipeline/data/sample_posts.json
    python pipeline/batch_fixstyle.py --post-ids 1415,1485
    python pipeline/batch_fixstyle.py --multimodal --output pipeline/data/fixstyle_input.jsonl
"""
import argparse
import base64
import io
import json
import re
import sys
import os
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from blog.models import Post

# preprocessor 임포트 (이미지 전처리 재사용)
PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))
from preprocessor import preprocess_content

DATA_DIR = Path(__file__).parent / "data"
FIXSTYLE_INPUT_FILE = DATA_DIR / "fixstyle_input.jsonl"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"

BLOG_BASE = "https://blog.dorae222.com"
MAX_CONTENT_CHARS = 50000   # gpt-5-mini 400K context 기준 충분히 여유
MAX_SOURCE_CHARS  = 12000   # 원본 노션 파일 (입력)
MAX_PDF_CHARS     = 3000
MAX_IMAGES        = 4

# vault/로컬 경로 (서버에서 마운트되지 않으면 스킵)
VAULT_DIR = Path(os.environ.get("VAULT_DIR", "/Users/dorae222/Documents/Obsidian/hyeongjun"))
PDF_DIR   = VAULT_DIR / "90.Settings" / "94.Project-Attachments"

# ──────────────────────────────────────────────
# 소스 파일 경로 매핑 (source_path prefix → 로컬 디렉토리)
# ──────────────────────────────────────────────
SOURCE_MAP = {
    # 긴 prefix 먼저 (longest-match)
    "20.AI/23.Deep Learning":  Path("/Users/dorae222/Downloads/my page/[My Page]/[ML & DL]/[ Deep Learning ]"),
    "20.AI/28.Paper Review":   Path("/Users/dorae222/Downloads/my page/[My Page]/[ML & DL]/ Paper Review "),
    # Obsidian vault 기반 경로 (Downloads에 없는 하위폴더)
    "20.AI/21. Math":          VAULT_DIR / "20.AI/21. Math & Statistics",
    "20.AI/22. ML":            VAULT_DIR / "20.AI/22. ML",
    "20.AI/24. NLP":           VAULT_DIR / "20.AI/24. NLP",
    "20.AI/25. Vision":        VAULT_DIR / "20.AI/25. Vision",
    "20.AI/26. Multimodal":    VAULT_DIR / "20.AI/26. Multimodal",
    "20.AI/27. MFU":           VAULT_DIR / "20.AI/27. MFU",
    "20.AI/29.LLM":            VAULT_DIR / "20.AI/29.LLM & GenAI",
    "40.DEV/42.Git":           Path("/Users/dorae222/Downloads/my page/[My Page]/[Etc]/Git"),
    "40.DEV/43.Linux":         Path("/Users/dorae222/Downloads/my page/[My Page]/[Etc]/LINUX_UBUNTU"),
    "40.DEV/42.Frontend":      VAULT_DIR / "40.DEV/42.Frontend",
    "40.DEV/41.Backend":       Path("/Users/dorae222/Downloads/my page/[My Page]/[Front+Back]"),
    "40.DEV":                  Path("/Users/dorae222/Downloads/my page/[My Page]/[Front+Back]"),
    "33.Database":             Path("/Users/dorae222/Downloads/my page/[My Page]/[Front+Back]/[MongoDB]"),
    "30.Data/31.Hadoop":       VAULT_DIR / "30.Data/31.Hadoop",
    "30.Data/32.Spark":        VAULT_DIR / "30.Data/32.Spark",
    "30.Data/33.Database":     VAULT_DIR / "30.Data/33.Database",
    "30.Data/34.Data Pipeline": VAULT_DIR / "30.Data/34.Data Pipeline",
    "30.Data":                 Path("/Users/dorae222/Downloads/my page/[My Page]/[Big Data Solution]"),
    "60.Project":              Path("/Users/dorae222/Downloads/portfolio notion export/포트폴리오/교외 AI 프로젝트"),
    "10.Cloud":                VAULT_DIR / "10.Cloud",
    "20.AI":                   Path("/Users/dorae222/Downloads/my page/[My Page]/[ML & DL]"),
}

# prefix를 긴 것 먼저 정렬 (dict insertion order는 Python 3.7+에서 보장되나, 명시적 정렬)
_SORTED_SOURCE_MAP = sorted(SOURCE_MAP.items(), key=lambda x: len(x[0]), reverse=True)

# ──────────────────────────────────────────────
# image_map 로드
# ──────────────────────────────────────────────
def _load_ref_map() -> dict:
    if IMAGE_MAP_FILE.exists():
        with open(IMAGE_MAP_FILE) as f:
            d = json.load(f)
        return d.get("ref_map", {})
    return {}

_REF_MAP = _load_ref_map()

# ──────────────────────────────────────────────
# JSON 스키마
# ──────────────────────────────────────────────
REWRITE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "blog_rewrite",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title":          {"type": "string"},
                "content":        {"type": "string"},
                "summary":        {"type": "string"},
                "tags":           {"type": "array", "items": {"type": "string"}},
                "quality_score":  {"type": "number"},
                "should_archive": {"type": "boolean"},
                "archive_reason": {"type": "string"},
            },
            "required": [
                "title", "content", "summary", "tags",
                "quality_score", "should_archive", "archive_reason",
            ],
            "additionalProperties": False,
        },
    },
}

# ──────────────────────────────────────────────
# 시스템 프롬프트 (전면 재작성)
# ──────────────────────────────────────────────
BASE_RULES = """당신은 도형준(DO HyeongJun)이라는 AI/ML 엔지니어가 직접 공부하며 작성한 노트를
블로그 포스트로 정제합니다.

[렌더링 환경]
- Markdown: ReactMarkdown + remark-gfm
- 수식: remark-math + rehype-katex (KaTeX)  → 인라인 $...$, 블록 $$...$$
- 코드: rehype-highlight  → fenced block + 언어 지정 필수
- 절대 금지: \\(...\\), \\[...\\], \\begin{equation}

[구조 규칙 — 가장 중요]
- 원본의 bullet list 구조를 반드시 유지. 산문체(paragraph)로 전환 금지.
- 원본이 2-4단계 들여쓰기면 출력도 동일 구조 유지.
- bullet을 "이어 설명하면..."식 prose로 병합하지 말 것.
- 섹션 제목(##, ###)은 원본 구조에 따라 추가 가능하되 과도하게 추가 금지.

[말투 — 1인칭 경험 기록]
- 핵심: "내가 공부하면서 직접 경험한 것을 기록한 느낌"
- 권장: "해보니까", "처음엔 몰랐는데", "결론부터 말하면", "이 부분에서 막혔는데"
- 금지(절대): "이를 통해 알 수 있습니다", "살펴보도록 하겠습니다",
              "이번 포스팅에서는", "위에서 살펴본 바와 같이",
              "주목할 만합니다", "이해할 수 있습니다"
- 경어체 (~합니다/~입니다) 유지하되 교과서 투 제거.
- 이모지 금지.

[내용 보존 — 절대 원칙]
- 원본(소스 마크다운)의 모든 항목을 빠짐없이 포함.
- 요약/압축 금지. 단, 명백한 중복·반복은 제거 가능.
- 코드 블록: 절대 수정 금지. 언어 태그 없으면 추가만 허용.
- LaTeX 수식: 원본 수식 표기 유지. 단, \\(...\\) → $...$로 포맷 변환.
- 이미지 placeholder [이미지: ...]: 그대로 유지.
- GitHub/외부 링크: 그대로 유지.

[내용 충실도 — 최우선 원칙]
- 소스 파일에 있는 내용만 사용할 것. 소스에 없는 새 섹션, 개념, 설명 추가 절대 금지.
- AI의 일반 지식으로 내용을 "보강"하지 말 것.
- 단, 소스 내용이 200자 미만인 기술 주제(도구/개념 이름이 제목에 있음) → 해당 주제로 블로그 포스트 작성.
  이 경우 1인칭 경험 기록 형식 유지, 공부하며 정리한 느낌으로 작성.

[아카이브 판정 should_archive = true]
- 과제/시험 문제/회의록임이 명확한 경우 (제목 또는 내용에서 분명히 드러남).
- 기술적 내용이 전혀 없이 링크·TODO·일정만 나열.
- 개인 메모/초안 수준으로 블로그로서 가치 없음.

[아카이브 금지 — 내용 부족해도 기술 주제면 생성]
- 기술 도구/개념 이름이 제목/소스 경로에 있으면 → 해당 주제로 블로그 포스트 작성.
- 예: "[HIVE]" → Apache Hive에 대한 기술 블로그 포스트 생성.
- 작성 시 1인칭 경험 기록 형식 유지.
- 경험이 없는 내용에 대해 "직접 해보니까..." 같은 거짓 경험담 작성 금지.

[출력 금지 — 반드시 준수]
- 출력 content 필드에 입력 마커 포함 절대 금지:
  <INPUT_DRAFT>, </INPUT_DRAFT>, <SOURCE_ORIGINAL>, </SOURCE_ORIGINAL>, <PDF_REFERENCE>, </PDF_REFERENCE>
- "[... content truncated ...]", "[내용 잘림]", "원본이 제한됨" 등 시스템 메타 텍스트 금지.
- 입력 구조 설명, 처리 과정 주석, 시스템 노트 일체 금지.
- 출력은 순수 마크다운 블로그 포스트 내용만 포함할 것.

quality_score: 0-10 (개선 후 기준)"""

PROMPTS = {
    "tutorial": BASE_RULES + """

[포스트 타입: Tutorial]
- 구성: 핵심 개념 → 설치/설정 → 실전 코드 → 주의사항 (이 순서 권장)
- 코드 예제는 모두 보존. 언어 태그 추가만 허용.
- "» 기호"로 표시된 항목 → "-" 변환.
- 단계별 bullet은 numbered list로 변환 가능.

[출력 예시 — 올바른 형태]
## JSP 기본 구조

- JSP는 HTML에 Java 코드를 삽입하는 방식입니다.
  - Servlet보다 뷰 레이어 작업이 훨씬 편했습니다.
  - `<% %>` 스크립틀릿, `<%= %>` 표현식, `<%! %>` 선언부로 구분됩니다.

```java
<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<html>
<body>
  <% int count = 0; %>
  <%= count %>
</body>
</html>
```

직접 써보니까 Servlet에서 response.getWriter()로 HTML 출력하던 것보다
JSP 쪽이 훨씬 가독성이 좋았습니다.""",

    "article": BASE_RULES + """

[포스트 타입: Article]
- 개념 설명 중심. bullet 구조 유지하면서 섹션별 핵심 설명 추가.
- 수식 있으면 반드시 KaTeX 포맷으로 보존.
- "처음 배울 때 이 개념이 왜 필요한지..." 형태로 동기 부여 문장 1-2개 추가 가능.

[출력 예시]
## Backpropagation 핵심 개념

- 손실 함수의 미분값을 역방향으로 전파해 가중치를 업데이트합니다.
  - Chain rule: $\\frac{\\partial L}{\\partial w} = \\frac{\\partial L}{\\partial o} \\cdot \\frac{\\partial o}{\\partial w}$
  - 처음엔 왜 역방향으로 계산하는지 직관이 안 왔는데, 계산 그래프 그려보니까 바로 이해됐습니다.
- Learning rate가 너무 크면 발산, 너무 작으면 수렴이 느립니다.
  - 실험해보니 0.001 근처가 대부분의 경우 안정적이었습니다.""",

    "til": BASE_RULES + """

[포스트 타입: TIL (Today I Learned)]
- 짧게, 핵심만. 오늘 배운 것 1-2개. 500-1000자 이내 권장.
- "오늘 알게 된 것은..." 같은 도입부 제거하고 바로 내용으로.
- bullet 구조 그대로 유지.""",

    "paper_review": BASE_RULES + """

[포스트 타입: Paper Review]
- 구성: ## 논문 정보 → ## 핵심 아이디어 → ## 방법론 → ## 실험 결과 → ## 개인 의견
- 수식: 논문 원본 LaTeX 그대로. 필요하면 KaTeX 포맷으로만 변환.
- Notion aside 박스 내용 → ## 들어가며 또는 ## 개인 의견 섹션으로 통합.
- arXiv 링크, 논문 제목 보존.

[출력 예시]
## 핵심 아이디어

GAN은 Generator와 Discriminator가 서로 경쟁하면서 학습합니다.

- Generator $G$: 노이즈 $z$로부터 가짜 데이터 생성
  - $G(z;\\theta_g)$: $\\theta_g$는 Generator 파라미터
- Discriminator $D$: 진짜/가짜를 구별
  - $D(x;\\theta_d)$: 출력이 1이면 진짜, 0이면 가짜 판정

$$\\min_G \\max_D V(D,G) = \\mathbb{E}_{x\\sim p_{data}}[\\log D(x)] + \\mathbb{E}_{z\\sim p_z}[\\log(1-D(G(z)))]$$

이 minimax 게임이 내시 균형에 수렴하면 $G$가 실제 데이터 분포를 완벽히 모방합니다.
읽으면서 이 수식이 의외로 직관적이라는 걸 알았습니다.""",

    "project": BASE_RULES + """

[포스트 타입: Project]
- 내용이 링크·파일명·수상 기록 위주인 경우: 해당 정보를 그대로 유지. 없는 내용 추가 금지.
- PDF 첨부 언급은 content에서 제거 (PDFViewer가 별도 표시).
- 수상/결과 정보: 원본 그대로 유지. 과장하지 말 것.
- should_archive = false (프로젝트 기록은 내용 빈약해도 보존).""",
}

# ──────────────────────────────────────────────
# 콘텐츠 사전 필터링 (배치 전 제거)
# ──────────────────────────────────────────────
ARCHIVE_PATTERNS = [
    r"과제|assignment|homework|report|제출|발표자료",
    r"회의록|미팅|meeting|agenda|회고록",
    r"(?:^|/)메모|(?:^|/)memo|TODO|일정계획",
    r"\d{4}_\d{2}\d{2}",
]

CONTENT_SKIP_PATTERNS = [
    r"^문제\s*\d+",
    r"^\s*Q\d+\.",
    r"제출\s*(기한|일시)",
    r"(출석|결석)\s*확인",
]

# 기술 주제 키워드 — 이 패턴이 제목/경로에 있으면 내용 부족해도 배치에 포함
TECHNICAL_TITLE_PATTERNS = [
    r'\b(hive|hadoop|spark|kafka|docker|kubernetes|aws|gcp|git|sql|python|java|linux)\b',
    r'\b(deep.?learning|machine.?learning|nlp|cv|bert|gpt|transformer|neural)\b',
    r'\b(algorithm|data.?structure|network|api|rest|graphql|react|django)\b',
    r'\b(cnn|rnn|lstm|gan|vae|attention|embedding|classification|regression)\b',
    r'\b(mongodb|postgresql|redis|elasticsearch|airflow|jenkins|terraform)\b',
]


def should_skip_pre(post) -> bool:
    """True면 배치 제외 + archived 처리."""
    content = post.content or ""
    title = post.title or ""
    source = post.source_path or ""

    # 기술 키워드가 있으면 내용 부족해도 배치에 포함 (AI가 생성)
    combined = f"{title} {source}".lower()
    if any(re.search(p, combined, re.I) for p in TECHNICAL_TITLE_PATTERNS):
        return False

    if len(content) < 200:
        return True

    if any(re.search(p, source, re.I) for p in ARCHIVE_PATTERNS):
        return True

    snippet = content[:500]
    if any(re.search(p, snippet, re.M) for p in CONTENT_SKIP_PATTERNS):
        return True

    return False


# ──────────────────────────────────────────────
# 소스 파일 탐색 + 전처리
# ──────────────────────────────────────────────
def find_and_preprocess_source(source_path: str) -> str:
    """source_path → 전처리된 원본 마크다운 반환 (API 입력용).

    1. SOURCE_MAP에서 prefix 매칭 (긴 것 우선)
    2. rglob으로 파일명 매칭
    3. preprocessor.preprocess_content() 적용
    4. 미변환 로컬 이미지 참조 → [이미지: alt] placeholder
    5. MAX_SOURCE_CHARS 자름
    """
    if not source_path:
        return ""

    stem = Path(source_path).stem

    for prefix, base_dir in _SORTED_SOURCE_MAP:
        if not source_path.startswith(prefix):
            continue
        if not base_dir.exists():
            continue

        # 파일명 일치 탐색 (stem 기반, 대소문자 무시)
        stem_lower = stem.lower()
        for md_file in base_dir.rglob("*.md"):
            if md_file.stem.lower() == stem_lower or md_file.stem.lower().startswith(stem_lower):
                try:
                    raw = md_file.read_text(encoding="utf-8", errors="ignore")
                    processed, _ = preprocess_content(raw, source_path, _REF_MAP)
                    # 아직 남은 로컬 이미지 참조 → placeholder
                    processed = re.sub(
                        r'!\[([^\]]*)\]\((?!(?:/media/|https?://))[^)]+\)',
                        lambda m: f'[이미지: {m.group(1) or "그림"}]',
                        processed,
                    )
                    return processed[:MAX_SOURCE_CHARS]
                except Exception:
                    return ""

    # Fallback: Obsidian vault 전체 탐색 (SOURCE_MAP에 없는 경로)
    if VAULT_DIR.exists():
        stem_lower = stem.lower()
        for md_file in VAULT_DIR.rglob("*.md"):
            if md_file.stem.lower() == stem_lower:
                try:
                    raw = md_file.read_text(encoding="utf-8", errors="ignore")
                    processed, _ = preprocess_content(raw, source_path, _REF_MAP)
                    processed = re.sub(
                        r'!\[([^\]]*)\]\((?!(?:/media/|https?://))[^)]+\)',
                        lambda m: f'[이미지: {m.group(1) or "그림"}]',
                        processed,
                    )
                    return processed[:MAX_SOURCE_CHARS]
                except Exception:
                    pass

    return ""


# ──────────────────────────────────────────────
# 이미지 로컬 경로 추출 (multimodal tier용)
# ──────────────────────────────────────────────
_IMG_PATTERN = re.compile(r"!\[.*?\]\((/media/[^\)]+)\)")

MEDIA_DIR = Path(__file__).resolve().parent.parent / "backend" / "media"


def extract_image_urls(content: str, max_images: int = MAX_IMAGES) -> list[str]:
    matches = _IMG_PATTERN.findall(content)
    return [BLOG_BASE + url for url in matches[:max_images]]


def find_local_images(content: str, max_images: int = MAX_IMAGES) -> list[Path]:
    """content에서 /media/ 이미지 URL을 추출하고 로컬 파일 경로 반환."""
    matches = _IMG_PATTERN.findall(content)
    paths = []
    for url in matches[:max_images]:
        # /media/posts/imported/... → backend/media/posts/imported/...
        local = MEDIA_DIR / url.lstrip("/media/").lstrip("/")
        if not local.exists():
            # URL decoded 버전도 시도
            from urllib.parse import unquote
            decoded_url = unquote(url)
            local = MEDIA_DIR / decoded_url.lstrip("/media/").lstrip("/")
        if local.exists():
            paths.append(local)
    return paths


# ──────────────────────────────────────────────
# 멀티모달: 이미지 리사이즈 + PDF→이미지 변환
# ──────────────────────────────────────────────
def resize_image_for_api(img_path: Path, max_kb: int = 300) -> str | None:
    """이미지를 max_kb 이하로 리사이즈 후 base64 반환. Pillow 없으면 None."""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(img_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)

        if buf.tell() > max_kb * 1024:
            img.thumbnail((768, 768), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)

        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def pdf_pages_to_images(pdf_path: Path, max_pages: int = 3) -> list[str]:
    """PDF 첫 N 페이지를 JPEG base64로 변환. pdf2image 없으면 빈 리스트."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return []

    try:
        pages = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=150)
        images_b64 = []
        for page in pages:
            buf = io.BytesIO()
            page.save(buf, format="JPEG", quality=80)
            images_b64.append(base64.b64encode(buf.getvalue()).decode())
        return images_b64
    except Exception:
        return []


# ──────────────────────────────────────────────
# 멀티모달 tier 라우팅
# ──────────────────────────────────────────────
TIER_CONFIG = {
    "text_only": {
        "model": "gpt-5-mini",
        "max_images": 0,
    },
    "light_multimodal": {
        "model": "gpt-5-mini",
        "max_images": 5,
        "max_img_kb": 300,
    },
    "heavy_multimodal": {
        "model": "gpt-4.1-mini",
        "max_images": 15,
        "max_img_kb": 300,
    },
}


def classify_tier(local_images: list[Path], has_pdf: bool) -> str:
    """포스트의 멀티모달 tier 결정."""
    if len(local_images) == 0 and not has_pdf:
        return "text_only"
    if len(local_images) <= 5 and not has_pdf:
        return "light_multimodal"
    return "heavy_multimodal"


# ──────────────────────────────────────────────
# user message 구성
# ──────────────────────────────────────────────
def build_user_message(
    content: str,
    source_content: str = "",
    pdf_text: str = "",
    images_b64: list[str] | None = None,
    pdf_b64_pages: list[str] | None = None,
    tier: str = "text_only",
) -> list[dict]:
    """텍스트 + 선택적 이미지 메시지 구성. XML 태그로 섹션 구분."""
    text_body = f"""<INPUT_DRAFT>
{content[:MAX_CONTENT_CHARS]}
</INPUT_DRAFT>

<SOURCE_ORIGINAL>
{source_content[:MAX_SOURCE_CHARS] if source_content else '(원본 파일 없음 — draft 내용 기준으로 정제)'}
</SOURCE_ORIGINAL>"""

    if pdf_text:
        text_body += f"\n\n<PDF_REFERENCE>\n{pdf_text[:MAX_PDF_CHARS]}\n</PDF_REFERENCE>"

    parts = [{"type": "text", "text": text_body}]

    # 멀티모달 tier: 이미지 base64 첨부
    if tier != "text_only" and images_b64:
        max_imgs = TIER_CONFIG[tier]["max_images"]
        for b64 in images_b64[:max_imgs]:
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
            })

    # PDF 페이지 이미지
    if pdf_b64_pages:
        for b64 in pdf_b64_pages:
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
            })

    return parts


# ──────────────────────────────────────────────
# PDF 텍스트 추출 (60.Project 전용)
# ──────────────────────────────────────────────
def extract_pdf_text(pdf_path: Path, max_chars: int = MAX_PDF_CHARS) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages[:5])
        return text[:max_chars]
    except Exception:
        return ""


def find_related_pdf(source_path: str) -> str:
    if not source_path.startswith("60.Project"):
        return ""
    if not PDF_DIR.exists():
        return ""

    title_keywords = Path(source_path).stem.lower().split()
    best_match: Path | None = None
    best_score = 0

    for pdf_path in PDF_DIR.glob("*.pdf"):
        pdf_name_lower = pdf_path.stem.lower()
        score = sum(1 for kw in title_keywords if kw in pdf_name_lower)
        if score > best_score:
            best_score = score
            best_match = pdf_path

    if best_match and best_score >= 1:
        return extract_pdf_text(best_match)
    return ""


# ──────────────────────────────────────────────
# max_completion_tokens 동적 계산
# ──────────────────────────────────────────────
def estimate_max_tokens(content_chars: int, source_chars: int = 0) -> int:
    """한국어 ~1.8 chars/token, 출력 = 입력 1.5배 + 오버헤드."""
    total_input_chars = content_chars + source_chars
    estimated = int(total_input_chars / 1.8 * 1.5) + 2048
    return max(16384, min(estimated, 32768))


# ──────────────────────────────────────────────
# 메인 준비 함수
# ──────────────────────────────────────────────
MAX_BATCH_FILE_SIZE = 95 * 1024 * 1024  # 95MB (100MB 제한에 여유)


def prepare_fixstyle(
    sample_ids: set[int] | None = None,
    output_file: Path | None = None,
    enable_multimodal: bool = False,
):
    posts = Post.objects.filter(status="published").select_related("category").only(
        "id", "title", "content", "source_path", "post_type", "category"
    )

    if sample_ids:
        posts = posts.filter(id__in=sample_ids)

    # tier별 요청 분류
    tier_requests: dict[str, list[dict]] = {
        "text_only": [],
        "light_multimodal": [],
        "heavy_multimodal": [],
    }
    stats = Counter()

    for post in posts:
        content = (post.content or "").strip()

        # pre-filter
        if should_skip_pre(post):
            post.status = "archived"
            post.save(update_fields=["status"])
            stats["pre_filtered_archived"] += 1
            continue

        # 소스 파일 탐색 + 전처리
        source_content = find_and_preprocess_source(post.source_path or "")
        if source_content:
            stats["with_source"] += 1

        # 포스트 타입별 시스템 프롬프트
        system_prompt = PROMPTS.get(post.post_type, PROMPTS["article"])

        # PDF 컨텍스트 (60.Project 계열)
        pdf_text = find_related_pdf(post.source_path or "")
        has_pdf = bool(pdf_text)
        if has_pdf:
            stats["with_pdf"] += 1

        # 멀티모달 처리
        images_b64 = []
        pdf_b64_pages = []
        tier = "text_only"

        if enable_multimodal:
            local_images = find_local_images(content)
            tier = classify_tier(local_images, has_pdf)

            if tier != "text_only":
                max_kb = TIER_CONFIG[tier].get("max_img_kb", 300)
                for img_path in local_images[:TIER_CONFIG[tier]["max_images"]]:
                    b64 = resize_image_for_api(img_path, max_kb)
                    if b64:
                        images_b64.append(b64)

            # PDF 페이지 이미지 (project 포스트)
            if has_pdf and (post.source_path or "").startswith("60.Project"):
                pdf_path = _find_pdf_file(post.source_path or "")
                if pdf_path:
                    pdf_b64_pages = pdf_pages_to_images(pdf_path)
        else:
            # 멀티모달 비활성 → 이미지 유무만 통계
            image_urls = extract_image_urls(content)
            if image_urls:
                stats["with_images"] += 1

        if images_b64:
            stats["with_images"] += 1
        stats[f"tier_{tier}"] += 1

        user_parts = build_user_message(
            content, source_content, pdf_text,
            images_b64=images_b64,
            pdf_b64_pages=pdf_b64_pages,
            tier=tier,
        )

        custom_id = post.source_path if post.source_path else f"post-{post.id}"
        model = TIER_CONFIG[tier]["model"]

        request = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_parts},
                ],
                "response_format": REWRITE_SCHEMA,
                "max_completion_tokens": estimate_max_tokens(len(content), len(source_content)),
            },
        }
        tier_requests[tier].append(request)
        stats["prepared"] += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # JSONL 파일 출력 (tier별 분할 또는 단일 파일)
    written_files = []

    if enable_multimodal:
        # tier별로 별도 JSONL 파일 생성
        for tier_name, requests in tier_requests.items():
            if not requests:
                continue
            dest = output_file or FIXSTYLE_INPUT_FILE
            tier_dest = dest.parent / f"{dest.stem}_{tier_name}{dest.suffix}"
            _write_jsonl_split(requests, tier_dest, stats)
            written_files.append((tier_name, tier_dest, len(requests)))
    else:
        # 전체 단일 파일
        all_requests = []
        for reqs in tier_requests.values():
            all_requests.extend(reqs)
        dest = output_file or FIXSTYLE_INPUT_FILE
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            for req in all_requests:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        written_files.append(("all", dest, len(all_requests)))

    # 결과 출력
    print(f"\n=== Fixstyle Batch Preparation ===")
    print(f"Prepared:        {stats['prepared']}건")
    print(f"Pre-filtered:    {stats['pre_filtered_archived']}건 (archived 처리)")
    print(f"With source md:  {stats['with_source']}건")
    print(f"With images:     {stats['with_images']}건")
    print(f"With PDF:        {stats['with_pdf']}건")

    if enable_multimodal:
        print(f"\nTier 분류:")
        for t in ["text_only", "light_multimodal", "heavy_multimodal"]:
            print(f"  {t}: {stats.get(f'tier_{t}', 0)}건")

    for tier_name, dest, count in written_files:
        if dest.exists():
            file_size = dest.stat().st_size / (1024 * 1024)
            print(f"\n[{tier_name}] {count}건 → {dest} ({file_size:.1f} MB)")

    print(f"\nNext:")
    for _, dest, _ in written_files:
        print(f"  python pipeline/batch_process.py \\")
        print(f"    --input  {dest} \\")
        print(f"    --output {dest.parent / dest.name.replace('input', 'output')}")


def _write_jsonl_split(requests: list[dict], base_path: Path, stats: Counter):
    """JSONL을 MAX_BATCH_FILE_SIZE 이하로 분할 기록."""
    base_path.parent.mkdir(parents=True, exist_ok=True)
    part = 0
    current_size = 0
    current_file = None

    for req in requests:
        line = json.dumps(req, ensure_ascii=False) + "\n"
        line_bytes = len(line.encode("utf-8"))

        if current_file is None or current_size + line_bytes > MAX_BATCH_FILE_SIZE:
            if current_file:
                current_file.close()
            part += 1
            if part == 1:
                path = base_path
            else:
                path = base_path.parent / f"{base_path.stem}_part{part}{base_path.suffix}"
            current_file = open(path, "w", encoding="utf-8")
            current_size = 0

        current_file.write(line)
        current_size += line_bytes

    if current_file:
        current_file.close()


def _find_pdf_file(source_path: str) -> Path | None:
    """60.Project 포스트에 관련된 PDF 파일 경로 반환."""
    if not source_path.startswith("60.Project"):
        return None
    if not PDF_DIR.exists():
        return None

    title_keywords = Path(source_path).stem.lower().split()
    best_match: Path | None = None
    best_score = 0

    for pdf_path in PDF_DIR.rglob("*.pdf"):
        pdf_name_lower = pdf_path.stem.lower()
        score = sum(1 for kw in title_keywords if kw in pdf_name_lower)
        if score > best_score:
            best_score = score
            best_match = pdf_path

    return best_match if best_match and best_score >= 1 else None


def main():
    parser = argparse.ArgumentParser(description="fixstyle 배치 입력 JSONL 준비")
    parser.add_argument(
        "--sample",
        type=str,
        default=None,
        help="샘플 포스트 JSON 파일 경로 (post_id 목록). 지정 시 해당 포스트만 처리.",
    )
    parser.add_argument(
        "--post-ids",
        type=str,
        default=None,
        help="처리할 포스트 ID (쉼표 구분). 예: --post-ids 1415,1485",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="출력 JSONL 파일 경로 (기본: pipeline/data/fixstyle_input.jsonl)",
    )
    parser.add_argument(
        "--multimodal",
        action="store_true",
        help="멀티모달 모드 활성화 (이미지/PDF base64 포함, tier별 JSONL 분할)",
    )
    args = parser.parse_args()

    sample_ids: set[int] | None = None

    if args.post_ids:
        sample_ids = {int(x.strip()) for x in args.post_ids.split(",")}
        print(f"지정 포스트 모드: {len(sample_ids)}건만 처리 ({args.post_ids})")
    elif args.sample:
        sample_file = Path(args.sample)
        if not sample_file.exists():
            print(f"샘플 파일을 찾을 수 없습니다: {sample_file}")
            return
        with open(sample_file, encoding="utf-8") as f:
            samples = json.load(f)
        # [{"post_id": 123, ...}, ...] 형식
        sample_ids = {int(s["post_id"]) for s in samples}
        print(f"샘플 모드: {len(sample_ids)}건만 처리")

    output_file = Path(args.output) if args.output else None
    prepare_fixstyle(
        sample_ids=sample_ids,
        output_file=output_file,
        enable_multimodal=args.multimodal,
    )


if __name__ == "__main__":
    main()
