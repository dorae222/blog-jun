<!-- infographic-hero -->
![RAG Evolution Overview 핵심 요약](figures/infographic.svg)

*Figure: RAG Evolution Overview 한 장 요약 인포그래픽*

# RAG 진화: Standard에서 Beyond까지

> 시리즈 안내: 5편 중 1편 - RAG 진화의 큰 그림과 로드맵

## 개요

2020년 Lewis et al.이 제안한 Retrieval-Augmented Generation(RAG)은 LLM의 두 가지 고질병인 환각(hallucination)과 지식 컷오프(knowledge cutoff)를 동시에 해결하는 우아한 방법이었습니다. 외부 문서를 청킹하고, 임베딩으로 변환해 벡터 DB에 저장한 뒤, 쿼리와 가장 유사한 청크를 찾아 LLM의 컨텍스트로 주입한다는 단순한 아이디어가 ChatGPT 시대의 표준이 됐습니다.

그러나 2024년을 지나며 Standard RAG의 한계가 명확해졌습니다. "왜 우리 챗봇은 사내 문서가 다 들어있는데도 엉뚱한 답을 내놓을까?"라는 질문이 모든 팀에서 반복됐고, 2025년에는 GraphRAG, Self-RAG, Agentic RAG 등 새로운 패러다임이 쏟아졌습니다. 이 시리즈는 그 진화의 흐름을 5편으로 정리합니다. 첫 편에서는 전체 지도를 그립니다.

## Standard RAG의 3가지 구조적 한계

### 한계 1: 청킹이 컨텍스트를 절단한다

전통 RAG의 첫 단계는 문서를 500-1000 토큰 단위로 자르는 것입니다. 그런데 임베딩 모델은 각 청크를 독립적으로 인코딩하기 때문에, "그 회사", "위 표에서 보듯이" 같은 지시 표현(anaphora)이 등장하는 청크는 원래 의미를 잃어버립니다. 한 보고서에서 1페이지에 정의된 약어가 50페이지에서 등장하면, 50페이지 청크의 임베딩은 약어의 의미를 모릅니다.

### 한계 2: 단일 retrieval pass

Standard RAG는 쿼리 한 번 → 검색 한 번 → 생성 한 번이라는 선형 구조를 따릅니다. 검색 결과가 부족하거나 어긋나도 보정할 기회가 없습니다. 사용자가 "2024년 매출과 2025년 전망을 비교해줘"라고 물으면 두 기간을 각각 검색해야 하지만, 단일 임베딩으로는 한쪽만 가져올 가능성이 큽니다.

### 한계 3: 검색 충분성을 모른다

가장 본질적인 문제입니다. RAG는 검색이 잘됐는지, 더 찾아야 하는지, 아예 검색이 필요 없는 질문인지 구분하지 못합니다. "안녕하세요"라는 인사에도 벡터 DB를 뒤지고, 답이 문서에 없는데도 어떻게든 답을 만들어냅니다.

## 진화의 5가지 방향

이 한계들에 대응해 등장한 5가지 진화 방향을 표로 정리합니다.

| 방향 | 대표 기법 | 해결하는 문제 | 시리즈 |
|------|-----------|---------------|--------|
| 그래프 기반 | GraphRAG, LazyGraphRAG | 멀티홉 추론, thematic 질의 | 2편 |
| 자기 검토 | Self-RAG, CRAG | 검색 충분성 판단, 환각 감소 | 3편 |
| 에이전트화 | Agentic RAG, ReAct + RAG | 복잡 쿼리 분해, 도구 활용 | 4편 |
| Late Chunking | Jina Late Chunking | 청크 컨텍스트 손실 | 5편 |
| 적응형 라우팅 | Adaptive-RAG | 쿼리별 파이프라인 선택 | 5편 |

### 방향 1: 그래프 기반 (Graph-based)

문서를 청크가 아닌 엔티티-관계 그래프로 표현합니다. Microsoft GraphRAG는 LLM으로 엔티티를 추출하고 Leiden 알고리즘으로 커뮤니티를 찾은 뒤, 각 커뮤니티의 요약을 미리 만들어 둡니다. "이 회사의 핵심 인물 네트워크는?" 같은 글로벌 질의에서 강력합니다.

### 방향 2: 자기 검토 (Self-reflective)

LLM이 [Retrieve], [IsRel], [IsSup], [IsUse] 같은 reflection token을 통해 검색 결과의 관련성과 충분성을 스스로 평가합니다. 검색이 필요 없는 질문은 패스하고, 검색이 부족하면 다시 검색합니다.

### 방향 3: 에이전트화 (Agentic)

retrieval을 도구(tool) 중 하나로 취급합니다. LLM이 쿼리를 재작성하고, 여러 sub-query로 분해하고, 검색 결과를 보고 다음 행동을 결정합니다. LangGraph, LlamaIndex Workflows가 대표 프레임워크입니다.

### 방향 4: Late Chunking

청크별로 임베딩하는 대신 전체 문서를 long-context 임베딩 모델에 통과시킨 뒤, 토큰 수준 출력을 청크 경계로 풀링합니다. 청크가 문서 전체의 컨텍스트를 인지한 임베딩을 가집니다.

### 방향 5: 적응형 라우팅

모든 쿼리에 같은 RAG 파이프라인을 쓰지 않습니다. 단순 사실 질의는 vector RAG, 멀티홉은 graph RAG, 추론 필요는 agentic RAG로 동적 라우팅합니다.

## 동작 원리: Standard RAG vs Beyond

