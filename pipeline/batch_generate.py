"""
30건 신규 콘텐츠 생성 JSONL 준비.

갭 분석 기반 주제 목록에서 gpt-5로 신규 블로그 포스트 생성.

실행:
    python pipeline/batch_generate.py
    python pipeline/batch_process.py \\
        --input  pipeline/data/generate_input.jsonl \\
        --output pipeline/data/generate_output.jsonl
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
GENERATE_INPUT_FILE = DATA_DIR / "generate_input.jsonl"

GENERATE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "blog_generate",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title":          {"type": "string"},
                "content":        {"type": "string"},
                "summary":        {"type": "string"},
                "tags":           {"type": "array", "items": {"type": "string"}},
                "quality_score":  {"type": "number"},
                "category_slug":  {"type": "string"},
            },
            "required": ["title", "content", "summary", "tags", "quality_score", "category_slug"],
            "additionalProperties": False,
        },
    },
}

GENERATE_SYSTEM = """당신은 도형준(DO HyeongJun)이라는 NLP/AI 엔지니어입니다.
본인의 개인 기술 블로그에 직접 포스트를 작성하세요.

[작성 규칙]
1. 이모지·이모티콘 완전 금지 (제목, 본문, 코드 모두)
2. 분량: 1500~2500자 (코드 제외, 한국어 기준)
3. 구성: ## 들어가며 → ## 핵심 개념 → ## 실전 구현 → ## 주의사항 → ## 마무리
4. 코드: Python 또는 Shell, import문 포함한 실행 가능한 완전한 예시
5. 경어체 ("~합니다", "~입니다"), 직접 경험 기반 자연스러운 문장
   예: "직접 구축해보니 이 부분이 까다로웠습니다", "실무에서 자주 마주치는 패턴입니다"
