<!-- infographic-hero -->
![LLM 관측성과 비용: TTFT, ITL, throughput, token cost 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: LLM 관측성과 비용: TTFT, ITL, throughput, token cost 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# LLM 관측성과 비용: TTFT, ITL, throughput, token cost

LLM serving 관측성은 GPU utilization 하나로 끝나지 않는다. 사용자는 TTFT를 체감하고, stream 중에는 inter-token latency를 체감한다. 운영자는 queue time, prefill/decode throughput, cache hit, error rate, token cost를 본다. 비용 최적화는 latency를 해치고, batching은 throughput을 올리지만 tail latency를 늘릴 수 있다.

![LLM 관측성과 비용: TTFT, ITL, throughput, token cost 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: LLM 관측성과 비용: TTFT, ITL, throughput, token cost 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 GPU utilization 대시보드를 만드는 글이 아니다. 사용자가 체감하는 TTFT와 inter-token latency, 운영자가 보는 queue time과 throughput, 재무 관점의 token cost를 같은 화면에서 해석하는 기준을 다룬다. 지표 하나하나를 외우기보다, 각 지표가 request lifecycle의 어느 단계에서 생기고 어떤 자원에 좌우되는지를 연결해 두는 것이 목적이다.

## 핵심 지연 지표: TTFT, ITL, end-to-end latency

LLM 추론 한 번은 크게 prefill 단계와 decode 단계로 나뉜다. prefill은 입력 프롬프트 전체를 한 번에 병렬로 처리해 첫 토큰을 만드는 단계이고, decode는 그 뒤로 토큰을 한 개씩 순차 생성하는 단계다. 지연 지표는 이 두 단계에 그대로 대응한다.

- **TTFT (Time To First Token)**: 요청이 들어온 뒤 첫 토큰이 나오기까지의 시간이다. prefill 단계와 그 앞의 queue 대기 시간을 함께 반영한다. 프롬프트가 길수록, prefix cache가 비어 있을수록, 배치 큐가 밀려 있을수록 TTFT는 커진다. 사용자가 "느리다"고 느끼는 첫인상이 대부분 여기서 결정된다.
- **ITL / TPOT (Inter-Token Latency, Time Per Output Token)**: 첫 토큰 이후 토큰과 토큰 사이의 간격이다. decode 단계의 속도를 나타내며 stream을 볼 때의 매끄러움을 좌우한다. batch에 몰린 동시 시퀀스 수, KV cache에서의 memory bandwidth, 모델 크기에 좌우된다. decode는 순차적이라 memory bandwidth에 병목이 잘 걸린다.
- **end-to-end latency**: 요청 전체가 끝날 때까지의 시간이다. 출력 토큰 수가 $N_{out}$일 때 근사적으로 다음과 같이 분해된다.

$$L_{e2e} \approx t_{queue} + t_{prefill} + (N_{out} - 1)\cdot t_{ITL}$$

이 분해가 중요한 이유는, 같은 end-to-end latency라도 원인이 다르기 때문이다. 프롬프트가 길어 prefill이 무거운 경우와, 출력이 길어 decode 구간이 늘어난 경우는 완전히 다른 처방을 요구한다. 그래서 관측 대시보드는 처음부터 TTFT와 ITL을 분리해서 기록해야 하고, 하나로 뭉친 평균 응답 시간만 보면 병목을 놓친다.

decode 구간을 줄이는 대표적 기법이 speculative decoding으로, 작은 draft 모델이 여러 토큰을 미리 제안하고 큰 모델이 한 번에 검증한다. 이때 acceptance rate가 관측 축으로 추가된다. 자세한 동작은 [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]]에서 다룬다. runtime이 prefill과 decode를 어떻게 스케줄링하는지는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]를 함께 보면 된다.

## 처리량과 효율: throughput, batching, KV cache

지연이 개별 요청의 관점이라면, throughput은 시스템 전체 관점이다. 두 축을 함께 봐야 배치 정책의 효과가 보인다.

