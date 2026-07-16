<!-- infographic-hero -->
![Istio/Gateway API 추론 라우팅: InferencePool과 Endpoint Picker 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Istio/Gateway API 추론 라우팅: InferencePool과 Endpoint Picker 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# Istio/Gateway API 추론 라우팅: InferencePool과 Endpoint Picker

일반 HTTP load balancing은 LLM replica의 내부 상태를 모른다. 어떤 pod는 KV cache가 꽉 찼고, 어떤 pod는 queue가 길며, 어떤 pod는 특정 LoRA adapter를 이미 올려두었을 수 있다. Gateway API Inference Extension은 InferencePool과 Endpoint Picker를 통해 이런 정보를 라우팅에 반영하려는 흐름이다.

![Istio/Gateway API 추론 라우팅: InferencePool과 Endpoint Picker 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Istio/Gateway API 추론 라우팅: InferencePool과 Endpoint Picker 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 Gateway를 L7 reverse proxy로만 보지 않는다. LLM serving에서는 replica의 queue length, KV cache locality, LoRA adapter 적재 상태, active batch 상태가 routing 품질에 영향을 준다. Gateway API Inference Extension과 Istio/Envoy 계열 구성을 이 관점에서 설명한다. 스펙의 세부 필드보다 각 컴포넌트가 어느 결정을 책임지는지, 그리고 그 결정을 무엇으로 관측하는지에 무게를 둔다.

## 왜 일반 L7 라우팅으로는 부족한가

일반적인 L7 load balancing은 요청을 거의 동일한 비용으로 가정하고 분배한다. round-robin이나 least-connection은 모든 backend가 비슷한 속도로 요청을 처리한다는 전제에서 잘 동작한다. web API나 stateless microservice에서는 이 전제가 대체로 맞다.

LLM 추론은 이 전제를 깬다. 요청마다 처리 비용과 지연 편차가 크다. prompt 길이에 따라 prefill 연산량이 달라지고, 생성 토큰 수에 따라 decode 시간이 달라진다. 같은 모델이라도 짧은 질의와 긴 문서 요약은 GPU 점유 시간이 크게 벌어진다. 게다가 backend가 stateful하고 GPU-bound다. 각 replica는 KV cache를 들고 있고, 그 cache가 특정 대화나 prefix에 묶여 있으며, 한 번에 처리할 수 있는 batch 크기가 GPU 메모리에 제약된다.

이 조건에서 단순 round-robin은 queue 쏠림을 만든다. 이미 긴 요청을 처리 중이라 queue가 쌓인 pod에도 균등하게 요청이 들어가고, 방금 처리를 마쳐 KV cache가 비어 있는 pod가 놀 수 있다. 특정 prefix의 cache를 이미 올려둔 pod를 무시하고 다른 pod로 보내면 cache를 다시 채워야 해서 첫 토큰 지연(TTFT)이 흔들린다. 요청을 어디로 보낼지 정할 때 backend의 내부 상태를 보지 않으면, 평균 처리량은 괜찮아 보여도 꼬리 지연(tail latency)이 커진다.

Gateway API Inference Extension은 이 문제를 라우팅 계층에서 다루려는 접근이다. Gateway는 여전히 진입점과 L7 정책을 담당하되, "어느 replica로 보낼 것인가"라는 결정을 추론 특화 컴포넌트에 위임한다.

## InferencePool: 추론 백엔드를 하나의 리소스로

InferencePool은 추론 backend(모델 서버 pod)의 묶음을 추론 특화 정책으로 다루는 리소스다. Gateway API의 확장으로 정의되며, 일반 Service가 pod 집합을 단순한 엔드포인트 목록으로 보는 것과 달리, InferencePool은 그 집합을 "같은 모델을 서빙하는, 상태를 가진 replica 그룹"으로 본다.

핵심 차이는 이 그룹에 붙는 정책이다. 일반 Service backend는 selector로 pod를 고르고 Gateway가 균등 분배한다. InferencePool은 여기에 추론 관점의 선택 기준을 결합할 자리를 만든다. 어느 pod가 지금 여유가 있는지, 어느 pod가 요청에 맞는 상태(cache, adapter)를 갖췄는지를 라우팅 결정에 넣을 수 있는 지점을 제공한다.

HTTPRoute는 여전히 경로와 헤더 기준으로 트래픽을 나눈다. 모델명이나 경로에 따라 다른 InferencePool로 보내는 식이다. 그다음 InferencePool 내부에서 개별 pod 선택이 일어난다. 즉 "어떤 pool인가"는 Gateway API의 route 규칙이 정하고, "그 pool 안에서 어떤 pod인가"는 추론 특화 선택이 정한다. 이 두 결정을 분리해 두면 route 정책과 endpoint 선택 로직을 따로 바꿀 수 있다.

서빙 런타임 자체(모델 로딩, batching, KV cache 관리)는 이 pool 아래에서 동작한다. 런타임 계층은 [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]]와 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]에서 다루고, 이 글은 그 위의 라우팅 경계에 집중한다.

