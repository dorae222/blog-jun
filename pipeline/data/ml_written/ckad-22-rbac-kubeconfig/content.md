<!-- infographic-hero -->
![kubeconfig, API group, RBAC 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: kubeconfig, API group, RBAC 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# kubeconfig, API group, RBAC 기본기

Kubernetes의 모든 작업은 API 요청이다. `kubectl get pods`도 API Server에 대한 인증된 요청이며, 사용자가 해당 resource에 대한 `get` verb 권한을 가져야 성공한다.

RBAC는 Role과 Binding을 분리한다. Role은 어떤 권한인지 정의하고, RoleBinding은 그 권한을 누구에게 줄지 정한다.

## 핵심 개념

- kubeconfig context는 cluster, user, namespace 조합이다.
- API group은 리소스 종류의 API namespace다. 예를 들어 Deployment는 `apps` group에 있다.
- Role은 namespace 범위이고 ClusterRole은 cluster 범위 또는 재사용 가능한 권한 묶음이다.
- RoleBinding은 subject와 Role/ClusterRole을 특정 namespace에서 연결한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl config current-context
kubectl api-resources --api-group=apps
kubectl auth can-i list pods
kubectl auth can-i list pods --as=system:serviceaccount:default:app-sa
kubectl get role,rolebinding
```

![kubeconfig, API group, RBAC 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: kubeconfig, API group, RBAC 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

RBAC는 YAML보다 질문 구조가 중요하다. 누가(subject), 어디서(namespace/cluster), 무엇을(resource), 어떤 동작으로(verb) 할 수 있는지를 표로 풀면 이해가 빠르다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Subject | 권한을 받을 주체가 User, Group, ServiceAccount 중 무엇인가 |
| Scope | namespace 범위 권한인지 cluster 범위 권한인지 구분했는가 |
| Verb | get/list/watch/create/update/delete 중 필요한 동작만 허용했는가 |
| 검증 | `kubectl auth can-i`로 실제 권한을 확인했는가 |

## 흔한 실수

- Role만 만들고 RoleBinding을 빠뜨린다.
- ClusterRoleBinding을 불필요하게 사용해 권한 범위를 넓힌다.
- apiGroups 값을 리소스 kind 이름으로 착각한다.
- kubeconfig context namespace와 RBAC namespace를 혼동한다.

## 시험 포인트

- **Role만 만들고 RoleBinding을 빠뜨리면 권한은 여전히 0이다.** RBAC는 권한 정의(Role)와 권한 부여(Binding)가 분리되어 있어 두 객체가 모두 있어야 동작한다. "SA에게 pod read 권한을 줘라" 같은 지문은 Role과 RoleBinding을 함께 만들어야 채점된다.
- **RoleBinding이 ClusterRole을 참조할 수 있다.** 이 경우 권한은 그 RoleBinding이 놓인 namespace로만 한정된다. cluster 전역 권한이 필요할 때만 ClusterRoleBinding을 쓰고, 습관적으로 ClusterRoleBinding을 쓰면 권한 범위가 과도하게 넓어진다.
- **apiGroups와 resources 표기를 헷갈리기 쉽다.** core 리소스(Pod, Service, ConfigMap)는 `apiGroups: [""]` 빈 문자열이고 Deployment는 `apps`, RBAC 객체는 `rbac.authorization.k8s.io`다. resources에는 kind가 아니라 복수형 리소스 이름(`pods`, `deployments`)을 쓴다.
- **kubeconfig context의 default namespace와 RBAC namespace를 혼동한다.** current-context가 가리키는 namespace를 확인하지 않고 다른 namespace 리소스를 조회하면 forbidden이 뜬다. `kubectl config current-context`로 위치를 먼저 맞춘 뒤 `kubectl auth can-i`로 범위를 검증한다.

## 관련 문서

- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - 이전 글, RBAC로 권한을 받을 ServiceAccount identity
- [[ckad-23-admission-crd-operator|Admission Controller, CRD, Operator 구조]] - 다음 글, 인증과 인가 다음 단계인 admission 심사
- [[ckad-01-lab-kubectl-setup|kubectl 실습 환경 구성]] - kubeconfig와 context를 처음 설정하는 지점
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본]] - Role 권한 범위를 가르는 namespace 개념
- [[ckad-27-secret-encryption-at-rest|Secret 저장 암호화]] - ServiceAccount token과 Secret을 저장 단계에서 보호
- [[ckad-13-logs-events-debug|logs, events, 디버깅]] - forbidden 응답과 권한 문제를 event로 확인
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Organizing Cluster Access Using kubeconfig Files](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [API Groups](https://kubernetes.io/docs/reference/using-api/#api-groups)
