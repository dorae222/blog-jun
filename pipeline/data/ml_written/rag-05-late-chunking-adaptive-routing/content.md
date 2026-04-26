<!-- infographic-hero -->
![Late Chunking and Adaptive RAG Routing 핵심 요약](figures/infographic.svg)

*Figure: Late Chunking and Adaptive RAG Routing 한 장 요약 인포그래픽*

# Late Chunking과 Adaptive RAG Routing

> 시리즈 안내: 5편 중 5편 - 청킹 혁신과 동적 파이프라인, 그리고 시리즈 종합

## 개요

[[rag-04-agentic-rag|4편]]까지 우리는 검색 단위(graph), 검색 충분성(self-reflection), 검색 제어(agent)라는 큰 축을 살펴봤습니다. 마지막 편은 두 가지 실용적 보완을 다룹니다.

첫 번째는 Late Chunking입니다. Jina AI가 2024년에 제안한 이 기법은 임베딩 단계에서 청크 컨텍스트 손실을 거의 제거합니다. 두 번째는 Adaptive RAG Routing입니다. 쿼리 복잡도에 따라 vector RAG, GraphRAG, Agentic RAG 중 어느 파이프라인을 쓸지 동적으로 결정합니다. 끝으로 5편 전체를 종합해 2026년 RAG 디자인 가이드를 제시합니다.

## 배경: 시리즈에서 남은 두 가지 갈증

[[rag-01-evolution-overview|1편]]에서 짚은 한계 중 "청킹 컨텍스트 손실"을 GraphRAG가 구조적으로 풀었다면, Late Chunking은 임베딩 자체에서 더 가볍게 풉니다. 한편 [[rag-02-graphrag-lazygraphrag|2편]]부터 [[rag-04-agentic-rag|4편]]까지 다양한 파이프라인을 봤지만, 모든 쿼리에 같은 파이프라인을 쓰는 것은 비효율입니다. 단순 사실 질문에 agentic loop를 돌리는 것은 명백한 낭비고, 멀티홉 질문에 vector RAG를 쓰는 것은 정확도 손실입니다. Adaptive Routing이 이 매칭 문제를 풉니다.

## Part 1. Late Chunking

### 핵심 개념

전통 청킹의 흐름:

```text
[Document] → [Chunk 1, 2, 3, ...] → [각 chunk 독립 임베딩]
```

Late Chunking의 흐름:

```text
[Document]
   ↓ (long-context embedding model)
[Token-level embeddings (전 문서)]
   ↓ (mean pool by chunk boundary)
[Chunk embeddings (컨텍스트 인지)]
```

핵심은 임베딩 모델이 전체 문서를 한 번에 본 뒤, 토큰 임베딩을 청크 경계로 풀링한다는 점입니다. 그래서 50페이지에 등장한 약어가 1페이지의 정의를 인지한 임베딩으로 표현됩니다.

이 기법이 가능한 이유는 long-context embedding model의 등장입니다. jina-embeddings-v3, voyage-3, BGE-M3 같은 모델은 8K-32K 토큰을 한 번에 인코딩할 수 있습니다.

### 동작 원리

문서 $D$의 토큰 시퀀스를 $(t_1, ..., t_n)$이라 하고, 임베딩 모델이 출력하는 토큰 임베딩을 $(e_1, ..., e_n)$이라 합시다. 청크 경계 $[s_k, e_k]$가 주어지면 청크 임베딩은 다음과 같습니다.

$$\bar{e}_k = \frac{1}{e_k - s_k + 1} \sum_{i=s_k}^{e_k} e_i$$

전통 청킹은 각 청크를 독립적으로 입력해 $e_i$가 청크 내부 정보만 반영하는 반면, Late Chunking의 $e_i$는 attention을 통해 문서 전체 정보를 봤기 때문에 컨텍스트가 풍부합니다.

### 코드 예제

Jina API:

```python
import requests

response = requests.post(
    "https://api.jina.ai/v1/embeddings",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={
        "model": "jina-embeddings-v3",
        "task": "retrieval.passage",
        "late_chunking": True,
        "input": [long_document_text],
    },
)
chunk_embeddings = response.json()["data"]
```

`sentence-transformers`로 직접 구현하는 방식:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)

