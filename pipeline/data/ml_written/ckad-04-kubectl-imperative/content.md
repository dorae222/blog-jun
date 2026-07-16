<!-- infographic-hero -->
![kubectl 명령형 작성과 YAML 생성 패턴 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: kubectl 명령형 작성과 YAML 생성 패턴 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# kubectl 명령형 작성과 YAML 생성 패턴

명령형 `kubectl`은 선언형 운영의 반대가 아니라 manifest를 빠르게 만들기 위한 보조 도구로 쓸 수 있다. 처음부터 모든 YAML을 손으로 작성하기보다 `--dry-run=client -o yaml`로 골격을 만들고 필요한 필드를 채우면 API 구조를 덜 틀린다.

중요한 기준은 최종 상태를 파일로 남기는 것이다. 일회성 명령으로 만든 리소스도 이후 유지보수가 필요하면 manifest로 전환해야 한다.

## 핵심 개념

- 명령형 명령은 빠르지만 변경 이력을 파일로 남기지 않으면 재현성이 떨어진다.
- `--dry-run=client`는 API server에 객체를 만들지 않고 client 측에서 YAML을 출력한다.
- 생성된 YAML에는 불필요한 기본값이 포함될 수 있으므로 핵심 필드만 남겨도 된다.
- `kubectl explain`과 함께 쓰면 field 경로를 확인하면서 YAML을 보완할 수 있다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl run web --image=nginx:1.27 --dry-run=client -o yaml > pod.yaml
kubectl create deployment web --image=nginx:1.27 --dry-run=client -o yaml > deploy.yaml
kubectl expose deployment web --port=80 --target-port=80 --dry-run=client -o yaml > svc.yaml
kubectl create configmap app-config --from-literal=MODE=prod --dry-run=client -o yaml > configmap.yaml
```

![kubectl 명령형 작성과 YAML 생성 패턴 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: kubectl 명령형 작성과 YAML 생성 패턴 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

명령으로 만든 YAML은 그대로 쓰기 전에 `metadata.creationTimestamp`, 빈 status, 불필요한 기본값을 제거한다. 블로그나 운영 문서에는 명령과 최종 YAML을 둘 다 제시하면 독자가 API 구조와 생성 과정을 함께 이해할 수 있다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 재현성 | 최종 manifest가 파일로 남아 있는가 |
| Selector | 명령으로 생성된 selector와 label이 의도와 일치하는가 |
| 불필요 필드 | status나 runtime field를 manifest에 남기지 않았는가 |
| 검증 | 생성된 YAML을 apply하기 전 `kubectl explain`으로 주요 field를 확인했는가 |

## 흔한 실수

- 명령형으로 만든 리소스를 나중에 수동으로 계속 수정한다.
- dry-run 없이 리소스를 먼저 만들고 YAML을 잃어버린다.
- Service expose가 만든 selector를 확인하지 않는다.
- 생성된 YAML의 status 필드를 그대로 저장한다.

## 시험 포인트

- CKAD는 시간 싸움이다. `kubectl run`, `create`, `expose`에 `--dry-run=client -o yaml > file.yaml`을 붙여 골격을 빠르게 만든 뒤 필요한 필드만 채우는 흐름을 손에 익힌다.
- `--dry-run=client`는 API server에 객체를 만들지 않고 YAML만 출력한다. 실제로 생성하는 명령과 골격만 뽑는 명령을 구분해, 시험에서 의도치 않게 리소스를 만들지 않는다.
- 생성된 YAML을 그대로 제출하지 않는다. `metadata.creationTimestamp`와 빈 `status`, 불필요한 기본값을 지우고, 필드 경로가 헷갈리면 `kubectl explain`으로 확인한다.
- `kubectl expose`가 자동으로 만든 selector와 label이 의도와 맞는지 확인한다. 이 selector가 Service와 Pod를 잇는 계약이므로 어긋나면 Service가 엉뚱한 Pod를 고르거나 아무것도 고르지 못한다.

## 관련 문서

- [[ckad-03-pod-yaml|Pod와 YAML 기본 구조]] - 이전 글, 명령으로 생성한 YAML이 따르는 객체 구조
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment 기본기]] - 다음 글, `create deployment`가 만드는 리소스의 실제 동작
- [[ckad-01-lab-kubectl-setup|kubectl 작업 환경과 기본 조회 흐름]] - dry-run과 explain을 처음 소개한 편
- [[ckad-07-configmap-secret-env|ConfigMap과 Secret, 환경변수]] - `create configmap --from-literal` 예제가 이어지는 편
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본]] - `kubectl expose`가 만드는 Service를 자세히 다루는 편
- [[ckad-08-command-args-image|command, args, image 설정]] - 생성한 골격에 채워 넣는 container 필드
- [[ckad-00-kubernetes-application-map|CKAD 애플리케이션 지도]] - 전체 시리즈 지도

## 참고 자료

- [Managing Kubernetes Objects Using Imperative Commands](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/imperative-command/)
- [Declarative Management](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)
- [kubectl Commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
