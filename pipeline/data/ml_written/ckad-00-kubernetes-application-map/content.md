<!-- infographic-hero -->
![Kubernetes 기본기 목차: CKAD에서 운영형 애플리케이션까지 핵심 요약](figures/infographic.svg?v=part-hubs-20260706)

*Figure 1: Kubernetes 기본기 목차: CKAD에서 운영형 애플리케이션까지 핵심 요약. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*

# Kubernetes 기본기 목차: CKAD에서 운영형 애플리케이션까지

Kubernetes 기본기는 CKAD 시험 목차로만 보면 좁다. 하지만 AI serving, ArgoCD, KServe, Ray Serve를 이해하려면 결국 Pod, Service, ConfigMap, Secret, RBAC, Ingress, Volume, Helm, Kustomize 기본기가 필요하다. 이 글은 Kubernetes 기본기 대분류의 허브다.

## 하위 파트 1: YAML과 kubectl

[[ckad-03-pod-yaml|Pod와 YAML 기본 구조]]와 [[ckad-04-kubectl-imperative|kubectl 명령형 작성]]은 Kubernetes API object를 읽는 눈을 만든다. YAML을 외우기보다 `apiVersion`, `kind`, `metadata`, `spec`, `status`가 어떤 책임을 갖는지 익힌다.

## 하위 파트 2: Workload

Pod는 실행 단위이고 Deployment는 rollout 단위다. [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]], [[ckad-16-jobs-cronjobs|Job과 CronJob]], [[ckad-20-statefulset-headless|StatefulSet]]은 workload를 목적별로 나눈다. AI serving에서는 model server가 Deployment인지, Ray worker가 어떤 controller로 관리되는지 이해하는 기반이 된다.

## 하위 파트 3: Network와 노출

[[ckad-06-namespace-service-basics|Namespace, Service, DNS]], [[ckad-18-ingress|Service와 Ingress]], [[ckad-17-networkpolicy|NetworkPolicy]]는 traffic path를 이해하는 기본기다. Gateway API나 Istio를 보기 전에 Service endpoint와 DNS가 어떻게 연결되는지 알아야 한다.

## 하위 파트 4: Config, Storage, Security

[[ckad-07-configmap-secret-env|ConfigMap/Secret]], [[ckad-19-volumes-pv-pvc|Volume/PV/PVC]], [[ckad-21-securitycontext-serviceaccount|SecurityContext/ServiceAccount]], [[ckad-22-rbac-kubeconfig|RBAC]]는 운영에서 가장 자주 문제를 만든다. 모델 weight credential, private registry, object storage secret, namespace 권한이 모두 여기에 걸린다.

## 하위 파트 5: Debugging과 Packaging

[[ckad-13-logs-events-debug|logs/events/debug]], [[ckad-15-rolling-update-rollback|rolling update/rollback]], [[ckad-24-helm-basics|Helm]], [[ckad-25-kustomize-basics|Kustomize]]는 운영형 Kubernetes로 넘어가는 다리다. AI serving 장애도 결국 `kubectl describe`, event, rollout history, rendered manifest에서 시작한다.

## 작성 대기열

| 우선순위 | 글 후보 | 연결 글 |
|---|---|---|
| P0 | Kubernetes object 읽는 법: spec/status/events | CKAD 01~04 |
| P0 | Deployment rollout과 readiness를 AI serving에 연결 | CKAD 12/15 |
| P1 | RBAC와 Secret boundary로 model serving 보호 | CKAD 21/22 |
| P1 | Helm/Kustomize에서 ArgoCD로 넘어가기 | CKAD 24/25 |
| P2 | Troubleshooting playbook을 GPU/KServe/Ray로 확장 | [[kubernetes-ai-infra-hub|Kubernetes AI Infra]] |

## 참고 자료

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [CKAD curriculum](https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/)

## 파트 안의 파트 설계

Kubernetes 기본기는 `Object`, `Workload`, `Network`, `Config`, `Storage`, `Security`, `Debug`, `Packaging`으로 나눈다. CKAD 글들은 이 순서를 따라가되, 단순 시험 대비가 아니라 운영형 애플리케이션 이해로 확장한다. 예를 들어 Probe 글은 vLLM readiness와 연결되고, RBAC 글은 KServe controller 권한과 연결되며, Helm 글은 ArgoCD와 연결된다.

| 깊이 | 예시 목차 | 작성 기준 |
|---|---|---|
| 대분류 | Kubernetes 기본기 | 모든 AI serving infra의 기반 |
| 하위 파트 | Pod, Deployment, Service, Config, Storage, Security | Kubernetes API 객체별 이해 |
| 세부 파트 | probe, rollout, NetworkPolicy, RBAC, Helm | 운영 오류가 자주 나는 지점 |
| 실전 글 | AI serving 장애를 CKAD 기본기로 추적 | 기본기를 실전 runbook으로 연결 |

## 완성 기준

기본기 글은 명령어 암기가 아니라 문제를 좁히는 능력을 만들어야 한다. Pod가 Pending이면 scheduler와 resource를 보고, Ready가 아니면 probe와 model load를 보며, Service가 안 되면 endpoint와 selector를 본다. 이 사고 방식이 있어야 이후 Kubernetes AI Infra와 ArgoCD/GitOps 글을 자연스럽게 읽을 수 있다.

![Kubernetes 기본기 목차: CKAD에서 운영형 애플리케이션까지 구조도](figures/architecture.svg?v=part-hubs-20260706)

*Figure 2: Kubernetes 기본기 목차: CKAD에서 운영형 애플리케이션까지 하위 파트 구조도. (Source: 공식 문서와 기존 blog-jun 콘텐츠 기반 자체 작성)*
