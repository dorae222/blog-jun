<!-- infographic-hero -->
![nodeSelector, affinity, taints/tolerations 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: nodeSelector, affinity, taints/tolerations 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# nodeSelector, affinity, taints/tolerations 기본기

Kubernetes scheduler는 Pod를 아무 node에나 배치하지 않는다. resource request, node 상태, label, affinity, taint/toleration 같은 조건을 모두 고려한다.

`nodeSelector`와 affinity는 Pod가 원하는 node를 고르는 방식이고, taint는 node가 원하지 않는 Pod를 밀어내는 방식이다. 두 모델을 구분하면 scheduling 문제를 훨씬 빨리 해석할 수 있다.

## 핵심 개념

- `nodeSelector`는 key-value가 정확히 일치하는 node에만 Pod를 배치한다.
- node affinity는 required와 preferred를 통해 필수 조건과 선호 조건을 나눈다.
- taint는 node에 설정하고 toleration은 Pod에 설정한다.
- toleration은 배치를 허용할 뿐 특정 node로 반드시 보내는 규칙은 아니다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: scheduled-app
spec:
  nodeSelector:
    workload: app
  tolerations:
    - key: dedicated
      operator: Equal
      value: app
      effect: NoSchedule
  containers:
    - name: app
      image: nginx:1.27
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl label node <node-name> workload=app
kubectl taint node <node-name> dedicated=app:NoSchedule
kubectl apply -f scheduling.yaml
kubectl get pod scheduled-app -o wide
kubectl describe pod scheduled-app
```

![nodeSelector, affinity, taints/tolerations 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: nodeSelector, affinity, taints/tolerations 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

배치 규칙은 반드시 node 상태와 함께 설명한다. Pod YAML만 보여주면 왜 Pending이 되는지 이해하기 어렵다. `kubectl describe pod`의 Events에서 scheduler 메시지를 함께 확인해야 한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Node label | Pod가 요구하는 label이 실제 node에 있는가 |
| Taint | node taint에 대응하는 toleration이 Pod에 있는가 |
| Resource | 규칙을 만족하는 node에 충분한 allocatable resource가 있는가 |
| Effect | NoSchedule, PreferNoSchedule, NoExecute 차이를 이해했는가 |

## 흔한 실수

- toleration을 쓰면 해당 node로 반드시 배치된다고 생각한다.
- nodeSelector label typo를 event 확인 없이 지나친다.
- required affinity를 과하게 써서 배치 가능한 node를 없앤다.
- taint를 제거하지 않고 테스트 Pod가 계속 Pending인 이유를 찾지 못한다.

## 시험 포인트

- 두 방향을 구분한다. `nodeSelector`와 affinity는 Pod가 원하는 node를 고르는 규칙이고, taint는 node가 원치 않는 Pod를 밀어내는 규칙이다. 이 구분이 서면 Pending 원인을 훨씬 빨리 좁힌다.
- toleration은 배치를 허용할 뿐 특정 node로 보내는 규칙이 아니다. 특정 node에 반드시 올리려면 nodeSelector나 affinity를 함께 써야 한다.
- taint effect를 구분한다. NoSchedule은 새 Pod 배치를 막고, PreferNoSchedule은 가급적 피하며, NoExecute는 이미 떠 있는 Pod까지 축출한다.
- Pod가 Pending이면 추측하지 말고 `kubectl describe pod`의 Events에서 scheduler 메시지를 읽는다. node label typo, 대응 toleration 누락, allocatable resource 부족을 서로 다른 원인으로 분리할 수 있다.

## 관련 문서

- [[ckad-09-resources-requests-limits|requests, limits, quota]] - 이전 글, scheduler가 배치 조건과 함께 보는 resource request
- [[ckad-11-multicontainer-pods|멀티 컨테이너 Pod]] - 다음 글, 한 node에 배치된 뒤 Pod 안에서 container를 구성하는 방법
- [[ckad-14-label-selector-annotation|Label과 Selector, Annotation]] - node label과 selector 매칭 규칙을 더 깊이 다룬다
- [[ckad-02-kubernetes-architecture|Kubernetes 아키텍처]] - 배치를 담당하는 scheduler가 control plane에서 하는 역할
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - Pending Pod의 scheduler 이벤트를 읽는 순서
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Assign Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)
