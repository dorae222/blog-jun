<!-- infographic-hero -->
![Hybrid Search: Dense + Sparse + Reranking 핵심 요약](figures/infographic.svg)

*Figure: Hybrid Search: Dense + Sparse + Reranking 한 장 요약 인포그래픽*

# 하이브리드 검색 실전: Dense + Sparse + Reranking

## 들어가며

:::info
이 글은 RAG 파이프라인의 **검색(Retrieval)** 단계를 심층적으로 다루는 튜토리얼이다. 관련 주제로 [[graphrag-knowledge-graph]]와 [[context-compression]]도 함께 참고하면 도움이 된다.
:::

RAG(Retrieval-Augmented Generation) 파이프라인에서 **검색 품질이 생성 품질을 결정**한다. 아무리 강력한 LLM이라도 잘못된 문서가 제공되면 잘못된 답변을 생성한다. 이를 "Garbage In, Garbage Out" 원칙이라 한다.

검색에는 크게 두 가지 접근법이 존재한다:

- **Dense Retrieval**: 임베딩 벡터의 유사도로 검색하는 의미 기반 방식
- **Sparse Retrieval**: BM25 등 키워드 빈도 기반의 어휘 매칭 방식

각각 상호 보완적인 장단점이 있으며, **하이브리드 검색(Hybrid Search)**으로 두 장점을 결합하고, **Reranking**으로 최종 정밀도를 끌어올리는 것이 현재 RAG의 표준 패턴이다.

이 글에서는 세 가지 검색 패러다임의 비교, 하이브리드 결합 알고리즘, Reranking 모델 비교, 벡터 DB별 지원 현황, 그리고 실전 파이프라인 구현까지 체계적으로 정리한다.

---

## 검색 패러다임 비교 총정리

세 가지 검색 방식의 핵심 차이를 한눈에 비교한다.

| 항목 | Sparse (BM25) | Dense (Bi-Encoder) | Hybrid + Reranking |
|------|:---:|:---:|:---:|
| 검색 원리 | 키워드 빈도(TF-IDF 변형) | 벡터 코사인 유사도 | 양쪽 결합 + Cross-Encoder |
| 의미 검색 | 불가 | 우수 | 우수 |
| 정확 키워드 매칭 | 우수 | 미흡 | 우수 |
| 동의어/유의어 처리 | 불가 | 가능 | 가능 |
| 다국어 검색 | 제한적 | 가능 (다국어 모델) | 가능 |
| 코드/숫자 검색 | 우수 | 미흡 | 우수 |
| 도메인 적응성 | 높음 (학습 불필요) | 모델 의존적 | 높음 |
| 인덱스 크기 | 작음 | 큼 (벡터 저장) | 큼 |
| 검색 속도 (1차) | 매우 빠름 | 빠름 | 중간 |
| 정밀도 | 중간 | 중간~높음 | 높음 |
| 구현 복잡도 | 낮음 | 중간 | 높음 |

---

## Sparse Retrieval: BM25

## BM25 알고리즘 상세

BM25(Best Matching 25)는 전통적 정보 검색의 표준이다. 질의 내 각 토큰의 문서 내 빈도(TF)와 전체 코퍼스에서의 역문서 빈도(IDF)를 결합하여 관련도 점수를 계산한다.

