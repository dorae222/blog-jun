<!-- infographic-hero -->
![GraphRAG and LazyGraphRAG 핵심 요약](figures/infographic.svg)

*Figure: GraphRAG and LazyGraphRAG 한 장 요약 인포그래픽*

# GraphRAG와 LazyGraphRAG: 지식그래프 기반 검색

> 시리즈 안내: 5편 중 2편 - 청크가 아닌 그래프로 검색하는 RAG

## 개요

[[rag-01-evolution-overview|1편]]에서 짚은 Standard RAG의 첫 번째 한계는 청킹이 컨텍스트를 절단한다는 것이었습니다. "이 회사의 핵심 인물 네트워크는?", "두 보고서에 공통적으로 등장하는 위험 요소는?" 같은 질문은 단일 청크 검색으로는 풀 수 없습니다. 답이 여러 문서에 흩어져 있고, 그것들을 연결하는 관계 정보가 필요하기 때문입니다.

Microsoft Research가 2024년 4월 공개한 GraphRAG는 이 문제를 정면으로 풉니다. 청크 임베딩 대신 LLM으로 문서에서 엔티티(entity)와 관계(relation)를 추출해 지식 그래프를 만들고, 커뮤니티 탐지 알고리즘으로 그래프를 계층적으로 요약합니다. 후속작 LazyGraphRAG(2024년 11월)는 동일한 품질을 유지하면서 인덱싱 비용을 0.1% 수준으로 낮췄습니다. 이 편에서는 두 기법의 동작 원리와 trade-off를 분석합니다.

## 배경: 왜 그래프인가

청크 기반 검색은 "비슷한 문장 찾기"에 최적화돼 있습니다. 하지만 실제 비즈니스 질문은 종종 "A와 B의 관계", "C에 영향을 주는 요인들의 합집합" 같은 구조적 정보를 요구합니다. 지식 그래프는 이런 구조를 명시적으로 표현합니다.

Microsoft 연구진이 발표한 벤치마크에서 GraphRAG는 사내 위키, 뉴스 모음, 팟캐스트 트랜스크립트 같은 비정형 코퍼스에서 글로벌 질의(전체 corpus를 통합해 답해야 하는 질문)에 대해 baseline RAG 대비 70-80% 더 높은 comprehensiveness 점수를 기록했습니다.

## 핵심 개념

### 인덱싱 단계 (offline)

GraphRAG의 인덱싱은 4단계로 구성됩니다.

1. 청킹: 문서를 적당한 크기로 분할
2. 엔티티/관계 추출: LLM에 청크를 입력해 (entity, type, description)과 (source, target, relation) 튜플을 추출
3. 커뮤니티 탐지: 그래프 전체에 Leiden 알고리즘을 적용해 계층적 커뮤니티 구조를 만듦
4. 커뮤니티 요약: 각 커뮤니티에 속한 엔티티와 관계를 LLM에 입력해 자연어 요약 생성

Leiden 알고리즘은 2018년 발표된 커뮤니티 탐지 기법으로, 기존 Louvain 알고리즘이 만들 수 있는 disconnected community 문제를 해결합니다. 그래프의 modularity를 최대화하면서 안정적인 계층 구조를 만들어냅니다.

### 쿼리 단계 (online)

GraphRAG는 두 가지 질의 모드를 제공합니다.

- Local query: 특정 엔티티에 대한 질문. 해당 엔티티의 이웃 엔티티, 관계, 원본 텍스트를 모아 컨텍스트로 사용
- Global query: 전체 corpus에 대한 thematic 질문. 커뮤니티 요약들을 map-reduce 방식으로 통합

Global query 흐름은 다음과 같습니다.

```text
[Query] → [각 community summary와 비교]
        → [community별 부분 답안 생성 (map)]
        → [부분 답안들을 통합 (reduce)]
        → [최종 답]
```

## 동작 원리: 수식과 다이어그램

엔티티 추출은 본질적으로 information extraction 작업입니다. 청크 $c$에서 추출된 엔티티 집합을 $E_c$, 관계 집합을 $R_c$라 하면 전체 그래프는 다음과 같습니다.

$$G = (V, E) = \left(\bigcup_c E_c, \bigcup_c R_c\right)$$

Leiden 알고리즘은 modularity $Q$를 최대화하는 파티션 $P$를 찾습니다.

$$Q = \frac{1}{2m} \sum_{i,j} \left(A_{ij} - \frac{k_i k_j}{2m}\right) \delta(c_i, c_j)$$

여기서 $A$는 인접 행렬, $k_i$는 노드 $i$의 차수, $m$은 총 엣지 수, $\delta$는 같은 커뮤니티에 속하면 1입니다. 결과는 계층적이라서, 작은 커뮤니티들이 모여 더 큰 커뮤니티를 이루는 트리 구조를 얻습니다.

```text
          [Root community]
          /              \
  [Sub-community A]   [Sub-community B]
      /     \             /     \
  [Leaf]  [Leaf]      [Leaf]  [Leaf]
```

각 레벨마다 커뮤니티 요약이 만들어지고, 글로벌 질의는 적절한 레벨의 요약들을 조합합니다.

## 코드 예제

오픈소스 구현체인 `nano-graphrag`로 인덱싱 흐름을 보여드립니다.

