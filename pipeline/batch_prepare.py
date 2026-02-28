"""
Prepare OpenAI Batch API JSONL for content refinement.
Uses gpt-5-mini with Structured Outputs (json_schema) for:
- Content quality improvement
- Summary generation
- Tag extraction
- post_type classification
- quality_score rating

Integrates with preprocessor for automatic content cleaning.
Filters skip/large files from catalog.
"""
import json
from collections import Counter
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "hyeongjun"
DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"
BATCH_INPUT_FILE = DATA_DIR / "batch_input.jsonl"

MAX_CONTENT_CHARS = 15000

# Structured Outputs 스키마 — json_schema로 100% 준수 보장
RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "blog_post_refinement",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "summary": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "post_type": {
                    "type": "string",
                    "enum": ["article", "paper_review", "tutorial", "til", "project", "activity_log"],
                },
                "quality_score": {"type": "number"},
            },
            "required": ["title", "content", "summary", "tags", "post_type", "quality_score"],
            "additionalProperties": False,
        },
    },
}

# 시스템 프롬프트 — Structured Outputs가 포맷을 보장하므로 품질 개선에 집중
SYSTEM_PROMPT = """You are a technical blog content editor specializing in Korean tech blogs.
Given a markdown document, improve its quality for a professional tech blog.

Guidelines:
1. Improve sentence clarity and readability in Korean. Fix grammar and awkward phrasing.
2. Keep ALL code blocks, LaTeX formulas, and technical terms completely intact.
3. Preserve the original meaning, structure, and technical accuracy.
4. Generate a concise Korean summary (2-3 sentences) capturing the key points.
5. Extract 5-10 relevant tags in English (lowercase, e.g. "docker", "deep-learning", "aws-lambda").
6. Classify post_type based on content nature.
7. Rate quality_score 0-10 based on depth, clarity, completeness, and educational value.
8. Do NOT add content that wasn't in the original. Do NOT remove technical details."""


def estimate_max_tokens(content_chars: int) -> int:
    """입력 콘텐츠 길이 기반 max_completion_tokens 추정.

    한국어 토큰 비율 ~1.8 chars/token (실측 기반).
    출력 = 리파인된 콘텐츠 + 메타데이터(title, summary, tags 등 ~1500 tokens).
    """
    estimated_output_tokens = int(content_chars / 1.8) + 1500
    return max(4096, min(estimated_output_tokens, 32768))


def load_preprocessed_or_raw(item: dict, ref_map: dict) -> str | None:
    """전처리된 파일 로드. 없으면 즉석 전처리."""
    preprocessed_path = PREPROCESSED_DIR / item["path"].replace("/", "__")
    if preprocessed_path.exists():
        return preprocessed_path.read_text(encoding="utf-8")

    # 전처리 파일이 없으면 원본에서 즉석 전처리
    file_path = VAULT_ROOT / item["path"]
    if not file_path.exists():
        return None

    from preprocessor import preprocess_content
    content = file_path.read_text(encoding="utf-8")
    processed, _ = preprocess_content(content, item["path"], ref_map)
    return processed


def prepare_batch():
    """Create batch JSONL file with Structured Outputs."""
    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    # image_map 로드
    ref_map = {}
    if IMAGE_MAP_FILE.exists():
        with open(IMAGE_MAP_FILE) as f:
            map_data = json.load(f)
        ref_map = map_data.get("ref_map", {})

    requests = []
    stats = Counter()

    for item in catalog:
        # skip 파일 제외
        if item.get("skip", False):
            stats["skipped_stub"] += 1
            continue

        content = load_preprocessed_or_raw(item, ref_map)
        if content is None:
            stats["skipped_missing"] += 1
            continue

        # 빈 콘텐츠 제외
        if len(content.strip()) < 50:
            stats["skipped_empty_after_preprocess"] += 1
            continue

        # large 파일 truncation + 경고
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
                "model": "gpt-5-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Category: {item['category_name']}\n"
                            f"Subcategory: {item.get('subcategory', '')}\n"
                            f"Quality grade: {item.get('quality', 'A')}\n"
                            f"{'[NOTE: Content was truncated due to length]' if truncated else ''}\n"
                            f"\n---\n\n{content}"
                        ),
                    },
                ],
                "response_format": RESPONSE_SCHEMA,
                "max_completion_tokens": estimate_max_tokens(len(content)),
            },
        }
        requests.append(request)
        stats["prepared"] += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(BATCH_INPUT_FILE, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    # 비용 추정: gpt-5-mini batch pricing (50% discount)
    # Input: $0.125/1M tokens, Output: $1.00/1M tokens (batch: 50% off)
    est_input_tokens = stats["prepared"] * 1000
    est_output_tokens = stats["prepared"] * 2000
    est_cost = (est_input_tokens * 0.125 / 1_000_000) + (est_output_tokens * 1.0 / 1_000_000)

    print(f"\n=== Batch Preparation Results ===")
    print(f"Prepared: {stats['prepared']} requests → {BATCH_INPUT_FILE}")
    for key, val in stats.most_common():
        if key != "prepared":
            print(f"  {key}: {val}")
    print(f"\nEstimated cost (batch 50% discount): ~${est_cost:.2f}")
    print(f"Batch limits: {stats['prepared']}/50,000 requests")

    # JSONL 파일 크기 확인
    file_size = BATCH_INPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"JSONL file size: {file_size:.1f} MB / 200 MB limit")


if __name__ == "__main__":
    prepare_batch()
