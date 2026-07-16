<!-- infographic-hero -->
![Kubernetes 애플리케이션 트러블슈팅 플레이북 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Kubernetes 애플리케이션 트러블슈팅 플레이북 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Kubernetes 애플리케이션 트러블슈팅 플레이북

Kubernetes 애플리케이션 장애는 상태 이름에서 출발하면 빠르게 좁힐 수 있다. Pending은 아직 node 배치 전이고, ImagePullBackOff는 image를 가져오지 못한 상태이며, CrashLoopBackOff는 container가 반복 종료되는 상태다.

좋은 플레이북은 모든 명령을 외우는 것이 아니라 증상별 첫 확인 지점을 정해두는 것이다.

## 핵심 개념

- Pending은 logs보다 describe events가 먼저다.
- ImagePullBackOff는 image 이름, tag, pull secret, registry 접근을 확인한다.
- CrashLoopBackOff는 `kubectl logs --previous`가 핵심이다.
- Service 통신 장애는 Service, endpoints, Pod readiness, NetworkPolicy 순서로 본다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get pod -o wide
kubectl describe pod <pod>
kubectl logs <pod> --previous
kubectl get events --sort-by=.lastTimestamp
kubectl get svc,endpoints
kubectl describe ingress <ingress>
kubectl auth can-i get pods --as=<subject>
```

![Kubernetes 애플리케이션 트러블슈팅 플레이북 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Kubernetes 애플리케이션 트러블슈팅 플레이북 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

이 글은 운영 디버깅 흐름을 정리하는 reference로 둔다. 상태별로 원인 후보와 확인 명령을 연결하고, 각 명령이 어떤 계층의 증거를 주는지 설명한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 증상 분류 | 현재 문제가 scheduling, image, runtime, probe, network 중 어디에 가까운가 |
| Event | Kubernetes component가 남긴 event를 확인했는가 |
| App log | container 현재/이전 로그를 확인했는가 |
| 연결 경로 | Service endpoint와 Ingress backend까지 확인했는가 |

## 시험 포인트

트러블슈팅은 이 시리즈의 마지막 편이자, 앞 편들에서 익힌 명령을 증상 하나에 꿰어 쓰는 연습이다.

- **증상 이름이 확인 순서를 정한다** - Pending은 아직 스케줄 전이라 로그가 없으니 `kubectl describe`의 Events부터 본다. ImagePullBackOff는 image 이름, tag, pull secret, registry 접근을, CrashLoopBackOff는 `kubectl logs --previous`를 먼저 본다. 모든 장애에 같은 명령을 반복하면 시간만 쓴다.
- **"객체가 있다"와 "트래픽이 흐른다"는 다르다** - Service 통신이 안 되면 Ingress부터 고치지 말고 Service, endpoints, Pod readiness, NetworkPolicy 순으로 내려간다. endpoints가 비어 있으면 selector label 불일치나 readiness 실패가 원인인 경우가 많다.
- **OOMKilled를 앱 버그로 오인하지 않는다** - 반복 재시작이 보이면 `kubectl describe`의 Last State에서 종료 사유를 확인한다. OOMKilled면 코드가 아니라 resource limit 문제이므로 requests와 limits를 먼저 본다.
- **get, describe, logs, network를 한 흐름으로 꿴다** - phase를 잡고, Events를 읽고, 앱 로그를 보고, 필요하면 RBAC와 NetworkPolicy까지 내려가는 순서는 앞 편들에서 다룬 조각을 이어 붙인 것이다. 증상 하나를 보고 어느 계층부터 볼지 즉시 정하는 것이 점수를 만든다.

## 관련 문서

- [[ckad-28-api-deprecation|API version과 deprecation 점검]] - 이전 편, apply 실패의 한 원인인 apiVersion 문제
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - get, describe, logs, events로 증거를 모으는 기본기
- [[ckad-12-probes-health-checks|프로브와 헬스 체크]] - readiness와 liveness가 Pending과 CrashLoop 진단의 핵심
- [[ckad-09-resources-requests-limits|리소스 requests와 limits]] - OOMKilled와 스케줄 실패를 가르는 자원 설정
- [[ckad-10-scheduling-basics|스케줄링 기본]] - Pending 상태를 만드는 배치 제약의 원인
- [[ckad-06-namespace-service-basics|네임스페이스와 서비스 기본]] - Service endpoint 연결을 확인하는 통신 계층
- [[ckad-18-ingress|Ingress]] - Service 뒤 Ingress backend까지 이어지는 연결 경로
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 시리즈 지도로 돌아가기

## 참고 자료

- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Events](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
