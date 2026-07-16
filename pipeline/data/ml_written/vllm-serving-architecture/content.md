<!-- infographic-hero -->
![vLLM Serving Runtime: Scheduler, KV Cache, Prefix Cache, Structured Output 핵심 요약](figures/infographic.svg?v=runtime-tabs-20260706)

*Figure 1: vLLM Serving Runtime: Scheduler, KV Cache, Prefix Cache, Structured Output 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# vLLM Serving Runtime: Scheduler, KV Cache, Prefix Cache, Structured Output

vLLM은 `OpenAI-compatible server`를 띄우는 도구로만 보면 금방 얕아진다. 실제 운영에서 vLLM은 generation runtime의 기준면이다. client는 OpenAI API를 호출하지만, 내부에서는 tokenizer, chat template, scheduler, prefill/decode phase, KV cache block, prefix cache, structured output backend, speculative decoding, metrics exporter가 서로 다른 책임을 가진다.

이 글은 `LLM Serving Runtime Stack` 안의 한 항목이 아니라 `vLLM` 독립 파트의 첫 글이다. 앞으로 vLLM만으로도 PagedAttention, prefix caching, disaggregated prefill, speculative decoding, structured output, tool calling, quantization, multi-GPU parallelism, 운영 metric을 각각 별도 글로 확장할 수 있다.

## vLLM을 어디까지 runtime으로 볼 것인가

vLLM은 모델 weight를 GPU에 올리고 token을 생성하는 실행 엔진이지만, production에서는 API contract와 scheduler contract까지 포함해서 본다. OpenAI-compatible endpoint는 client integration을 쉽게 만들지만, endpoint가 같다고 내부 성능이나 error behavior가 같은 것은 아니다. streaming chunk, tool call schema, structured output, tokenizer 차이, max token 처리 방식은 모두 운영 contract다.

운영자는 평균 latency보다 `TTFT`, `inter-token latency`, `queue time`, `input/output token/sec`, `KV cache pressure`, `prefix cache hit`, `GPU memory`, `preemption`, `error type`을 본다. 이 지표가 없으면 vLLM이 느린지, Gateway가 느린지, 모델이 긴 prompt 때문에 느린지 분리할 수 없다.

## Scheduler와 KV cache

vLLM의 강점은 PagedAttention과 continuous batching에서 출발한다. PagedAttention은 KV cache를 block 단위로 관리해 긴 sequence와 동시 요청에서 메모리 낭비를 줄인다. 운영에서는 이것이 block usage, eviction, cache hit, max model length, max num sequences 같은 설정으로 나타난다. prompt가 길고 동시성이 높으면 GPU memory는 빠르게 압박을 받고, queue time이 TTFT로 전이된다.

prefill과 decode는 같은 request 안에서도 성격이 다르다. prefill은 긴 prompt를 한 번에 처리하는 구간이고, decode는 output token을 순차적으로 생성하는 구간이다. chunked prefill이나 disaggregated prefill을 검토할 때는 TTFT와 ITL을 따로 본다. TTFT만 좋아졌는데 decode tail latency가 나빠질 수도 있고, decode throughput만 좋아졌는데 긴 prompt 사용자가 여전히 느릴 수도 있다.

## Structured output과 tool call

JSON schema, grammar, function/tool call은 API 기능처럼 보이지만 실제로는 decoding constraint다. vLLM 문서 기준 structured output은 xgrammar나 guidance 같은 backend를 활용한다. 이 기능을 켜면 응답 형식 안정성은 좋아지지만, schema 복잡도와 token 분포에 따라 latency가 달라진다. 따라서 structured output은 기능 플래그가 아니라 별도 benchmark 대상이다.

Tool call도 마찬가지다. 모델이 function call을 안정적으로 내보내는지, streaming 중 tool call fragment를 client가 어떻게 조립하는지, error body가 OpenAI-compatible client와 맞는지 확인해야 한다. 운영 contract test에는 일반 채팅, 긴 context, JSON schema, tool call, streaming cancel, timeout, rate limit을 모두 포함한다.

## vLLM 파트에서 파생할 글

| 글 후보 | 다룰 내용 | 연결 논문/운영 글 |
|---|---|---|
| vLLM PagedAttention | block table, KV cache, continuous batching | [[paged-attention|PagedAttention 논문 리뷰]] |
| vLLM Prefix Caching | prompt reuse, cache hit, tenant/model별 cache strategy | [[llm-observability-cost|관측성과 비용]] |
| vLLM Structured Output | JSON schema, grammar, tool calling, latency cost | MCP/A2A tool call 글 |
| vLLM Disaggregated Prefill | prefill/decode 분리, TTFT/ITL 튜닝 | KServe/Ray Serve 배포 글 |
| vLLM Speculative Decoding | draft/target, acceptance rate, DeepSpec 연결 | [[speculative-decoding|Speculative Decoding]] |

## 운영 Runbook

장애가 나면 먼저 증상을 나눈다. `TTFT`가 높으면 queue time, prefill length, cold model, prefix cache miss를 본다. `ITL`이 높으면 decode throughput, GPU memory pressure, parallelism 설정을 본다. OOM이면 max context, batch, KV cache block, quantization, tensor parallel을 본다. JSON 응답이 깨지면 structured output backend, schema, tokenizer, client parser를 본다. 5xx가 늘면 model load, worker crash, Gateway timeout, client cancel을 분리한다.

