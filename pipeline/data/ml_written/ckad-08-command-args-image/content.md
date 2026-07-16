<!-- infographic-hero -->
![Container image, command, args 동작 원리 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Container image, command, args 동작 원리 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Container image, command, args 동작 원리

Kubernetes에서 container를 실행할 때 image의 기본 명령을 그대로 사용할 수도 있고 PodSpec에서 덮어쓸 수도 있다. Dockerfile의 ENTRYPOINT는 Kubernetes `command`, Dockerfile의 CMD는 Kubernetes `args`와 대응한다.

이 관계를 모르면 container가 즉시 종료되거나 의도하지 않은 인자로 실행될 때 원인을 찾기 어렵다.

## 핵심 개념

- `image`는 실행 파일과 기본 실행 방식을 포함한다.
- `command`를 지정하면 image ENTRYPOINT를 override한다.
- `args`를 지정하면 image CMD를 override한다.
- shell 기능이 필요하면 `sh -c`를 명시해야 한다. 배열 형식은 shell을 자동으로 거치지 않는다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sleeper
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c"]
      args: ["echo started; sleep 3600"]
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f pod.yaml
kubectl logs sleeper
kubectl describe pod sleeper
kubectl get pod sleeper -o jsonpath='{.spec.containers[0].command}'
kubectl get pod sleeper -o jsonpath='{.spec.containers[0].args}'
```

![Container image, command, args 동작 원리 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Container image, command, args 동작 원리 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

command/args 예시는 반드시 배열 형식과 shell 형식의 차이를 설명해야 한다. `command: ["echo hello"]`는 하나의 실행 파일 이름으로 해석될 수 있으므로, shell built-in이나 pipe가 필요하면 `command: ["sh", "-c"]`와 `args`를 사용한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| ENTRYPOINT | image의 기본 ENTRYPOINT를 override해야 하는 상황인가 |
| CMD | args만 바꾸면 충분한가 |
| Shell | pipe, 변수 확장, redirect가 필요해 `sh -c`가 필요한가 |
| Exit | 프로세스가 즉시 종료되어 Pod가 Completed/CrashLoopBackOff가 되지 않는가 |

## 흔한 실수

- Dockerfile CMD와 Kubernetes command를 같은 것으로 이해한다.
- 배열 command에서 shell 문법이 자동으로 동작한다고 생각한다.
- 컨테이너 주 프로세스가 종료되면 Pod도 종료된다는 사실을 놓친다.
- debug용 sleep을 운영 manifest에 남긴다.

## 시험 포인트

- `command`는 image의 ENTRYPOINT를, `args`는 CMD를 override한다. Dockerfile의 CMD와 Kubernetes의 `command`를 같은 것으로 착각하지 않는다.
- shell 기능(pipe, 변수 확장, redirect)이 필요하면 `command: ["sh", "-c"]`에 명령을 `args`로 넘긴다. 배열 형식은 shell을 거치지 않으므로 `command: ["echo hello"]`는 `echo hello`라는 하나의 실행 파일 이름으로 해석된다.
- container의 주 프로세스가 끝나면 Pod도 끝난다. 명령이 즉시 종료되면 Pod는 Completed가 되거나 재시작을 반복하며 CrashLoopBackOff가 되므로, 짧게 끝나는 명령인지 먼저 의심한다.
- 실제로 적용된 값은 manifest가 아니라 `kubectl get pod <name> -o jsonpath='{.spec.containers[0].command}'`로 확인한다. override가 반영됐는지 눈으로 보는 것이 가장 빠르다.

## 관련 문서

- [[ckad-07-configmap-secret-env|ConfigMap, Secret, env 주입]] - 이전 글, command와 args가 소비하는 설정값을 주입하는 방법
- [[ckad-09-resources-requests-limits|requests, limits, quota]] - 다음 글, 같은 container에 리소스 상한을 붙이는 단계
- [[ckad-03-pod-yaml|Pod YAML]] - command와 args가 들어가는 PodSpec의 전체 구조
- [[ckad-12-probes-health-checks|Probe와 health check]] - 즉시 종료와 CrashLoopBackOff를 probe 실패와 구분
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - container가 바로 죽을 때 로그와 이벤트로 원인 찾기
- [[ckad-11-multicontainer-pods|멀티 컨테이너 Pod]] - init container와 sidecar에서 command를 나눠 쓰는 패턴
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Define a Command and Arguments](https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/)
- [Images](https://kubernetes.io/docs/concepts/containers/images/)
- [Containers](https://kubernetes.io/docs/concepts/containers/)