6. **굵게** 남발 금지 — 핵심 키워드만 강조
7. 2024-2025 기준 최신 라이브러리 버전 반영
8. 독자: 현업 1-3년차 개발자, CS 전공 취준생"""

# 갭 분석 기반 30개 주제
GAP_TOPICS = [
    # Data Engineering & DB (8편)
    {
        "title": "pgvector 실전 가이드: PostgreSQL에서 벡터 검색 구현하기",
        "category": "data-engineering",
        "tags": ["pgvector", "postgresql", "vector-search", "rag"],
    },
    {
        "title": "ETL vs ELT: 현대 데이터 파이프라인 설계 패턴 비교",
        "category": "data-engineering",
        "tags": ["etl", "elt", "data-pipeline", "dbt"],
    },
    {
        "title": "Apache Kafka 입문: 이벤트 스트리밍 아키텍처 핵심 개념",
        "category": "data-engineering",
        "tags": ["kafka", "event-streaming", "message-queue"],
    },
    {
        "title": "PostgreSQL 쿼리 튜닝 실전: EXPLAIN ANALYZE와 인덱스 전략",
        "category": "data-engineering",
        "tags": ["postgresql", "query-optimization", "index"],
    },
    {
        "title": "Redis 캐싱 전략: 실전 패턴과 피해야 할 안티패턴",
        "category": "data-engineering",
        "tags": ["redis", "caching", "python"],
    },
    {
        "title": "데이터 품질 관리 입문: Great Expectations로 파이프라인 검증",
        "category": "data-engineering",
        "tags": ["data-quality", "great-expectations", "testing"],
    },
    {
        "title": "MongoDB Aggregation Pipeline 실전 가이드",
        "category": "data-engineering",
        "tags": ["mongodb", "aggregation", "nosql", "python"],
    },
    {
        "title": "시계열 데이터 처리 패턴: 수집·저장·분석 완전 가이드",
        "category": "data-engineering",
        "tags": ["timeseries", "influxdb", "pandas"],
    },
    # DevOps & Infrastructure (8편)
    {
        "title": "GitHub Actions CI/CD 완전 가이드: Django + Docker 배포 자동화",
        "category": "cloud",
        "tags": ["github-actions", "ci-cd", "docker", "django"],
    },
    {
        "title": "Kubernetes 입문: Pod, Service, Deployment 핵심 개념 실습",
        "category": "cloud",
        "tags": ["kubernetes", "k8s", "container", "devops"],
    },
    {
        "title": "Nginx 리버스 프록시 + SSL/TLS 완전 설정 가이드",
        "category": "cloud",
        "tags": ["nginx", "ssl", "reverse-proxy"],
    },
    {
        "title": "Prometheus + Grafana로 Django 앱 모니터링 구축하기",
        "category": "cloud",
        "tags": ["prometheus", "grafana", "monitoring", "django"],
    },
    {
        "title": "LXD 컨테이너 운영 가이드: Docker 없이 가상 서버 관리하기",
        "category": "cloud",
        "tags": ["lxd", "container", "linux", "infrastructure"],
    },
    {
        "title": "Cloudflare Tunnel 배포 가이드: 서버 노출 없이 서비스 공개하기",
        "category": "cloud",
        "tags": ["cloudflare", "tunnel", "zero-trust", "deployment"],
    },
    {
        "title": "Docker Compose 멀티서비스 프로덕션 패턴: DB·Redis·앱 구성",
        "category": "cloud",
        "tags": ["docker-compose", "docker", "postgresql", "redis"],
    },
    {
        "title": "리눅스 서버 보안 하드닝 실전 체크리스트",
        "category": "cloud",
        "tags": ["linux", "security", "hardening", "ssh"],
    },
    # AI Production & LLMOps (8편)
    {
        "title": "RAG 시스템 구축 완전 가이드: pgvector + LangChain 실전",
        "category": "ai-ml",
        "tags": ["rag", "langchain", "pgvector", "llm", "openai"],
    },
    {
        "title": "OpenAI Batch API 완전 가이드: 비용 50% 절감 대량 처리 전략",
        "category": "ai-ml",
        "tags": ["openai", "batch-api", "cost-optimization", "python"],
    },
    {
        "title": "프롬프트 엔지니어링 실전: Few-shot, CoT, 구조화 출력 마스터",
        "category": "ai-ml",
        "tags": ["prompt-engineering", "few-shot", "chain-of-thought", "llm"],
    },
    {
        "title": "LangGraph로 멀티스텝 에이전트 워크플로우 구현하기",
        "category": "ai-ml",
        "tags": ["langgraph", "agent", "langchain", "workflow", "llm"],
    },
    {
        "title": "LLM 파인튜닝 입문: LoRA와 PEFT로 도메인 특화 모델 만들기",
        "category": "ai-ml",
        "tags": ["fine-tuning", "lora", "peft", "huggingface", "llm"],
    },
    {
        "title": "벡터 데이터베이스 비교 분석: pgvector vs Pinecone vs Weaviate",
        "category": "ai-ml",
        "tags": ["vector-db", "pgvector", "pinecone", "weaviate", "rag"],
    },
    {
        "title": "LLM 출력 평가 메트릭 가이드: BLEU, ROUGE, BERTScore 비교",
        "category": "ai-ml",
        "tags": ["evaluation", "bleu", "rouge", "bertscore", "nlp"],
    },
    {
        "title": "SSE(Server-Sent Events)로 LLM 스트리밍 응답 구현하기",
        "category": "ai-ml",
        "tags": ["sse", "streaming", "django", "openai", "fastapi"],
    },
    # Backend Architecture (6편)
    {
        "title": "Django REST Framework 고급 패턴: 확장 가능한 API 설계 원칙",
        "category": "development",
        "tags": ["django", "drf", "api-design", "rest", "python"],
    },
    {
        "title": "Celery + Redis로 비동기 작업 처리: 실전 구성 가이드",
        "category": "development",
        "tags": ["celery", "redis", "async", "django", "task-queue"],
    },
    {
        "title": "JWT 인증 심화: Refresh Token 로테이션과 보안 전략",
        "category": "development",
        "tags": ["jwt", "authentication", "security", "django"],
    },
    {
        "title": "Django 쿼리셋 N+1 문제 해결: select_related, prefetch_related 완전 가이드",
        "category": "development",
        "tags": ["django", "orm", "performance", "n-plus-1"],
    },
    {
        "title": "API 레이트 리밋 구현: Django + Redis로 요청 제한 적용하기",
        "category": "development",
        "tags": ["rate-limiting", "django", "redis", "api"],
    },
    {
        "title": "마이크로서비스 전환 전략: Django 모놀리스를 분리하는 실용적 접근",
        "category": "development",
        "tags": ["microservices", "architecture", "django", "api-gateway"],
    },
]


def prepare_generate():
    """갭 주제 기반 신규 콘텐츠 생성 JSONL 준비."""
    requests = []

    for i, topic in enumerate(GAP_TOPICS):
        custom_id = f"generate-{i:03d}"
        tags_str = ", ".join(topic["tags"])
        user_content = (
            f"카테고리: {topic['category']}\n"
            f"태그: {tags_str}\n\n"
            f"다음 주제로 블로그 포스트를 작성하세요:\n{topic['title']}"
        )

        request = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5",
                "messages": [
                    {"role": "system", "content": GENERATE_SYSTEM},
                    {"role": "user", "content": user_content},
                ],
                "response_format": GENERATE_SCHEMA,
                "max_completion_tokens": 16384,
            },
        }
        requests.append(request)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(GENERATE_INPUT_FILE, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    # 비용 추정: gpt-5 batch (50% discount)
    # Input: $0.625/1M, Output: $5.00/1M
    est_input_tokens = len(requests) * 1000
    est_output_tokens = len(requests) * 5000
    est_cost = (est_input_tokens * 0.625 / 1_000_000) + (est_output_tokens * 5.0 / 1_000_000)

    print(f"\n=== Generate Batch Preparation ===")
    print(f"Prepared: {len(requests)} requests → {GENERATE_INPUT_FILE}")
    print(f"Estimated cost (gpt-5 batch 50% discount): ~${est_cost:.2f}")
    file_size = GENERATE_INPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"JSONL file size: {file_size:.2f} MB / 200 MB limit")
    print(f"\nNext: python pipeline/batch_process.py \\")
    print(f"        --input  {GENERATE_INPUT_FILE} \\")
    print(f"        --output {DATA_DIR}/generate_output.jsonl")


if __name__ == "__main__":
    prepare_generate()
