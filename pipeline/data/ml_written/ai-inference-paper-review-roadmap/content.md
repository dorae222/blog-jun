<!-- infographic-hero -->
![AI Inference Paper Review Roadmap: PagedAttention, Speculative Decoding, RAG 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: AI Inference Paper Review Roadmap: PagedAttention, Speculative Decoding, RAG 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# AI Inference Paper Review Roadmap: PagedAttention, Speculative Decoding, RAG

논문 리뷰는 모델 이름을 외우는 글이 아니다. 운영에 남는 논문은 대부분 병목을 정확히 이름 붙인다. PagedAttention은 KV cache 메모리 낭비를 OS paging 문제로 해석했고, Speculative Decoding은 자기회귀 decoding의 순차 병목을 draft/target 검증 구조로 바꿨다. RAG 계열 논문은 지식 접근과 답변 생성을 분리했고, AgentBench와 Toolformer는 도구 사용과 agent 평가를 실험 단위로 만들었다.

## 먼저 읽을 논문 리뷰

- [[paged-attention|PagedAttention]]: vLLM을 이해하기 전에 반드시 봐야 하는 메모리 관리 논문이다. KV cache block, block table, continuous batching을 운영 지표와 연결한다.
- [[speculative-decoding|Speculative Decoding]]: DeepSpec이나 draft model 가속을 보기 전에 읽어야 하는 decoding 가속 논문이다.
- [[rag|RAG]]와 [[self-rag|Self-RAG]]: retrieval과 generation을 분리하고, 검색이 충분한지 모델이 판단하는 흐름을 이해한다.
- [[graphrag|GraphRAG]]와 [[ares-rag-eval|ARES]]: RAG가 검색 품질과 평가 체계로 확장되는 지점을 본다.
- [[toolformer|Toolformer]], [[agentbench|AgentBench]], [[swe-agent|SWE-agent]]: tool use와 agent task 평가가 어떻게 논문화됐는지 본다.

## 리뷰할 때 볼 것

첫째, 논문이 해결하는 병목을 한 문장으로 쓴다. 둘째, figure가 실제 시스템의 어느 컴포넌트로 바뀌는지 본다. 셋째, paper metric이 운영 metric과 어떻게 다른지 확인한다. 예를 들어 PagedAttention의 throughput 개선은 운영에서는 TTFT, queue time, KV cache pressure로 다시 쪼개야 한다. Speculative Decoding의 speedup은 acceptance rate와 p95 latency로 다시 검증해야 한다.

## 기존 운영 글과 연결

논문 리뷰는 이론 파트로만 두지 않고 runtime 글과 연결한다. PagedAttention은 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]로 이어지고, Speculative Decoding은 [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]]으로 이어진다. RAG 논문은 [[tei-rag-embedding-rerank|TEI와 RAG 운영]]에서 embedding/rerank/generation 분리로 이어진다. Agent 논문은 [[agent-protocol-stack|에이전트 통신 표준 지도]]와 연결된다.


## 논문 리뷰를 파트로 나누는 기준

논문을 많이 읽는 것보다 중요한 것은 같은 병목을 다루는 논문끼리 묶는 일이다. 이 블로그에서는 AI inference 논문을 네 파트로 나눈다. 첫째, serving memory와 batching. 둘째, decoding acceleration. 셋째, retrieval-augmented generation. 넷째, agent/tool-use evaluation이다.

### 1. Serving memory와 batching

[[paged-attention|PagedAttention]]은 vLLM을 이해하기 위한 핵심 논문이다. KV cache를 block으로 나누고 block table로 매핑한다는 아이디어는 OS paging과 닮았다. 이 논문을 읽을 때는 throughput 숫자만 보지 말고, 기존 시스템의 reserved waste, internal fragmentation, external fragmentation을 어떻게 줄였는지 봐야 한다. 이후 운영 글에서는 이 개념이 KV cache pressure, eviction, prefix cache hit, scheduler queue로 바뀐다.

### 2. Decoding acceleration

[[speculative-decoding|Speculative Decoding]]은 target model의 분포를 보존하면서 draft model을 활용하는 방법을 제시한다. 여기서 중요한 것은 "작은 모델로 빨라진다"가 아니라 accept/reject가 target distribution을 어떻게 유지하는가다. [[deepspec-speculative-decoding|DeepSpec]] 글에서는 이 아이디어가 draft model 훈련과 evaluation pipeline으로 이어진다.

### 3. RAG와 평가

[[rag|RAG]]는 retriever와 generator를 결합하는 출발점이다. [[self-rag|Self-RAG]]는 검색 충분성과 생성 품질을 모델이 스스로 점검하는 방향을 제시하고, [[graphrag|GraphRAG]]는 global question과 community summary 관점으로 확장한다. [[ares-rag-eval|ARES]]는 RAG 평가를 자동화하려는 흐름이다. 운영에서는 이 논문들이 TEI embedding, vector DB, reranker, LLM endpoint, evaluation dataset으로 나뉜다.

### 4. Agent와 tool use