Standard RAG의 데이터 흐름을 텍스트 다이어그램으로 그리면 다음과 같습니다.

```text
[Document] → [Chunk] → [Embed] → [Vector DB]
                                      ↓
[Query] → [Embed] → [Top-k Retrieve] → [LLM] → [Answer]
```

Beyond RAG는 여기에 분기와 루프가 추가됩니다.

```text
[Query] → [Router] ─┬─ Simple → Standard RAG
                    ├─ Multi-hop → GraphRAG
                    └─ Complex → Agentic Loop
                                   ↓
                            [Plan → Retrieve → Critic]
                                   ↓ (insufficient)
                            [Re-plan → Retrieve again]
                                   ↓
                                [Answer]
```

## 코드로 보는 차이

Standard RAG의 골격을 LangChain으로 표현하면 다음과 같습니다.

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 청킹과 인덱싱
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
chunks = splitter.split_documents(documents)
vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())

# 2. 검색과 생성 (단일 pass)
def standard_rag(query: str) -> str:
    docs = vectorstore.similarity_search(query, k=4)
    context = "\n\n".join(d.page_content for d in docs)
    llm = ChatOpenAI(model="gpt-4o-mini")
    return llm.invoke(
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    ).content
```

Self-RAG 스타일로 확장하면 reflection 단계가 추가됩니다.

```python
def self_rag(query: str) -> str:
    # 1. 검색 필요성 판단
    needs_retrieval = llm.invoke(
        f"Does this query need retrieval? {query}"
    ).content.lower().startswith("yes")

    if not needs_retrieval:
        return llm.invoke(query).content

    # 2. 검색 + 관련성 평가
    docs = vectorstore.similarity_search(query, k=4)
    relevant = [
        d for d in docs
        if "yes" in llm.invoke(
            f"Is this relevant?\n{d.page_content}\nQ:{query}"
        ).content.lower()
    ]

    # 3. 컨텍스트로 답 생성 + 자기 검토
    answer = llm.invoke(
        f"Context: {relevant}\nQ: {query}"
    ).content
    return answer
```

이 단순한 비교만으로도 RAG가 더 이상 "벡터 검색"에 머물지 않는다는 것이 보입니다.

## 2026 트렌드: RAG에서 Context Engine으로

2026년 현재 업계 담론은 "RAG"라는 용어를 넘어서고 있습니다. Anthropic, OpenAI, LangChain의 엔지니어링 블로그에서는 "Context Engineering"이라는 표현이 자리잡았습니다. 단순히 문서를 검색하는 것이 아니라, LLM이 작업을 수행하는 데 필요한 모든 컨텍스트(과거 대화, 사용자 프로파일, 도구 사용 결과, 외부 문서, 그래프, 메모리)를 동적으로 조립하는 엔진을 만드는 것이 목표입니다.

이 관점에서 보면 5가지 진화 방향은 모두 같은 방향을 가리킵니다. 컨텍스트의 품질, 적시성, 관련성을 높이는 것입니다. GraphRAG는 구조적 컨텍스트를, Self-RAG는 검증된 컨텍스트를, Agentic RAG는 동적으로 수집된 컨텍스트를 제공합니다.

## 한계 및 trade-off

각 방향은 만능이 아닙니다.

- 그래프 기반: 인덱싱 비용이 높음(LazyGraphRAG로 완화)
- 자기 검토: critic 학습 비용, 추론 latency 증가
- 에이전트화: multiple LLM call로 비용 폭증
- Late Chunking: long-context 임베딩 모델 필수
- 라우팅: classifier 품질에 의존

따라서 실무에서는 하나만 쓰는 것이 아니라 조합합니다. "vector RAG + agentic loop"나 "GraphRAG + self-reflection" 같은 하이브리드가 일반적입니다.

## 시리즈 로드맵

- 2편 [[rag-02-graphrag-lazygraphrag|GraphRAG와 LazyGraphRAG]]: Microsoft의 그래프 기반 접근
- 3편 [[rag-03-self-rag|Self-RAG]]: reflection token으로 자기 검토
- 4편 [[rag-04-agentic-rag|Agentic RAG]]: LLM이 retrieval을 제어
- 5편 [[rag-05-late-chunking-adaptive-routing|Late Chunking과 Adaptive Routing]]: 청크 컨텍스트 보존과 동적 파이프라인

## 정리 + 다음 편 예고

Standard RAG의 한계는 청킹의 컨텍스트 손실, 단일 retrieval, 충분성 인식 부재였습니다. 이 문제들을 풀기 위해 그래프, 자기 검토, 에이전트, late chunking, 적응형 라우팅이라는 5가지 진화 방향이 등장했습니다. 다음 편에서는 그 첫 번째인 GraphRAG와 LazyGraphRAG를 깊이 있게 다룹니다. 청크 임베딩에서 지식 그래프로 패러다임을 옮기면 어떤 일이 가능해지는지, 그리고 그 비용을 어떻게 1000분의 1로 줄였는지 살펴봅니다.

## 관련 문서

- [[rag-02-graphrag-lazygraphrag|GraphRAG와 LazyGraphRAG]] - 2편: 지식그래프 기반 검색
- [[rag-03-self-rag|Self-RAG]] - 3편: 자기 검토 RAG
- [[rag-04-agentic-rag|Agentic RAG]] - 4편: 에이전트형 RAG
- [[rag-05-late-chunking-adaptive-routing|Late Chunking과 Adaptive Routing]] - 5편: 청킹 혁신과 동적 라우팅
