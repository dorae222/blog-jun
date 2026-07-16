<!-- infographic-hero -->
![Readiness, Liveness, Startup Probe 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Readiness, Liveness, Startup Probe 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Readiness, Liveness, Startup Probe

Probe는 애플리케이션이 살아 있는지, 트래픽을 받을 준비가 되었는지, 시작 중인지를 Kubernetes가 판단하게 해준다. readiness와 liveness를 같은 endpoint로 대충 묶으면 장애 대응이 오히려 불안정해진다.

readiness는 트래픽 제어, liveness는 재시작 제어, startup은 느린 시작 보호라는 역할로 나눠야 한다.

## 핵심 개념

- readinessProbe가 실패하면 Pod는 Running이어도 Service endpoint에서 빠질 수 있다.
- livenessProbe가 반복 실패하면 kubelet이 container를 재시작한다.
- startupProbe가 설정되면 성공 전까지 liveness/readiness 판단을 지연할 수 있다.
- HTTP, TCP, exec 방식 중 애플리케이션 특성에 맞는 probe를 고른다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probed-web
spec:
  containers:
    - name: web
      image: nginx:1.27
      ports:
        - containerPort: 80
      readinessProbe:
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 3
        periodSeconds: 5
      livenessProbe:
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 10
        periodSeconds: 10
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f probes.yaml
kubectl get pod probed-web
kubectl describe pod probed-web
kubectl get endpoints web
kubectl get events --sort-by=.lastTimestamp
```

![Readiness, Liveness, Startup Probe 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Readiness, Liveness, Startup Probe 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

probe 문서에는 실패 시 Kubernetes가 무엇을 하는지까지 써야 한다. readiness 실패와 liveness 실패는 결과가 완전히 다르다. readiness는 트래픽 제외이고 liveness는 재시작이다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Endpoint | readiness endpoint가 외부 dependency까지 과도하게 검사하지 않는가 |
| Restart | liveness 실패가 실제로 재시작으로 해결될 문제인가 |
| Delay | 앱 시작 시간에 맞춰 initialDelay/startupProbe를 설정했는가 |
| Threshold | 일시적인 지연으로 재시작 폭주가 나지 않는가 |

## 흔한 실수

- readiness와 liveness를 같은 무거운 endpoint로 둔다.
- DB가 잠깐 느릴 때 liveness 실패로 앱을 재시작한다.
- 느린 앱에 startupProbe 없이 liveness를 바로 적용한다.
- probe 실패 원인을 Events에서 확인하지 않는다.

## 시험 포인트

- readiness 실패와 liveness 실패는 결과가 다르다. readiness가 실패하면 Pod는 Running이어도 Service endpoint에서 빠지고, liveness가 threshold를 넘겨 실패하면 kubelet이 container를 재시작한다. "왜 endpoint가 비었나"와 "왜 재시작되나"를 이 기준으로 나눈다.
- 느린 앱에 startupProbe 없이 liveness만 걸면 부팅이 채 끝나기 전에 재시작이 반복된다. 시작이 오래 걸리는 앱은 startupProbe로 부팅 구간을 먼저 통과시킨다.
- readiness endpoint에 외부 DB 같은 dependency까지 검사로 넣으면 DB 순단에 모든 Pod가 동시에 endpoint에서 빠져 장애가 오히려 커진다. readiness는 자기 자신이 트래픽을 받을 수 있는지만 본다.
- probe 실패 원인은 `kubectl describe pod`의 Events에 남는 `Unhealthy` 메시지에서 확인한다. logs만 봐서는 timeout인지 threshold 초과인지 판단하기 어렵다.

## 관련 문서

- 이전 글: [[ckad-11-multicontainer-pods|Multi-Container Pod와 Init/Sidecar]] - probe를 붙일 container가 여러 개일 때의 전제
- 다음 글: [[ckad-13-logs-events-debug|logs, events, exec 디버깅]] - probe 실패를 Events에서 읽어내는 실전 흐름
- [[ckad-06-namespace-service-basics|Namespace와 Service 기초]] - readiness가 Service endpoint 편입을 좌우하는 지점
- [[ckad-15-rolling-update-rollback|Rolling Update와 Rollback]] - 무중단 배포 안전성이 readiness에 의존하는 이유
- [[ckad-09-resources-requests-limits|Resource Requests와 Limits]] - resource 부족이 probe timeout으로 번지는 경우
- [[ckad-03-pod-yaml|Pod YAML 구조]] - probe 필드를 container spec에 배치하는 위치
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 학습 흐름에서 이 글의 위치

## 참고 자료

- [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
