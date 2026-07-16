<!-- infographic-hero -->
![KServe LLMInferenceService: Kubernetes-native LLM Serving Control Plane 핵심 요약](figures/infographic.svg?v=runtime-tabs-20260706)

*Figure 1: KServe LLMInferenceService: Kubernetes-native LLM Serving Control Plane 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# KServe LLMInferenceService: Kubernetes-native LLM Serving Control Plane

KServe는 단순히 모델 서버를 감싸는 wrapper가 아니다. Kubernetes API를 model serving control plane으로 쓰겠다는 선택이다. 특히 LLMInferenceService는 generative inference workload를 Kubernetes-native CRD로 표현한다. 이 글은 KServe와 Ray Serve를 함께 설명하지 않고, KServe만 독립 파트로 다룬다.

KServe를 선택한다는 것은 모델 serving lifecycle을 YAML, CRD, controller, status condition, Gateway, RBAC, GitOps로 관리하겠다는 뜻이다. Python application graph보다 platform API가 중요하고, 여러 팀이 같은 cluster에서 모델을 운영하며, ArgoCD와 RBAC로 변경을 통제해야 한다면 KServe가 자연스럽다.

## LLMInferenceService의 역할

KServe 공식 CRD reference 기준 LLMInferenceService는 단일 LLM deployment를 나타내며 underlying Kubernetes resources, 예를 들어 Deployment와 Service, networking 노출을 orchestrate한다. 최신 문서에서는 LLMInferenceService가 Gateway API ingress, intelligent scheduler, storage initializer, multi-node deployment, prefill-decode separation 같은 generative inference 운영 주제를 포함한다.

중요한 점은 LLMInferenceService가 model server 자체가 아니라 control plane API라는 것이다. 실제 token generation runtime은 vLLM 같은 engine일 수 있고, KServe는 그 runtime을 Kubernetes 리소스로 배치하고 상태를 관리한다. 따라서 KServe metric만 보면 부족하고, underlying runtime metric도 같이 봐야 한다.

## YAML과 운영 contract

KServe 운영 문서에는 spec만이 아니라 status condition을 같이 써야 한다. Git에는 desired state가 있고, controller는 live state를 reconcile한다. Pod가 떠 있는지, model weight가 준비됐는지, endpoint가 route에 붙었는지, scheduler가 traffic을 보낼 수 있는지 condition과 event로 확인해야 한다.

```yaml
apiVersion: serving.kserve.io/v1alpha2
kind: LLMInferenceService
metadata:
  name: llama-prod
spec:
  model:
    uri: hf://meta-llama/Llama-3.1-8B-Instruct
  replicas: 3
```

이 예시는 실제 운영 manifest의 축만 보여준다. production에서는 ServiceAccount, Secret, storage credential, GPU request, runtime config, Gateway route, autoscaling, monitoring annotation, network policy가 함께 들어간다. CRD가 간단하다고 운영이 간단한 것은 아니다.

## Gateway와 scheduler

LLM traffic은 일반 REST traffic보다 routing 기준이 많다. endpoint가 ready인지, prefix cache가 있는지, load가 높은지, prefill/decode 역할이 나뉘는지에 따라 routing decision이 달라진다. KServe 문서에서는 Gateway API와 intelligent scheduler, prefix cache routing, load-aware scheduling 같은 주제를 다룬다. 즉 KServe는 단순 Service load balancing보다 LLM 특화 routing으로 확장되는 흐름에 있다.

Gateway route를 열기 전 model endpoint가 ready인지 확인해야 한다. ArgoCD health도 Deployment Available만 보면 부족하고, LLMInferenceService status와 route availability를 함께 봐야 한다. Gateway, KServe, vLLM metric이 연결되지 않으면 사용자는 503을 보는데 ArgoCD는 Healthy로 보일 수 있다.

## KServe 파트에서 파생할 글

| 글 후보 | 다룰 내용 | 연결 글 |
|---|---|---|
| LLMInferenceService spec | model, runtime, replicas, worker, status condition | 이 글 |
| KServe Gateway 운영 | Gateway API, InferencePool, scheduler, route health | [[istio-gateway-inference-routing|Gateway 라우팅]] |
| KServe GitOps | CRD/controller/model/route sync wave와 health | [[argocd-ai-serving-gitops-deep-dive|ArgoCD]] |
| KServe Storage | storage initializer, model download, private model | Kubernetes storage 글 |
| KServe vs Ray Serve | CRD control plane과 Python graph 선택 기준 | [[kserve-ray-serve-llm|비교 허브]] |

## 운영 Runbook

LLMInferenceService가 준비되지 않으면 먼저 CRD와 controller 상태를 본다. controller가 reconcile하지 못하면 RBAC, namespace, CRD version, event를 확인한다. Pod가 생성됐지만 모델이 준비되지 않으면 storage initializer, model URI, Secret, PVC, image pull을 본다. endpoint는 있는데 외부 요청이 실패하면 Gateway, HTTPRoute, scheduler, Service endpoint를 본다. latency가 높으면 KServe가 아니라 runtime(vLLM) metric으로 내려간다.