def late_chunking(text: str, chunk_size: int = 512):
    tokenizer = model.tokenizer
    tokens = tokenizer(text, return_offsets_mapping=True, return_tensors="pt")
    input_ids = tokens["input_ids"]
    offsets = tokens["offset_mapping"][0].tolist()

    # 1. 전체 문서 임베딩 (token-level)
    with torch.no_grad():
        outputs = model.auto_model(input_ids=input_ids)
    token_embeds = outputs.last_hidden_state[0]

    # 2. 청크 경계 결정 (단순 fixed-size)
    chunk_embeds = []
    for i in range(0, len(offsets), chunk_size):
        chunk_tokens = token_embeds[i:i + chunk_size]
        chunk_embeds.append(chunk_tokens.mean(dim=0).numpy())

    return np.stack(chunk_embeds)
```

### Late Chunking vs 전통 Chunking 벤치마크

Jina AI의 공개 벤치마크에서 Late Chunking은 다음과 같은 개선을 보였습니다.

| 데이터셋 | Naive Chunking | Late Chunking | 개선 |
|----------|----------------|---------------|------|
| SciFact | 64.2 | 66.1 | +1.9 |
| TRECCOVID | 66.1 | 68.7 | +2.6 |
| FiQA2018 | 33.3 | 33.8 | +0.5 |
| NFCorpus | 23.5 | 29.6 | +6.1 |

긴 문서가 많은 NFCorpus 같은 데이터셋에서 개선이 두드러집니다. 추가 비용은 거의 없습니다(임베딩 한 번 + 풀링).

## Part 2. Adaptive RAG Routing

### 핵심 개념

Adaptive-RAG(Jeong et al., NAACL 2024)는 쿼리 복잡도를 3단계로 분류합니다.

| 복잡도 | 예시 | 적합 파이프라인 |
|--------|------|------------------|
| A. 비-검색 | "안녕하세요" | LLM 직접 응답 |
| B. 단일-step 검색 | "GraphRAG 발표 연도는?" | Standard RAG |
| C. 멀티-step 추론 | "A의 경쟁사 중 매출 1위 기업의 CTO는?" | Multi-hop / GraphRAG / Agentic |

라우팅 모델은 작은 classifier(예: distilbert-base) 또는 LLM zero-shot으로 구현됩니다.

### 라우팅 다이어그램

```text
[Query]
   ↓
[Classifier]
   ├─ class A (no retrieval) ─→ LLM
   ├─ class B (single-step)  ─→ Vector RAG
   └─ class C (multi-step)
         ├─ thematic ─→ GraphRAG
         └─ reasoning ─→ Agentic RAG
                ↓
            [Answer]
```

### 코드 예제

LangGraph로 라우터를 구현합니다.

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class State(TypedDict):
    query: str
    route: Literal["llm_only", "vector_rag", "graph_rag", "agentic_rag"]
    answer: str

def classify(state: State) -> State:
    prompt = f"""
질문 복잡도를 분류:
- llm_only: 일반 상식, 인사, 검색 불필요
- vector_rag: 단일 사실 질의
- graph_rag: 여러 엔티티 관계, thematic
- agentic_rag: 다단계 추론, 도구 필요

질문: {state['query']}
답: (단어만)
"""
    state["route"] = llm.invoke(prompt).content.strip()
    return state

def llm_only(state):
    state["answer"] = llm.invoke(state["query"]).content
    return state

def vector_rag(state):
    docs = vectorstore.similarity_search(state["query"], k=4)
    ctx = "\n".join(d.page_content for d in docs)
    state["answer"] = llm.invoke(
        f"Context:\n{ctx}\nQ:{state['query']}"
    ).content
    return state

def graph_rag(state):
    state["answer"] = graphrag_engine.query(state["query"])
    return state

def agentic_rag(state):
    state["answer"] = agent_app.invoke({
        "messages": [HumanMessage(content=state["query"])]
    })["messages"][-1].content
    return state

graph = StateGraph(State)
graph.add_node("classify", classify)
graph.add_node("llm_only", llm_only)
graph.add_node("vector_rag", vector_rag)
graph.add_node("graph_rag", graph_rag)
graph.add_node("agentic_rag", agentic_rag)
graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify",
    lambda s: s["route"],
    {
        "llm_only": "llm_only",
        "vector_rag": "vector_rag",
        "graph_rag": "graph_rag",
        "agentic_rag": "agentic_rag",
    },
)
for node in ["llm_only", "vector_rag", "graph_rag", "agentic_rag"]:
    graph.add_edge(node, END)
app = graph.compile()
```

### 라우팅 효과

원논문 결과에 따르면 Adaptive-RAG는 단일 파이프라인 대비 다음과 같은 trade-off를 달성합니다.