## Endpoint Picker: 추론 인지적 엔드포인트 선택

Endpoint Picker(EPP)는 요청을 InferencePool 안의 어느 엔드포인트로 보낼지 결정하는 컴포넌트다. 일반 load balancer가 연결 수나 순번 같은 트래픽 지표만 보는 것과 달리, EPP는 추론 backend의 상태 신호를 참고해 선택한다.

참고하는 신호는 개념적으로 다음과 같은 것들이다. 각 replica의 queue 길이와 현재 batch 점유로 부하를 판단하고, KV cache 상태를 봐서 이미 관련 prefix를 들고 있는 pod에 붙이며(cache locality), 요청이 특정 모델이나 LoRA adapter를 요구할 때 그 adapter를 이미 적재한 pod로 보낸다(model/adapter affinity). 이렇게 하면 cache를 다시 채우거나 adapter를 새로 올리는 비용을 줄일 수 있다.

일반 로드밸런서와의 차이는 "무엇을 최적화하는가"에 있다. 일반 로드밸런서는 연결을 고르게 나누는 것이 목표다. EPP는 요청을 가장 싸게 처리할 수 있는 backend, 즉 지금 여유가 있으면서 요청에 맞는 상태를 갖춘 backend를 고르는 것이 목표다. 목표가 다르기 때문에 같은 트래픽에서도 선택 결과가 달라진다.

이 방식은 하나의 실패 지점을 만든다. 선택 컴포넌트가 죽으면 라우팅이 멈출 수 있다. 그래서 EPP 장애 시 기본 라우팅으로 degrade할 수 있는지, 즉 상태 신호 없이도 요청이 backend에 도달하는지를 설계 단계에서 확인해야 한다. 이것은 어느 특정 구현의 세부라기보다, 추론 인지적 라우팅을 도입할 때 공통으로 따져야 하는 지점이다.

## Istio/Gateway API와의 결합

전체 그림에서 각 계층의 책임은 이렇게 나뉜다. Gateway(Istio/Envoy 계열 구현 포함)는 진입점이다. 외부 트래픽을 받고, TLS 종료, 인증, rate limit, L7 route 규칙 같은 표준 Gateway 기능을 담당한다. 이 부분은 일반 Ingress/Gateway와 다르지 않다. 일반 진입 개념은 [[ckad-18-ingress|Service와 Ingress]]에서 이어진다.

추론 특화 라우팅은 이 위에 얹히는 확장이 담당한다. Gateway가 요청을 InferencePool로 넘기면, EPP가 pool 안에서 endpoint를 고른다. 즉 Gateway는 "어디로 들어와서 어떤 pool로 가는가"까지 책임지고, "그 pool 안에서 정확히 어느 pod인가"는 추론 확장이 책임진다. Gateway 구현을 Istio로 하든 다른 Gateway API 구현으로 하든, 이 경계 자체는 유지된다.

이 분리의 장점은 표준 Gateway 기능과 추론 특화 로직을 섞지 않는다는 것이다. 인증과 rate limit은 Gateway 앞단에서 한 번 처리되고, 모델별 route는 HTTPRoute가, endpoint 선택은 EPP가 맡는다. 한 컴포넌트가 이 셋을 다 떠안으면 구현은 빨라도 장애가 났을 때 어느 계층의 문제인지 분리하기 어렵다.

GPU 스케줄링은 이 라우팅과 별개의 계층이다. 어느 pod가 어느 GPU에 뜨는지, 얼마나 많은 replica를 띄울 수 있는지는 scheduler의 몫이고, 이는 [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링]]에서 다룬다. 라우팅은 이미 뜬 replica 사이에서 요청을 나누는 문제이고, 스케줄링은 replica 자체를 배치하는 문제다.

