<!-- infographic-hero -->
![Kubernetes AI Serving Infra: GPU, Runtime, Gateway, Observability 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Kubernetes AI Serving Infra: GPU, Runtime, Gateway, Observability 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# Kubernetes AI Serving Infra: GPU, Runtime, Gateway, Observability

AI 모델 서빙을 Kubernetes에서 운영한다는 것은 GPU가 달린 Pod를 띄우는 일이 아니다. 모델 weight를 어디에 둘지, runtime이 어떤 방식으로 GPU를 잡을지, Gateway가 어떤 replica로 요청을 보낼지, autoscaler가 어떤 신호를 볼지까지 한 번에 설계해야 한다. 그래서 이 글은 `ai-model-serving-platform-map`의 하위 목차가 아니라 Kubernetes 파트의 독립 기준 글로 둔다.

## Kubernetes에서 먼저 나눌 경계

첫 번째 경계는 cluster와 workload다. cluster에는 GPU node pool, CNI, storage class, observability agent, Gateway controller가 들어간다. workload에는 model server, tokenizer, embedding/rerank endpoint, worker, autoscaler가 들어간다. 이 둘을 섞으면 모델 교체와 cluster 운영이 함께 흔들린다.

두 번째 경계는 GPU allocation이다. 단순한 `resources.limits.nvidia.com/gpu: 1`은 시작점일 뿐이다. multi-GPU inference, MIG, NUMA/NVLink locality, DRA ResourceClaim이 등장하면 scheduler가 어떤 device를 어떤 Pod에 붙였는지 추적해야 한다. 이 부분은 [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링]] 글에서 더 자세히 본다.

세 번째 경계는 serving runtime이다. vLLM은 OpenAI-compatible endpoint와 KV cache/scheduler 관점이 중요하고, KServe는 CRD 기반 model lifecycle, Ray Serve는 Python serving graph와 worker lifecycle이 중요하다. Kubernetes에서는 이 차이가 Deployment, Service, head/worker, CRD, Gateway 리소스로 드러난다.

## 운영자가 보는 상태

Kubernetes 운영자는 Pod `Running`만 보지 않는다. 모델 서버에서는 TTFT, inter-token latency, queue time, cache hit, OOM, model load time이 중요하다. Gateway에서는 HTTP status보다 route별 latency와 retry, rate limit, upstream selection이 중요하다. GPU node에서는 allocatable, memory pressure, ECC/Xid, device plugin heartbeat가 중요하다.

따라서 대시보드는 네 층을 같이 보여줘야 한다. 첫째, Kubernetes 상태(Pod, Node, Event). 둘째, runtime 상태(vLLM scheduler, KV cache, Ray worker). 셋째, traffic 상태(Gateway route, InferencePool endpoint). 넷째, business 상태(tenant, model, token cost). 이 네 층이 끊기면 장애 시점에 어느 레이어가 병목인지 설명하기 어렵다.

## 기존 글과 이어서 보기

- 기본 Kubernetes 리소스 흐름은 [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]]에서 본다.
- GPU allocation은 [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링]]에서 본다.
- 모델 서버 내부는 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]에서 본다.
- CRD와 Python serving graph 비교는 [[kserve-ray-serve-llm|KServe와 Ray Serve LLM]]에서 본다.
- 추론 라우팅은 [[istio-gateway-inference-routing|Istio/Gateway API 추론 라우팅]]에서 본다.
- GitOps 운영은 [[argocd-ai-serving-gitops-deep-dive|ArgoCD AI Serving GitOps]]에서 본다.


## 리소스 경계를 어떻게 자를까

Kubernetes AI serving manifest는 한 디렉터리에 모두 넣을 수 있지만, 운영 경계는 분리해서 생각해야 한다. `00-namespace-rbac.yaml`은 권한과 namespace를 만들고, `10-runtime.yaml`은 serving runtime이나 controller를 준비하며, `20-model.yaml`은 실제 model workload를 만든다. `30-service-route.yaml`은 Service, HTTPRoute, Gateway 연결을 만들고, `40-observability.yaml`은 ServiceMonitor, PodMonitor, dashboard annotation을 담당한다.

이렇게 나누는 이유는 장애 원인이 서로 다르기 때문이다. RBAC가 틀리면 controller가 리소스를 watch하지 못하고, runtime이 준비되지 않으면 model custom resource가 reconcile되지 않는다. 모델 weight가 늦게 내려오면 Pod는 떠 있어도 endpoint가 준비되지 않을 수 있고, Gateway route가 잘못되면 내부 endpoint는 정상이지만 외부 요청은 실패한다.

| 파일 경계 | 포함 리소스 | 검증 명령 |
|---|---|---|
| platform | CRD, controller, GatewayClass, GPU operator | `kubectl get crd`, `kubectl get deploy -n platform` |
| namespace | Namespace, ServiceAccount, RoleBinding, Secret | `kubectl auth can-i`, `kubectl get secret` |
| runtime | RuntimeClass, ServingRuntime, Deployment, RayCluster | `kubectl describe pod`, `kubectl get events` |
| model | LLMInferenceService, Deployment, PVC, ConfigMap | `kubectl get pods,endpoints,pvc` |
| route | Gateway, HTTPRoute, InferencePool, Service | `kubectl get httproute`, `kubectl describe gateway` |
| observe | ServiceMonitor, log pipeline, dashboard | Prometheus target, trace span, log correlation |

