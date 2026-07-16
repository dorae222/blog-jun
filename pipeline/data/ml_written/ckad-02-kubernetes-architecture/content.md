<!-- infographic-hero -->
![애플리케이션 개발자를 위한 Kubernetes 아키텍처 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: 애플리케이션 개발자를 위한 Kubernetes 아키텍처 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# 애플리케이션 개발자를 위한 Kubernetes 아키텍처

Kubernetes에서 애플리케이션을 배포한다는 것은 컨테이너를 직접 실행하는 것이 아니라 API 객체의 원하는 상태를 제출하는 일이다. API Server는 그 상태를 저장하고, controller와 scheduler가 실제 cluster를 그 상태에 가깝게 만든다.

개발자에게 중요한 지점은 장애가 어느 계층에서 발생했는지 구분하는 것이다. YAML 검증 실패는 API 계층, Pending은 scheduling 계층, ImagePullBackOff는 node/runtime 계층에서 시작될 가능성이 높다.

## 핵심 개념

- Control plane은 cluster의 원하는 상태를 저장하고 조정한다.
- Worker node는 kubelet과 container runtime을 통해 Pod를 실제로 실행한다.
- Controller는 선언된 desired state와 현재 observed state의 차이를 줄이는 reconcile loop를 수행한다.
- Scheduler는 resource request, node selector, affinity, taint/toleration 등을 고려해 Pod를 node에 배치한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get nodes -o wide
kubectl cluster-info
kubectl get pods -A -o wide
kubectl describe pod <pod-name>
kubectl get events --sort-by=.lastTimestamp
```

![애플리케이션 개발자를 위한 Kubernetes 아키텍처 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: 애플리케이션 개발자를 위한 Kubernetes 아키텍처 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

아키텍처를 설명할 때 component 이름만 나열하면 실제 문제 해결에 도움이 적다. 사용자의 manifest가 API Server에 저장되고, controller가 Pod를 만들고, scheduler가 node를 고르고, kubelet이 container runtime을 호출하는 흐름으로 연결해야 한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| API 단계 | 객체가 생성되었는지 `kubectl get`으로 확인되는가 |
| Scheduling 단계 | Pod가 Pending이면 node selector, taint, resource 부족을 확인했는가 |
| Runtime 단계 | Pod가 node에 배치된 뒤 image pull, command, probe 문제가 있는가 |
| Event | controller와 scheduler가 남긴 event를 확인했는가 |

## 흔한 실수

- Deployment를 만들었는데 Pod가 없으면 Deployment만 보고 원인을 찾는다.
- Pending Pod를 container runtime 문제로 착각한다.
- control plane component와 node component의 책임을 섞어서 설명한다.
- etcd를 애플리케이션 데이터베이스처럼 이해한다.

## 시험 포인트

- troubleshooting 문제는 증상으로 계층을 좁히는 속도가 관건이다. YAML 검증 실패는 API 계층, `Pending`은 scheduling 계층, `ImagePullBackOff`는 node/runtime 계층에서 시작된다. 계층을 정해야 어느 명령으로 파고들지가 정해진다.
- 계층마다 확인 명령이 다르다. 객체가 만들어졌는지는 `kubectl get`, 배치 이유와 controller/scheduler가 남긴 기록은 `kubectl describe`와 `kubectl get events --sort-by=.lastTimestamp`로 읽는다.
- 선언형 API 감각을 시험에서 그대로 쓴다. `kubectl apply` 성공은 요청이 접수됐다는 뜻일 뿐이므로, Deployment를 만들었는데 Pod가 없으면 spec이 아니라 event부터 본다.
- 개념 문제 대비로 control plane(API server, scheduler, controller, etcd)과 node(kubelet, container runtime)의 책임을 한 문장씩 말할 수 있어야 한다. etcd는 원하는 상태 저장소이지 애플리케이션 데이터베이스가 아니다.

## 관련 문서

- [[ckad-01-lab-kubectl-setup|kubectl 작업 환경과 기본 조회 흐름]] - 이전 글, 이 구조를 관찰하는 kubectl 명령의 기초
- [[ckad-03-pod-yaml|Pod와 YAML 기본 구조]] - 다음 글, API server에 제출하는 최소 객체의 형태
- [[ckad-10-scheduling-basics|스케줄링 기본]] - scheduler가 node를 고르는 계층을 자세히 다루는 편
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment 기본기]] - controller의 reconcile loop가 실제로 동작하는 예
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - event로 어느 계층에서 문제가 났는지 구분하는 방법
- [[ckad-29-troubleshooting-playbook|트러블슈팅 플레이북]] - 계층별 장애 진단을 종합한 편
- [[ckad-00-kubernetes-application-map|CKAD 애플리케이션 지도]] - 전체 시리즈 지도

## 참고 자료

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes API Concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/)
