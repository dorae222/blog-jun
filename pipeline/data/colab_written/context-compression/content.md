# Context Compression: 긴 입력을 효율적으로 처리하기

## 들어가며

LLM의 컨텍스트 윈도우가 100K+ 토큰으로 확장되었지만, **긴 입력 = 높은 비용 + 높은 지연시간**이다. API 비용은 입력 토큰 수에 비례하고, Prefill 시간은 시퀀스 길이의 제곱에 비례한다.

**Context Compression**은 LLM에 전달하는 입력을 **핵심만 남기고 압축**하여 비용과 지연시간을 줄이는 전략이다.

---

## 왜 압축이 필요한가

### 비용 계산 예시

RAG 파이프라인에서 5개 문서(각 2,000 토큰)를 검색한 경우:

| 방식 | 입력 토큰 | GPT-4o 비용 (per query) |
|------|----------|----------------------|
| 전체 전달 | 10,000 | $0.025 |
| 50% 압축 | 5,000 | $0.0125 |
| 80% 압축 | 2,000 | $0.005 |

일일 10,000건 처리 시 월 비용:
- 압축 없음: **$7,500/월**
- 80% 압축: **$1,500/월** (5배 절감)

### 지연시간

[[inference-optimization-mfu|추론 최적화]]에서 다뤘듯이, Prefill 단계는 입력 길이에 크게 영향을 받는다. 입력을 절반으로 줄이면 Prefill 시간도 대폭 감소한다.

---

## 압축 기법

### 1. 프롬프트 압축 (Prompt Compression)

#### LLMLingua

Jiang et al.(2023)이 제안한 **토큰 레벨 프롬프트 압축**. 작은 LLM(GPT-2 등)을 사용하여 각 토큰의 **정보량(perplexity)**을 측정하고, 정보량이 낮은 토큰을 제거한다.

```python
from llmlingua import PromptCompressor

compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"
)

original_prompt = """
다음 문서들을 참고하여 질문에 답하세요.

문서 1: Transformer는 2017년 Google에서 발표한 아키텍처입니다.
Self-attention 메커니즘을 통해 시퀀스의 모든 위치 간
의존성을 학습합니다. 이전의 RNN/LSTM 대비 병렬 처리가
가능하여 학습 속도가 크게 향상되었습니다...

질문: Transformer의 핵심 메커니즘은?
"""

compressed = compressor.compress_prompt(
    original_prompt,
    rate=0.5,   # 50%로 압축
    force_tokens=["질문:", "답하세요"]  # 보존할 토큰
)
# 압축된 프롬프트: 핵심 정보만 유지
```

LLMLingua의 장점:
- 토큰 수를 2~10배 줄이면서 **성능 저하 최소화**
- 질문과 관련 없는 부분을 우선 제거

#### LongLLMLingua

RAG에 특화된 버전. 질문과의 관련성을 고려하여 문서별로 **다른 압축률**을 적용한다:
- 관련성 높은 문서: 압축률 낮음 (정보 보존)
- 관련성 낮은 문서: 압축률 높음 (핵심만)

### 2. 문서 요약 기반 압축

LLM 자체를 사용하여 긴 문서를 **핵심 요약**으로 변환한 후, 요약을 컨텍스트로 사용한다.

```python
def summarize_and_query(documents, query, llm):
    # 1단계: 각 문서 요약
    summaries = []
    for doc in documents:
        summary = llm.invoke(f"다음 문서를 3문장으로 요약하라:\n{doc}")
        summaries.append(summary)

    # 2단계: 요약을 컨텍스트로 사용
    context = "\n".join(summaries)
    answer = llm.invoke(f"Context: {context}\n\nQuestion: {query}")
    return answer
```

장점: 직관적, 구현 간단
단점: 요약 과정에서 정보 손실, 요약 자체의 LLM 비용

### 3. 선택적 검색 (Selective Retrieval)

처음부터 **정확하게 검색**하여 불필요한 문서를 제외한다.

```python
# 1단계: 넓은 검색 (top-20)
candidates = hybrid_search(query, top_k=20)

# 2단계: Reranking으로 정밀 선택 (top-3)
reranked = cross_encoder_rerank(query, candidates, top_k=3)

# 결과: 3개 문서만 LLM에 전달 (20개 → 3개 = 85% 감소)
```

[[hybrid-search-reranking|하이브리드 검색 + Reranking]]이 이 전략의 핵심이다.

### 4. 청크 크기 최적화

RAG에서 청크 크기를 줄이면 각 검색 결과의 토큰 수가 줄어든다:

| 청크 크기 | 검색 결과 5개 시 총 토큰 |
|----------|---------------------|
| 1,000 토큰 | 5,000 |
| 500 토큰 | 2,500 |
| 200 토큰 | 1,000 |

단, 너무 작은 청크는 **컨텍스트가 부족**하여 검색 품질 저하. 200~500 토큰이 일반적인 균형점이다.

---

## RAG에서의 컨텍스트 최적화

### 계층적 압축 파이프라인

```
질문 → 넓은 검색(top-20) → Reranking(top-5) → 프롬프트 압축(50%) → LLM
```

각 단계에서 정보를 정제하여 **최종적으로 최소한의 고품질 컨텍스트**만 LLM에 전달한다.

### 적응적 컨텍스트 길이

질문의 복잡도에 따라 컨텍스트 양을 조절:

| 질문 유형 | 필요 컨텍스트 | 전략 |
|----------|------------|------|
| 간단한 사실 | 1~2 청크 | 최소 검색 |
| 비교/분석 | 3~5 청크 | 중간 검색 + 압축 |
| 종합적 요약 | 5~10 청크 | 넓은 검색 + 강한 압축 |

---

## 압축과 품질의 트레이드오프

### 압축률별 성능 변화

일반적인 패턴:
- **0~50% 압축**: 성능 저하 거의 없음 (중복/관용적 표현 제거)
- **50~70% 압축**: 약간의 성능 저하 (부차적 정보 손실)
- **70~90% 압축**: 유의미한 성능 저하 (핵심 정보 손실 시작)
- **90%+ 압축**: 심각한 성능 저하

:::tip
**실전 권장**: 50~60% 압축률이 비용 절감과 품질 유지의 최적 균형점이다.
:::

### "Lost in the Middle" 완화

[[long-context-techniques|Long Context]]에서 다뤘듯이, LLM은 중간에 위치한 정보를 무시하는 경향이 있다. 압축을 통해 전체 길이를 줄이면 이 문제가 자연스럽게 완화된다.

---

## 정리

| 기법 | 압축률 | 비용 | 품질 유지 |
|------|-------|------|----------|
| 프롬프트 압축 (LLMLingua) | 50~80% | 낮음 (작은 모델) | 높음 |
| 문서 요약 | 70~90% | 중간 (LLM 호출) | 중간 |
| 선택적 검색 + Reranking | 60~85% | 중간 (Reranker) | 높음 |
| 청크 크기 최적화 | 50~75% | 없음 | 중간 |

Context Compression은 **"더 많은 정보를 넣는 것"에서 "더 좋은 정보만 넣는 것"**으로의 전환이다. 비용 절감뿐 아니라, 불필요한 정보를 제거함으로써 LLM이 핵심에 집중하게 하여 **응답 품질 자체를 높이는 효과**도 있다.