## 장애를 레이어별로 나누기

Kubernetes 기반 AI serving 장애는 한 줄 에러로 끝나지 않는다. `Pending`이면 scheduler와 GPU allocation을 보고, `ContainerCreating`이면 image pull, volume mount, Secret, model weight download를 본다. `Running`인데 503이면 readiness, model load, endpoint, Gateway route를 본다. latency가 늘면 Pod 상태보다 runtime queue와 KV cache, GPU memory를 먼저 봐야 한다.

특히 GPU 관련 장애는 Kubernetes event와 runtime metric을 함께 봐야 한다. scheduler는 GPU가 충분하다고 판단했지만 실제 runtime은 model parallelism 때문에 memory가 부족할 수 있다. 반대로 GPU memory는 충분하지만 Gateway가 cache locality를 고려하지 않아 tail latency가 늘어날 수 있다. 그래서 node metric, runtime metric, route metric을 같은 request id로 연결하는 것이 중요하다.

## 설계 체크리스트

- GPU node pool과 일반 worker node pool이 분리되어 있는가.
- Device Plugin 또는 DRA ResourceClaim이 실제 node 상태에 반영되는가.
- model weight 저장소, image registry, Secret 접근이 namespace RBAC와 맞는가.
- Service endpoint가 준비되기 전 Gateway route가 트래픽을 보내지 않는가.
- route별 TTFT, queue time, GPU memory, token/sec를 같은 대시보드에서 보는가.
- GitOps rollback이 image, values, route, model weight 단위로 분리되는가.

## 예시 매니페스트를 읽는 순서

실제 manifest를 볼 때는 YAML을 위에서 아래로 읽지 말고 의존성 순서로 읽는다. `Namespace`와 `ServiceAccount`는 권한 경계를 만들고, `ConfigMap`과 `Secret`은 model server가 시작할 때 필요한 값을 준다. 그 다음 `Deployment`나 `LLMInferenceService`가 GPU request를 선언하고, `Service`가 endpoint를 만들며, `HTTPRoute`나 `InferencePool`이 외부 요청을 연결한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-vllm
spec:
  template:
    spec:
      containers:
        - name: server
          image: vllm/vllm-openai:stable
          resources:
            limits:
              nvidia.com/gpu: "1"
          ports:
            - containerPort: 8000
```

이 YAML에서 중요한 것은 image 이름보다 `resources`, port, readiness, volume mount다. 모델 weight가 container image 안에 있는지, initContainer가 object storage에서 내려받는지, PVC를 붙이는지에 따라 rollout 시간이 크게 달라진다. 또한 GPU limit만 보고 용량을 판단하면 안 된다. 같은 1 GPU라도 모델 크기, tensor parallel, max model length, max num sequences에 따라 실제 처리량은 달라진다.

## 운영 Runbook의 형태

Runbook은 "Pod가 안 뜬다"로 시작하면 너무 넓다. 먼저 상태를 다섯 갈래로 나눈다. `Pending`은 scheduler, quota, GPU allocatable, taint/toleration을 본다. `ContainerCreating`은 image pull, volume, Secret, initContainer를 본다. `Running but not Ready`는 model load와 readiness probe를 본다. `Ready but 5xx`는 Service endpoint와 Gateway route를 본다. `Ready but slow`는 runtime queue, KV cache, GPU memory, upstream selection을 본다.

이 흐름이 문서화되어 있으면 새 모델이 들어와도 운영자는 같은 방식으로 장애를 좁힌다. 반대로 각 모델마다 다른 대시보드와 다른 runbook을 쓰면 장애 대응이 개인 경험에 의존하게 된다.

## 설계 리뷰 때 던질 질문

AI serving PR을 리뷰할 때는 manifest 문법보다 운영 질문을 먼저 던진다. 이 모델은 어느 namespace와 AppProject 안에서 관리되는가. GPU request는 실제 모델 크기와 max context를 반영하는가. readiness는 container가 뜬 상태가 아니라 모델이 요청을 받을 수 있는 상태를 확인하는가. Gateway route는 canary나 rollback을 고려하는가. metric label은 tenant/model/route 단위 분석을 가능하게 하는가.

이 질문에 답할 수 있으면 Kubernetes는 단순 배포 도구가 아니라 모델 운영의 기준면이 된다. 답이 없다면 아직 platform map이 아니라 개별 YAML 조각만 있는 상태다.
## 참고 자료

- [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Gateway API Inference Extension](https://gateway-api-inference-extension.sigs.k8s.io/)
- [KServe LLMInferenceService](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview)

![Kubernetes AI Serving Infra: GPU, Runtime, Gateway, Observability 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Kubernetes AI Serving Infra: GPU, Runtime, Gateway, Observability 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
