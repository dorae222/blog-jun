<!-- infographic-hero -->
![Helm/ArgoCD로 AI Serving 배포하기: values, sync waves, health 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Helm/ArgoCD로 AI Serving 배포하기: values, sync waves, health 한 장 요약. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

# Helm/ArgoCD로 AI Serving 배포하기: values, sync waves, health

AI serving 배포는 Deployment 하나가 아니라 Secret, PVC, Runtime, Model, Service, HTTPRoute, autoscaler가 함께 움직인다. Helm values는 모델과 runtime 설정을 반복 가능한 입력으로 만들고, ArgoCD sync waves는 CRD, controller, model workload, route의 적용 순서를 만든다. Health check가 약하면 GitOps 화면은 녹색인데 endpoint는 아직 준비되지 않은 상태가 된다.

![Helm/ArgoCD로 AI Serving 배포하기: values, sync waves, health 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Helm/ArgoCD로 AI Serving 배포하기: values, sync waves, health 운영 흐름. (Source: 공식 문서와 원문 저장소 기반 자체 작성)*

## 어디까지 다루는 글인가

이 글은 Helm과 ArgoCD를 일반 배포 도구로 설명하지 않는다. 모델명, runtime flag, GPU request, Secret, PVC, Service, HTTPRoute, autoscaling threshold가 함께 바뀌는 AI serving 배포를 GitOps 단위로 정리한다. 서빙 런타임 자체의 내부 구조나 GPU 스케줄링 세부는 각 주제 글로 연결만 하고, 여기서는 "값을 어떻게 파라미터화하고, 어떤 순서로 적용하며, 무엇을 준비 완료로 판정하는가"에 집중한다.

## 체크포인트

| 항목 | 확인 기준 |
|------|-----------|
| Values | 모델별 override와 환경별 override가 섞이지 않았는가 |
| Sync wave | CRD/controller가 workload보다 먼저 적용되는가 |
| Health | Pod ready만이 아니라 model endpoint health를 반영하는가 |
| Rollback | 모델 weight, image, route 변경을 어떤 단위로 되돌릴지 정했는가 |

## Helm으로 서빙 리소스 패키징하기

AI serving 배포는 Deployment 하나로 끝나지 않는다. runtime, model, autoscaler, Service, route, Secret, PVC가 한 묶음으로 움직이고, 모델을 바꾸거나 환경을 옮길 때마다 이 묶음 전체가 조금씩 달라진다. Helm chart는 이 묶음을 template으로 고정하고, 달라지는 값만 values로 빼내는 도구다.

핵심은 무엇을 values로 열어 둘지 정하는 것이다. 모델명, runtime 종류(vLLM, KServe runtime 등), replica 수, GPU request, 메모리 limit, autoscaling threshold처럼 배포마다 바뀌는 값은 values로 파라미터화한다. 반대로 label 규칙, probe 경로, security context처럼 조직 전체가 공유하는 값은 template 안에 고정해 매번 재입력하지 않게 한다.

```yaml
# values.yaml - chart가 노출하는 입력
model:
  name: my-llm
  storageUri: pvc://model-store/my-llm
runtime:
  kind: vllm
  args:
    - "--max-model-len=8192"
replicas: 2
resources:
  limits:
    nvidia.com/gpu: 1
    memory: 24Gi
autoscaling:
  minReplicas: 1
  maxReplicas: 4
```

같은 chart를 environment별 values로 나눠 재사용한다. dev에서는 replica 하나에 작은 GPU를, prod에서는 replica 여러 개에 큰 GPU를 배정하는 식이다. 이렇게 하면 dev와 prod가 같은 template을 공유하므로, "dev에서는 되는데 prod에서만 깨지는" 구성 drift를 줄일 수 있다. values를 겹쳐 쓰는 방식이 부담스러우면 [[ckad-25-kustomize-basics|Kustomize 기본기]]의 overlay 방식과 비교해 팀에 맞는 쪽을 고른다. Helm 자체가 처음이라면 [[ckad-24-helm-basics|Helm 기본기]]에서 template과 values 구조를 먼저 잡는 편이 좋다.

서빙 runtime을 template으로 감쌀 때는 runtime마다 리소스 모양이 다르다는 점을 기억한다. KServe의 InferenceService, vLLM Deployment, Ray Serve application은 각각 스펙이 다르므로, 하나의 chart로 모두 감싸기보다 runtime별 chart를 두고 values로 모델만 갈아끼우는 편이 단순하다. runtime 선택 자체는 [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]]과 [[vllm-serving-architecture|vLLM 서빙 아키텍처]]에서 판단하고, KServe 리소스는 [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService 심화]], Ray 기반 서빙은 [[kserve-ray-serve-llm|KServe와 Ray Serve LLM]]에서 이어 본다.

## ArgoCD로 GitOps 파이프라인 구성하기

