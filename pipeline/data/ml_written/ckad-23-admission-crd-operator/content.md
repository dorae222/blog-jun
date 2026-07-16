<!-- infographic-hero -->
![Admission Controller, CRD, Operator 구조 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Admission Controller, CRD, Operator 구조 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Admission Controller, CRD, Operator 구조

Kubernetes는 내장 리소스만 사용하는 플랫폼이 아니다. Admission controller는 API 요청이 저장되기 전 정책을 적용하고, CRD는 새로운 리소스 종류를 API에 추가한다. Operator는 CRD와 controller를 결합해 특정 도메인 운영 지식을 자동화하는 패턴이다.

CKAD 관점에서는 admission, CRD, operator를 깊게 구현하기보다 이들이 manifest 적용 흐름과 오류 메시지에 어떤 영향을 주는지 이해하는 것이 중요하다.

## 핵심 개념

- Mutating admission은 객체가 저장되기 전 default나 sidecar 등을 주입할 수 있다.
- Validating admission은 정책 위반 객체를 거부할 수 있다.
- CRD는 Kubernetes API에 새로운 kind를 추가한다.
- Operator는 custom resource의 desired state를 보고 실제 리소스를 reconcile한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl api-resources | grep -i custom
kubectl get crd
kubectl explain crd.spec
kubectl get validatingwebhookconfiguration
kubectl get mutatingwebhookconfiguration
kubectl describe <custom-resource> <name>
```

![Admission Controller, CRD, Operator 구조 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Admission Controller, CRD, Operator 구조 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

CRD와 Operator 설명은 KServe, Argo CD, cert-manager 같은 실제 예시와 연결하면 좋다. 단, 기본 글에서는 특정 제품 세부 구현보다 `custom resource + controller loop`라는 공통 구조를 먼저 설명한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Admission error | apply 실패가 schema 오류인지 admission 거부인지 메시지로 구분했는가 |
| CRD 존재 | custom resource를 만들기 전에 CRD가 설치되어 있는가 |
| Controller | CRD만 있고 controller가 없으면 실제 동작이 일어나지 않는다는 점을 이해했는가 |
| Status | custom resource의 status와 event를 확인했는가 |

## 흔한 실수

- CRD를 만들면 자동으로 workload가 생성된다고 생각한다.
- admission webhook 장애를 YAML 문법 문제로만 본다.
- custom resource status를 확인하지 않는다.
- operator를 단순 Helm chart와 같은 것으로 설명한다.

## 시험 포인트

- **apply 실패 메시지의 출처를 구분한다.** 같은 "apply 실패"라도 schema validation 오류와 admission webhook 거부는 원인과 해결이 다르다. webhook 서버가 죽어 있으면 `failurePolicy` 설정에 따라 관련 요청 전체가 막힐 수 있으니 메시지 문구를 먼저 읽는다.
- **CRD를 설치했다고 workload가 생기지 않는다.** CRD는 API에 새 kind를 추가할 뿐이고, 실제 동작은 그 custom resource를 watch하는 controller(Operator)가 있어야 일어난다. controller 없이 CR만 만들면 status가 갱신되지 않는다.
- **Operator와 Helm chart를 같은 것으로 설명하지 않는다.** Helm은 배포 시점에 manifest를 렌더링하고 끝나지만, Operator는 custom resource의 desired state를 지속적으로 reconcile한다. 다음 편 Helm과 대비해 두면 헷갈리지 않는다.
- **CKAD 범위를 넘겨짚지 않는다.** admission이나 CRD, operator를 직접 구현하는 문제보다 `kubectl get crd`, `kubectl api-resources`, `kubectl explain`으로 클러스터에 설치된 확장을 탐색하고 custom resource의 status와 event를 읽는 수준을 요구한다.

## 관련 문서

- [[ckad-22-rbac-kubeconfig|kubeconfig, API group, RBAC 기본기]] - 이전 글, API 요청이 admission 앞에서 거치는 인증과 인가
- [[ckad-24-helm-basics|Helm 기본기]] - 다음 글, 배포 시점 렌더링과 지속 reconcile(Operator)의 차이
- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - Pod Security admission이 securityContext 정책을 강제하는 예
- [[ckad-28-api-deprecation|API deprecation 대응]] - CRD와 API version 관리, deprecated API 마이그레이션
- [[ckad-13-logs-events-debug|logs, events, 디버깅]] - admission 거부와 reconcile 실패를 event로 읽기
- [[kubernetes-ai-serving-infra|Kubernetes AI 서빙 인프라]] - KServe 등 CRD와 Operator로 구성되는 실제 확장 사례
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
