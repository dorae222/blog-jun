<!-- infographic-hero -->
![Self-RAG: Self-Reflective Retrieval 핵심 요약](figures/infographic.svg)

*Figure: Self-RAG: Self-Reflective Retrieval 한 장 요약 인포그래픽*

# Self-RAG: 검색 충분성을 자기 검토하는 RAG

> 시리즈 안내: 5편 중 3편 - 모델이 스스로 검색을 판단하고 평가하는 RAG

## 개요

[[rag-02-graphrag-lazygraphrag|2편]]에서 다룬 GraphRAG는 검색 단위를 청크에서 그래프로 옮겨 컨텍스트 손실을 줄였습니다. 그러나 Standard RAG의 또 다른 핵심 한계인 "검색이 충분한지 모른다"는 문제는 여전히 남아 있습니다. 검색이 부족한데 답을 만들면 환각이 생기고, 검색이 필요 없는 질문에도 검색을 돌리면 비용과 latency가 낭비됩니다.

Self-RAG(Asai et al., ICLR 2024)는 이 문제를 학습으로 해결합니다. 모델이 4가지 reflection token을 출력하면서 retrieval 필요성, 검색 결과 관련성, 답변의 근거 정도, 답변의 유용성을 스스로 평가합니다. 이 편에서는 reflection token의 의미, 학습 파이프라인, 추론 동작, 그리고 후속 발전인 CRAG와 DRAGIN까지 정리합니다.

## 배경: 왜 자기 검토인가

전통 RAG의 흐름을 다시 보면 retrieval과 generation이 두 개의 독립 모듈입니다. retriever는 자신이 가져온 결과가 좋은지 모르고, generator는 받은 컨텍스트가 답에 적절한지 평가하지 않습니다. 그 결과 다음 두 가지 실패 모드가 흔합니다.

- 불필요한 검색: "안녕"이라는 인사에도 벡터 DB를 뒤지고 어색한 컨텍스트를 답에 붙임
- 부적절한 검색 신뢰: 검색 결과가 질문과 어긋나는데도 그것을 근거로 답을 만들어 환각 발생

Self-RAG는 모델이 생성 과정에서 reflection token을 출력하게 학습시킵니다. 인간이 검토하듯, 모델이 자기 출력을 메타 평가하는 것입니다.

## 핵심 개념: 4가지 Reflection Token

Self-RAG는 vocabulary에 4종류의 특수 토큰을 추가합니다.

| 토큰 | 의미 | 출현 위치 |
|------|------|-----------|
| [Retrieve] | 지금 검색이 필요한가 | 생성 전후 |
| [IsRel] | 검색된 패시지가 관련 있는가 | 패시지마다 |
| [IsSup] | 답변이 패시지로 충분히 뒷받침되는가 | 답변마다 |
| [IsUse] | 답변이 사용자에게 유용한가 | 최종 답에 |

각 토큰은 다시 등급으로 갈라집니다. 예를 들어 [IsRel]은 `Relevant` / `Irrelevant` 두 값을, [IsSup]은 `Fully supported` / `Partially supported` / `No support` 세 값을 가집니다. [Retrieve]는 `Yes` / `No` / `Continue`(이전 검색을 재사용) 세 값을 가집니다.

## 동작 원리

### 학습 파이프라인

Self-RAG의 학습은 두 단계로 진행됩니다.

```text
Step 1. Critic 학습
  GPT-4로 (query, passage, answer)에 reflection token 라벨 부여
  → 작은 critic model을 supervised로 fine-tune

Step 2. Generator 학습
  Critic으로 학습 corpus에 reflection token 자동 라벨링
  → 단일 LM이 reflection token까지 next-token으로 예측하도록 학습
```

이 구조의 미덕은 추론 시점에 critic이 별도로 호출되지 않는다는 점입니다. Generator 하나가 reflection token을 직접 출력합니다. 결과적으로 latency 증가가 작습니다.

### 추론 흐름