[[toolformer|Toolformer]]는 모델이 도구 사용을 학습하는 관점을 열었고, [[agentbench|AgentBench]]는 LLM을 agent로 평가하는 benchmark 흐름을 만든다. [[swe-agent|SWE-agent]]는 코드 수정 agent를 실제 환경과 연결한다. 이 파트는 MCP/A2A/AG-UI 글과 이어진다. 논문이 tool use를 어떻게 평가했는지와 운영 프로토콜이 tool call을 어떻게 기록하는지를 함께 봐야 한다.

## 논문 리뷰 템플릿

새 논문을 리뷰할 때는 다음 순서를 고정한다.

1. 문제 정의: 어떤 병목이나 실패를 해결하는가.
2. 핵심 아이디어: figure 하나로 설명할 수 있는가.
3. 방법론: 입력, 모델, 알고리즘, system component가 무엇인가.
4. 실험: paper metric과 운영 metric이 어떻게 다른가.
5. 한계: 어떤 traffic, model, 데이터에서는 약해지는가.
6. 운영 연결: 이 논문이 vLLM, TEI, KServe, Gateway, agent protocol 중 어디로 이어지는가.

이 템플릿을 쓰면 논문 리뷰가 단독 지식으로 끝나지 않고, 실제 콘텐츠 파트와 연결된다.

## 이미지와 표지 설계

논문 리뷰 글에서는 원문 figure를 적극적으로 쓰되, 목적을 명확히 나눈다. 표지는 논문 제목과 핵심 아이디어를 보여주는 16:9 커버로 두고, 본문 첫 figure는 논문의 대표 구조도를 쓴다. 단, 논문 figure를 그대로 장식처럼 반복하지 않는다. PagedAttention 글에서는 block table과 KV cache layout figure를 중심으로 두고, 운영 글에서는 이를 재구성한 runtime metric 다이어그램을 쓴다.

Speculative Decoding 글에서는 draft/target 검증 figure가 핵심이다. DeepSpec 같은 후속 글에서는 논문 figure를 그대로 가져오기보다 codebase workflow, evaluation pipeline, acceptance rate 측정 위치를 자체 SVG로 만든다. RAG 글에서는 original RAG architecture figure와 production RAG pipeline SVG를 분리한다. Agent 논문은 benchmark task taxonomy와 tool call trace를 별도 그림으로 만든다.

## 우선순위

우선순위는 운영 영향도 기준으로 둔다. 첫째, vLLM과 직접 연결되는 PagedAttention을 가장 먼저 상세 보강한다. 둘째, DeepSpec과 최신 추론 가속 글을 뒷받침하는 Speculative Decoding을 보강한다. 셋째, TEI/RAG 운영과 연결되는 RAG, Self-RAG, GraphRAG, ARES를 묶어 보강한다. 넷째, MCP/A2A/AG-UI와 이어지는 Toolformer, AgentBench, SWE-agent를 agent protocol 파트와 연결한다.

각 논문 리뷰는 단순 요약이 아니라 "이 논문을 읽은 뒤 어떤 운영 결정을 더 잘 내릴 수 있는가"를 마지막에 남긴다. 예를 들어 PagedAttention은 KV cache와 batching 설정, Speculative Decoding은 draft model 선택과 acceptance metric, RAG는 embedding/rerank/generation 분리, AgentBench는 agent task 평가 설계로 이어져야 한다.

## 다음에 보강할 논문 큐

추론 효율 쪽에서는 PagedAttention 이후 FlashAttention, continuous batching, speculative decoding 계열을 함께 본다. FlashAttention은 training/inference kernel 이해에 가깝고, PagedAttention은 serving memory에 가깝다. 이 둘을 구분하면 GPU 최적화 글과 serving runtime 글을 섞지 않을 수 있다.

모델 계열 쪽에서는 DeepSeek, Qwen, Kimi, GLM 계열 글을 모델 비교로만 끝내지 않는다. 각 모델이 어떤 context length, tool use, code capability, serving cost를 갖는지 보고, 실제 vLLM/TEI/KServe 운영에서 어떤 제약이 생기는지 연결한다. DeepSpec은 codebase와 README workflow 기반 SVG를 만들고, 논문이 있는 경우에는 별도 논문 리뷰로 분리한다.

Agent 쪽에서는 Toolformer, AgentBench, SWE-agent를 MCP/A2A/AG-UI와 연결한다. 논문은 task와 evaluation을 설명하고, 프로토콜 글은 message, tool call, session state, user interaction을 설명한다. 이 둘이 연결되어야 agent 글이 단순 표준 소개가 아니라 평가와 운영까지 이어지는 콘텐츠가 된다.
## 참고 자료

- [PagedAttention paper](https://arxiv.org/abs/2309.06180)
- [Speculative Decoding paper](https://arxiv.org/abs/2211.17192)
- [Retrieval-Augmented Generation paper](https://arxiv.org/abs/2005.11401)
- [ARES RAG evaluation](https://arxiv.org/abs/2311.09476)

![AI Inference Paper Review Roadmap: PagedAttention, Speculative Decoding, RAG 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: AI Inference Paper Review Roadmap: PagedAttention, Speculative Decoding, RAG 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
