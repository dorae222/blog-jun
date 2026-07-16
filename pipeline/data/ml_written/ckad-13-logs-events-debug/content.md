<!-- infographic-hero -->
![logs, events, exec, describe 디버깅 흐름 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: logs, events, exec, describe 디버깅 흐름 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# logs, events, exec, describe 디버깅 흐름

Kubernetes 디버깅은 감으로 명령을 치는 작업이 아니다. 먼저 Pod 상태를 보고, Events로 Kubernetes가 남긴 원인을 확인한 뒤, container 로그와 exec로 애플리케이션 내부를 확인한다.

Pending은 scheduler 영역, ImagePullBackOff는 image pull 영역, CrashLoopBackOff는 container 프로세스 영역, readiness 실패는 트래픽 준비 상태와 관련이 깊다.

## 핵심 개념

- `kubectl get`은 넓게 보고 `describe`는 객체 주변 event와 condition을 본다.
- `kubectl logs --previous`는 재시작 직전 container 로그를 볼 때 중요하다.
- `kubectl exec`는 container가 실행 중일 때만 사용할 수 있다.
- Events는 시간이 지나면 사라질 수 있으므로 장애 직후 확인하는 것이 좋다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get pod <pod> -o wide
kubectl describe pod <pod>
kubectl logs <pod> -c <container>
kubectl logs <pod> -c <container> --previous
kubectl exec -it <pod> -- sh
kubectl get events --sort-by=.lastTimestamp
```

![logs, events, exec, describe 디버깅 흐름 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: logs, events, exec, describe 디버깅 흐름 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

디버깅 콘텐츠는 상태별로 첫 명령을 정해줘야 한다. Pending이면 logs보다 describe event가 먼저이고, CrashLoopBackOff면 logs와 previous logs가 먼저다. 명령 나열보다 분기 기준이 더 중요하다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Pending | resource, nodeSelector, taint/toleration event를 확인했는가 |
| ImagePull | image 이름, tag, registry secret, 네트워크를 확인했는가 |
| CrashLoop | 현재 로그와 previous 로그를 둘 다 확인했는가 |
| Readiness | probe event와 Service endpoint 상태를 함께 확인했는가 |

## 흔한 실수

- Pending Pod에 logs를 시도한다.
- CrashLoopBackOff에서 `--previous`를 보지 않는다.
- Event 메시지를 읽지 않고 YAML만 계속 수정한다.
- multi-container Pod에서 container 이름을 지정하지 않는다.

## 시험 포인트

- Pending Pod에 `kubectl logs`는 소용이 없다. 아직 container가 뜨지 않았기 때문이다. Pending은 `kubectl describe pod`의 Events에 남은 scheduling 실패 이유(resource 부족, taint, nodeSelector)부터 본다.
- CrashLoopBackOff에서는 현재 로그가 이미 재시작 후 로그일 수 있다. `kubectl logs <pod> --previous`로 죽기 직전 container 로그를 봐야 근본 원인이 드러난다.
- `kubectl exec`는 running container에서만 동작한다. CrashLoop이나 Pending처럼 container가 뜨지 않은 상태에서는 exec가 아니라 상태와 Events 확인이 먼저다.
- Events는 기본적으로 약 1시간 뒤 사라진다. 장애 직후 `kubectl get events --sort-by=.lastTimestamp`로 원인 메시지를 먼저 확보한다.

## 관련 문서

- 이전 글: [[ckad-12-probes-health-checks|Readiness, Liveness, Startup Probe]] - probe 실패도 결국 Events로 진단한다
- 다음 글: [[ckad-14-label-selector-annotation|Label, Selector, Annotation]] - 리소스가 연결되지 않는 문제를 label로 추적
- [[ckad-11-multicontainer-pods|Multi-Container Pod와 Init/Sidecar]] - `-c`로 container를 지정해 로그를 보는 이유
- [[ckad-10-scheduling-basics|스케줄링 기초]] - Pending의 원인이 되는 scheduling 조건
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, 환경변수]] - 잘못된 env 주입이 CrashLoop으로 이어지는 경로
- [[ckad-29-troubleshooting-playbook|트러블슈팅 플레이북]] - 증상별 디버깅 순서를 종합한 정리
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 학습 흐름에서 이 글의 위치

## 참고 자료

- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [kubectl logs](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#logs)
