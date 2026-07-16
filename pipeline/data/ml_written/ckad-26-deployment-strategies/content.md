<!-- infographic-hero -->
![Blue-Green과 Canary 배포를 Kubernetes 기본 리소스로 이해하기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Blue-Green과 Canary 배포를 Kubernetes 기본 리소스로 이해하기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Blue-Green과 Canary 배포를 Kubernetes 기본 리소스로 이해하기

Blue-Green과 Canary는 Kubernetes의 별도 리소스 이름이 아니라 배포 전략이다. 기본 Kubernetes 리소스만으로 구현할 때는 Deployment와 Service selector, version label을 조합한다.

정교한 비율 기반 traffic split이 필요하면 Ingress controller, Gateway API, service mesh 같은 L7 계층이 필요할 수 있다. 기본 리소스만으로 가능한 것과 아닌 것을 구분해야 한다.

## 핵심 개념

- Blue-Green은 old/new 환경을 나란히 준비한 뒤 traffic 대상을 전환한다.
- Canary는 새 버전을 작은 비율 또는 작은 replica 수로 노출해 검증한다.
- Service selector는 label 기반이므로 version label 설계가 중요하다.
- Kubernetes Service만으로 정밀한 1%, 5% traffic weight를 직접 표현하기 어렵다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get deploy,pod,svc --show-labels
kubectl patch service web -p '{"spec":{"selector":{"app":"web","version":"v2"}}}'
kubectl rollout status deployment/web-v2
kubectl logs -l app=web,version=v2
```

![Blue-Green과 Canary 배포를 Kubernetes 기본 리소스로 이해하기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Blue-Green과 Canary 배포를 Kubernetes 기본 리소스로 이해하기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

배포 전략 글은 멋진 이름보다 실제 selector 변화가 핵심이다. 어떤 label이 traffic 대상을 결정하고, 어떤 시점에 전환되는지 그림으로 보여줘야 한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Version label | 버전별 Pod를 구분할 label이 있는가 |
| Service selector | traffic 전환이 어떤 selector 변경으로 일어나는가 |
| Readiness | 새 버전이 준비되기 전 Service에 잡히지 않도록 했는가 |
| 한계 | 정밀 traffic weight가 필요한 경우 적절한 routing 계층을 쓰는가 |

## 시험 포인트

- **Blue-Green은 Deployment의 strategy 필드가 아니다** - Deployment의 `.spec.strategy`는 `RollingUpdate`와 `Recreate`만 가진다. Blue-Green은 별도 Deployment 두 개와 Service selector 전환으로 사람이 구성하는 패턴이므로, 필드 하나로 켤 수 있다고 답하면 틀린다.
- **selector를 바꾼 다음에는 endpoints를 본다** - `kubectl patch service`로 selector를 v2로 옮겨도 traffic이 실제로 넘어갔는지는 `kubectl get endpoints`로 확인해야 한다. 새 Pod가 아직 Ready가 아니면 endpoints가 비어 순단이 생긴다.
- **Canary와 rolling update를 구분한다** - rolling update는 같은 Deployment가 Pod를 점진 교체하는 것이고, Canary는 새 버전을 소수 replica로 따로 띄워 관찰하는 것이다. "일부만 새 버전으로 노출"을 요구하는 지문은 replica 수나 별도 version label로 답해야 한다.
- **정밀 traffic weight는 기본 Service로 안 된다** - 1%, 5% 같은 비율 분배는 Service selector로 표현할 수 없다. 이 요구가 보이면 Ingress, Gateway API, service mesh 같은 L7 계층이 필요하다는 점을 명시한다.

## 관련 문서

- [[ckad-25-kustomize-basics|Kustomize 기본]] - 이전 편, overlay로 환경별 배포 값을 분리하는 방법
- [[ckad-27-secret-encryption-at-rest|Secret 암호화 at rest]] - 다음 편, 배포 다음에 따라오는 민감정보 경계
- [[ckad-05-replicaset-deployment|ReplicaSet와 Deployment]] - Blue-Green과 Canary가 얹히는 기본 Deployment 리소스
- [[ckad-15-rolling-update-rollback|롤링 업데이트와 롤백]] - Deployment strategy 필드와 배포 전략의 차이를 대비
- [[ckad-14-label-selector-annotation|레이블 셀렉터와 애노테이션]] - version label 설계가 traffic 전환의 핵심
- [[ckad-06-namespace-service-basics|네임스페이스와 서비스 기본]] - selector 전환이 실제로 작동하는 Service 계층
- [[ckad-18-ingress|Ingress]] - 정밀 traffic weight가 필요할 때 붙는 L7 계층
- [[ckad-12-probes-health-checks|프로브와 헬스 체크]] - readiness로 새 버전 전환의 안전성을 확보
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 시리즈 흐름 다시 보기

## 참고 자료

- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
