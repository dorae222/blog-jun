<!-- infographic-hero -->
![LLM Serving Runtime 목차: vLLM, TEI, KServe, Ray Serve 핵심 요약](figures/infographic.svg?v=part-hubs-20260706)

*Figure 1: LLM Serving Runtime 목차: vLLM, TEI, KServe, Ray Serve 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# LLM Serving Runtime 목차: vLLM, TEI, KServe, Ray Serve

LLM serving runtime은 한 글에 담을 수 있는 주제가 아니다. vLLM, TEI, KServe, Ray Serve는 이름만 나란히 놓으면 같은 계층처럼 보이지만 실제 책임은 다르다. vLLM은 token generation engine이고, TEI는 embedding/rerank serving runtime이다. KServe는 Kubernetes-native model lifecycle control plane이고, Ray Serve는 Python-native serving graph다.

이 글은 runtime 묶음 글을 없애고, 각 runtime을 독립 탭으로 읽게 만드는 허브다. 앞으로 runtime 글은 이 글 아래에 계속 추가한다.

## 하위 파트 1: vLLM

[[vllm-serving-architecture|vLLM Serving Runtime]]은 scheduler, KV cache, prefix caching, structured output, speculative decoding을 다룬다. 후속 글은 `vLLM 설치와 OpenAI API`, `PagedAttention/KV cache`, `Prefix caching`, `Structured output/tool calling`, `Speculative decoding`, `Disaggregated prefill`, `vLLM benchmark와 운영 runbook`으로 나눈다.

## 하위 파트 2: TEI

[[tei-rag-embedding-rerank|TEI Serving Runtime]]은 RAG의 embedding/rerank path를 generation runtime과 분리한다. 후속 글은 `TEI embedding 운영`, `TEI rerank 운영`, `index versioning`, `RAG observability`, `offline ingestion과 online query 분리`, `TEI cache와 개인정보`로 나눈다.

## 하위 파트 3: KServe

[[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]는 Kubernetes CRD와 controller로 model lifecycle을 관리한다. 후속 글은 `KServe 설치 계층`, `LLMInferenceService spec`, `storage initializer`, `Gateway/Scheduler`, `ArgoCD custom health`, `multi-node serving`으로 나눈다.

## 하위 파트 4: Ray Serve

[[ray-serve-llm-deep-dive|Ray Serve LLM]]은 Python graph와 Ray actor를 중심으로 LLM application을 운영한다. 후속 글은 `Ray Serve 기본`, `Ray Serve LLM with vLLM`, `serving graph 설계`, `KubeRay 운영`, `autoscaling`, `Ray dashboard와 stage latency`로 나눈다.

## 선택표

| 필요 | 먼저 볼 파트 |
|---|---|
| chat/completion token generation | [[vllm-serving-architecture|vLLM]] |
| RAG embedding/rerank 분리 | [[tei-rag-embedding-rerank|TEI]] |
| Kubernetes CRD/GitOps model lifecycle | [[kserve-llminferenceservice-deep-dive|KServe]] |
| Python multi-stage serving graph | [[ray-serve-llm-deep-dive|Ray Serve]] |
| 전체 비용/지연/품질 대시보드 | [[llm-observability-cost|LLM 관측성과 비용]] |

## 참고 자료

- [vLLM documentation](https://docs.vllm.ai/)
- [Text Embeddings Inference documentation](https://huggingface.co/docs/text-embeddings-inference/en/index)
- [KServe LLMInferenceService](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview)
- [Ray Serve LLM](https://docs.ray.io/en/latest/serve/llm/index.html)

## 파트 안의 파트 설계

Runtime 대분류는 `engine`, `embedding/rerank`, `control plane`, `serving graph`, `observability`로 나눈다. vLLM은 engine 파트이고, TEI는 embedding/rerank 파트다. KServe는 Kubernetes control plane이며, Ray Serve는 Python serving graph다. LLM 관측성과 비용은 이 네 축을 가로지르는 공통 파트다.

| 깊이 | 예시 목차 | 작성 기준 |
|---|---|---|
| 대분류 | LLM Serving Runtime | request 유형별 runtime 선택 |
| 하위 파트 | vLLM, TEI, KServe, Ray Serve | 각 runtime의 책임 경계 |
| 세부 파트 | KV cache, rerank, CRD, graph, autoscaling | 설정과 metric 중심 |
| 실전 글 | benchmark, dashboard, rollback, runbook | 운영 증거와 장애 대응 포함 |

## 완성 기준

runtime 글은 기능 목록이 아니라 request path를 설명해야 한다. 어떤 요청이 들어와 어떤 queue, cache, controller, actor, route를 지나가는지 보여야 한다. 또한 각 runtime이 맡지 않는 책임도 써야 한다. 그래야 vLLM과 KServe, TEI와 vLLM, Ray Serve와 Kubernetes의 경계가 섞이지 않는다.

![LLM Serving Runtime 목차: vLLM, TEI, KServe, Ray Serve 구조도](figures/architecture.svg?v=part-hubs-20260706)

*Figure 2: LLM Serving Runtime 목차: vLLM, TEI, KServe, Ray Serve 하위 파트 구조도. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