## 기존 글과 이어서 보기

- Kubernetes 기준선은 [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]]에서 본다.
- generation runtime 내부는 [[vllm-serving-architecture|vLLM]]에서 본다.
- ArgoCD 운영은 [[argocd-ai-serving-gitops-deep-dive|ArgoCD AI Serving GitOps]]에서 본다.
- Ray Serve와의 선택 기준은 [[kserve-ray-serve-llm|KServe vs Ray Serve]]에서 본다.

## 참고 자료

- [KServe LLMInferenceService overview](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview)
- [KServe CRD API reference](https://kserve.github.io/website/docs/reference/crd-api)
- [KServe documentation](https://kserve.github.io/website/)

## 설치 계층과 소유권

KServe 운영은 세 계층으로 나눠야 한다. 첫째, platform 계층에는 CRD, KServe controller, Gateway controller, cert-manager, GPU operator 같은 cluster-wide component가 들어간다. 둘째, namespace 계층에는 ServiceAccount, RoleBinding, Secret, NetworkPolicy, storage credential이 들어간다. 셋째, service 계층에는 LLMInferenceService, route, autoscaling, monitoring 리소스가 들어간다.

이 계층을 한 Helm release에 모두 넣으면 rollout과 rollback이 어려워진다. controller upgrade는 platform team이 관리하고, model deployment는 model team이 관리하는 편이 안전하다. AppProject와 RBAC도 이 경계를 반영해야 한다. 모델 팀이 CRD나 GatewayClass를 바꾸지 못하게 하고, platform 팀은 model weight와 prompt 설정에 불필요하게 관여하지 않는 구조가 좋다.

## Multi-node와 대형 모델

대형 LLM은 단일 Pod와 단일 GPU로 끝나지 않는다. multi-node serving에서는 worker lifecycle, network topology, NCCL/RDMA, model download, startup ordering이 중요하다. KServe 문서가 LeaderWorkerSet, multi-node deployment, prefill/decode separation 같은 주제를 다루는 이유가 여기에 있다. Kubernetes YAML만 보면 간단해 보여도 실제 운영은 distributed system이다.

대형 모델 rollout은 특히 느리다. image pull보다 model weight download와 warmup이 더 오래 걸릴 수 있고, Gateway route를 너무 빨리 열면 ready가 아닌 endpoint로 traffic이 간다. 그래서 smoke test, readiness, route open 순서를 명시해야 한다. ArgoCD sync wave와 KServe status condition을 함께 보는 이유도 이 때문이다.

## Custom health와 diff

ArgoCD 기본 health는 LLMInferenceService의 실제 준비 상태를 충분히 설명하지 못할 수 있다. custom health를 두거나 KServe condition을 읽어 `Ready`, `ModelLoaded`, `RouteReady` 같은 상태를 UI에서 보이게 만든다. diff customization도 필요하다. controller가 채우는 status/timestamp는 무시하지만, model URI, resource limit, route policy, Secret reference 변경은 반드시 잡아야 한다.

KServe를 도입하는 목표는 "모델을 YAML로 배포했다"가 아니다. 모델 lifecycle이 review 가능하고, rollback 가능하며, 상태를 설명할 수 있어야 한다. 이 기준을 만족하지 못하면 CRD를 써도 운영은 여전히 수동 절차에 의존한다.

## 실제로 분리해서 쓸 하위 목차

KServe 탭은 Kubernetes 운영자 관점에서 충분히 큰 주제다. 첫째, 설치 글에서는 CRD, controller, Gateway controller, cert-manager, namespace 정책을 다룬다. 둘째, LLMInferenceService spec 글에서는 model URI, runtime, replica, worker, status condition을 다룬다. 셋째, storage 글에서는 storage initializer, private/gated model, PVC, object storage, download retry를 다룬다. 넷째, routing 글에서는 Gateway API, scheduler, InferencePool, endpoint health를 다룬다. 다섯째, GitOps 글에서는 ArgoCD sync wave, custom health, diff customization, rollback을 다룬다. 여섯째, multi-node 글에서는 LeaderWorkerSet, RDMA, topology, prefill/decode separation을 다룬다.

이 구조가 있으면 KServe는 vLLM을 배포하는 부속 도구가 아니라 model platform control plane으로 다뤄진다. runtime과 control plane을 분리해야 KServe와 vLLM의 책임도 명확해진다.

## 운영 문서 최소 구성

이 runtime 파트의 모든 후속 글은 같은 형식을 따른다. 먼저 어떤 request path를 책임지는지 한 문장으로 정의한다. 다음으로 배포 단위, 설정값, metric, 장애 증상, rollback 단위를 표로 적는다. 마지막에는 "이 runtime이 맡지 않는 책임"을 명시한다. 이 경계가 있어야 vLLM, TEI, KServe, Ray Serve가 서로 섞이지 않고 독립 탭처럼 쌓인다.

![KServe LLMInferenceService: Kubernetes-native LLM Serving Control Plane 운영 구조](figures/architecture.svg?v=runtime-tabs-20260706)

*Figure 2: KServe LLMInferenceService: Kubernetes-native LLM Serving Control Plane 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
