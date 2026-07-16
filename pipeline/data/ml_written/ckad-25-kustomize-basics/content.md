<!-- infographic-hero -->
![Kustomize base, overlay, patch 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Kustomize base, overlay, patch 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Kustomize base, overlay, patch 기본기

Kustomize는 template 언어를 쓰지 않고 Kubernetes YAML을 조합한다. 공통 리소스는 base에 두고, 환경별 차이는 overlay와 patch로 표현한다.

Helm이 package와 template 중심이라면 Kustomize는 원본 YAML을 유지한 채 변경 조각을 쌓는 방식에 가깝다. 둘 중 어느 것이 더 좋다기보다 팀의 manifest 관리 방식과 배포 도구에 맞춰 선택한다.

## 핵심 개념

- `kustomization.yaml`은 resources, patches, images, configMapGenerator 같은 조합 규칙을 담는다.
- base는 직접 배포 가능한 공통 리소스 묶음이다.
- overlay는 base를 참조하고 환경별 patch를 적용한다.
- `kubectl apply -k`는 kustomization 결과를 바로 적용한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl kustomize overlays/dev
kubectl apply -k overlays/dev
kubectl diff -k overlays/prod
kubectl delete -k overlays/dev
```

![Kustomize base, overlay, patch 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Kustomize base, overlay, patch 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Kustomize 콘텐츠는 디렉터리 구조를 함께 보여줘야 한다. `base/`와 `overlays/dev`, `overlays/prod`가 어떤 파일을 참조하는지 트리로 설명하면 template이 없다는 장점이 잘 드러난다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Base | base가 환경 독립적인 공통 manifest만 담고 있는가 |
| Overlay | 환경별 차이가 overlay patch에만 있는가 |
| Build | 적용 전 `kubectl kustomize` 결과를 확인했는가 |
| Secret | generator 사용 시 민감값 관리 방식을 별도로 정했는가 |

## 흔한 실수

- overlay마다 전체 manifest를 복사해 중복을 만든다.
- patch가 어떤 resource에 적용되는지 name/namespace를 맞추지 않는다.
- 빌드 결과를 확인하지 않고 apply한다.
- Helm values처럼 동적인 template 표현식을 기대한다.

## 시험 포인트

- **Kustomize에는 template 언어가 없다.** Helm values 같은 동적 표현식을 기대하면 안 되고, 환경별 차이는 patch로 원본 위에 덮어쓴다.
- **patch는 target이 정확히 일치해야 적용된다.** patch가 가리키는 name, kind, namespace가 base 리소스와 어긋나면 조용히 무시되어 아무 변화가 없다. 적용 전 `kubectl kustomize`로 실제 반영 여부를 확인한다.
- **적용 전에 렌더 결과를 본다.** `kubectl kustomize <dir>` 또는 `kubectl diff -k`로 최종 manifest를 확인하고 `kubectl apply -k`로 반영한다. `-k`는 kustomization 결과를 바로 적용하므로 확인 없이 쓰면 의도치 않은 변경이 들어간다.
- **base는 환경 독립적이어야 한다.** overlay마다 전체 manifest를 복사하면 중복이 쌓여 Kustomize의 장점이 사라진다. 공통은 base, 차이는 overlay patch로만 둔다.

## 관련 문서

- [[ckad-24-helm-basics|Helm 기본기]] - 이전 글, template 기반 package manager와의 접근 차이
- [[ckad-26-deployment-strategies|배포 전략]] - 다음 글, overlay로 만든 manifest를 어떤 전략으로 배포할지
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, 환경변수]] - configMapGenerator와 secretGenerator로 설정 생성
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본]] - overlay가 환경별 namespace를 바꾸는 흔한 패턴
- [[ckad-15-rolling-update-rollback|rolling update와 rollback]] - overlay로 image tag를 바꿔 rolling update를 유발
- [[kubernetes-ai-serving-infra|Kubernetes AI 서빙 인프라]] - GitOps 배포에서 Kustomize overlay 활용
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [kubectl kustomize](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#kustomize)
- [Declarative Management](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)
