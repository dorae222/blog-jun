# GraphRAG: 그래프 기반 RAG로 글로벌 질문에 답하기

## 논문 개요

:::info
**Paper:** From Local to Global: A Graph RAG Approach to Query-Focused Summarization (arXiv:2404.16130, 2024.04)
**저자:** Darren Edge, Ha Trinh, Newman Cheng et al.
**소속:** Microsoft Research
**코드:** [GitHub: microsoft/graphrag](https://github.com/microsoft/graphrag)
:::

기존 RAG(Retrieval-Augmented Generation)는 **"서울의 인구는?"** 같은 로컬 질문에 강하다. 관련 문서를 검색하고 해당 부분을 참조하면 되기 때문이다.

그러나 **"이 데이터셋의 주요 테마는 무엇인가?"** 같은 글로벌 질문에는 약하다. 이런 질문은 **전체 코퍼스에 걸친 이해**가 필요하며, 소수의 청크를 검색하는 것으로는 해결되지 않는다.

GraphRAG는 이 문제를 **지식 그래프 + 커뮤니티 기반 요약**으로 해결한다.

---

## 기존 RAG의 한계

### 로컬 vs 글로벌 질문

| 유형 | 예시 | 기존 RAG |
|------|------|---------|
| 로컬 | "BERT의 학습 목적함수는?" | 잘 작동 |
| 글로벌 | "이 논문 모음의 공통 트렌드는?" | 실패 |

글로벌 질문이 어려운 이유:
1. **관련 정보가 분산**: 전체 코퍼스에 걸쳐 있음
2. **단순 검색 불가**: 특정 키워드로 검색할 수 없음
3. **요약 필요**: 개별 문서가 아니라 문서 간 관계와 패턴 파악 필요

### Naive RAG의 시도

단순히 모든 텍스트를 LLM에 넣으면(map-reduce 방식) 해결되지만:
- **비용**: 전체 코퍼스를 매 질문마다 처리 → 비실용적
- **컨텍스트 한계**: 수백만 토큰의 코퍼스를 한 번에 처리 불가
- **정밀도**: 모든 정보를 동등하게 취급 → 핵심 정보 희석

---

## GraphRAG 파이프라인

### Phase 1: 지식 그래프 구축

입력 텍스트를 청크로 분할한 후, LLM을 사용하여 각 청크에서 **엔티티(노드)**와 **관계(엣지)**를 추출한다.

```
텍스트: "OpenAI의 GPT-4는 Transformer 아키텍처를 기반으로 하며,
        RLHF로 정렬되었다."

추출 결과:
  엔티티: [OpenAI, GPT-4, Transformer, RLHF]
  관계: [OpenAI -개발→ GPT-4,
         GPT-4 -기반→ Transformer,
         GPT-4 -정렬방법→ RLHF]
```

기존의 NER/RE 파이프라인과 달리, **LLM이 직접 추출**하므로 도메인 특화 학습 없이 범용적으로 적용 가능하다.

### Phase 2: 커뮤니티 탐지

구축된 그래프에서 **Leiden 알고리즘**으로 커뮤니티(밀접하게 연결된 노드 그룹)를 탐지한다.

```
커뮤니티 A: {Transformer, Attention, Self-Attention, Multi-Head}
커뮤니티 B: {RLHF, DPO, PPO, Alignment}
커뮤니티 C: {RAG, Vector DB, Embedding, Retrieval}
```

각 커뮤니티는 특정 **주제나 테마**를 나타낸다. 이는 글로벌 질문에 답하기 위한 핵심 구조다.

### Phase 3: 커뮤니티 요약

각 커뮤니티에 대해 LLM이 **요약 보고서**를 생성한다:

```
커뮤니티 B 요약:
"이 그룹은 LLM 정렬 기법에 관한 것이다. RLHF가 기본 패러다임이며,
DPO가 보상 모델 없이 정렬하는 대안으로 등장했다. PPO는 RLHF의
표준 최적화 알고리즘이다. 최근 트렌드는 보상 모델 의존성을
줄이는 방향으로..."
```

이 요약은 **인덱싱 시 한 번만** 생성되므로, 쿼리 시에는 추가 비용이 들지 않는다.

### Phase 4: 계층적 검색

글로벌 질문이 들어오면:

1. 관련 커뮤니티 요약을 검색
2. 가장 관련성 높은 커뮤니티들의 요약을 LLM에 전달
3. 커뮤니티 요약을 기반으로 글로벌 답변 생성

로컬 질문에 대해서는 기존 RAG와 유사하게 벡터 검색으로 관련 엔티티/관계를 찾아 답변한다.

---

## 로컬 검색 vs 글로벌 검색

### 로컬 검색 (Local Search)

질문과 관련된 **특정 엔티티**를 기반으로 검색:
1. 질문에서 핵심 엔티티 추출
2. 그래프에서 해당 엔티티와 연결된 이웃 노드/관계 탐색
3. 관련 텍스트 청크와 함께 LLM에 전달

기존 RAG보다 장점: **엔티티 간 관계 정보**도 함께 제공하므로, 더 풍부한 컨텍스트로 답변 생성.

### 글로벌 검색 (Global Search)

전체 코퍼스에 걸친 질문에 답변:
1. **커뮤니티 요약**을 검색 대상으로 사용
2. 관련 커뮤니티 요약을 수집
3. Map-Reduce: 각 요약에서 부분 답변 생성(Map) → 통합(Reduce)

핵심 혁신: 전체 코퍼스를 매번 읽는 대신, **미리 생성된 커뮤니티 요약**을 사용하여 비용을 대폭 절감.

---

## 실험 결과

### 비교 대상

- **Naive RAG**: 벡터 검색 + top-k 청크
- **Map-Reduce**: 전체 코퍼스를 LLM으로 순회
- **GraphRAG (Local)**: 그래프 기반 로컬 검색
- **GraphRAG (Global)**: 커뮤니티 기반 글로벌 검색

### 글로벌 질문 성능

글로벌 질문에서 GraphRAG(Global)가 모든 비교 대상을 유의미하게 능가했다. 특히:

- **포괄성(Comprehensiveness)**: Naive RAG 대비 큰 폭 향상 — 전체 데이터셋의 주요 테마를 빠짐없이 포착
- **다양성(Diversity)**: 다양한 관점과 각도에서 답변 제공
- **비용**: Map-Reduce 대비 토큰 사용량 대폭 감소

### 로컬 질문 성능

로컬 질문에서는 GraphRAG(Local)가 Naive RAG와 **비슷하거나 약간 우위**. 그래프 구조가 제공하는 관계 정보가 답변 품질을 향상시키지만, 단순 사실 질문에서의 차이는 크지 않다.

---

## 비용과 트레이드오프

### 인덱싱 비용

GraphRAG의 가장 큰 단점은 **인덱싱 비용**이다:

- 모든 텍스트 청크에 대해 LLM으로 엔티티/관계 추출 → **입력 텍스트 대비 수배의 LLM 호출**
- 커뮤니티 요약 생성 → 추가 LLM 호출
- 총 인덱싱 비용: 일반 RAG 대비 **10-100배**

### 언제 GraphRAG를 사용해야 하는가

| 상황 | 권장 |
|------|------|
| 글로벌/요약 질문이 빈번 | GraphRAG |
| 로컬 사실 질문만 | 일반 RAG |
| 코퍼스가 자주 변경 | 일반 RAG (재인덱싱 비용) |
| 코퍼스가 고정, 질문이 다양 | GraphRAG |

---

## 한계와 열린 질문

### 1. 그래프 품질

LLM의 엔티티/관계 추출 품질이 전체 파이프라인의 병목이다. 추출 오류(잘못된 관계, 누락된 엔티티)가 커뮤니티 구조를 왜곡할 수 있다.

### 2. 커뮤니티 세분도

Leiden 알고리즘의 해상도(resolution) 파라미터에 따라 커뮤니티 크기가 달라진다. 최적 해상도는 데이터와 질문 유형에 따라 다르며, 자동 선택 방법은 아직 미해결이다.

### 3. 동적 업데이트

새로운 문서가 추가되면 그래프 전체를 재구축해야 하는가, 점진적 업데이트가 가능한가? 현재 구현에서는 전체 재구축이 필요하다.

## Paper Summary

| 항목 | 내용 |
|------|------|
| 제목 | From Local to Global: A Graph RAG Approach to Query-Focused Summarization |
| 저자 | Darren Edge, Ha Trinh et al. |
| 소속 | Microsoft Research |
| 연도 | 2024 |
| 학회 | arXiv preprint |
| 원문 | [arXiv:2404.16130](https://arxiv.org/abs/2404.16130) |
| 코드 | [GitHub: microsoft/graphrag](https://github.com/microsoft/graphrag) |
| 핵심 키워드 | Knowledge Graph, Community Detection, RAG, Global Search, Query-Focused Summarization |
