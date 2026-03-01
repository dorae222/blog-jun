"""
전체 716건 원본 Obsidian 파일 → gpt-5 단일패스 재작성 JSONL 준비.

batch_prepare.py 기반이나 다음 항목 변경:
- 모델: gpt-5 (최고 품질)
- 스키마: should_archive, archive_reason 추가
- 시스템 프롬프트: 개인 블로그 스타일, 이모지 완전 금지
- estimate_max_tokens: gpt-5 128K 출력 지원, 상한 제거

실행:
    python pipeline/batch_rewrite.py
    python pipeline/batch_process.py \\
        --input  pipeline/data/rewrite_input.jsonl \\
        --output pipeline/data/rewrite_output.jsonl
"""
import json
from collections import Counter
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "hyeongjun"
DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"
REWRITE_INPUT_FILE = DATA_DIR / "rewrite_input.jsonl"

MAX_CONTENT_CHARS = 15000

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

REWRITE_SYSTEM = """당신은 도형준(DO HyeongJun)이라는 NLP/AI 엔지니어의 개인 기술 블로그 포스트를 정제합니다.
마치 도형준 본인이 직접 공부하고 경험한 것을 기록한 글처럼 자연스럽게 다시 작성하세요.

[필수 규칙]
1. 이모지·이모티콘 완전 제거 (제목, 본문, 코드블록, 헤더 모두 포함)
2. 문법 오류·맞춤법 100% 수정
3. 경어체 유지 ("~합니다", "~입니다") — 자연스럽고 직접적인 문장
4. 반복·중복 내용 삭제, 과도한 서론/결론 축약
5. 코드 예시는 실행 가능한 형태로 정리 (import문 확인, 불필요 주석 제거)
6. 원본 분량 ±30% 이내 유지 (긴 것은 핵심만 남겨 축약)
7. **굵게** 남발 금지 — 핵심 키워드만 강조
8. "AI가 작성한 것 같은" 인위적 표현 최소화
9. 사실 오류 수정 (2024-2025 기준 최신 정보 반영)
10. 코드 블록, LaTeX 수식, 기술 용어는 완전히 그대로 유지

[아카이브 판정 기준 — should_archive = true]
아래 조건 중 하나라도 해당하면 should_archive = true, archive_reason 한 줄 기록:
- 내용이 스크래치 메모/TODO 수준으로 기술적 가치가 없음 (200자 미만)
- 설명 없이 링크 목록만 나열된 북마크
- 내부용 일정·회의록·개인 메모로 블로그 발행 부적합

quality_score: 0-10 (개선 후 기준으로 평가)"""


def estimate_max_tokens(content_chars: int) -> int:
    """동적 max_completion_tokens 계산.

    한국어 ~1.8 chars/token, 재작성 출력 = 최대 입력 1.5배 + 스키마 오버헤드.
    gpt-5 max output 128K이므로 상한 제거 → 출력 잘림 방지.
    """
    estimated_output_tokens = int(content_chars / 1.8 * 1.5) + 2048
    return max(16384, estimated_output_tokens)


def load_preprocessed_or_raw(item: dict, ref_map: dict) -> str | None:
    """전처리된 파일 로드. 없으면 즉석 전처리."""
    preprocessed_path = PREPROCESSED_DIR / item["path"].replace("/", "__")
    if preprocessed_path.exists():
        return preprocessed_path.read_text(encoding="utf-8")

    file_path = VAULT_ROOT / item["path"]
    if not file_path.exists():
        return None

    from preprocessor import preprocess_content
    content = file_path.read_text(encoding="utf-8")
    processed, _ = preprocess_content(content, item["path"], ref_map)
    return processed


def prepare_rewrite():
    """원본 파일 기반 재작성 JSONL 생성."""
    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    ref_map = {}
    if IMAGE_MAP_FILE.exists():
        with open(IMAGE_MAP_FILE) as f:
            map_data = json.load(f)
        ref_map = map_data.get("ref_map", {})

    requests = []
    stats = Counter()

    for item in catalog:
        if item.get("skip", False):
            stats["skipped_stub"] += 1
            continue

        content = load_preprocessed_or_raw(item, ref_map)
        if content is None:
            stats["skipped_missing"] += 1
            continue

        if len(content.strip()) < 50:
            stats["skipped_empty"] += 1
            continue

        truncated = False
        if item.get("large", False) or len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + "\n\n[... content truncated for processing ...]"
            truncated = True
            stats["truncated_large"] += 1

        request = {
            "custom_id": item["path"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5",
                "messages": [
                    {"role": "system", "content": REWRITE_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Category: {item['category_name']}\n"
                            f"Subcategory: {item.get('subcategory', '')}\n"
                            f"{'[NOTE: Content was truncated due to length]' if truncated else ''}\n"
                            f"\n---\n\n{content}"
                        ),
                    },
                ],
                "response_format": REWRITE_SCHEMA,
                "max_completion_tokens": estimate_max_tokens(len(content)),
            },
        }
        requests.append(request)
        stats["prepared"] += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REWRITE_INPUT_FILE, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    # 비용 추정: gpt-5 batch pricing (50% discount)
    # Input: $0.625/1M, Output: $5.00/1M
    est_input_tokens = stats["prepared"] * 4000
    est_output_tokens = stats["prepared"] * 3500
    est_cost = (est_input_tokens * 0.625 / 1_000_000) + (est_output_tokens * 5.0 / 1_000_000)

    print(f"\n=== Rewrite Batch Preparation ===")
    print(f"Prepared: {stats['prepared']} requests → {REWRITE_INPUT_FILE}")
    for key, val in stats.most_common():
        if key != "prepared":
            print(f"  {key}: {val}")
    print(f"\nEstimated cost (gpt-5 batch 50% discount): ~${est_cost:.2f}")
    print(f"Batch limits: {stats['prepared']}/50,000 requests")

    file_size = REWRITE_INPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"JSONL file size: {file_size:.1f} MB / 200 MB limit")
    print(f"\nNext: python pipeline/batch_process.py \\")
    print(f"        --input  {REWRITE_INPUT_FILE} \\")
    print(f"        --output {DATA_DIR}/rewrite_output.jsonl")


if __name__ == "__main__":
    prepare_rewrite()
