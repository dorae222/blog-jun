# 하이브리드 검색 실전: Dense + Sparse + Reranking

## 들어가며

RAG 파이프라인에서 **검색 품질이 생성 품질을 결정**한다. 아무리 강력한 LLM이라도, 잘못된 문서가 제공되면 잘못된 답변을 생성한다.

검색에는 크게 두 가지 접근법이 있다:
- **Dense Retrieval**: 임베딩 벡터의 유사도로 검색 (의미 기반)
- **Sparse Retrieval**: BM25 등 키워드 매칭 (어휘 기반)

각각 장단점이 있으며, **하이브리드 검색 + Reranking**으로 두 장점을 결합할 수 있다.

---

## Dense vs Sparse

### Dense Retrieval (벡터 검색)

텍스트를 고차원 벡터로 변환하고, 코사인 유사도로 검색한다.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")
query_vec = model.encode("Transformer의 attention 메커니즘")
doc_vecs = model.encode(documents)

# 코사인 유사도로 top-k 검색
similarities = query_vec @ doc_vecs.T
```

장점:
- **의미적 유사성** 포착 — "자동차"로 "차량" 관련 문서도 검색
- 다국어 검색 가능 (다국어 임베딩 모델 사용 시)

단점:
- **정확한 키워드 매칭 약함** — "GPT-4o-mini"라는 정확한 모델명 검색이 약할 수 있음
- 임베딩 모델의 학습 도메인에 의존
- 숫자, 코드, 특수 용어 검색이 약함

### Sparse Retrieval (BM25)

전통적 정보 검색 — 토큰 빈도와 문서 빈도 기반:

$$\text{BM25}(q, d) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, d) \cdot (k_1 + 1)}{f(t, d) + k_1 \cdot (1 - b + b \cdot |d| / \text{avgdl})}$$

장점:
- **정확한 키워드 매칭** — 전문 용어, 모델명, 코드 검색에 강함
- 학습 불필요, 도메인 독립적
- 빠르고 해석 가능

단점:
- 동의어/유의어 처리 불가
- 의미적 유사성 무시

---

## 하이브리드 검색

### Reciprocal Rank Fusion (RRF)

Dense와 Sparse 결과를 결합하는 가장 널리 쓰이는 방법:

$$\text{RRF}(d) = \sum_{r \in \text{rankings}} \frac{1}{k + r(d)}$$

여기서 $k$는 상수(보통 60), $r(d)$는 해당 랭킹에서의 순위.

```python
def reciprocal_rank_fusion(dense_results, sparse_results, k=60):
    scores = {}
    for rank, doc_id in enumerate(dense_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    for rank, doc_id in enumerate(sparse_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### 가중 결합

```python
# Dense 점수와 Sparse 점수의 가중 합
alpha = 0.7  # Dense 가중치
final_score = alpha * dense_score + (1 - alpha) * sparse_score
```

`alpha` 값은 도메인에 따라 조절:
- **기술 문서** (정확한 용어 중요): alpha = 0.5 (sparse 비중 높임)
- **일반 대화** (의미 검색 중요): alpha = 0.8 (dense 비중 높임)

---

## Reranking: 정밀도 향상

하이브리드 검색으로 후보를 넓게 수집한 후, **Cross-Encoder Reranker**로 최종 순위를 재조정한다.

### Cross-Encoder vs Bi-Encoder

| | Bi-Encoder (Dense) | Cross-Encoder (Reranker) |
|--|---|---|
| 입력 | query와 doc을 **독립적**으로 인코딩 | query와 doc을 **함께** 인코딩 |
| 속도 | 빠름 (벡터 미리 계산) | 느림 (매번 쌍으로 계산) |
| 정밀도 | 중간 | 높음 |
| 용도 | 1차 검색 (수천→수십) | 2차 검색 (수십→최종 k) |

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# 1차 검색 결과 (top-50)
candidates = hybrid_search(query, top_k=50)

# Reranking
pairs = [(query, doc.text) for doc in candidates]
scores = reranker.predict(pairs)

# 최종 top-5 선택
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:5]
```

### Reranking의 효과

검색 벤치마크에서 하이브리드 + Reranking은 일반적으로:
- Dense만 사용 대비 **5~15% nDCG 향상**
- Sparse만 사용 대비 **10~20% 향상**

특히 **도메인 특화 질문**에서 Reranker의 효과가 두드러진다.

---

## 실전 파이프라인 구성

### RAG with 하이브리드 검색

```python
def rag_pipeline(query, documents, llm):
    # 1. 하이브리드 검색 (top-50)
    dense_results = vector_search(query, top_k=50)
    sparse_results = bm25_search(query, top_k=50)
    candidates = reciprocal_rank_fusion(dense_results, sparse_results)[:50]

    # 2. Reranking (top-5)
    reranked = cross_encoder_rerank(query, candidates, top_k=5)

    # 3. LLM 생성
    context = "\n\n".join([doc.text for doc in reranked])
    answer = llm.generate(f"Context: {context}\n\nQuestion: {query}")
    return answer
```

### 벡터 DB별 하이브리드 지원

| 벡터 DB | 하이브리드 검색 | BM25 내장 |
|---------|-------------|----------|
| pgvector | 외부 BM25 필요 | X (PostgreSQL tsvector 활용) |
| Qdrant | RRF/DBSF 내장 | O (Sparse Vector) |
| Weaviate | Hybrid Alpha 설정 | O (내장 BM25) |
| Milvus | 외부 구현 | X |
| Pinecone | 내장 | O (Sparse-Dense) |

---

## 정리

| 단계 | 역할 | 비용 |
|------|------|------|
| Dense Search | 의미 기반 넓은 검색 | 중간 (임베딩 생성) |
| Sparse Search | 키워드 기반 정확 검색 | 낮음 |
| RRF 결합 | 두 결과 통합 | 무시 가능 |
| Reranking | 최종 정밀도 향상 | 중간 (Cross-Encoder) |

**검색 품질 = RAG 품질**. Dense만으로 부족하고, Sparse만으로도 부족하다. 하이브리드 검색 + Reranking은 현재 RAG에서 **검색 품질을 극대화하는 표준 패턴**이다.