## 기존 글과 이어서 보기

- 이 글의 이론적 기반은 [[paged-attention|PagedAttention 논문 리뷰]]다.
- draft/target 가속은 [[speculative-decoding|Speculative Decoding]]과 [[deepspec-speculative-decoding|DeepSpec]]에서 본다.
- Kubernetes에 올리는 방식은 [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]와 [[ray-serve-llm-deep-dive|Ray Serve LLM]]에서 나눠 본다.
- 전체 runtime 입구는 [[llm-serving-runtime-stack|LLM Serving Runtime Stack]]에 둔다.

## 참고 자료

- [vLLM documentation](https://docs.vllm.ai/)
- [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [vLLM serve CLI](https://docs.vllm.ai/en/stable/cli/serve/)

## 설정값을 운영 언어로 바꾸기

vLLM 설정은 단순히 CLI 옵션 목록으로 외우면 운영 문서가 되지 않는다. `max-model-len`은 지원 context 길이이면서 KV cache 압박을 결정하고, `max-num-seqs`는 동시성 한계이면서 queue time과 OOM 가능성을 바꾼다. tensor parallel 설정은 multi-GPU throughput을 바꾸지만 topology와 NCCL/RDMA 상태에 의존한다. quantization은 memory footprint를 줄이지만 품질과 latency profile을 다시 검증해야 한다.

운영 문서에는 각 설정을 "왜 이 값을 골랐는가"로 남겨야 한다. 예를 들어 customer support 챗봇은 긴 context보다 안정적인 TTFT가 중요할 수 있고, codebase assistant는 긴 prompt와 prefix cache가 더 중요할 수 있다. 같은 모델이라도 traffic shape가 다르면 vLLM 설정은 달라진다.

## Benchmark 계획

vLLM benchmark는 prompt 길이, output 길이, 동시성, streaming 여부, structured output 여부를 조합해 만든다. 짧은 prompt와 긴 output, 긴 prompt와 짧은 output, 긴 prompt와 긴 output은 서로 다른 병목을 만든다. prefix cache를 평가하려면 같은 prefix를 반복하는 traffic과 매번 다른 prefix를 쓰는 traffic을 나눠야 한다. speculative decoding은 acceptance rate가 높은 prompt와 낮은 prompt를 따로 봐야 한다.

결과 표에는 평균 latency보다 p50/p95 TTFT, p95 ITL, output token/sec, queue time, GPU memory, cache hit를 넣는다. 비용 관점에서는 request당 GPU time과 token당 비용을 함께 본다. 이 기준이 있으면 "vLLM이 빠르다"가 아니라 "우리 traffic에서 어느 설정이 어떤 지표를 개선했다"로 설명할 수 있다.

## 보안과 멀티테넌시

OpenAI-compatible endpoint를 외부에 열면 인증, rate limit, request body size, max token, model allow-list가 필요하다. tenant별로 model을 나누는지, 같은 model을 공유하되 quota만 나누는지에 따라 cache와 비용 배분이 달라진다. prompt와 output log를 남길 때는 개인정보와 보안 데이터가 섞이지 않도록 redaction 정책도 필요하다.

운영 플랫폼에서는 vLLM 자체보다 Gateway와 policy layer가 이 책임을 맡는 경우가 많다. 하지만 vLLM 대시보드가 tenant/model/route label을 받지 못하면 비용과 장애 원인을 뒤에서 분석하기 어렵다. 따라서 Gateway, vLLM, billing pipeline의 label contract를 함께 설계한다.

## 실제로 분리해서 쓸 하위 목차

vLLM 탭은 앞으로 최소 여섯 갈래로 확장할 수 있다. 첫째, 설치와 기본 serving 글에서는 container image, model download, OpenAI API server, health endpoint를 다룬다. 둘째, scheduler 글에서는 continuous batching, request queue, prefill/decode split을 다룬다. 셋째, memory 글에서는 PagedAttention, KV block, prefix cache, eviction을 다룬다. 넷째, output control 글에서는 JSON schema, grammar, tool call, client contract test를 다룬다. 다섯째, acceleration 글에서는 speculative decoding, chunked prefill, disaggregated prefill을 다룬다. 여섯째, production 글에서는 Gateway, autoscaling, observability, cost allocation을 다룬다.

이렇게 쪼개면 vLLM은 더 이상 runtime stack의 한 줄이 아니라 독립 학습 트랙이 된다. 각 글은 반드시 "설정값", "측정 지표", "장애 runbook", "운영에서 틀리기 쉬운 가정"을 포함한다.

## 운영 문서 최소 구성

이 runtime 파트의 모든 후속 글은 같은 형식을 따른다. 먼저 어떤 request path를 책임지는지 한 문장으로 정의한다. 다음으로 배포 단위, 설정값, metric, 장애 증상, rollback 단위를 표로 적는다. 마지막에는 "이 runtime이 맡지 않는 책임"을 명시한다. 이 경계가 있어야 vLLM, TEI, KServe, Ray Serve가 서로 섞이지 않고 독립 탭처럼 쌓인다.

![vLLM Serving Runtime: Scheduler, KV Cache, Prefix Cache, Structured Output 운영 구조](figures/architecture.svg?v=runtime-tabs-20260706)

*Figure 2: vLLM Serving Runtime: Scheduler, KV Cache, Prefix Cache, Structured Output 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
