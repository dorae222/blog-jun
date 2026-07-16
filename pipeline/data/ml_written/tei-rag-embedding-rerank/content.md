<!-- infographic-hero -->
![TEI Serving Runtime: Embedding, Rerank, Dynamic Batching, Observability 핵심 요약](figures/infographic.svg?v=runtime-tabs-20260706)

*Figure 1: TEI Serving Runtime: Embedding, Rerank, Dynamic Batching, Observability 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# TEI Serving Runtime: Embedding, Rerank, Dynamic Batching, Observability

TEI(Text Embeddings Inference)는 RAG pipeline의 부속 유틸리티가 아니다. 운영 관점에서는 embedding과 rerank를 generation runtime에서 분리해주는 별도 serving runtime이다. vLLM이 token generation을 맡는다면, TEI는 query/document embedding, sequence classification, rerank, batch 처리, Prometheus metric, OpenTelemetry trace를 담당한다.

RAG 장애를 모두 LLM 품질 문제로 처리하면 원인을 놓친다. query embedding이 잘못됐는지, vector index가 오래됐는지, reranker top-k가 너무 큰지, context assembly가 citation을 잃었는지, generation이 hallucination을 냈는지 분리해야 한다. TEI 파트는 이 분리를 가능하게 하는 runtime 기준 글이다.

## TEI의 책임 경계

TEI는 open source text embedding model을 효율적으로 serving하기 위한 도구다. Hugging Face 문서 기준 TEI는 dynamic batching, optimized inference, Safetensors loading, Prometheus metrics, OpenTelemetry tracing 같은 production 기능을 제공한다. 따라서 TEI 글은 "embedding API 하나 띄우기"가 아니라 embedding/rerank endpoint를 운영하는 방법을 다룬다.

첫 번째 contract는 embedding dimension이다. 모델을 바꾸면 vector DB index dimension이 바뀔 수 있고, pooling/normalization 정책이 바뀌면 검색 품질도 달라진다. embedding 모델 버전과 vector index version을 함께 기록하지 않으면, 새 모델을 배포한 뒤 기존 문서와 query가 서로 다른 embedding space에 놓일 수 있다.

두 번째 contract는 rerank top-k다. vector search top-100을 rerank하면 품질은 좋아질 수 있지만 latency와 비용이 늘어난다. top-20만 rerank하면 빠르지만 long-tail answer를 놓칠 수 있다. 그래서 rerank는 API 기능이 아니라 SLA와 품질 지표를 동시에 보는 운영 결정이다.

## Batch와 capacity

Embedding workload는 request/sec보다 token/sec와 batch size가 중요하다. 짧은 query가 많은 서비스와 긴 document가 많은 ingestion job은 같은 TEI endpoint를 쓰더라도 capacity model이 다르다. 온라인 query embedding은 p95 latency가 중요하고, offline document embedding은 throughput과 failure retry가 중요하다. 이 둘을 같은 autoscaling 기준으로 보면 한쪽이 흔들린다.

TEI는 token-based dynamic batching을 제공하므로 max batch tokens, max input length, model size, CPU/GPU 선택을 함께 본다. CPU로 충분한 소형 embedding 모델도 있고, GPU가 필요한 대형 reranker도 있다. air-gapped 환경에서는 모델 weight를 미리 내려받고 volume으로 mount하는 절차까지 운영 문서에 들어가야 한다.

## 관측성

RAG 관측성은 단계별로 쪼개야 한다. `embedding_latency`, `vector_search_latency`, `rerank_latency`, `context_tokens`, `generation_ttft`, `answer_quality`, `citation_coverage`가 같은 request id로 묶여야 한다. TEI가 Prometheus metric과 OpenTelemetry trace를 제공하더라도, application이 stage label을 붙이지 않으면 원인 분석은 어렵다.

실패도 분리한다. retrieval miss는 검색/embedding/index 문제다. rerank 실패는 후보 압축 문제다. generation hallucination은 LLM 문제일 수 있지만 retrieval context가 부실해서 생길 수도 있다. 따라서 TEI dashboard에는 throughput만이 아니라 top-k, sequence length, model version, index version, cache hit가 필요하다.

## TEI 파트에서 파생할 글

| 글 후보 | 다룰 내용 | 연결 글 |
|---|---|---|
| TEI Embedding 운영 | model dimension, batch, index versioning | [[rag|RAG 논문 리뷰]] |
| TEI Rerank 운영 | top-k, cross-encoder latency, quality trade-off | [[ares-rag-eval|ARES RAG 평가]] |
| RAG Observability | retrieval miss와 hallucination 분리 | [[llm-observability-cost|LLM 관측성과 비용]] |
| Air-gapped TEI | weight download, volume mount, private/gated model | Kubernetes/GitOps 글 |
| TEI vs vLLM boundary | embedding/rerank와 generation endpoint 분리 | [[vllm-serving-architecture|vLLM]] |

## 운영 Runbook

검색 결과가 나쁘면 먼저 embedding model과 index version을 확인한다. latency가 나쁘면 embedding batch queue와 rerank top-k를 분리한다. ingestion이 느리면 online query endpoint와 batch embedding job이 같은 리소스를 쓰는지 본다. 답변 citation이 틀리면 retrieval context와 prompt assembly를 확인한다. generation model을 바꾸기 전에 TEI와 vector DB 단계가 정상인지 확인하는 습관이 필요하다.

