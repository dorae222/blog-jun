<!-- infographic-hero -->
![Label, Selector, Annotation 설계 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Label, Selector, Annotation 설계 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Label, Selector, Annotation 설계

Kubernetes에서 label은 장식이 아니라 리소스 연결의 핵심이다. Deployment는 selector로 자신이 관리할 Pod를 찾고, Service는 selector로 traffic을 보낼 Pod를 찾는다. label이 틀리면 리소스는 존재하지만 서로 연결되지 않는다.

Annotation도 metadata지만 selector 대상이 아니다. 사람이 읽거나 도구가 참고하는 부가 정보를 담는 영역이다.

## 핵심 개념

- Label은 객체 선택에 쓰이므로 안정적인 key 체계를 가져야 한다.
- Selector는 equality-based와 set-based 조건을 사용할 수 있다.
- Deployment selector는 Pod template label과 맞아야 한다.
- Annotation은 큰 문자열이나 도구 metadata를 넣을 수 있지만 선택에는 쓰지 않는다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
spec:
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        tier: backend
      annotations:
        description: "backend api pod"
    spec:
      containers:
        - name: api
          image: nginx:1.27
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get pods --show-labels
kubectl get pods -l app=api
kubectl label pod <pod> track=stable
kubectl annotate pod <pod> owner=platform
kubectl get svc <svc> -o jsonpath='{.spec.selector}'
```

![Label, Selector, Annotation 설계 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Label, Selector, Annotation 설계 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

label 예시는 반드시 selector와 함께 보여준다. label만 설명하면 중요성이 잘 드러나지 않는다. Service endpoint가 비어 있는 문제 대부분은 selector-label 불일치에서 시작된다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Selector 계약 | selector가 참조하는 label을 임의로 바꾸지 않는가 |
| Key 체계 | app, component, version, managed-by 같은 label 체계가 일관적인가 |
| Annotation | 선택에 쓰지 않는 정보를 annotation에 두는가 |
| 검증 | `kubectl get -l`로 selector 결과를 확인했는가 |

## 흔한 실수

- annotation을 selector처럼 쓰려고 한다.
- Deployment selector와 template label을 다르게 둔다.
- version label을 Service selector에 넣어 의도치 않게 traffic을 끊는다.
- label key를 글마다 다르게 만들어 운영 조회가 어려워진다.

## 시험 포인트

- Service endpoint가 비어 있으면 대개 Service selector와 Pod label이 어긋난 것이다. `kubectl get svc <svc> -o jsonpath='{.spec.selector}'`와 `kubectl get pods --show-labels`를 대조해 확인한다.
- Deployment의 `spec.selector.matchLabels`는 생성 후 사실상 바꿀 수 없다. 처음부터 Pod template label과 정확히 일치시켜야 하며, 불일치하면 apply 자체가 거부된다.
- annotation은 selector 대상이 아니다. `-l`로 annotation을 거를 수 없으므로 선택이나 그룹핑에 쓰는 정보는 반드시 label에 둔다.
- Service selector에 version처럼 자주 바뀌는 label을 넣으면 배포 도중 selector가 어긋나 traffic이 끊길 수 있다. selector에는 안정적인 key만 넣는다.

## 관련 문서

- 이전 글: [[ckad-13-logs-events-debug|logs, events, exec 디버깅]] - endpoint가 빈 문제를 Events와 함께 추적
- 다음 글: [[ckad-15-rolling-update-rollback|Rolling Update와 Rollback]] - rollout 중 ReplicaSet을 label로 구분
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]] - selector와 Pod template label의 계약 관계
- [[ckad-06-namespace-service-basics|Namespace와 Service 기초]] - selector가 endpoint를 만들어내는 원리
- [[ckad-10-scheduling-basics|스케줄링 기초]] - nodeSelector도 label 기반으로 동작하는 지점
- [[ckad-04-kubectl-imperative|kubectl 명령형 조작]] - `kubectl label`과 `kubectl annotate` 사용법
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 학습 흐름에서 이 글의 위치

## 참고 자료

- [Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- [Annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/)
- [Recommended Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
