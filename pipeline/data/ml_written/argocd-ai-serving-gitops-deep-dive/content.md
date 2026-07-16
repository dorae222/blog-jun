<!-- infographic-hero -->
![ArgoCD AI Serving GitOps: Application, Sync Wave, Health, Rollback 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: ArgoCD AI Serving GitOps: Application, Sync Wave, Health, Rollback 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# ArgoCD AI Serving GitOps: Application, Sync Wave, Health, Rollback

ArgoCD는 Helm chart를 배포하는 UI가 아니다. 운영 관점에서 ArgoCD는 Git에 선언된 desired state와 cluster의 live state를 비교하고, sync와 health를 통해 배포 상태를 판단하는 control plane이다. AI serving에서는 이 역할이 더 중요하다. 모델 서버는 image, model weight, GPU resource, Secret, PVC, Gateway route가 함께 움직이기 때문이다.

## Application을 어떻게 자를까

AI serving에서 Application 경계는 팀 경계와 rollback 경계를 함께 고려해야 한다. `model-runtime` Application에는 vLLM/KServe/Ray Serve runtime과 공통 ServiceAccount를 넣고, `model-serving-prod` Application에는 실제 모델 workload, values, route를 넣을 수 있다. Gateway controller나 CRD는 platform Application으로 분리하는 편이 좋다. 이렇게 나누면 모델 교체가 platform controller rollout과 함께 묶이지 않는다.

AppProject는 이 경계를 강제하는 장치다. source repo, destination namespace, cluster, resource kind를 제한하면 모델 팀이 cluster-wide 리소스를 실수로 바꾸는 일을 줄일 수 있다. 특히 GPU node, Gateway, Secret, ExternalSecret 같은 민감한 리소스는 AppProject와 RBAC로 경계를 분명히 둬야 한다.

## Sync wave와 health

AI serving 배포는 순서가 중요하다. CRD가 먼저 있어야 custom resource를 apply할 수 있고, controller가 준비되어야 LLMInferenceService나 InferencePool 상태가 갱신된다. 그 다음 Secret/PVC/model workload, 마지막으로 Gateway route를 열어야 한다. ArgoCD sync wave는 이 순서를 manifest annotation으로 표현한다.

Health check도 기본값만으로 부족하다. Deployment가 Available이어도 모델 weight load가 끝나지 않았거나 OpenAI-compatible endpoint가 503을 반환할 수 있다. KServe/Ray/Kubernetes custom resource는 필요하면 ArgoCD custom health를 두고, model endpoint readiness와 route availability를 함께 보도록 만든다.

## Diff와 rollback

AI serving workload는 runtime controller가 status와 일부 annotation을 채운다. 이 필드를 drift로 오해하면 항상 OutOfSync가 된다. 반대로 실제 drift, 예를 들어 운영자가 live cluster에서 resource limit이나 route weight를 직접 바꾼 상황은 반드시 잡아야 한다. diff customization은 무시할 필드와 반드시 잡을 필드를 나누는 작업이다.

Rollback은 네 단위로 나눠야 한다. 첫째, container image rollback. 둘째, model weight/version rollback. 셋째, Helm values rollback. 넷째, traffic route rollback. 이 넷을 하나의 commit으로만 묶으면 빠르게 되돌릴 수 없다. 특히 대형 모델은 image보다 weight load 시간이 길기 때문에 route rollback을 먼저 수행하고 model rollout을 뒤에서 정리하는 전략이 필요하다.

## 기존 글과 이어서 보기

- Helm values와 chart 기본기는 [[helm-argocd-ai-serving-gitops|Helm/ArgoCD로 AI Serving 배포하기]]와 [[ckad-24-helm-basics|Helm chart 기본기]]에서 본다.
- Kubernetes 리소스 적용 순서는 [[kubernetes-ai-serving-infra|Kubernetes AI Serving Infra]]에서 본다.
- Gateway route rollback은 [[istio-gateway-inference-routing|Istio/Gateway API 추론 라우팅]]과 연결된다.


## ApplicationSet과 환경 분리

단일 cluster만 운영해도 ApplicationSet을 고려할 만하다. dev, staging, prod가 같은 chart를 쓰되 values만 달라진다면 ApplicationSet의 list, git, matrix generator로 환경별 Application을 생성할 수 있다. 중요한 것은 generator가 편하다는 점이 아니라 환경별 차이를 선언적으로 보이게 만든다는 점이다.

AI serving에서는 환경별 차이가 많다. dev는 작은 모델과 낮은 GPU request를 쓰고, staging은 prod와 같은 route 구조를 쓰며, prod는 autoscaling, rate limit, alert, rollback 정책을 갖는다. 이 차이가 values 파일에 숨으면 review가 어렵다. ApplicationSet template에는 destination namespace, values 파일, sync policy, project를 명시적으로 둔다.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: model-serving-prod
spec:
  project: ai-serving
  source:
    repoURL: https://git.example.com/platform/model-serving.git
    targetRevision: main
    path: charts/model-serving
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-serving
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Sync wave 예시

ArgoCD sync wave는 AI serving에서 특히 유용하다. CRD와 controller가 먼저 적용되지 않으면 custom resource가 실패하고, model workload가 준비되기 전에 Gateway route가 열리면 사용자는 503을 받는다. wave는 이 순서를 리소스 annotation으로 명시한다.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "20"
```

권장 순서는 대략 `0 CRD`, `5 controller`, `10 namespace/RBAC/secret`, `20 runtime/model workload`, `30 service/route`, `40 monitor/alert`이다. hook은 DB migration이나 one-shot 준비 작업처럼 명확히 종료되는 작업에만 쓰고, 장시간 실행되는 모델 서버를 hook처럼 다루지 않는다.

## Health와 diff 운영

ArgoCD 기본 health는 Kubernetes built-in 리소스에는 충분하지만 model serving CRD에는 부족할 수 있다. 예를 들어 LLMInferenceService나 RayService가 내부적으로 Deployment와 Service를 만들더라도, custom resource status가 model ready를 나타내지 않으면 ArgoCD 화면은 실제 endpoint 상태를 설명하지 못한다. 이때는 custom health script를 두거나 controller가 status condition을 명확히 채우도록 설계해야 한다.

Diff customization도 조심해야 한다. runtime controller가 채우는 status 필드나 timestamp는 무시할 수 있지만, resource limit, image tag, route weight, Secret reference drift는 반드시 보여야 한다. 무시 목록을 넓게 잡으면 편하지만, 운영자가 live cluster에서 급히 수정한 값이 Git으로 돌아오지 않는 문제가 생긴다.

## 운영 체크리스트

- AppProject가 namespace, cluster, source repo, resource kind를 제한하는가.
- sync wave로 CRD, controller, Secret, workload, route 순서가 고정되는가.
- model endpoint readiness가 ArgoCD health에 반영되는가.
- self-heal과 prune을 prod에서 어디까지 허용할지 정했는가.
- rollback은 commit revert만이 아니라 route weight와 model version 단위로 가능한가.
- sync 실패, health degraded, diff 발생이 알림으로 연결되는가.

## 배포 시나리오로 보는 ArgoCD

새 모델 버전을 배포한다고 가정해보자. 첫 commit은 model weight version과 image tag를 바꾼다. ArgoCD는 diff를 보여주고, reviewer는 GPU request와 route 정책까지 함께 본다. sync가 시작되면 runtime 리소스가 먼저 갱신되고, model workload가 새 Pod를 만들며, readiness가 통과한 뒤 route가 열려야 한다. 여기서 route를 먼저 바꾸면 사용자는 아직 준비되지 않은 endpoint로 들어가게 된다.

두 번째 시나리오는 빠른 rollback이다. 새 모델의 품질 문제가 발견됐지만 Pod 자체는 정상이라면 image rollback보다 route weight rollback이 먼저일 수 있다. Gateway나 InferencePool이 트래픽 weight를 지원한다면 old endpoint로 traffic을 되돌리고, 뒤에서 Git commit을 정리한다. ArgoCD가 모든 drift를 즉시 self-heal하도록 설정되어 있으면 이런 긴급 조치와 충돌할 수 있으므로 prod에서는 break-glass 정책과 Git 반영 절차를 함께 정의해야 한다.

세 번째 시나리오는 controller upgrade다. Gateway controller, KServe controller, Ray operator 같은 platform component를 모델 workload와 같은 Application에 넣으면 controller upgrade 실패가 모델 rollout과 함께 묶인다. controller는 platform Application, model은 service Application으로 나누고 sync window도 다르게 잡는 것이 운영상 명확하다.

## ArgoCD 화면에서 봐야 할 신호

ArgoCD UI에서 `Synced`와 `Healthy`만 보는 것은 부족하다. 어떤 resource가 어떤 wave에서 적용됐는지, Hook이 실패했는지, live manifest에서 runtime controller가 채운 필드와 Git에 없는 drift가 섞였는지 확인해야 한다. AI serving에서는 model endpoint가 실제로 ready인지가 핵심이므로 health condition이 endpoint readiness를 반영하지 못한다면 UI가 정상처럼 보여도 사용자는 실패를 겪을 수 있다.

따라서 ArgoCD 화면은 배포의 시작점이고, 최종 판단은 Gateway metric, runtime metric, smoke test 결과와 함께 내려야 한다.
## 참고 자료

- [Argo CD Sync Phases and Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)
- [Argo CD Resource Health](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/)
- [Argo CD ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/)
- [Argo CD Diff Customization](https://argo-cd.readthedocs.io/en/stable/user-guide/diffing/)

![ArgoCD AI Serving GitOps: Application, Sync Wave, Health, Rollback 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: ArgoCD AI Serving GitOps: Application, Sync Wave, Health, Rollback 운영 구조. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