쿼리 $q$가 들어오면 Self-RAG는 다음 절차를 따릅니다.

```text
1. [Retrieve] 토큰 예측
   - "No"면 검색 없이 바로 답 생성
   - "Yes"면 retriever 호출

2. 검색된 각 패시지 p_i에 대해 병렬로:
   2a. [IsRel] 평가 (관련 없으면 버림)
   2b. p_i 컨텍스트로 답 후보 y_i 생성
   2c. y_i에 [IsSup], [IsUse] 토큰 부여

3. 후보 답안 (y_1, ..., y_k) 중 reflection token 점수가 가장 높은 것 선택
```

이 과정에서 가중치 $w$를 활용해 다양한 정책을 만들 수 있습니다.

$$\text{score}(y_i) = w_{rel} \cdot s_{IsRel} + w_{sup} \cdot s_{IsSup} + w_{use} \cdot s_{IsUse}$$

예를 들어 의료 도메인에서는 $w_{sup}$를 높여 근거가 약한 답을 페널티 주고, 창의적 글쓰기에서는 $w_{use}$를 높여 다양성을 살립니다.

## 코드 예제

HuggingFace에 공개된 selfrag/selfrag_llama2 모델을 사용한 추론입니다.

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("selfrag/selfrag_llama2_7b")
model = AutoModelForCausalLM.from_pretrained(
    "selfrag/selfrag_llama2_7b",
    device_map="auto",
)

def selfrag_generate(query: str, retriever) -> str:
    prompt = f"### Instruction:\n{query}\n\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=10)
    pred = tokenizer.decode(out[0], skip_special_tokens=False)

    if "[Retrieve=Yes]" in pred:
        passages = retriever.retrieve(query, k=5)
        candidates = []
        for p in passages:
            ctx = f"[Retrieval]<paragraph>{p}</paragraph>"
            full_prompt = prompt + ctx
            full = model.generate(
                **tokenizer(full_prompt, return_tensors="pt").to(model.device),
                max_new_tokens=200,
            )
            decoded = tokenizer.decode(full[0], skip_special_tokens=False)
            candidates.append(decoded)
        # reflection token 점수로 선택 (실제는 token logprob을 종합)
        return select_best(candidates)
    else:
        full = model.generate(
            **inputs, max_new_tokens=200,
        )
        return tokenizer.decode(full[0], skip_special_tokens=True)
```

LangGraph로 Self-RAG 패턴을 처음부터 구현하는 방식도 자주 쓰입니다.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class State(TypedDict):
    query: str
    docs: List[str]
    answer: str
    needs_retrieval: bool

def decide_retrieval(state):
    prompt = f"이 질문에 검색이 필요한가? Yes/No\n{state['query']}"
    state["needs_retrieval"] = "yes" in llm.invoke(prompt).content.lower()
    return state

def retrieve(state):
    state["docs"] = vectorstore.similarity_search(state["query"], k=5)
    return state

def grade_docs(state):
    state["docs"] = [
        d for d in state["docs"]
        if "yes" in llm.invoke(
            f"관련 있는가?\n{d}\nQ:{state['query']}"
        ).content.lower()
    ]
    return state

def generate(state):
    ctx = "\n".join(d.page_content for d in state["docs"])
    state["answer"] = llm.invoke(
        f"Context:\n{ctx}\nQ:{state['query']}"
    ).content
    return state

graph = StateGraph(State)
graph.add_node("decide", decide_retrieval)
graph.add_node("retrieve", retrieve)
graph.add_node("grade", grade_docs)
graph.add_node("generate", generate)
graph.set_entry_point("decide")
graph.add_conditional_edges(
    "decide",
    lambda s: "retrieve" if s["needs_retrieval"] else "generate",
)
graph.add_edge("retrieve", "grade")
graph.add_edge("grade", "generate")
graph.add_edge("generate", END)
app = graph.compile()
```

## 벤치마크 결과

원논문의 주요 결과를 정리합니다(Llama2-7B/13B 기반).