Helm이 "무엇을 배포할지"를 template으로 만든다면, ArgoCD는 "Git에 적힌 상태를 클러스터에 계속 맞추는" 역할을 한다. Git repository가 desired state이고, ArgoCD가 실제 cluster state와 비교해 차이(diff)를 없애는 방향으로 동기화한다. 사람이 `kubectl apply`를 직접 치지 않고, 변경은 항상 Git commit으로 들어온다. 그래서 "누가 무엇을 언제 바꿨는가"가 commit history로 남는다.

기본 단위는 Application이다. Application은 "이 Git 경로의 manifest를 이 cluster/namespace에 sync한다"는 선언이고, Helm chart와 values 경로를 여기서 가리킨다.

```yaml
# ArgoCD Application - Git 경로와 대상 클러스터를 연결
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-llm-serving
spec:
  source:
    repoURL: https://git.example.com/serving
    path: charts/llm-serving
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    namespace: serving
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

여기서 두 옵션이 GitOps의 성격을 결정한다. prune은 Git에서 사라진 리소스를 cluster에서도 지운다. selfHeal은 누군가 cluster를 직접 손대 Git과 어긋나면 다시 Git 상태로 되돌린다. 즉 Git이 유일한 진실이 되고, 수동 변경은 흡수된다.

AI serving에서 특히 중요한 것이 sync wave다. serving 묶음은 적용 순서가 있다. CRD와 namespace가 먼저 있어야 InferenceService 같은 custom resource가 인식되고, controller가 떠 있어야 그 resource가 실제 workload로 풀린다. gateway route는 workload가 준비된 뒤에 붙어야 한다. ArgoCD는 `argocd.argoproj.io/sync-wave` annotation으로 이 순서를 만든다. 숫자가 작은 wave가 먼저 적용된다.

```yaml
# 낮은 wave부터 순서대로 적용된다
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-1"   # CRD, namespace
# "0"  controller, runtime
# "1"  model workload (InferenceService 등)
# "2"  gateway route, autoscaler
```

health check는 "이 리소스가 준비됐는가"를 판정하는 규칙이다. ArgoCD는 기본 리소스(Deployment, Service 등)에 대한 health 판정을 내장하지만, InferenceService 같은 custom resource는 별도 health 규칙이 있어야 제대로 판정된다. 이 판정이 약하면 ArgoCD 화면은 녹색인데 model endpoint는 아직 로딩 중인 상태가 된다. 그리고 sync wave는 health가 정확할 때만 의미가 있다. 앞 wave가 "준비됨"으로 잘못 판정되면 뒤 wave가 너무 일찍 적용되기 때문이다. Application, AppProject, health 규칙, rollback을 더 깊게 다루는 내용은 [[argocd-ai-serving-gitops-deep-dive|ArgoCD AI Serving GitOps 심화]]에, GitOps 개념 전반은 [[argocd-gitops-hub|ArgoCD GitOps 허브]]에 정리돼 있다.

## AI 서빙에 특유한 고려사항

일반 웹 서비스 GitOps와 달리, 모델 서빙에는 배포를 느리고 무겁게 만드는 요소가 있다. 이 차이를 무시하면 sync가 "성공"으로 뜬 뒤에도 한참 동안 실제 트래픽을 못 받는다.

첫째, 이미지와 가중치가 크다. runtime 컨테이너 이미지 자체도 무겁고, 모델 weight는 수 GB에서 수십 GB에 이른다. 이미지에 weight를 굽지 않고 PVC나 object storage에서 불러오는 구조가 흔한데, 그러면 Pod가 뜬 뒤에도 weight를 내려받고 메모리로 올리는 시간이 필요하다. health check는 이 시간을 반영해야 한다. Pod ready와 model ready는 다른 사건이다.

둘째, GPU가 스케줄링 병목이다. GPU를 요구하는 Pod는 GPU node가 있어야만 뜬다. sync는 즉시 되지만 Pod는 Pending으로 오래 남을 수 있다. 배포 순서를 짤 때 GPU 자원 확보를 전제로 두어야 하며, 스케줄링 세부는 [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링과 DRA]]에서 다룬다. 인프라 계층 전반은 [[kubernetes-ai-serving-infra|쿠버네티스 AI 서빙 인프라]]와 [[kubernetes-ai-infra-hub|쿠버네티스 AI 인프라 허브]]로 잇는다.

셋째, 롤아웃 시 워밍업이 필요하다. 새 replica는 weight 로딩과 CUDA graph, KV cache 초기화를 마쳐야 정상 지연시간을 낸다. 이 준비가 끝나기 전에 gateway가 트래픽을 보내면 초기 요청의 지연이 튄다. 그래서 readiness probe와 gateway route 연결 시점을 sync wave로 늦춰, 워밍업이 끝난 replica에만 트래픽이 가도록 한다. gateway 라우팅 설계는 [[istio-gateway-inference-routing|Istio Gateway 추론 라우팅]]을 참고한다.

넷째, 의존 순서가 실제로 존재한다. runtime CRD 다음 controller, 그다음 model workload, 그다음 route와 autoscaler 순서가 지켜지지 않으면, custom resource가 무시되거나 route가 빈 backend를 가리킨다. 이 순서를 문서 밖 암묵지로 두지 말고 sync wave 숫자로 코드에 박아 둔다.

## 실무 설계: sync wave와 health를 어떻게 나눌까

프로덕션으로 옮길 때 먼저 못박아야 할 결정은 네 가지다. 앞의 체크포인트 표를 각 결정으로 풀어 쓴 것이다.

values 분리 기준을 정한다. 모델별로 바뀌는 값(모델명, weight 경로)과 환경별로 바뀌는 값(replica, GPU 크기)을 다른 파일로 나눈다. 두 축이 한 파일에 섞이면, prod의 GPU 설정을 바꾸려다 모델 설정까지 건드리는 사고가 난다.

sync wave 경계를 정한다. 최소한 CRD/namespace, controller/runtime, model workload, route/autoscaler 네 단계로 나눈다. 단계를 너무 잘게 쪼개면 배포가 느려지고, 너무 뭉치면 순서 보장이 깨진다. 위에서 본 -1 / 0 / 1 / 2 정도가 출발점으로 무난하다.

health를 endpoint까지 확장한다. Pod ready에서 멈추지 말고, model endpoint가 실제 응답하는지를 health 규칙에 넣는다. 이래야 ArgoCD의 녹색이 "트래픽 받을 준비 완료"와 같은 뜻이 된다.

rollback 단위를 나눠 기록한다. 서빙에서 되돌릴 대상은 하나가 아니다. runtime image, model weight, gateway route는 각각 독립적으로 문제를 일으킬 수 있으므로, 무엇을 어느 commit으로 되돌릴지 단위를 미리 정한다. GitOps에서 rollback은 이전 commit으로 되돌리는 일이므로, 커밋 하나에 여러 축을 섞지 않는 것이 rollback을 쉽게 만든다.

이 네 결정을 세우고 나면 운영 중 관찰 대상도 분명해진다. drift(Git과 cluster의 차이), sync 실패, health 오판정, 그리고 배포 후 실제 지연시간과 비용이다. 특히 서빙은 배포가 "성공"해도 지연시간과 비용이 나빠질 수 있으므로, 배포 지표와 서빙 지표를 함께 본다. 서빙 관측성과 비용은 [[llm-observability-cost|LLM 관측성과 비용]]에서, 서빙 스택 전체 지도는 [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]]에서 이어 본다.

## 참고 자료

- [Helm values files](https://helm.sh/docs/chart_template_guide/values_files/)
- [Argo CD sync waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)
- [Argo CD health checks](https://argo-cd.readthedocs.io/en/latest/operator-manual/health/)

## 관련 문서

- [[ai-model-serving-platform-map|AI 모델 서빙 플랫폼 지도]] - 서빙 스택 전체 분기점
- [[argocd-ai-serving-gitops-deep-dive|ArgoCD AI Serving GitOps 심화]] - Application, sync wave, health, rollback 상세
- [[argocd-gitops-hub|ArgoCD GitOps 허브]] - GitOps 개념 전반
- [[llm-serving-runtime-stack|LLM 서빙 런타임 스택]] - runtime 선택 지도
- [[kserve-llminferenceservice-deep-dive|KServe LLMInferenceService 심화]] - KServe 서빙 리소스
- [[kserve-ray-serve-llm|KServe와 Ray Serve LLM]] - Ray Serve 기반 서빙
- [[ray-serve-llm-deep-dive|Ray Serve LLM 심화]] - Ray Serve 내부 구조
- [[vllm-serving-architecture|vLLM 서빙 아키텍처]] - vLLM runtime 내부
- [[kubernetes-ai-serving-infra|쿠버네티스 AI 서빙 인프라]] - 서빙 인프라 계층
- [[kubernetes-ai-infra-hub|쿠버네티스 AI 인프라 허브]] - 인프라 주제 허브
- [[k8s-gpu-scheduling-dra|K8s GPU 스케줄링과 DRA]] - GPU 스케줄링
- [[istio-gateway-inference-routing|Istio Gateway 추론 라우팅]] - gateway 라우팅
- [[llm-observability-cost|LLM 관측성과 비용]] - 배포 후 지표와 비용
- [[model-inference-research-hub|모델 추론 리서치 허브]] - 추론 최적화 연구 지도
- [[ckad-24-helm-basics|Helm 기본기]] - Helm template과 values
- [[ckad-25-kustomize-basics|Kustomize 기본기]] - values 대신 overlay 방식
