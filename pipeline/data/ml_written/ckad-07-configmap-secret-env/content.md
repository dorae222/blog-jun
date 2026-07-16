<!-- infographic-hero -->
![ConfigMap, Secret, env 주입 패턴 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: ConfigMap, Secret, env 주입 패턴 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# ConfigMap, Secret, env 주입 패턴

컨테이너 image는 가능한 한 환경 독립적으로 유지하고, 실행 환경별 값은 Kubernetes 객체로 분리하는 것이 좋다. ConfigMap은 일반 설정에, Secret은 비밀번호나 token처럼 민감한 값에 사용한다.

다만 Secret이라는 이름이 곧 암호화된 안전한 저장소를 의미하지는 않는다. 접근 권한, etcd 암호화, 외부 secret manager 연동까지 함께 고려해야 한다.

## 핵심 개념

- ConfigMap과 Secret은 Pod에 자동 주입되지 않는다. PodSpec에서 명시적으로 참조해야 한다.
- `env`는 개별 key를 원하는 변수 이름으로 매핑할 때 적합하다.
- `envFrom`은 여러 key를 한 번에 환경변수로 가져올 때 편하다.
- volume mount 방식은 파일 설정을 읽는 애플리케이션에 적합하다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_MODE: production
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  API_TOKEN: change-me
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "env && sleep 3600"]
      envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secret
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl create configmap app-config --from-literal=APP_MODE=production
kubectl create secret generic app-secret --from-literal=API_TOKEN=change-me
kubectl describe configmap app-config
kubectl describe secret app-secret
kubectl exec app -- env | sort
```

![ConfigMap, Secret, env 주입 패턴 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: ConfigMap, Secret, env 주입 패턴 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

설정 주입 글에서는 `ConfigMap을 만들었다`와 `Pod가 그 값을 사용한다`를 분리해 보여줘야 한다. 특히 Secret은 값을 화면에 직접 노출하지 않도록 예시를 구성하고, 민감값은 placeholder로 둔다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 참조 | PodSpec에서 ConfigMap/Secret 이름을 정확히 참조하는가 |
| Key | 참조한 key가 실제 객체에 존재하는가 |
| 변경 반영 | 설정 변경 후 Pod 재시작 또는 volume update 동작을 이해했는가 |
| 권한 | Secret 조회 권한이 불필요하게 넓지 않은가 |

## 흔한 실수

- Secret 값을 Git에 평문으로 넣고 그대로 apply한다.
- ConfigMap 이름만 만들고 PodSpec 참조를 빠뜨린다.
- 환경변수로 주입한 값이 실행 중 자동 갱신된다고 생각한다.
- ConfigMap에 민감정보를 넣는다.

## 시험 포인트

- `env`로 주입한 값은 Pod가 생성될 때 한 번 고정된다. ConfigMap이나 Secret을 나중에 바꿔도 실행 중인 container의 환경변수는 자동으로 갱신되지 않으므로, 값을 반영하려면 Pod를 다시 만들어야 한다. volume mount로 붙인 파일은 갱신될 수 있다는 점과 구분한다.
- `env`와 `envFrom`을 구분한다. `env`는 개별 key를 원하는 변수 이름으로 매핑할 때, `envFrom`은 객체의 모든 key를 그대로 환경변수로 가져올 때 쓴다.
- Secret은 암호화가 아니라 base64 인코딩일 뿐이다. 이름이 Secret이어도 값 자체는 평문에 가깝게 저장되므로, 접근 권한과 etcd 저장 시 암호화를 별도로 챙겨야 한다.
- 참조한 ConfigMap/Secret 이름이나 key가 실제로 없으면 값이 비거나 Pod가 뜨지 못한다. `kubectl describe`로 객체를 확인하고 `kubectl exec app -- env | sort`로 실제 주입 결과를 검증한다.

## 관련 문서

- [[ckad-06-namespace-service-basics|Namespace와 Service 기본기]] - 이전 글, 설정을 주입할 앱을 Service로 노출하는 단계
- [[ckad-08-command-args-image|image, command, args]] - 다음 글, 주입한 설정을 command와 args가 어떻게 소비하는지
- [[ckad-27-secret-encryption-at-rest|Secret 저장 시 암호화]] - Secret을 etcd에 저장할 때 실제로 암호화하는 방법
- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - Pod가 Secret에 접근하는 권한과 ServiceAccount
- [[ckad-22-rbac-kubeconfig|RBAC와 kubeconfig]] - Secret 조회 권한을 RBAC로 좁히는 방법
- [[ckad-19-volumes-pv-pvc|Volume, PV, PVC]] - env 대신 volume mount로 설정 파일을 주입하는 경로
- [[ckad-24-helm-basics|Helm 기본기]] - 환경별 ConfigMap/Secret 값을 chart로 관리
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Define Environment Variables](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/)