## 언제 이 라우팅이 필요한가

모든 서빙에 추론 인지적 라우팅이 필요한 것은 아니다. 도입 판단은 대체로 다음 조건에서 갈린다.

- replica가 여러 개이고 요청 비용 편차가 크다. 단일 replica이거나 요청이 균질하면 round-robin으로 충분하다. 긴 요청과 짧은 요청이 섞이고 replica가 여럿일 때 EPP의 부하 인지 선택이 의미를 갖는다.
- KV cache locality가 성능에 영향을 준다. 같은 prefix나 대화가 반복되는 워크로드에서 cache를 재사용하면 TTFT가 크게 줄어든다. cache locality를 무시한 라우팅은 이 이득을 버린다.
- 여러 모델이나 LoRA adapter를 한 pool에서 서빙한다. model/adapter affinity를 반영하면 adapter 교체 비용을 줄인다. 단일 모델 단일 adapter라면 이 신호는 필요 없다.

반대로 트래픽이 적거나 replica가 하나면, 이 계층을 추가하는 복잡도가 이득을 넘어설 수 있다. 라우팅 문제인지 먼저 확인하고, 라우팅 문제가 아니라면 런타임이나 스케줄링 계층을 본다. 서빙 스택 전체의 분기점은 [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]]에서, 런타임 선택지 비교는 [[llm-serving-runtime-stack|LLM Serving Runtime 스택]]에서 정리한다.

## 운영에서 볼 신호

추론 라우팅을 운영에 넣을 때는 "성공/실패"만으로는 병목을 설명할 수 없다. 최소한 다음 축을 로그와 metric에 실어야 어느 요청이 어느 route를 지나 어느 endpoint로 갔고, 거기서 왜 느렸는지 재구성할 수 있다.

- route와 model: 요청이 어느 HTTPRoute, 어느 InferencePool, 어느 모델로 갔는가
- 부하 신호: 선택 시점의 queue 길이, batch 점유, endpoint별 in-flight 요청 수
- cache 신호: cache hit 여부, prefix 재사용률
- 지연 분해: queue 대기 시간, 첫 토큰 지연(TTFT), 토큰 간 지연(ITL)
- 토큰 회계: input/output token 수 (비용 및 처리량 분석)

이 신호들을 endpoint 선택과 연결해 보면, EPP의 선택이 실제로 부하와 cache를 반영했는지 검증할 수 있다. 관측 축을 설계하고 비용으로 연결하는 방법은 [[llm-observability-cost|LLM 관측성과 비용]]에서 다룬다. 서빙 리소스를 GitOps로 배포하고 라우팅 정책을 버전 관리하는 흐름은 [[helm-argocd-ai-serving-gitops|Helm/ArgoCD GitOps]]에서 이어진다.

도입 전 점검해 둘 항목을 정리하면 다음과 같다.

| 항목 | 확인 기준 |
|------|-----------|
| Endpoint signal | queue, cache, adapter 상태를 picker가 볼 수 있는가 |
| Failure mode | picker 장애 시 기본 routing으로 degrade 가능한가 |
| Multi-model | 모델명/adapter별 route 분리가 명확한가 |
| Security | Gateway 인증, rate limit, audit log가 model endpoint 앞에 있는가 |

## 관련 문서

- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]] - 서빙 스택 전체 분기점
- [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService]] - InferencePool 아래의 서빙 런타임
- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - KV cache와 batching을 다루는 런타임 계층
- [[llm-serving-runtime-stack|LLM Serving Runtime 스택]] - 런타임 선택지 비교
- [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링]] - replica 배치를 정하는 스케줄링 계층
- [[llm-observability-cost|LLM 관측성과 비용]] - route/endpoint 신호와 비용 분석
- [[helm-argocd-ai-serving-gitops|Helm/ArgoCD GitOps]] - 서빙 리소스 배포 자동화
- [[ckad-18-ingress|Service와 Ingress]] - 일반 진입 라우팅의 기본 개념
- [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]] - GPU/런타임/Gateway/관측 인프라 개관

## 참고 자료

- [Gateway API Inference Extension](https://gateway-api-inference-extension.sigs.k8s.io/)
- [InferencePool API](https://gateway-api-inference-extension.sigs.k8s.io/api-types/inferencepool/)
- [Istio Inference Extension task](https://istio.io/latest/docs/tasks/traffic-management/ingress/gateway-api-inference-extension/)
