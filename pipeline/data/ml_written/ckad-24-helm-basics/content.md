<!-- infographic-hero -->
![Helm chart, values, template, release 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Helm chart, values, template, release 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Helm chart, values, template, release 기본기

Helm은 Kubernetes API 자체가 아니라 manifest를 만들고 배포 이력을 관리하는 package manager다. chart는 template 묶음이고, values는 환경별 입력값이며, release는 cluster에 설치된 chart instance다.

Helm을 이해할 때 가장 중요한 것은 `helm template`으로 생성되는 최종 Kubernetes YAML을 확인하는 습관이다. 결국 cluster에 적용되는 것은 Helm template이 아니라 렌더링된 manifest다.

## 핵심 개념

- Chart는 Kubernetes manifest template과 chart metadata를 포함한다.
- values.yaml은 image tag, replica, service port 같은 환경별 값을 분리한다.
- `helm template`은 cluster 적용 없이 최종 YAML을 확인하게 해준다.
- release revision은 upgrade/rollback 이력을 관리한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
helm create web
helm template web ./web -f values.yaml
helm install web ./web
helm upgrade web ./web --set image.tag=1.28
helm history web
helm rollback web 1
helm uninstall web
```

![Helm chart, values, template, release 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Helm chart, values, template, release 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Helm 글에서는 chart 내부 template보다 렌더링 결과를 먼저 보여주는 편이 실용적이다. 독자는 Helm 문법보다 최종적으로 어떤 Deployment, Service, ConfigMap이 만들어지는지를 알아야 한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Render | helm template 결과가 유효한 Kubernetes manifest인가 |
| Values | 환경별 차이가 values로 분리되어 있는가 |
| Release | install/upgrade/rollback 이력을 확인했는가 |
| Ownership | Helm이 관리하는 리소스를 kubectl로 직접 수정해 drift를 만들지 않는가 |

## 흔한 실수

- Helm chart를 Kubernetes 리소스라고 설명한다.
- template 결과를 보지 않고 install부터 실행한다.
- values에 secret 평문을 넣고 Git에 저장한다.
- Helm release가 관리하는 리소스를 수동 수정해 다음 upgrade에서 덮어쓴다.

## 시험 포인트

- **cluster에 적용되는 건 chart가 아니라 rendered manifest다.** `helm template`으로 최종 YAML을 먼저 확인하는 습관을 들이면, 문제 원인이 chart 문법인지 렌더 결과인지 빠르게 나뉜다.
- **Helm이 관리하는 리소스를 kubectl로 직접 수정하면 drift가 생긴다.** 수동 변경은 다음 `helm upgrade`에서 덮어써진다. 변경은 values나 chart를 고쳐 release로 반영한다.
- **values에 secret 평문을 넣고 Git에 커밋하지 않는다.** 민감값은 별도 Secret 관리 흐름으로 분리하고, chart repository에는 참조만 남긴다.
- **rollback은 release revision 단위다.** `helm history <name>`로 revision을 확인하고 `helm rollback <name> <revision>`으로 되돌린다. Deployment 자체의 rollout rollback과는 관리 주체가 다르다.

## 관련 문서

- [[ckad-23-admission-crd-operator|Admission Controller, CRD, Operator 구조]] - 이전 글, 렌더링 후 배포와 지속 reconcile(Operator)의 차이
- [[ckad-25-kustomize-basics|Kustomize 기본기]] - 다음 글, template 없이 YAML을 조합하는 대안 접근
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, 환경변수]] - values가 최종적으로 만들어 내는 ConfigMap과 Secret
- [[ckad-15-rolling-update-rollback|rolling update와 rollback]] - release rollback과 Deployment rollback의 관계
- [[ckad-27-secret-encryption-at-rest|Secret 저장 암호화]] - values 평문 대신 Secret을 안전하게 다루는 방법
- [[kubernetes-ai-serving-infra|Kubernetes AI 서빙 인프라]] - Helm과 GitOps로 배포하는 실제 서빙 스택
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Helm Docs](https://helm.sh/docs/)
- [Helm Charts](https://helm.sh/docs/topics/charts/)
- [Helm Template Guide](https://helm.sh/docs/chart_template_guide/)
