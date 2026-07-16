<!-- infographic-hero -->
![Kubernetes AI Infra 목차: GPU, Gateway, Storage, Serving Control Plane 핵심 요약](figures/infographic.svg?v=part-hubs-20260706)

*Figure 1: Kubernetes AI Infra 목차: GPU, Gateway, Storage, Serving Control Plane 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# Kubernetes AI Infra 목차: GPU, Gateway, Storage, Serving Control Plane

Kubernetes AI Infra는 GPU Pod를 띄우는 글 하나로 끝나지 않는다. AI serving에서는 GPU scheduling, model weight storage, Gateway routing, serving control plane, observability, security, autoscaling이 모두 필요하다. 이 글은 Kubernetes AI Infra 대분류의 허브이고, [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]]는 이 허브 안의 첫 기준 글이다.

## 하위 파트 1: GPU scheduling

[[k8s-gpu-scheduling-dra|K8s GPU 스케줄링]]은 Device Plugin에서 DRA까지 다룬다. 후속 글은 MIG, topology manager, NUMA/NVLink locality, quota, GPU sharing, failure event, GPU operator 운영으로 나눈다. AI serving에서는 GPU가 잡혔다는 사실보다 어떤 model과 어떤 traffic에 적합하게 배정됐는지가 중요하다.

## 하위 파트 2: Gateway와 추론 라우팅

[[istio-gateway-inference-routing|Istio/Gateway API 추론 라우팅]]은 일반 HTTP routing을 넘어 InferencePool, Endpoint Picker, load-aware routing까지 연결한다. LLM traffic은 prompt length, cache locality, endpoint readiness, tenant quota 같은 기준이 필요하다. 이 파트는 Gateway API, Inference Extension, Envoy AI Gateway, rate limit, canary route로 확장한다.

## 하위 파트 3: Serving control plane

KServe와 Ray Serve는 Kubernetes 위에서 서로 다른 방식으로 모델을 운영한다. [[kserve-llminferenceservice-deep-dive|KServe]]는 CRD와 controller 중심이고, [[ray-serve-llm-deep-dive|Ray Serve]]는 Ray cluster와 Python graph 중심이다. [[kserve-ray-serve-llm|KServe vs Ray Serve]]는 선택 기준 허브로 둔다.

## 하위 파트 4: Storage와 model artifact

대형 모델 운영에서는 image보다 weight가 더 중요할 수 있다. object storage, PVC, initContainer, storage initializer, private/gated model credential, cache invalidation을 별도 목차로 둔다. 모델 weight가 준비되지 않았는데 route가 열리면 사용자는 503이나 timeout을 경험한다.

## 하위 파트 5: Observability와 Runbook

Kubernetes event, Pod 상태, node GPU metric, vLLM/TEI/Ray/KServe metric, Gateway access log를 같은 request id와 model label로 묶어야 한다. 장애 runbook은 `Pending`, `ContainerCreating`, `Running but not Ready`, `Ready but 5xx`, `Ready but slow`로 나눈다.

## 작성 대기열

| 우선순위 | 글 후보 | 연결 글 |
|---|---|---|
| P0 | GPU DRA 실전 manifest와 scheduler event 읽기 | [[k8s-gpu-scheduling-dra|GPU 스케줄링]] |
| P0 | Gateway API Inference Extension 구조 | [[istio-gateway-inference-routing|Gateway 라우팅]] |
| P1 | Model weight storage와 rollout 순서 | [[kserve-llminferenceservice-deep-dive|KServe]] |
| P1 | Ray on Kubernetes와 KubeRay 운영 | [[ray-serve-llm-deep-dive|Ray Serve]] |
| P2 | AI serving observability dashboard 설계 | [[llm-observability-cost|관측성과 비용]] |

## 참고 자료

- [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [Gateway API Inference Extension](https://gateway-api-inference-extension.sigs.k8s.io/)
- [KServe documentation](https://kserve.github.io/website/)

## 파트 안의 파트 설계

Kubernetes AI Infra는 `GPU`, `Gateway`, `Storage`, `Serving control plane`, `Observability`, `Security`로 나눈다. GPU 파트 안에는 Device Plugin, DRA, MIG, topology, quota가 들어간다. Gateway 파트 안에는 Gateway API, InferencePool, endpoint picker, rate limit이 들어간다. Storage 파트 안에는 model weight, PVC, object storage, cache, credential이 들어간다.

| 깊이 | 예시 목차 | 작성 기준 |
|---|---|---|
| 대분류 | Kubernetes AI Infra | cluster와 model workload 경계 |
| 하위 파트 | GPU, Gateway, Storage, Control Plane | Kubernetes resource 책임 분리 |
| 세부 파트 | DRA, InferencePool, PVC, KServe, Ray | manifest와 event 중심 |
| 실전 글 | 장애 runbook, dashboard, autoscaling | Pod 상태와 runtime metric 연결 |

## 완성 기준

Kubernetes 글은 YAML 예시만으로 끝나면 안 된다. `kubectl get`, `describe`, event, metric, Gateway route, runtime endpoint로 실제 상태를 확인하는 절차가 있어야 한다. 특히 AI serving에서는 Pod가 Running이어도 모델이 준비되지 않을 수 있으므로 readiness와 route 상태를 따로 본다.

![Kubernetes AI Infra 목차: GPU, Gateway, Storage, Serving Control Plane 구조도](figures/architecture.svg?v=part-hubs-20260706)

*Figure 2: Kubernetes AI Infra 목차: GPU, Gateway, Storage, Serving Control Plane 하위 파트 구조도. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
