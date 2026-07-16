<!-- infographic-hero -->
![ArgoCD/GitOps 목차: Helm, ApplicationSet, Sync Wave, Health, Rollback 핵심 요약](figures/infographic.svg?v=part-hubs-20260706)

*Figure 1: ArgoCD/GitOps 목차: Helm, ApplicationSet, Sync Wave, Health, Rollback 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# ArgoCD/GitOps 목차: Helm, ApplicationSet, Sync Wave, Health, Rollback

ArgoCD/GitOps는 AI serving 배포에서 독립 대분류가 될 만큼 크다. Helm values 몇 개를 바꾸는 글로는 부족하다. 모델 서버는 image, model weight, GPU resource, Secret, PVC, Gateway route, autoscaling, monitor가 함께 움직인다. 이 글은 ArgoCD/GitOps 대분류의 허브이고, [[argocd-ai-serving-gitops-deep-dive|ArgoCD AI Serving GitOps]]는 이 허브 안의 기준 글이다.

## 하위 파트 1: Helm values와 chart 경계

[[helm-argocd-ai-serving-gitops|Helm/ArgoCD로 AI Serving 배포하기]]는 values와 sync wave의 출발점이다. 후속 글은 chart boundary, values schema, environment overlay, secret reference, model version promotion으로 나눈다. Helm chart는 편의 도구가 아니라 배포 contract다.

## 하위 파트 2: Application, AppProject, ApplicationSet

AI serving에서는 platform component와 model workload를 분리해야 한다. Gateway controller, KServe controller, Ray operator는 platform Application이고, model endpoint는 service Application이다. AppProject는 repo, cluster, namespace, resource kind를 제한하고 ApplicationSet은 dev/staging/prod 환경을 반복 생성한다.

## 하위 파트 3: Sync wave와 health

CRD가 먼저, controller가 다음, Secret/PVC/runtime이 다음, model workload가 다음, route가 마지막이다. 이 순서가 깨지면 배포는 성공처럼 보여도 사용자는 503을 받는다. Health는 Deployment Available이 아니라 model endpoint readiness를 반영해야 한다. KServe/Ray/Gateway CRD는 custom health가 필요할 수 있다.

## 하위 파트 4: Diff, rollback, emergency patch

controller가 채우는 status와 timestamp는 무시해도 되지만, image tag, model URI, resource limit, route weight drift는 반드시 잡아야 한다. rollback은 commit revert만으로 끝나지 않는다. image rollback, model weight rollback, values rollback, route weight rollback을 따로 설계한다.

## 작성 대기열

| 우선순위 | 글 후보 | 연결 글 |
|---|---|---|
| P0 | ArgoCD ApplicationSet으로 AI serving multi-env 구성 | [[argocd-ai-serving-gitops-deep-dive|ArgoCD 기준 글]] |
| P0 | Sync wave로 CRD/controller/model/route 순서 고정 | [[helm-argocd-ai-serving-gitops|Helm/ArgoCD]] |
| P1 | KServe/Ray custom health와 diff customization | [[kserve-llminferenceservice-deep-dive|KServe]] |
| P1 | 모델 weight promotion과 route rollback | [[kubernetes-ai-infra-hub|Kubernetes AI Infra]] |
| P2 | GitOps 보안: AppProject, RBAC, Secret boundary | Kubernetes 기본기/RBAC |

## 참고 자료

- [Argo CD Sync Phases and Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)
- [Argo CD ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/)
- [Argo CD Resource Health](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/)

## 파트 안의 파트 설계

ArgoCD/GitOps는 `Helm`, `Application`, `Sync`, `Health`, `Diff`, `Rollback`, `Promotion`으로 나눈다. Helm 파트 안에는 values schema와 environment overlay가 들어간다. Application 파트 안에는 AppProject와 ApplicationSet이 들어간다. Sync 파트 안에는 CRD, controller, Secret, workload, route 순서가 들어간다. Rollback 파트 안에는 image, model weight, values, route weight가 각각 들어간다.

| 깊이 | 예시 목차 | 작성 기준 |
|---|---|---|
| 대분류 | ArgoCD/GitOps | Git에서 cluster까지 배포 흐름 |
| 하위 파트 | Helm, ApplicationSet, Sync wave, Health | 운영자가 보는 단위 |
| 세부 파트 | custom health, diff ignore, sync window | 실패와 rollback 기준 |
| 실전 글 | model promotion, emergency patch, canary | 실제 운영 절차 포함 |

## 완성 기준

GitOps 글은 manifest 적용법이 아니라 desired/live 차이를 설명해야 한다. ArgoCD UI에서 어떤 리소스가 OutOfSync인지, health가 왜 degraded인지, controller가 채우는 필드와 실제 drift를 어떻게 구분하는지까지 적어야 한다. AI serving에서는 route rollback이 image rollback보다 먼저일 수 있다는 점도 문서에 남긴다.

![ArgoCD/GitOps 목차: Helm, ApplicationSet, Sync Wave, Health, Rollback 구조도](figures/architecture.svg?v=part-hubs-20260706)

*Figure 2: ArgoCD/GitOps 목차: Helm, ApplicationSet, Sync Wave, Health, Rollback 하위 파트 구조도. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