```python
from nano_graphrag import GraphRAG, QueryParam

# 1. 그래프 인덱싱
graph_func = GraphRAG(
    working_dir="./graphrag_cache",
    enable_llm_cache=True,
    chunk_token_size=1200,
)

with open("./report.txt") as f:
    graph_func.insert(f.read())

# 2. Local query (특정 엔티티)
local_answer = graph_func.query(
    "삼성전자의 주요 경쟁사는?",
    param=QueryParam(mode="local"),
)

# 3. Global query (theme 전체)
global_answer = graph_func.query(
    "이 보고서들의 공통 위험 요소를 종합 분석해줘",
    param=QueryParam(mode="global"),
)
```

LangChain의 `GraphCypherQAChain`을 Neo4j와 결합하면 직접 Cypher 쿼리를 생성하는 형태도 가능합니다.

```python
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI

graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password",
)

chain = GraphCypherQAChain.from_llm(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    graph=graph,
    verbose=True,
)

result = chain.invoke({
    "query": "A 회사와 거래한 모든 자회사를 찾고, 그 중 2024년 매출이 100억 이상인 곳"
})
```

## LazyGraphRAG: 인덱싱 비용 0.1%

GraphRAG의 가장 큰 약점은 인덱싱 비용입니다. 모든 청크에 대해 LLM으로 엔티티와 관계를 추출하고, 커뮤니티마다 요약을 생성하기 때문에 GPT-4 기준 1GB 코퍼스에 수천 달러가 듭니다. LazyGraphRAG는 이 부담을 제거합니다.

핵심 아이디어는 단순합니다.

- 인덱싱 시점에는 LLM을 거의 호출하지 않습니다. 대신 NLP 라이브러리(spaCy 등)로 noun phrase를 추출해 엔티티 후보로 삼고, 동시 출현(co-occurrence) 관계로 그래프를 만듭니다.
- 커뮤니티 요약은 미리 만들지 않습니다. 쿼리가 들어왔을 때 관련된 커뮤니티만 골라 그 시점에 요약을 생성합니다(on-demand).

벤치마크 결과:

| 항목 | GraphRAG | LazyGraphRAG | 비율 |
|------|----------|--------------|------|
| 인덱싱 LLM cost | $$$ | ~$$ | 0.1% |
| Global query 응답 품질 | baseline | 동등 또는 우수 | - |
| Local query 응답 시간 | 보통 | 약간 느림 | - |

## 실제 케이스: LinkedIn

LinkedIn은 2024년 GraphRAG 기반 고객 서비스 챗봇 사례를 공개했습니다. 사내 도움말 문서, FAQ, 지원 티켓을 그래프로 인덱싱한 결과 응답 시간이 평균 28.6% 단축됐고, 정확도도 개선됐습니다. 핵심은 "왜 내 캠페인이 거절됐나"처럼 여러 정책 문서와 사례를 연결해야 답할 수 있는 질문에서 효과가 컸다는 점입니다.

## vs Standard RAG

같은 코퍼스, 같은 질문에 대한 두 시스템의 행동을 비교합니다.

| 항목 | Standard RAG | GraphRAG |
|------|--------------|----------|
| 인덱싱 단위 | 청크 임베딩 | 엔티티-관계 그래프 |
| 인덱싱 비용 | 낮음 (임베딩만) | 높음 (LLM 호출 다수) |
| 단순 사실 질의 | 우수 | 우수 |
| 멀티홉 추론 | 약함 | 강함 |
| Thematic 글로벌 질의 | 매우 약함 | 매우 강함 |
| 신선도 (incremental update) | 쉬움 | 어려움 |

LazyGraphRAG는 인덱싱 비용 항목에서 Standard RAG에 거의 근접하면서 GraphRAG의 강점을 유지합니다.

## 한계 및 trade-off

- 그래프 품질이 곧 답변 품질입니다. 엔티티 추출이 부정확하면 그래프 전체가 왜곡됩니다.
- 도메인 특수 용어가 많으면 일반 LLM의 추출 능력이 떨어집니다. 도메인별 NER 모델이나 ontology 가이드가 필요할 수 있습니다.
- Incremental update가 까다롭습니다. 새 문서가 들어오면 커뮤니티 구조가 바뀔 수 있어 부분 재계산이 어렵습니다. LazyGraphRAG는 on-demand 요약 덕에 이 부담이 작습니다.
- 정밀한 인용(citation)이 어렵습니다. 답이 여러 커뮤니티 요약을 통합한 결과라서 원문 위치를 가리키기가 단순 RAG보다 까다롭습니다.

## 정리 + 다음 편 예고

GraphRAG는 청크 임베딩 한계를 그래프 구조화로 푸는 패러다임입니다. 멀티홉 추론과 thematic 질의에 압도적이고, LazyGraphRAG가 인덱싱 비용 문제까지 해결했습니다. 그러나 검색 자체의 충분성과 답변의 정합성은 여전히 모델이 자체적으로 판단하지 않습니다. 다음 편에서는 그 부분을 학습으로 풀어낸 Self-RAG를 살펴봅니다. reflection token이라는 작은 신호 하나로 RAG의 인지 능력이 어떻게 달라지는지 보여드립니다.

## 관련 문서

- [[rag-01-evolution-overview|RAG 진화 개요]] - 1편: 시리즈 출발점
- [[rag-03-self-rag|Self-RAG]] - 3편: 자기 검토 RAG
- [[rag-04-agentic-rag|Agentic RAG]] - 4편: 에이전트형 RAG
- [[rag-05-late-chunking-adaptive-routing|Late Chunking과 Adaptive Routing]] - 5편: 청킹 혁신과 동적 라우팅
