<!-- infographic-hero -->
![모델/추론 연구 목차: 최신 모델, 추론 가속, 논문 리뷰 핵심 요약](figures/infographic.svg?v=part-hubs-20260706)

*Figure 1: 모델/추론 연구 목차: 최신 모델, 추론 가속, 논문 리뷰 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# 모델/추론 연구 목차: 최신 모델, 추론 가속, 논문 리뷰

`AI 모델 서빙 플랫폼 전체 그림` 같은 한 장짜리 지도는 빠른 입구로는 좋지만, 모델/추론 연구를 담기에는 너무 좁다. 최신 모델은 매달 바뀌고, 추론 가속 알고리즘은 논문과 구현이 따로 움직이며, 실제 운영에서는 latency, cost, quality, safety가 함께 붙는다. 그래서 이 글은 모델/추론 연구 대분류의 허브로 둔다.

## 하위 파트 1: 최신 모델 흐름

최신 모델 글은 단순 발표 뉴스가 아니라 운영 의사결정 카드여야 한다. GLM, Qwen, Kimi, DeepSeek 계열을 볼 때는 parameter 수보다 context length, output length, tool use, code capability, license, serving requirement, quantization 지원, tokenizer, vLLM 호환성을 먼저 본다. [[latest-open-models-glm-deepspec-qwen-kimi|최신 오픈 모델 흐름]]은 이 파트의 시작점이고, 이후에는 모델별 profile 글을 쌓는다.

모델 profile 글의 목차는 고정한다. 첫째, 어떤 use case에 맞는가. 둘째, serving runtime에서 어떤 제약이 있는가. 셋째, benchmark 숫자를 어떤 방식으로 해석해야 하는가. 넷째, 실제 배포 시 비용과 latency가 어떻게 달라지는가. 이 형식이 있으면 모델 글이 단순 소개가 아니라 운영 판단 자료가 된다.

## 하위 파트 2: 추론 가속 알고리즘

추론 가속은 하나의 글로 묶기 어렵다. [[speculative-decoding|Speculative Decoding]]은 draft model과 target model 검증 구조를 다루고, [[deepspec-speculative-decoding|DeepSpec]]은 codebase와 workflow 관점으로 이어진다. PagedAttention은 memory management이고, prefix caching은 prompt reuse이며, disaggregated prefill은 prefill/decode phase 분리다. 이들은 모두 "빠르게 한다"는 공통점은 있지만 병목이 다르다.

이 파트의 후속 목차는 `Speculative Decoding`, `DeepSpec`, `EAGLE 계열`, `Prefix/Prompt cache`, `Disaggregated prefill`, `Serving benchmark 설계`로 나눈다. 각 글은 알고리즘 설명, 핵심 figure, 실험 metric, vLLM/KServe/Ray 적용 지점을 반드시 포함한다.

## 하위 파트 3: 논문 리뷰와 운영 연결

논문 리뷰는 별도 지식 창고가 아니라 운영 글의 근거다. [[paged-attention|PagedAttention]]은 vLLM KV cache로 연결되고, [[rag|RAG]]는 TEI embedding/rerank 분리로 연결된다. AgentBench, Toolformer, SWE-agent는 MCP/A2A/AG-UI 같은 agent protocol 글과 연결된다. 논문 원본 figure는 논문 리뷰 글에서 쓰고, 운영 글에서는 자체 SVG로 재구성한다.

## 작성 대기열

| 우선순위 | 글 후보 | 연결 글 |
|---|---|---|
| P0 | GLM/Qwen/Kimi/DeepSeek 모델 카드 비교 | [[latest-open-models-glm-deepspec-qwen-kimi|최신 모델 흐름]] |
| P0 | Speculative Decoding production benchmark | [[deepspec-speculative-decoding|DeepSpec]] |
| P1 | PagedAttention에서 vLLM KV cache까지 | [[vllm-serving-architecture|vLLM]] |
| P1 | RAG 논문에서 TEI 운영까지 | [[tei-rag-embedding-rerank|TEI]] |
| P2 | AgentBench/Toolformer와 MCP/A2A 평가 | [[agent-protocol-stack|Agent Protocol]] |

## 참고 자료

- [PagedAttention paper](https://arxiv.org/abs/2309.06180)
- [Speculative Decoding paper](https://arxiv.org/abs/2211.17192)
- [Retrieval-Augmented Generation paper](https://arxiv.org/abs/2005.11401)

## 파트 안의 파트 설계

이 대분류는 `모델`, `추론 알고리즘`, `논문 리뷰`, `평가`, `운영 적용`으로 다시 나눈다. 모델 파트 안에는 GLM, Qwen, Kimi, DeepSeek 같은 계열별 프로필을 둔다. 추론 알고리즘 안에는 speculative decoding, DeepSpec, cache-aware decoding, prefill/decode 분리를 둔다. 논문 리뷰 안에는 paper figure 해설과 production metric 연결을 둔다.

| 깊이 | 예시 목차 | 작성 기준 |
|---|---|---|
| 대분류 | 모델/추론 연구 | 최신 모델과 추론 연구 전체 입구 |
| 하위 파트 | 최신 모델, 추론 가속, 논문 리뷰, 평가 | 서로 다른 읽기 목적을 분리 |
| 개별 글 | GLM 모델 카드, DeepSpec, PagedAttention, RAG | figure, metric, 운영 연결 포함 |
| 실전 글 | benchmark 설계, serving cost 비교 | 실제 선택 기준과 runbook 포함 |

## 완성 기준

각 글은 발표 요약으로 끝나면 안 된다. 모델 글은 serving 제약과 비용을 남기고, 알고리즘 글은 어떤 병목을 줄이는지 남기며, 논문 리뷰는 원문 figure와 운영 metric의 연결을 남긴다. 이 기준을 만족해야 runtime 파트로 자연스럽게 이어진다.

![모델/추론 연구 목차: 최신 모델, 추론 가속, 논문 리뷰 구조도](figures/architecture.svg?v=part-hubs-20260706)

*Figure 2: 모델/추론 연구 목차: 최신 모델, 추론 가속, 논문 리뷰 하위 파트 구조도. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
