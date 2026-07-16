<!-- infographic-hero -->
![ReplicaSet과 Deployment 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: ReplicaSet과 Deployment 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# ReplicaSet과 Deployment 기본기

Deployment는 Kubernetes 애플리케이션 배포의 기본 단위다. 사용자가 기대하는 replica 수와 Pod template을 선언하면 Deployment controller가 ReplicaSet을 만들고, ReplicaSet controller가 실제 Pod 수를 맞춘다.

ReplicaSet을 직접 작성할 일은 많지 않지만 Deployment 동작을 이해하려면 반드시 알아야 한다. rollout, rollback, revision history는 Deployment가 여러 ReplicaSet을 관리한다는 사실에서 출발한다.

## 핵심 개념

- Deployment selector는 Pod template label과 일치해야 한다.
- Pod template이 바뀌면 새 ReplicaSet이 만들어지고 rollout이 시작된다.
- replicas는 원하는 Pod 개수이며 실제 개수는 상태와 event를 통해 확인한다.
- ReplicaSet은 보통 직접 관리하지 않고 Deployment의 하위 객체로 관찰한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f deployment.yaml
kubectl get deploy,rs,pod -l app=web
kubectl describe deploy web
kubectl rollout status deployment/web
kubectl rollout history deployment/web
```

![ReplicaSet과 Deployment 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: ReplicaSet과 Deployment 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Deployment manifest에서는 `spec.selector.matchLabels`와 `spec.template.metadata.labels`를 가장 먼저 맞춘다. selector는 생성 후 변경이 까다로운 계약이므로 임시 label을 넣지 않는다. image tag는 변경 추적이 가능한 버전으로 고정하고, readiness probe와 resource request는 운영 단계에서 함께 추가한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Selector | Deployment selector와 Pod template label이 일치하는가 |
| Replica | desired/current/available replica 수가 기대와 맞는가 |
| Revision | template 변경이 새 ReplicaSet으로 반영되었는가 |
| Status | `rollout status`가 완료되었는가 |

## 흔한 실수

- selector와 template label을 다르게 써서 Pod를 관리하지 못한다.
- ReplicaSet을 직접 수정해 Deployment 상태와 충돌시킨다.
- image tag를 `latest`로 둬 rollout 이력을 해석하기 어렵게 만든다.
- replicas만 맞으면 서비스 가능하다고 보고 readiness를 확인하지 않는다.

## 시험 포인트

- selector와 template label은 처음부터 일치시킨다. `spec.selector.matchLabels`는 생성 후 변경이 까다로운 계약이라, 시험에서 나중에 고치려 하면 Deployment를 다시 만들어야 하는 상황이 생긴다.
- rollout은 template 변경에서 시작된다. image나 template을 바꾸면 새 ReplicaSet이 생기므로 `kubectl rollout status deployment/web`으로 완료를 확인하고 `kubectl rollout history deployment/web`으로 revision을 읽는다.
- Pod 수만 세고 끝내지 않는다. `kubectl get deploy,rs,pod -l app=web`으로 desired/current/available를 함께 보고, replicas가 채워져도 readiness가 통과해야 트래픽을 받는다.
- ReplicaSet은 관찰 대상이지 편집 대상이 아니다. Deployment가 template hash별 ReplicaSet을 관리하므로, image tag를 `latest`로 두면 어떤 변경이 어떤 rollout을 유발했는지 이력을 해석하기 어렵다.

## 관련 문서

- [[ckad-04-kubectl-imperative|kubectl 명령형과 YAML 생성]] - 이전 글, Deployment manifest 골격을 명령으로 만드는 법
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본]] - 다음 글, Deployment가 만든 Pod를 Service로 노출
- [[ckad-15-rolling-update-rollback|롤링 업데이트와 롤백]] - 새 ReplicaSet 전환과 revision history를 심화한 편
- [[ckad-26-deployment-strategies|배포 전략]] - rolling 외의 배포 전략을 다루는 편
- [[ckad-14-label-selector-annotation|라벨, 셀렉터, 애노테이션]] - selector와 template label 계약을 다루는 편
- [[ckad-12-probes-health-checks|프로브와 헬스 체크]] - replicas 외에 readiness를 확인하는 probe
- [[ckad-00-kubernetes-application-map|CKAD 애플리케이션 지도]] - 전체 시리즈 지도

## 참고 자료

- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Rolling Update](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