| 데이터셋 | Standard RAG | Self-RAG-7B | Self-RAG-13B |
|----------|--------------|-------------|--------------|
| PubHealth (사실 검증) | 49.8 | 72.4 | 75.1 |
| ARC-Challenge (추론) | 43.3 | 67.3 | 73.1 |
| Bio (생성 정확도) | 40.7 | 81.2 | 83.7 |
| ASQA (citation 정확도) | 25.5 | 30.0 | 31.7 |

특히 citation 정확도와 환각률 감소가 두드러집니다. 답이 출처 패시지와 정합한지를 [IsSup] 토큰으로 학습했기 때문입니다.

## vs Standard RAG / GraphRAG

| 항목 | Standard RAG | Self-RAG | GraphRAG |
|------|--------------|----------|----------|
| 검색 필요성 판단 | 무조건 검색 | 학습된 토큰으로 판단 | 무조건 검색 |
| 검색 결과 평가 | 없음 | [IsRel], [IsSup] | community 점수 |
| 학습 비용 | 없음 | critic + generator 학습 | 인덱싱 LLM 비용 |
| 추론 latency | 낮음 | 약간 증가 | 보통 |
| 환각 감소 | 보통 | 강함 | 보통 |

## 한계 및 trade-off

- 학습 비용: critic 모델과 generator 모두 학습이 필요합니다. 데이터 라벨링에 GPT-4 호출이 대량 발생합니다.
- Critic 품질 의존: critic이 잘못된 라벨을 만들면 generator의 reflection도 왜곡됩니다.
- Closed-source 모델 적용 불가: GPT-4, Claude 같은 호스팅 모델에는 적용할 수 없습니다(추가 학습 불가).
- 도메인 적응: 일반 도메인으로 학습된 critic은 의료, 법률 같은 특수 도메인에서 정확도가 떨어집니다.

## 후속 발전: CRAG와 DRAGIN

Self-RAG의 아이디어는 빠르게 확장됐습니다.

### CRAG (Corrective RAG, 2024)

Self-RAG처럼 검색 결과를 평가하지만, 평가 결과에 따라 보정 행동을 합니다.

- Correct: 그대로 사용
- Incorrect: 웹 검색으로 새 문서 확보
- Ambiguous: 둘 다 사용

추가 학습 없이 prompt + 작은 evaluator로 동작해 closed-source 모델에도 적용 가능합니다.

### DRAGIN (Dynamic Retrieval, 2024)

생성 도중 매 토큰의 불확실성(token entropy)을 모니터링해, 임계값을 넘으면 그 시점에 retrieval을 트리거합니다. 긴 답변을 생성할 때 중간에 새로운 정보가 필요한 상황에서 강력합니다.

## 정리 + 다음 편 예고

Self-RAG는 검색 충분성 인식이라는 Standard RAG의 본질적 한계를 reflection token으로 풀었습니다. 학습 비용은 들지만, 환각 감소와 비용 절감을 동시에 달성합니다. 그런데 reflection도 결국 단일 LLM 안에서 일어납니다. 더 적극적으로 retrieval을 도구처럼 다루고, 여러 단계의 의사결정을 거쳐 답을 만들 수는 없을까요. 다음 편에서는 그 답인 Agentic RAG를 다룹니다. LangGraph로 multi-agent 패턴을 구현하면서, retrieval이 어떻게 LLM의 도구 중 하나로 변하는지 보여드립니다.

## 관련 문서

- [[rag-01-evolution-overview|RAG 진화 개요]] - 1편: 시리즈 출발점
- [[rag-02-graphrag-lazygraphrag|GraphRAG와 LazyGraphRAG]] - 2편: 지식그래프 기반 검색
- [[rag-04-agentic-rag|Agentic RAG]] - 4편: 에이전트형 RAG
- [[rag-05-late-chunking-adaptive-routing|Late Chunking과 Adaptive Routing]] - 5편: 청킹 혁신과 동적 라우팅