- **throughput**: request/sec 하나로는 부족하다. 같은 req/sec라도 요청마다 토큰 수가 다르기 때문이다. prefill throughput(input tokens/sec)과 decode throughput(output tokens/sec)을 나눠서 보는 편이 실제 GPU 부하를 더 잘 설명한다.
- **batching과 tail latency의 trade-off**: continuous batching은 실행 중인 시퀀스에 새 요청을 계속 끼워 넣어 GPU를 놀리지 않게 한다. 배치를 키우면 throughput은 오르지만, 한 배치 안의 요청들이 서로의 decode step을 기다리게 되어 p95/p99 tail latency가 늘어난다. 그래서 batch 크기는 throughput과 tail latency가 서로 밀어내는 지점을 관찰하며 정한다.
- **GPU utilization의 함정**: GPU 사용률이 높다고 효율적인 것은 아니다. 사용률은 "코어가 바쁜가"만 말할 뿐, 그 연산이 실제로 유용한 토큰을 만들고 있는지는 말하지 않는다. decode는 memory bound라 사용률이 높아도 실제 처리량이 낮을 수 있다.
- **KV cache 사용률**: 각 시퀀스는 지금까지의 토큰에 대한 key/value를 GPU 메모리에 쌓는다. 이 KV cache 용량이 동시에 처리 가능한 시퀀스 수의 상한을 정한다. cache가 가득 차면 새 요청은 queue에서 대기하거나 선점(preemption)되며, 이는 곧 TTFT 상승으로 나타난다. 따라서 KV cache 사용률은 지연과 처리량을 잇는 핵심 지표다.

## 비용: token cost와 요청당 비용

비용은 결국 토큰으로 환산된다. 요청당 비용은 개념적으로 input 토큰과 output 토큰의 단가에 각각 수량을 곱한 합이다.

$$C_{req} = c_{in}\cdot N_{in} + c_{out}\cdot N_{out}$$

여기서 output 단가 $c_{out}$이 input 단가 $c_{in}$보다 큰 경우가 일반적이다. prefill은 프롬프트 전체를 병렬로 처리하지만 decode는 토큰을 하나씩 순차 생성해 GPU 시간을 더 많이 쓰기 때문이다. 그래서 같은 총 토큰 수라도 출력이 긴 요청이 더 비싸다. 비용을 줄이려면 불필요하게 긴 출력을 제한하는 것이 프롬프트를 줄이는 것보다 효과가 큰 경우가 많다.

**prefix cache / cache hit의 비용 효과**도 여기에 직접 연결된다. 여러 요청이 같은 system prompt나 공통 문맥을 공유하면, 그 공통 prefix의 KV를 재사용해 prefill을 건너뛸 수 있다. cache hit이 나면 그만큼 prefill 연산과 지연이 줄고 TTFT도 낮아진다. 즉 prefix cache hit rate는 지연 지표이면서 동시에 비용 지표다.

운영에서 중요한 것은 이 비용을 어디에 귀속시키느냐다. model, tenant, route, feature 축으로 token cost를 집계할 수 있어야 어느 기능이 비용을 끌어올리는지 설명할 수 있다. 이 attribution이 없으면 총비용은 보여도 최적화할 지점을 못 찾는다.

## 무엇을 어디서 측정하는가

관측성 설계는 측정 지점을 먼저 정하는 데서 시작한다. 하나의 요청이 여러 컴포넌트를 지나므로, 각 지점이 책임지는 지표를 분리해 둔다.

| 측정 지점 | 얻는 지표 | 관측 축 |
|-----------|-----------|---------|
| runtime (vLLM 등) | prefill/decode throughput, KV cache 사용률, queue 길이, preemption | model, ttft, itl, cache_hit |
| gateway / router | route별 latency, 토큰 수, error rate, 요청 분배 | route, tenant, status |
| tracing | end-to-end span, retrieval와 generation 분리 | trace_id, span, queue_time |

관측 축의 이름은 처음부터 못박아 둔다. 최소한 `model`, `route`, `queue_time`, `ttft`, `itl`, `input_tokens`, `output_tokens`, `cache_hit`을 trace와 metric에 함께 실으면, 사용자 요청 하나가 어느 route에서 어떤 지연과 비용을 만들었는지 재구성할 수 있다. runtime 지표는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]가, route별 분배와 라우팅 지표는 [[istio-gateway-inference-routing|Gateway 추론 라우팅]]이 담당한다.