- 정확도: Multi-hop QA 데이터셋(2WikiMultiHop, MuSiQue)에서 단일 step RAG보다 +5-10% 개선
- 비용: 모든 쿼리에 multi-step을 쓰는 것보다 LLM call 수 30-50% 절감
- Latency: 단순 쿼리는 100-300ms, 복잡 쿼리만 수 초로 분리

## 시리즈 종합: 2026 RAG 디자인 가이드

### 어떤 패턴을 언제 쓰나

다음 의사결정표는 5편을 통합한 가이드입니다.

| 상황 | 권장 패턴 |
|------|-----------|
| 단순 FAQ, 사실 질의 | Standard RAG + Late Chunking |
| 긴 문서가 많음 | Late Chunking 필수 |
| 엔티티 관계, thematic 분석 | GraphRAG 또는 LazyGraphRAG |
| 환각 민감 (의료, 법률) | Self-RAG 또는 CRAG |
| 복잡 작업, 도구 필요 | Agentic RAG (LangGraph) |
| 다양한 쿼리가 섞임 | Adaptive Routing + 여러 파이프라인 |
| Closed-source 모델만 사용 | Agentic RAG + CRAG (학습 불필요) |
| 인덱싱 비용 절감 | LazyGraphRAG, Late Chunking |

### 권장 조합

production에서 자주 쓰이는 조합 두 가지입니다.

조합 1: 비용 효율형
- Late Chunking으로 임베딩
- Adaptive Routing으로 단순/복잡 분리
- 단순 → Vector RAG, 복잡 → Agentic + Web search

조합 2: 정확도 우선형
- 도메인 전문 GraphRAG 인덱싱
- Self-RAG 또는 CRAG로 답변 검증
- 미해결 시 Agentic loop으로 escalate

## 미래 전망: Context Engine

[[rag-01-evolution-overview|1편]]에서 언급한 "Context Engine"이라는 표현은 2026년 현재 업계 컨센서스에 가깝습니다. RAG는 더 이상 단일 검색 파이프라인이 아니라, LLM 작업에 필요한 모든 컨텍스트(문서, 그래프, 메모리, 사용자 프로파일, 도구 결과)를 동적으로 조립하는 엔진의 한 구성 요소입니다.

향후 1-2년 동안 다음 흐름이 가속될 것으로 보입니다.

- Memory + RAG 통합: 대화 메모리, 사용자 선호와 외부 문서를 한 인덱스에서 검색
- Multi-modal RAG: 이미지, 표, 음성을 포함한 통합 임베딩 (ColPali 같은 visual document RAG)
- Continual indexing: 실시간 데이터 흐름을 처리하는 streaming RAG
- Evaluation 자동화: RAGAS, TruLens 등 도구가 production 모니터링 표준이 됨
- 더 작은 specialist 모델: gpt-oss, Qwen3 같은 오픈 모델로 self-hosted RAG가 보편화

## 한계 및 trade-off

- Late Chunking: long-context 임베딩 모델 가용성에 의존, GPU 메모리 부담
- Adaptive Routing: classifier가 잘못 분류하면 결과가 망가짐. 모니터링과 fallback 필수
- 파이프라인 다중 운영: 여러 패턴을 동시에 운영하면 인프라 복잡도가 폭증

## 정리

5편 시리즈를 통해 우리는 Standard RAG의 한계에서 출발해 GraphRAG, Self-RAG, Agentic RAG, Late Chunking, Adaptive Routing까지 살펴봤습니다. 핵심 메시지는 단순합니다.

- "어떤 RAG를 쓰는가"보다 "어떤 컨텍스트가 필요한가"를 먼저 묻기
- 쿼리 다양성에 대응하려면 단일 파이프라인이 아닌 라우팅이 필요
- 비용/정확도/latency의 삼각관계는 패턴 조합으로 풀어야 함

RAG는 이제 정적인 기법이 아니라 살아있는 시스템 설계 영역입니다. 2026년 이후 LLM 애플리케이션의 차별화는 바로 이 Context Engine의 품질에서 결정될 것입니다.

## 관련 문서

- [[rag-01-evolution-overview|RAG 진화 개요]] - 1편: 시리즈 출발점
- [[rag-02-graphrag-lazygraphrag|GraphRAG와 LazyGraphRAG]] - 2편: 지식그래프 기반 검색
- [[rag-03-self-rag|Self-RAG]] - 3편: 자기 검토 RAG
- [[rag-04-agentic-rag|Agentic RAG]] - 4편: 에이전트형 RAG