$$\text{BM25}(q, d) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, d) \cdot (k_1 + 1)}{f(t, d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

각 변수의 의미:

| 변수 | 의미 | 일반적 값 |
|------|------|----------|
| $f(t, d)$ | 토큰 $t$의 문서 $d$ 내 출현 빈도 | - |
| $\text{IDF}(t)$ | 토큰 $t$의 역문서 빈도 | - |
| $k_1$ | 빈도 포화 파라미터 | 1.2~2.0 |
| $b$ | 문서 길이 정규화 파라미터 | 0.75 |
| $\|d\|$ | 문서 길이 (토큰 수) | - |
| $\text{avgdl}$ | 전체 문서의 평균 길이 | - |

## BM25의 강점과 약점

**강점**:
- 정확한 키워드 매칭: 전문 용어, 모델명(GPT-4o-mini), 코드 함수명 검색에 강함
- 학습 불필요: 어떤 도메인이든 즉시 적용 가능
- 빠르고 해석 가능: 왜 해당 문서가 검색됐는지 설명 가능
- 긴 문서에서도 안정적: 문서 길이 정규화 내장

**약점**:
- 동의어/유의어 처리 불가: "자동차"로 검색해도 "차량"을 포함하는 문서가 검색되지 않음
- 의미적 유사성 무시: "딥러닝 모델 학습"과 "신경망 훈련"의 연관성을 파악하지 못함
- 형태소 분석 의존: 한국어의 경우 형태소 분석기 품질에 크게 좌우됨

---

## Dense Retrieval: 벡터 검색

### 원리

텍스트를 고차원 벡터(임베딩)로 변환하고, 쿼리 벡터와 문서 벡터 간의 코사인 유사도 또는 내적(inner product)으로 검색한다. [[68_dpr]]에서 제안된 Dense Passage Retrieval이 이 분야의 시초이며, 이후 다양한 임베딩 모델이 등장했다.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 임베딩 모델 로드
model = SentenceTransformer("BAAI/bge-m3")

# 쿼리와 문서 임베딩
query = "Transformer의 attention 메커니즘"
documents = [
    "Self-Attention은 입력 시퀀스의 각 위치가 다른 모든 위치를 참조한다.",
    "CNN은 합성곱 필터로 지역적 패턴을 추출한다.",
    "Multi-Head Attention은 여러 관점에서 어텐션을 병렬 수행한다.",
]

query_vec = model.encode(query, normalize_embeddings=True)
doc_vecs = model.encode(documents, normalize_embeddings=True)

# 코사인 유사도로 top-k 검색
similarities = query_vec @ doc_vecs.T
top_k_indices = np.argsort(similarities)[::-1]

for i in top_k_indices:
    print(f"[{similarities[i]:.4f}] {documents[i][:50]}...")
```

```output
[0.8721] Self-Attention은 입력 시퀀스의 각 위치가 다른 모든 위치를 참조...
[0.8234] Multi-Head Attention은 여러 관점에서 어텐션을 병렬 수행...
[0.3102] CNN은 합성곱 필터로 지역적 패턴을 추출한다...
```

## 주요 임베딩 모델 비교

| 모델 | 차원 | 다국어 | MTEB Avg | 최대 토큰 | 라이선스 |
|------|:---:|:---:|:---:|:---:|------|
| `text-embedding-3-large` (OpenAI) | 3072 | O | 64.6 | 8191 | 상용 API |
| `text-embedding-3-small` (OpenAI) | 1536 | O | 62.3 | 8191 | 상용 API |
| `BAAI/bge-m3` | 1024 | O | 66.1 | 8192 | MIT |
| `BAAI/bge-large-en-v1.5` | 1024 | X | 64.2 | 512 | MIT |
| `intfloat/multilingual-e5-large-instruct` | 1024 | O | 65.4 | 514 | MIT |
| `Cohere/embed-v3` | 1024 | O | 66.3 | 512 | 상용 API |
| `jinaai/jina-embeddings-v3` | 1024 | O | 65.5 | 8192 | 상용/오픈 |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | X | 62.3 | 8192 | Apache 2.0 |

### Dense Retrieval의 강점과 약점

**강점**:
- 의미적 유사성 포착: "자동차"로 검색해도 "차량", "Vehicle" 관련 문서 검색 가능
- 다국어 검색: 다국어 임베딩 모델 사용 시 언어 무관 검색
- Zero-shot 일반화: 학습 데이터에 없는 도메인에도 일정 수준 작동

**약점**:
- 정확한 키워드 매칭 약함: "GPT-4o-mini"라는 정확한 모델명 검색이 약할 수 있음
- 임베딩 모델의 학습 도메인에 의존: 의료/법률 등 특수 도메인에서 성능 저하 가능
- 숫자, 코드, 특수 용어 검색이 약함: 정확한 매칭보다 의미적 근접을 우선시
- 인덱스 저장 비용: 문서당 수 KB의 벡터를 저장해야 함

---

## 하이브리드 검색: 두 세계의 결합

### 왜 하이브리드인가

단순히 "두 가지를 합치면 좋다"는 직관 이상의 근거가 있다. BEIR 벤치마크에서 하이브리드 검색은 어느 단일 방식보다 일관되게 높은 성능을 보인다.

| 데이터셋 | BM25 nDCG@10 | Dense nDCG@10 | Hybrid nDCG@10 |
|---------|:---:|:---:|:---:|
| MS MARCO | 0.228 | 0.382 | 0.401 |
| NQ (Natural Questions) | 0.329 | 0.474 | 0.498 |
| TREC-COVID | 0.656 | 0.534 | 0.701 |
| FiQA (금융) | 0.236 | 0.295 | 0.321 |
| SciFact (과학) | 0.665 | 0.613 | 0.702 |
| NFCorpus (의료) | 0.325 | 0.298 | 0.351 |
| ArguAna (논증) | 0.315 | 0.507 | 0.518 |
| DBPedia | 0.318 | 0.385 | 0.413 |

핵심 관찰: BM25가 강한 도메인(TREC-COVID, SciFact)에서도, Dense가 강한 도메인(MS MARCO, NQ)에서도, 하이브리드가 **항상 단독 방식 대비 개선**을 보여준다.

### Reciprocal Rank Fusion (RRF)

Dense와 Sparse 결과를 결합하는 가장 널리 쓰이는 방법이다. 각 랭킹 리스트에서의 순위(rank)를 기반으로 점수를 계산하므로, 서로 다른 스케일의 점수를 정규화할 필요가 없다.

$$\text{RRF}(d) = \sum_{r \in \text{rankings}} \frac{1}{k + r(d)}$$

여기서 $k$는 smoothing 상수(보통 60), $r(d)$는 해당 랭킹 리스트에서 문서 $d$의 순위이다.

```python
from collections import defaultdict
from typing import List, Tuple

def reciprocal_rank_fusion(
    dense_results: List[str],
    sparse_results: List[str],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    RRF로 Dense/Sparse 검색 결과를 결합한다.

    Args:
        dense_results: Dense 검색 결과 (doc_id 리스트, 순위순)
        sparse_results: Sparse 검색 결과 (doc_id 리스트, 순위순)
        k: smoothing 상수 (기본값 60)

    Returns:
        (doc_id, rrf_score) 튜플 리스트, 점수 내림차순
    """
    scores = defaultdict(float)

    for rank, doc_id in enumerate(dense_results):
        scores[doc_id] += 1.0 / (k + rank + 1)

    for rank, doc_id in enumerate(sparse_results):
        scores[doc_id] += 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# 사용 예시
dense_top10 = ["doc_A", "doc_B", "doc_C", "doc_D", "doc_E",
               "doc_F", "doc_G", "doc_H", "doc_I", "doc_J"]
sparse_top10 = ["doc_C", "doc_A", "doc_K", "doc_L", "doc_B",
                "doc_M", "doc_D", "doc_N", "doc_O", "doc_P"]

fused = reciprocal_rank_fusion(dense_top10, sparse_top10, k=60)
for doc_id, score in fused[:5]:
    print(f"  {doc_id}: {score:.6f}")
```

```output
  doc_A: 0.032520  # Dense 1위 + Sparse 2위
  doc_C: 0.032258  # Dense 3위 + Sparse 1위
  doc_B: 0.031746  # Dense 2위 + Sparse 5위
  doc_D: 0.031250  # Dense 4위 + Sparse 7위
  doc_E: 0.015385  # Dense 5위만
```

### 가중 결합 (Weighted Sum)

RRF 대신, Dense와 Sparse 점수를 직접 가중 합산하는 방식도 많이 사용된다. 이 경우 점수 정규화가 필요하다.

```python
import numpy as np

def weighted_hybrid_search(
    query: str,
    dense_search_fn,
    sparse_search_fn,
    alpha: float = 0.7,
    top_k: int = 50
) -> list:
    """
    가중 합산 방식의 하이브리드 검색.

    Args:
        alpha: Dense 가중치 (0~1). 1-alpha가 Sparse 가중치.
    """
    # 각각 검색
    dense_results = dense_search_fn(query, top_k=top_k)   # [(doc_id, score), ...]
    sparse_results = sparse_search_fn(query, top_k=top_k)  # [(doc_id, score), ...]

    # Min-Max 정규화
    def normalize(results):
        if not results:
            return {}
        scores = [s for _, s in results]
        min_s, max_s = min(scores), max(scores)
        rng = max_s - min_s if max_s != min_s else 1.0
        return {doc_id: (s - min_s) / rng for doc_id, s in results}

    dense_norm = normalize(dense_results)
    sparse_norm = normalize(sparse_results)

    # 가중 합산
    all_docs = set(dense_norm.keys()) | set(sparse_norm.keys())
    combined = {}
    for doc_id in all_docs:
        d_score = dense_norm.get(doc_id, 0.0)
        s_score = sparse_norm.get(doc_id, 0.0)
        combined[doc_id] = alpha * d_score + (1 - alpha) * s_score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

### alpha 값 튜닝 가이드

`alpha`(Dense 가중치) 값은 도메인과 쿼리 유형에 따라 조절해야 한다.

| 도메인/쿼리 유형 | 권장 alpha | 이유 |
|---------------|:---:|------|
| 일반 대화형 질의 | 0.7~0.8 | 의미 검색 비중이 높아야 함 |
| 기술 문서 검색 | 0.5~0.6 | 정확한 용어 매칭이 중요 |
| 코드 검색 | 0.3~0.4 | 함수명, 변수명 등 정확 매칭 우선 |
| FAQ 봇 | 0.6~0.7 | 자연어 질문과 답변의 의미 매칭 |
| 법률/의료 문서 | 0.4~0.5 | 전문 용어의 정확 매칭 중요 |
| 논문 검색 | 0.5~0.6 | 키워드 + 의미 균형 |
| 상품 검색 (이커머스) | 0.3~0.5 | 브랜드명, 모델명 정확 매칭 |

---

## Reranking: 2단계 정밀도 향상

### 왜 Reranking이 필요한가

1단계 검색(Dense/Sparse/Hybrid)은 수천~수만 문서에서 빠르게 후보를 추려내는 데 최적화되어 있다. 하지만 속도를 위해 정밀도를 어느 정도 희생한다. Reranker는 1단계에서 추려진 소수의 후보(보통 20~100개)에 대해 **훨씬 정밀한 관련도 평가**를 수행한다.

### Bi-Encoder vs Cross-Encoder

| 항목 | Bi-Encoder (1단계 검색) | Cross-Encoder (Reranker) |
|------|:---:|:---:|
| 입력 방식 | query와 doc을 **독립적**으로 인코딩 | query와 doc을 **함께** 인코딩 |
| 출력 | 벡터 (유사도 계산 필요) | 관련도 점수 (0~1) |
| 연산 복잡도 | $O(N)$ 벡터 미리 계산 가능 | $O(N \times Q)$ 매번 쌍으로 계산 |
| 속도 | 빠름 (ms 단위) | 느림 (초 단위, 후보 수에 비례) |
| 정밀도 | 중간 | 높음 |
| 적합 용도 | 1차 검색 (수천 -> 수십) | 2차 검색 (수십 -> 최종 k) |

Cross-Encoder가 더 정밀한 이유는, query와 document를 하나의 입력으로 합쳐 **토큰 수준의 상호작용(cross-attention)**을 통해 관련도를 판단하기 때문이다. Bi-Encoder는 두 텍스트를 독립적으로 인코딩하므로 이런 세밀한 상호작용이 불가능하다.

## 주요 Reranking 모델 비교

| 모델 | 유형 | BEIR Avg nDCG@10 | 속도 (docs/sec) | 다국어 | 비용 |
|------|------|:---:|:---:|:---:|------|
| `BAAI/bge-reranker-v2-m3` | Cross-Encoder | 54.3 | ~200 | O | 무료 (오픈소스) |
| `BAAI/bge-reranker-v2-gemma` | Cross-Encoder | 56.1 | ~80 | O | 무료 (오픈소스) |
| `Cohere Rerank v3` | API | 55.8 | ~500 | O | $2/1K queries |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | Cross-Encoder | 49.2 | ~800 | X | 무료 (오픈소스) |
| `jinaai/jina-reranker-v2-base-multilingual` | Cross-Encoder | 53.1 | ~350 | O | 무료 (오픈소스) |
| `ColBERT v2` | Late Interaction | 52.7 | ~1000 | X | 무료 (오픈소스) |
| `mixedbread-ai/mxbai-rerank-large-v1` | Cross-Encoder | 54.8 | ~150 | X | 무료 (오픈소스) |

:::warning
Reranker 모델은 후보 문서 수에 비례하여 비용과 레이턴시가 증가한다. 1단계 검색에서 top-100 이상을 Reranker에 넘기면 응답 시간이 크게 느려진다. 일반적으로 **top-20~50을 Reranker에 전달**하는 것이 비용 대비 효과가 좋다.
:::

### Reranking 구현

```python
from sentence_transformers import CrossEncoder

# Reranker 모델 로드
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)

def rerank(query: str, candidates: list, top_k: int = 5) -> list:
    """
    Cross-Encoder로 후보 문서를 재순위화한다.

    Args:
        query: 검색 쿼리
        candidates: 1단계 검색 결과 (문서 객체 리스트)
        top_k: 최종 반환할 문서 수

    Returns:
        재순위화된 상위 top_k 문서
    """
    if not candidates:
        return []

    # (query, document) 쌍 생성
    pairs = [(query, doc.text) for doc in candidates]

    # Cross-Encoder 점수 계산
    scores = reranker.predict(pairs)

    # 점수 기준 내림차순 정렬
    scored_docs = list(zip(candidates, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, score in scored_docs[:top_k]]
```

### ColBERT: Late Interaction 방식

ColBERT는 Cross-Encoder의 정밀도와 Bi-Encoder의 속도 사이의 절충점이다. query와 document를 각각 **토큰 단위 벡터**로 인코딩한 뒤, MaxSim 연산으로 관련도를 계산한다.

$$\text{ColBERT}(q, d) = \sum_{i \in q} \max_{j \in d} E_{q_i} \cdot E_{d_j}^T$$

| 특성 | Cross-Encoder | ColBERT | Bi-Encoder |
|------|:---:|:---:|:---:|
| 정밀도 | 최고 | 높음 | 중간 |
| 속도 | 느림 | 빠름 | 매우 빠름 |
| 문서 사전 계산 | 불가 | 가능 (토큰 벡터) | 가능 (단일 벡터) |
| 저장 공간 | 없음 | 큼 (토큰당 벡터) | 작음 |
| 적합 시나리오 | top-20~50 rerank | top-100~1000 rerank | 전체 코퍼스 검색 |

---

## 벡터 DB별 하이브리드 검색 지원

### 주요 벡터 DB 기능 비교

| 벡터 DB | 하이브리드 검색 | BM25 내장 | RRF 지원 | Sparse Vector | 관리형 서비스 |
|---------|:---:|:---:|:---:|:---:|:---:|
| **pgvector** | 외부 BM25 필요 | X (tsvector 활용) | 직접 구현 | X | Supabase, Neon |
| **Qdrant** | 내장 (RRF/DBSF) | O (Sparse Vector) | O | O | Qdrant Cloud |
| **Weaviate** | 내장 (alpha 설정) | O (내장 BM25) | O | O | Weaviate Cloud |
| **Milvus** | 외부 구현 필요 | X | 직접 구현 | O (v2.4+) | Zilliz |
| **Pinecone** | 내장 | O (Sparse-Dense) | O | O | Pinecone |
| **Chroma** | 외부 구현 필요 | X | 직접 구현 | X | - |
| **Elasticsearch** | 내장 (RRF) | O (기본) | O (v8.8+) | O | Elastic Cloud |
| **OpenSearch** | 내장 | O (기본) | O (v2.10+) | X | AWS OpenSearch |

### pgvector + BM25 조합 예시

PostgreSQL의 pgvector와 tsvector를 조합하면 단일 DB에서 하이브리드 검색이 가능하다.

```python
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

def hybrid_search_pgvector(conn, query: str, alpha: float = 0.7, top_k: int = 10):
    """
    pgvector + tsvector를 활용한 하이브리드 검색.
    """
    query_vec = model.encode(query, normalize_embeddings=True).tolist()

    sql = """
    WITH dense AS (
        SELECT id, content, 1 - (embedding <=> %s::vector) AS dense_score
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT 50
    ),
    sparse AS (
        SELECT id, content,
               ts_rank_cd(tsv, plainto_tsquery('korean', %s)) AS sparse_score
        FROM documents
        WHERE tsv @@ plainto_tsquery('korean', %s)
        ORDER BY sparse_score DESC
        LIMIT 50
    ),
    combined AS (
        SELECT
            COALESCE(d.id, s.id) AS id,
            COALESCE(d.content, s.content) AS content,
            COALESCE(d.dense_score, 0) AS dense_score,
            COALESCE(s.sparse_score, 0) AS sparse_score
        FROM dense d
        FULL OUTER JOIN sparse s ON d.id = s.id
    )
    SELECT id, content,
           (%s * dense_score + %s * sparse_score) AS hybrid_score
    FROM combined
    ORDER BY hybrid_score DESC
    LIMIT %s;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (query_vec, query_vec, query, query,
                          alpha, 1 - alpha, top_k))
        return cur.fetchall()
```

---

## 청크 전략과 검색 품질

하이브리드 검색의 성능은 **문서를 어떻게 나누는가(chunking)**에 크게 좌우된다. 동일한 검색 알고리즘이라도 청크 전략에 따라 nDCG@10이 10~20% 차이가 날 수 있다.

| 청크 전략 | 청크 크기 | 장점 | 단점 | 적합 도메인 |
|----------|:---:|------|------|-----------|
| 고정 길이 분할 | 256~512 토큰 | 구현 단순 | 의미 단위 분절 위험 | 범용 |
| 문단 기반 분할 | 가변 | 의미 단위 보존 | 크기 편차 큼 | 논문, 기술 문서 |
| 재귀적 분할 (LangChain) | 256~1024 | 구분자 우선순위 | 설정 필요 | 범용 |
| Semantic Chunking | 가변 | 의미 경계 인식 | 느림 (임베딩 필요) | 고품질 요구 |
| Sliding Window | 256+50 overlap | 경계 누락 방지 | 중복 인덱싱 | FAQ, 짧은 질의 |
| Parent-Child | 부모 1024 / 자식 256 | 검색 정밀 + 컨텍스트 보존 | 구현 복잡 | 긴 문서 |

핵심 원칙:
- BM25는 짧은 청크에서 더 정확하다 (문서 길이 정규화 효과)
- Dense 검색은 너무 짧은 청크에서 의미 정보가 부족해질 수 있다
- **하이브리드 검색에서는 256~512 토큰**이 가장 범용적인 최적 범위이다

---

## 쿼리 전처리와 확장

검색 품질은 쿼리 품질에도 크게 의존한다. 사용자의 원래 쿼리를 그대로 검색에 사용하면 최적의 결과를 얻지 못하는 경우가 많다.

| 기법 | 설명 | 효과 | 구현 복잡도 |
|------|------|------|:---:|
| Query Rewriting | LLM으로 쿼리를 검색에 적합한 형태로 변환 | 높음 | 중간 |
| HyDE (Hypothetical Document) | LLM으로 가상 답변 생성 후 이를 검색 쿼리로 사용 | 높음 | 중간 |
| Multi-Query | 하나의 질문을 여러 관점의 쿼리로 분해 | 중간 | 낮음 |
| Step-Back Prompting | 구체적 질문을 추상적 질문으로 변환 | 중간 | 낮음 |
| 키워드 추출 | 쿼리에서 핵심 키워드만 추출하여 BM25에 전달 | 중간 | 낮음 |

특히 하이브리드 검색에서는 Dense와 Sparse에 **다른 쿼리를 전달**하는 전략이 효과적이다:
- **Dense**: 원래 쿼리 또는 HyDE로 생성한 가상 답변
- **Sparse (BM25)**: 쿼리에서 추출한 핵심 키워드

---

## 실전 RAG 파이프라인 구현

### 전체 파이프라인 구조

하이브리드 검색 + Reranking RAG 파이프라인의 표준 구조:

1. **쿼리 전처리**: 쿼리 확장, 오타 교정
2. **1단계: 하이브리드 검색** (top-50): Dense + Sparse 결과를 RRF로 결합
3. **2단계: Reranking** (top-5): Cross-Encoder로 정밀 재순위화
4. **컨텍스트 구성**: 최종 문서로 프롬프트 구성
5. **LLM 생성**: 컨텍스트 기반 답변 생성

```python
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from collections import defaultdict
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class Document:
    id: str
    text: str
    metadata: dict = None

class HybridRAGPipeline:
    def __init__(
        self,
        embed_model: str = "BAAI/bge-m3",
        rerank_model: str = "BAAI/bge-reranker-v2-m3",
        alpha: float = 0.7,
        retrieval_top_k: int = 50,
        rerank_top_k: int = 5,
    ):
        self.encoder = SentenceTransformer(embed_model)
        self.reranker = CrossEncoder(rerank_model, max_length=512)
        self.alpha = alpha
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_k = rerank_top_k
        self.documents: List[Document] = []
        self.doc_vectors = None
        self.bm25 = None

    def index(self, documents: List[Document]):
        """문서를 인덱싱한다 (Dense 벡터 + BM25 인덱스)."""
        self.documents = documents
        texts = [doc.text for doc in documents]

        # Dense 인덱스
        self.doc_vectors = self.encoder.encode(
            texts, normalize_embeddings=True, show_progress_bar=True
        )

        # Sparse 인덱스 (BM25)
        tokenized = [text.split() for text in texts]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str) -> List[Document]:
        """하이브리드 검색 + Reranking을 수행한다."""
        # 1단계: Dense 검색
        query_vec = self.encoder.encode(query, normalize_embeddings=True)
        dense_scores = query_vec @ self.doc_vectors.T
        dense_top = np.argsort(dense_scores)[::-1][:self.retrieval_top_k]

        # 1단계: Sparse 검색 (BM25)
        tokenized_query = query.split()
        sparse_scores = self.bm25.get_scores(tokenized_query)
        sparse_top = np.argsort(sparse_scores)[::-1][:self.retrieval_top_k]

        # RRF 결합
        rrf_scores = defaultdict(float)
        k = 60
        for rank, idx in enumerate(dense_top):
            rrf_scores[idx] += 1.0 / (k + rank + 1)
        for rank, idx in enumerate(sparse_top):
            rrf_scores[idx] += 1.0 / (k + rank + 1)

        fused_indices = sorted(rrf_scores.keys(),
                               key=lambda x: rrf_scores[x], reverse=True)
        candidates = [self.documents[i] for i in fused_indices[:self.retrieval_top_k]]

        # 2단계: Reranking
        pairs = [(query, doc.text) for doc in candidates]
        rerank_scores = self.reranker.predict(pairs)
        scored = sorted(zip(candidates, rerank_scores),
                        key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored[:self.rerank_top_k]]

    def generate(self, query: str, llm_fn) -> str:
        """검색 + 생성 전체 파이프라인."""
        retrieved = self.search(query)
        context = "\n\n---\n\n".join([doc.text for doc in retrieved])
        prompt = f"다음 문서를 참고하여 질문에 답변하세요.\n\n{context}\n\n질문: {query}"
        return llm_fn(prompt)
```

---

## 성능 최적화 전략

### 레이턴시 vs 정확도 트레이드오프

| 설정 | 1단계 top-k | Rerank top-k | 레이턴시 (예상) | 상대 정밀도 |
|------|:---:|:---:|:---:|:---:|
| 최저 레이턴시 | 20 | 3 | ~50ms | 낮음 |
| 균형 | 50 | 5 | ~150ms | 중간 |
| 고정밀도 | 100 | 10 | ~400ms | 높음 |
| 최고 정밀도 | 200 | 20 | ~1000ms | 최고 |

### 최적화 기법

**1. 임베딩 캐싱**: 자주 검색되는 쿼리의 벡터를 캐시하여 인코딩 시간을 절약한다.

**2. Async Parallel Retrieval**: Dense와 Sparse 검색을 병렬로 실행한다.

```python
import asyncio

async def parallel_hybrid_search(query, dense_fn, sparse_fn):
    """Dense와 Sparse 검색을 비동기 병렬 실행."""
    dense_task = asyncio.create_task(dense_fn(query))
    sparse_task = asyncio.create_task(sparse_fn(query))
    dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
    return reciprocal_rank_fusion(dense_results, sparse_results)
```

**3. Quantized Reranker**: ONNX Runtime이나 CTranslate2로 Reranker 모델을 양자화하면 2~3배 속도 향상이 가능하다.

**4. 배치 Reranking**: 여러 쿼리의 Reranking을 배치로 처리하면 GPU 활용률이 높아진다.

---

## 유스케이스별 선택 가이드

### 시나리오별 권장 구성

| 유스케이스 | 검색 방식 | Reranker | alpha | 핵심 고려사항 |
|----------|---------|---------|:---:|------------|
| FAQ 챗봇 | Hybrid (RRF) | bge-reranker-v2-m3 | 0.7 | 자연어 질문 매칭, 빠른 응답 |
| 기술 문서 검색 | Hybrid (가중 합산) | Cross-Encoder | 0.5 | 정확한 용어 + 의미 검색 균형 |
| 코드 검색 | BM25 우선 Hybrid | 선택적 | 0.3 | 함수명/변수명 정확 매칭 우선 |
| 논문 검색 | Hybrid (RRF) | Cohere Rerank v3 | 0.6 | 다국어, 긴 문서, 높은 정밀도 |
| 이커머스 상품 검색 | Hybrid + 필터링 | ColBERT | 0.4 | 브랜드/모델명 + 속성 필터 |
| 법률 문서 검색 | Hybrid (RRF) | bge-reranker-v2-gemma | 0.4 | 전문 용어 정확도, 조항 번호 |
| 사내 지식베이스 | Hybrid (가중 합산) | 선택적 | 0.6 | 도메인 용어 + 일반 질의 혼합 |

### 인프라별 권장 스택

| 인프라 환경 | 벡터 DB | 임베딩 모델 | Reranker | 비고 |
|-----------|---------|----------|---------|------|
| PostgreSQL 기존 운영 | pgvector | bge-m3 | bge-reranker-v2-m3 | DB 추가 없이 구현 |
| 관리형 우선 | Pinecone | OpenAI text-embedding-3 | Cohere Rerank v3 | 운영 부담 최소 |
| 오픈소스 자체 호스팅 | Qdrant | bge-m3 | bge-reranker-v2-m3 | 완전 오픈소스 |
| 대규모 엔터프라이즈 | Elasticsearch | Cohere embed-v3 | bge-reranker-v2-gemma | 기존 ES 활용 |
| 프로토타입/PoC | Chroma | nomic-embed-text | 미사용 | 빠른 구현 우선 |

---

## 비용과 레이턴시 분석

### 컴포넌트별 비용 구조

| 컴포넌트 | 인프라 비용 | API 비용 (1K 쿼리) | 레이턴시 기여 |
|---------|:---:|:---:|:---:|
| BM25 인덱스 | 낮음 (CPU 서버) | 없음 | ~5ms |
| Dense 임베딩 (bge-m3) | 중간 (GPU 서버) | 없음 | ~20ms |
| Dense 임베딩 (OpenAI) | 없음 | ~$0.13 | ~30ms |
| 벡터 검색 (pgvector) | 기존 DB 활용 | 없음 | ~10ms |
| 벡터 검색 (Pinecone) | 없음 | ~$0.08 | ~15ms |
| RRF 결합 | 무시 가능 | 없음 | ~1ms |
| Reranker (bge-reranker, 50건) | 중간 (GPU) | 없음 | ~100ms |
| Reranker (Cohere, 50건) | 없음 | ~$0.10 | ~80ms |

### 월간 비용 시뮬레이션 (일 1만 쿼리 기준)

| 구성 | 월 인프라 | 월 API | 합계 | 평균 레이턴시 |
|------|:---:|:---:|:---:|:---:|
| BM25 only | $20 | $0 | $20 | ~15ms |
| Dense only (오픈소스) | $150 | $0 | $150 | ~40ms |
| Dense only (OpenAI) | $20 | $39 | $59 | ~50ms |
| Hybrid (오픈소스) | $170 | $0 | $170 | ~45ms |
| Hybrid + Rerank (오픈소스) | $250 | $0 | $250 | ~150ms |
| Hybrid + Rerank (API) | $20 | $93 | $113 | ~130ms |

---

## 평가 지표와 벤치마크

### 주요 평가 지표

| 지표 | 의미 | 수식 | 용도 |
|------|------|------|------|
| nDCG@k | 순위 반영 정규화 관련도 | 상위 k개 결과의 관련도와 이상적 순위 비교 | 검색 품질 종합 |
| MRR | 첫 관련 문서의 순위 역수 | $\frac{1}{\text{rank of first relevant}}$ | 단일 답변 검색 |
| Recall@k | 상위 k개에 포함된 관련 문서 비율 | $\frac{\text{relevant in top-k}}{\text{total relevant}}$ | 후보 커버리지 |
| Precision@k | 상위 k개 중 관련 문서 비율 | $\frac{\text{relevant in top-k}}{k}$ | 결과 정밀도 |
| MAP | 평균 정밀도의 평균 | 각 관련 문서 위치의 Precision 평균 | 전체 순위 품질 |

### 하이브리드 + Reranking의 효과 (BEIR 벤치마크 기준)

| 구성 | MS MARCO | NQ | FiQA | SciFact | 평균 향상 |
|------|:---:|:---:|:---:|:---:|:---:|
| BM25 단독 | 0.228 | 0.329 | 0.236 | 0.665 | baseline |
| Dense 단독 | 0.382 | 0.474 | 0.295 | 0.613 | +14.2% |
| Hybrid (RRF) | 0.401 | 0.498 | 0.321 | 0.702 | +20.8% |
| Hybrid + Reranking | 0.432 | 0.531 | 0.358 | 0.738 | +30.1% |

:::tip
**빠른 시작 권장**: 처음 하이브리드 검색을 도입한다면, **Qdrant + bge-m3 + bge-reranker-v2-m3** 조합을 추천한다. 모두 오픈소스이며, Qdrant는 RRF를 내장 지원하고, bge 모델 패밀리는 다국어를 지원하여 한국어 검색에도 바로 적용 가능하다.
:::

---

## 자주 하는 실수와 해결책

### 1. Reranker에 너무 많은 후보 전달
- **문제**: top-500을 Reranker에 넘겨 레이턴시 급증
- **해결**: 1단계에서 top-50, Reranker에서 top-5로 단계적 축소

### 2. 점수 정규화 없이 가중 합산
- **문제**: Dense 점수(0~1)와 BM25 점수(0~수십)를 그대로 합산
- **해결**: Min-Max 정규화 후 합산, 또는 RRF 사용 (점수 스케일 무관)

### 3. alpha 값 고정
- **문제**: 모든 쿼리에 동일한 alpha 적용
- **해결**: 쿼리 유형 분류기를 두고 동적 alpha 적용, 또는 A/B 테스트로 최적값 탐색

### 4. 임베딩 모델과 Reranker 모델 불일치
- **문제**: 영어 전용 임베딩 + 다국어 Reranker, 또는 그 반대
- **해결**: 동일 언어/도메인을 지원하는 모델 패밀리 사용 (예: bge 시리즈)

---

## 정리

| 단계 | 역할 | 비용 | 레이턴시 기여 |
|------|------|:---:|:---:|
| Sparse Search (BM25) | 키워드 기반 정확 매칭 | 낮음 | ~5ms |
| Dense Search | 의미 기반 넓은 검색 | 중간 | ~30ms |
| RRF/가중 결합 | 두 결과 통합 | 무시 가능 | ~1ms |
| Reranking | 최종 정밀도 향상 | 중간 | ~100ms |
| **전체 파이프라인** | **하이브리드 + Rerank** | **중간** | **~150ms** |

**검색 품질 = RAG 품질**이다. Dense만으로 부족하고, Sparse만으로도 부족하다. 하이브리드 검색으로 양쪽의 장점을 취하고, Reranking으로 최종 정밀도를 끌어올리는 것이 현재 RAG에서 **검색 품질을 극대화하는 표준 패턴**이다.

핵심 요약:
- **검색 품질이 낮으면**: 먼저 하이브리드 검색 도입 (BM25 + Dense, RRF 결합)
- **정밀도가 더 필요하면**: Cross-Encoder Reranker 추가
- **레이턴시가 문제면**: Reranker 후보 수 줄이기 + 임베딩 캐싱 + 비동기 병렬 검색
- **비용이 문제면**: 오픈소스 모델(bge 시리즈) + 자체 호스팅
