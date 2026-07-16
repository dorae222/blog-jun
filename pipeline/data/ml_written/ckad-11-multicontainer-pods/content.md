<!-- infographic-hero -->
![Multi-Container Pod, Sidecar, Init Container 패턴 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Multi-Container Pod, Sidecar, Init Container 패턴 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Multi-Container Pod, Sidecar, Init Container 패턴

Pod는 하나의 container만 담을 수 있는 객체가 아니다. 강하게 결합된 container들이 같은 network와 storage context를 공유해야 할 때 multi-container Pod를 사용한다.

가장 흔한 패턴은 init container와 sidecar다. init container는 app 시작 전에 준비 작업을 수행하고 종료된다. sidecar는 app container와 함께 실행되며 로그 수집, 설정 동기화, local proxy 같은 보조 기능을 맡는다.

## 핵심 개념

- 같은 Pod 안 container는 같은 Pod IP를 공유하고 localhost로 통신할 수 있다.
- container 간 파일 공유는 volume을 통해 명시적으로 구성한다.
- init container는 순서대로 실행되고 모두 성공해야 일반 container가 시작된다.
- 여러 container가 항상 같은 node와 lifecycle을 공유해야 할 때만 같은 Pod에 둔다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-init
spec:
  volumes:
    - name: shared
      emptyDir: {}
  initContainers:
    - name: init-html
      image: busybox:1.36
      command: ["sh", "-c", "echo hello > /work/index.html"]
      volumeMounts:
        - name: shared
          mountPath: /work
  containers:
    - name: web
      image: nginx:1.27
      volumeMounts:
        - name: shared
          mountPath: /usr/share/nginx/html
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f multi.yaml
kubectl get pod web-with-init
kubectl describe pod web-with-init
kubectl logs web-with-init -c init-html
kubectl logs web-with-init -c web
```

![Multi-Container Pod, Sidecar, Init Container 패턴 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Multi-Container Pod, Sidecar, Init Container 패턴 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

multi-container Pod 예시는 container별 로그 확인 명령을 반드시 포함한다. Pod 안 container가 여러 개면 `kubectl logs pod`만으로는 어떤 container 로그를 볼지 모호해진다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 결합도 | 두 container가 반드시 같은 Pod lifecycle을 공유해야 하는가 |
| Volume | 파일 공유가 필요한 경우 volumeMount가 양쪽에 있는가 |
| Init | init container 실패 시 app container가 시작되지 않는 점을 고려했는가 |
| Logs | container별 로그 확인 명령을 알고 있는가 |

## 흔한 실수

- 느슨하게 결합된 서비스를 한 Pod에 몰아넣는다.
- localhost 통신은 가능하지만 port 충돌이 날 수 있다는 점을 잊는다.
- init container가 계속 실행되는 sidecar라고 착각한다.
- container별 resource 설정을 빠뜨린다.

## 시험 포인트

- multi-container Pod에서 `kubectl logs <pod>`만 치면 어느 container 로그인지 모호하다. 반드시 `-c <container>`를 붙여 init container와 app container 로그를 구분한다.
- init container는 `initContainers:` 아래, sidecar는 `containers:` 아래에 둔다. 위치를 헷갈리면 실행 순서와 lifecycle이 완전히 달라진다.
- volume 공유는 양쪽 container 모두에 `volumeMounts`가 있어야 파일이 보인다. 한쪽만 mount하면 데이터가 전달되지 않는다.
- init container가 종료되지 않으면 app container는 영원히 시작되지 않고 Pod가 `Init` 상태에 멈춘다. init 작업은 반드시 끝나는 명령이어야 한다.

## 관련 문서

- 이전 글: [[ckad-10-scheduling-basics|스케줄링 기초]] - 같은 Pod를 어느 node에 배치할지 결정하는 앞 단계
- 다음 글: [[ckad-12-probes-health-checks|Readiness, Liveness, Startup Probe]] - 여러 container가 뜬 뒤 준비 상태를 판정하는 방법
- [[ckad-03-pod-yaml|Pod YAML 구조]] - initContainers와 containers를 배치하는 spec 기본기
- [[ckad-19-volumes-pv-pvc|Volume, PV, PVC]] - container 간 파일 공유에 쓰는 volume의 종류와 수명
- [[ckad-09-resources-requests-limits|Resource Requests와 Limits]] - container별 resource를 따로 잡아야 하는 이유
- [[ckad-13-logs-events-debug|logs, events, exec 디버깅]] - `-c` 옵션으로 container별 로그를 추적하는 흐름
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 학습 흐름에서 이 글의 위치

## 참고 자료

- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/)
