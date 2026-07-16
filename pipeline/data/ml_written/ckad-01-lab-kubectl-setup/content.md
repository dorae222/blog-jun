<!-- infographic-hero -->
![kubectl 작업 환경과 기본 조회 흐름 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: kubectl 작업 환경과 기본 조회 흐름 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# kubectl 작업 환경과 기본 조회 흐름

`kubectl`은 단순한 명령줄 도구가 아니라 Kubernetes API와 대화하는 가장 직접적인 인터페이스다. 좋은 작업 흐름은 context 확인, 리소스 발견, manifest 생성, 상태 점검을 반복하는 방식으로 만들어진다.

Kubernetes 글을 읽을 때도 같은 순서를 유지하면 좋다. 리소스를 만들기 전에 API 형태를 확인하고, 만든 뒤에는 object status와 event를 확인한다.

## 핵심 개념

- `context`는 cluster, user, namespace 조합이다.
- `kubectl explain`은 현재 cluster가 아는 API schema를 기준으로 필드를 설명한다.
- `--dry-run=client -o yaml`은 빠르게 시작 YAML을 만들 때 유용하다.
- 출력 형식은 문제 해결 속도를 크게 바꾼다. `wide`, `yaml`, `jsonpath`를 모두 익혀야 한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl config current-context
kubectl config view --minify
kubectl config set-context --current --namespace=default
kubectl api-resources
kubectl explain deployment.spec.template.spec.containers
kubectl run web --image=nginx --dry-run=client -o yaml
kubectl get pods -o wide
kubectl get pod web -o jsonpath='{.status.phase}'
```

![kubectl 작업 환경과 기본 조회 흐름 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: kubectl 작업 환경과 기본 조회 흐름 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

작업용 alias를 쓰더라도 문서에는 원래 명령을 함께 남기는 편이 낫다. 특히 팀 문서나 블로그에서는 `kubectl` 전체 명령을 기준으로 설명하고, 부록 수준에서 alias를 언급한다. manifest를 직접 외우기보다 `explain`과 dry-run으로 API 구조를 확인하는 습관이 중요하다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Context | 현재 context와 namespace가 의도한 대상인가 |
| API discovery | kind와 field를 `api-resources`, `explain`으로 확인했는가 |
| Output | 상태 확인에 필요한 출력 형식을 선택했는가 |
| Apply 이후 | `get`, `describe`, `events`로 결과를 검증했는가 |

## 흔한 실수

- namespace를 빼먹고 default에 리소스를 만든다.
- local 파일 YAML만 보고 cluster에 실제 반영된 상태를 확인하지 않는다.
- `create`와 `apply`의 사용 목적을 섞어서 변경 추적을 어렵게 만든다.
- `describe`의 Events 섹션을 보지 않고 spec만 확인한다.

## 시험 포인트

- CKAD는 문제마다 대상 namespace가 다르다. `kubectl config set-context --current --namespace=<ns>`로 기본 namespace를 먼저 고정하거나 매 명령에 `-n`을 붙이는 습관이 없으면, default namespace에 리소스를 만들고 채점에서 놓친다.
- YAML을 처음부터 손으로 쓰지 말고 `--dry-run=client -o yaml`로 골격을 만든 뒤 필요한 필드만 채운다. 이때 `--dry-run=client`는 API server에 실제 객체를 만들지 않고 client 측에서만 YAML을 출력한다는 점을 기억한다.
- 필드 경로가 헷갈리면 외우지 말고 `kubectl explain <kind>.<path>`로 현재 cluster가 아는 schema를 확인한다. 시험장 문서에서 필드명을 찾는 것보다 빠르다.
- 상태 검증은 출력 형식으로 속도가 갈린다. 전체 상황은 `-o wide`, 단일 값은 `-o jsonpath`, 전체 spec은 `-o yaml`로 나눠 보고, apply 성공 메시지가 아니라 `describe`의 Events를 근거로 판단한다.

## 관련 문서

- [[ckad-00-kubernetes-application-map|CKAD 애플리케이션 지도]] - 이전 글, 시리즈 전체 흐름과 학습 순서
- [[ckad-02-kubernetes-architecture|Kubernetes 아키텍처]] - 다음 글, kubectl 요청이 API server와 controller로 흐르는 구조
- [[ckad-04-kubectl-imperative|kubectl 명령형과 YAML 생성]] - 여기서 소개한 dry-run 생성 패턴을 본격적으로 다루는 편
- [[ckad-03-pod-yaml|Pod와 YAML 기본 구조]] - explain으로 확인한 필드를 실제 manifest로 옮기는 편
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - get/describe/events로 상태를 검증하는 관찰 흐름의 심화
- [[ckad-22-rbac-kubeconfig|RBAC와 kubeconfig]] - context와 kubeconfig가 인증/권한과 어떻게 연결되는지
- [[ckad-29-troubleshooting-playbook|트러블슈팅 플레이북]] - 조회와 관찰 순서를 장애 진단으로 확장한 종합 편

## 참고 자료

- [kubectl Overview](https://kubernetes.io/docs/reference/kubectl/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [kubectl JSONPath](https://kubernetes.io/docs/reference/kubectl/jsonpath/)