세 지점을 나누는 이유는 지표가 서로를 검증하기 때문이다. runtime이 보고한 decode throughput과 gateway가 집계한 output tokens/sec가 어긋나면 route 사이에 병목이나 재시도가 숨어 있다는 신호다. tracing에서 자주 하는 실수는 RAG retrieval latency와 generation latency를 같은 span에 뭉치는 것이다. 둘을 분리해야 어느 쪽이 병목인지 보인다. 같은 맥락에서 error rate와 timeout도 별도 축으로 남겨 성공한 요청의 지연 통계가 실패 요청에 오염되지 않게 한다.

## 실무 관점: SLO 설정과 병목 진단 순서

지표를 정했으면 목표값(SLO)을 붙인다. LLM 서빙에서 흔히 쓰는 SLO 축은 세 가지다. 첫째, TTFT의 p95를 정해 첫 응답 체감을 보장한다. 둘째, ITL의 p95를 정해 stream이 끊기지 않게 한다. 셋째, 처리량 목표(output tokens/sec 또는 req/sec)를 정해 용량을 관리한다. 평균이 아니라 p95/p99 tail로 잡아야 실제 사용자 경험을 대변한다.

병목을 진단할 때는 request lifecycle 순서를 따라 위에서 아래로 내려간다.

1. **queue**: 요청이 실행 전에 대기하고 있는가. queue time이 길면 용량 부족이거나 KV cache 포화다. 이때는 TTFT만 나쁘고 ITL은 정상인 패턴으로 나타난다.
2. **prefill**: 프롬프트가 긴가, prefix cache가 안 먹는가. TTFT가 프롬프트 길이에 비례해 커지면 prefill 병목이다.
3. **decode**: ITL이 큰가. 배치가 과밀하거나 출력이 지나치게 길다. batch 크기와 tail latency가 밀어내는 지점을 다시 본다.
4. **cost**: latency는 괜찮은데 비용이 튀는가. 어느 route/tenant에서 output 토큰이 몰리는지 attribution으로 확인한다.

다음 패턴이 보이면 관측 설계를 다시 나눈다.

- GPU 사용률만 높이면 효율적이라고 판단한다. 실제 유용한 토큰 처리량과 KV cache 사용률을 함께 봐야 한다.
- p95 latency와 비용 증가가 어느 route에서 생기는지 모른다. route/tenant 축의 attribution이 빠진 것이다.
- TTFT와 ITL을 하나의 평균 응답 시간으로 뭉쳐 본다. prefill 병목과 decode 병목을 구분할 수 없게 된다.

이런 실패는 대부분 기술 선택의 문제가 아니라 관측 축이 흐린 데서 시작한다. 어떤 요청이 어느 단계를 지나고, 그 사이에서 queue, cache, 상태 전이가 어디에 기록되는지 정해 두면 운영 중 병목 위치가 훨씬 빨리 보인다.

## 참고 자료

- [vLLM docs](https://docs.vllm.ai/)
- [TEI docs](https://huggingface.co/docs/text-embeddings-inference/en/index)
- [Ray Serve LLM](https://docs.ray.io/en/latest/serve/llm/index.html)

## 관련 문서

- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - generation runtime의 prefill/decode와 KV cache 관측
- [[istio-gateway-inference-routing|Gateway 추론 라우팅]] - route/tenant별 지연과 토큰 수 측정 지점
- [[deepspec-speculative-decoding|DeepSpec과 Speculative Decoding]] - decode 구간 가속과 acceptance rate
- [[llm-serving-runtime-stack|LLM Serving Runtime Stack]] - runtime 계층 전체 구성
- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼]] - 서빙 스택 전체 분기점
- [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]] - Kubernetes 위 서빙 인프라
- [[model-inference-research-hub|모델 추론 리서치 허브]] - 추론 최적화 자료 모음
