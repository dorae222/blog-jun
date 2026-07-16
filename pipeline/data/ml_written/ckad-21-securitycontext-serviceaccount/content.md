<!-- infographic-hero -->
![SecurityContext와 ServiceAccount 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: SecurityContext와 ServiceAccount 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# SecurityContext와 ServiceAccount

SecurityContext와 ServiceAccount는 모두 보안과 관련 있지만 다루는 계층이 다르다. SecurityContext는 container process가 어떤 Linux 권한으로 실행될지에 가깝고, ServiceAccount는 Pod가 Kubernetes API를 호출할 때 어떤 identity를 사용할지에 가깝다.

둘을 분리해서 이해해야 권한 문제를 줄일 수 있다. root로 실행하지 않는 것과 API 권한을 최소화하는 것은 서로 다른 작업이다.

## 핵심 개념

- Pod-level securityContext는 모든 container에 적용되는 기본 실행 보안 속성을 둔다.
- container-level securityContext는 개별 container 설정으로 Pod-level 값을 override할 수 있다.
- ServiceAccount는 namespace-scoped 객체다.
- ServiceAccount 자체는 identity이고 실제 권한은 RBAC binding으로 결정된다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
---
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  serviceAccountName: app-sa
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: nginx:1.27
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f security.yaml
kubectl get serviceaccount app-sa
kubectl describe pod secure-app
kubectl auth can-i get pods --as=system:serviceaccount:default:app-sa
```

![SecurityContext와 ServiceAccount 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: SecurityContext와 ServiceAccount 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

보안 글에서는 runtime 권한과 API 권한을 섞지 않는다. `runAsNonRoot`는 프로세스 권한이고, `ServiceAccount + RBAC`는 Kubernetes API 권한이다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Runtime | container가 root나 privilege escalation 없이 실행 가능한가 |
| Filesystem | readOnlyRootFilesystem을 켰을 때 필요한 writable path가 있는가 |
| Identity | Pod가 default ServiceAccount 대신 전용 ServiceAccount를 쓰는가 |
| RBAC | `kubectl auth can-i`로 권한 범위를 확인했는가 |

## 흔한 실수

- ServiceAccount를 만들면 자동으로 필요한 권한이 생긴다고 생각한다.
- securityContext를 설정하고 image가 root 권한을 요구하는지 확인하지 않는다.
- default ServiceAccount에 광범위한 권한을 부여한다.
- readOnlyRootFilesystem을 켜고 임시 파일 경로를 준비하지 않는다.

## 시험 포인트

- **Pod-level과 container-level securityContext가 겹치면 container-level이 이긴다.** "이 container만 root로 실행하지 마라" 같은 지문은 반드시 해당 container의 `securityContext`에 넣어야 한다. Pod-level에만 두면 같은 Pod의 다른 container까지 제약이 걸려 의도와 어긋난다.
- **`runAsNonRoot: true`는 UID를 지정하는 게 아니라 "root면 안 된다"는 제약이다.** image가 여전히 root(UID 0)로 기동하도록 만들어졌다면 kubelet이 container 생성을 거부해 Pod가 `CreateContainerConfigError`로 멈춘다. 이때는 `runAsUser`로 non-root UID를 명시하거나 image를 바꿔야 한다.
- **ServiceAccount를 만들고 `serviceAccountName`으로 연결해도 권한은 0이다.** identity(누구인가)와 permission(무엇을 할 수 있는가)은 분리되어 있고, 실제 권한은 다음 편의 RBAC binding에서 온다. `kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<ns>:<sa>`로 스스로 확인한다.
- **`capabilities.drop: ["ALL"]`은 문자열 리스트다.** 모두 버린 뒤 특정 capability(예: `NET_BIND_SERVICE`)가 필요하면 `add`로 되돌려야 한다. drop만 해두면 1024 미만 포트 bind 같은 동작이 조용히 막힌다.

## 관련 문서

- [[ckad-20-statefulset-headless|StatefulSet과 headless Service]] - 이전 글, 상태를 가지는 workload의 실행 단위
- [[ckad-22-rbac-kubeconfig|kubeconfig, API group, RBAC 기본기]] - 다음 글, ServiceAccount에 실제 권한을 부여하는 RBAC
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, 환경변수]] - 실행 보안과 함께 다루는 설정과 비밀값 주입
- [[ckad-27-secret-encryption-at-rest|Secret 저장 암호화]] - ServiceAccount token과 Secret을 저장 단계에서 보호
- [[ckad-23-admission-crd-operator|Admission Controller, CRD, Operator 구조]] - Pod Security admission이 securityContext 정책을 강제하는 지점
- [[ckad-13-logs-events-debug|logs, events, 디버깅]] - CreateContainerConfigError와 permission 거부를 event로 읽기
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Configure a Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