## 기존 글과 이어서 보기

- RAG 논문 흐름은 [[rag|RAG]]와 [[self-rag|Self-RAG]]에서 본다.
- 평가 흐름은 [[ares-rag-eval|ARES]]로 이어진다.
- generation runtime은 [[vllm-serving-architecture|vLLM]]에서 분리해서 본다.
- 전체 runtime 입구는 [[llm-serving-runtime-stack|LLM Serving Runtime Stack]]에 둔다.

## 참고 자료

- [Text Embeddings Inference documentation](https://huggingface.co/docs/text-embeddings-inference/en/index)
- [TEI Quick Tour](https://huggingface.co/docs/text-embeddings-inference/en/quick_tour)
- [TEI API reference](https://huggingface.github.io/text-embeddings-inference/)

## Index lifecycle과 모델 버전

TEI 운영에서 가장 자주 놓치는 부분은 vector index lifecycle이다. embedding 모델을 바꾸면 기존 document embedding과 새 query embedding이 같은 공간에 있지 않을 수 있다. 이 문제는 API 테스트로는 바로 드러나지 않고, 검색 품질 저하로 나타난다. 그래서 embedding model version, pooling/normalization policy, index version, chunking version을 함께 기록한다.

문서 ingestion pipeline도 운영 단위로 분리한다. online query embedding endpoint와 offline document embedding job이 같은 TEI deployment를 공유하면 ingestion 폭주가 사용자 query latency를 밀어낼 수 있다. production에서는 online과 batch를 별도 deployment로 나누거나 priority queue를 둔다. index rebuild는 rolling 방식으로 새 index를 만들고 traffic을 전환하는 절차가 필요하다.

## Rerank 품질과 latency trade-off

Reranker는 RAG 품질을 크게 올릴 수 있지만, 후보 문서 수와 sequence length에 민감하다. top-100을 rerank하면 latency가 커지고, top-10만 rerank하면 recall이 부족할 수 있다. 운영에서는 rerank top-k를 고정하지 말고 질문 유형, tenant SLA, document domain에 따라 실험한다. 기술 문서 검색과 법무 문서 검색은 필요한 recall과 precision이 다를 수 있다.

품질 평가는 단순 정답률보다 retrieval hit, citation coverage, nDCG, answer groundedness를 함께 본다. TEI rerank latency가 높아져도 final answer 품질이 충분히 좋아지지 않는다면 top-k나 model을 바꿔야 한다. 반대로 generation hallucination으로 보이는 문제가 실제로는 retrieval miss라면 LLM 교체보다 embedding/rerank 재설계가 먼저다.

## Cache와 개인정보

Embedding cache는 비용을 줄이지만 query에 민감한 정보가 들어갈 수 있다. cache key를 raw query로 둘지, normalized/hash된 query로 둘지, tenant isolation을 어떻게 보장할지 정해야 한다. document embedding cache도 문서 삭제/수정과 연결되어야 한다. 문서가 삭제됐는데 cache와 index에 남아 있으면 RAG는 오래된 내용을 계속 반환할 수 있다.

TEI 파트의 운영 기준은 결국 "검색 실패와 생성 실패를 분리할 수 있는가"다. 이 분리가 되면 RAG 품질 개선은 모델 교체가 아니라 pipeline 단계별 개선으로 바뀐다.

## 실제로 분리해서 쓸 하위 목차

TEI 탭은 embedding과 rerank를 한 글에만 두면 부족하다. 첫째, TEI 기본 운영 글에서는 image, model loading, CPU/GPU 선택, endpoint contract를 다룬다. 둘째, embedding 글에서는 dimension, pooling, normalization, index versioning, chunking 전략을 다룬다. 셋째, rerank 글에서는 cross-encoder latency, top-k tuning, quality/latency trade-off를 다룬다. 넷째, RAG pipeline 글에서는 TEI, vector DB, reranker, vLLM generation을 end-to-end로 연결한다. 다섯째, observability 글에서는 Prometheus, OTel, retrieval miss, citation coverage, answer groundedness를 묶는다. 여섯째, ingestion 글에서는 offline document embedding job과 online query endpoint를 분리한다.

이 목차를 따르면 TEI는 "RAG에서 쓰는 embedding 서버"가 아니라 검색 품질과 latency를 책임지는 독립 runtime 파트가 된다. 특히 모델 교체, index rebuild, cache invalidation은 별도 운영 절차로 써야 한다.

## 운영 문서 최소 구성

이 runtime 파트의 모든 후속 글은 같은 형식을 따른다. 먼저 어떤 request path를 책임지는지 한 문장으로 정의한다. 다음으로 배포 단위, 설정값, metric, 장애 증상, rollback 단위를 표로 적는다. 마지막에는 "이 runtime이 맡지 않는 책임"을 명시한다. 이 경계가 있어야 vLLM, TEI, KServe, Ray Serve가 서로 섞이지 않고 독립 탭처럼 쌓인다.

![TEI Serving Runtime: Embedding, Rerank, Dynamic Batching, Observability 운영 구조](figures/architecture.svg?v=runtime-tabs-20260706)

*Figure 2: TEI Serving Runtime: Embedding, Rerank, Dynamic Batching, Observability 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
