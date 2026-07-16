<!-- infographic-hero -->
![Pod와 YAML 기본 구조 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Pod와 YAML 기본 구조 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Pod와 YAML 기본 구조

Pod는 Kubernetes에서 컨테이너를 실행하는 최소 배포 단위다. 하나의 Pod 안 컨테이너는 네트워크 namespace와 일부 storage를 공유한다. 단일 컨테이너 Pod가 가장 흔하지만, sidecar나 init container처럼 여러 컨테이너를 함께 두는 패턴도 있다.

YAML은 Kubernetes 객체를 선언하는 형식일 뿐이다. 중요한 것은 `metadata`와 `spec`의 책임을 구분하고, status는 사용자가 쓰는 영역이 아니라 Kubernetes가 채우는 관측 결과라는 점을 이해하는 것이다.

## 핵심 개념

- Pod는 하나 이상의 container를 같은 실행 경계에 묶는다.
- Pod 안 컨테이너는 같은 Pod IP와 localhost를 공유한다.
- `spec.containers`는 리스트이므로 이름이 있는 container 객체가 하나 이상 필요하다.
- `status`는 manifest에 작성하는 desired state가 아니라 cluster가 기록한 observed state다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f pod.yaml
kubectl get pod web -o wide
kubectl describe pod web
kubectl get pod web -o yaml
```

![Pod와 YAML 기본 구조 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Pod와 YAML 기본 구조 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Pod manifest를 읽을 때는 먼저 `metadata.name`, `metadata.labels`, `spec.containers[].name`, `spec.containers[].image`를 확인한다. 이후 Service와 연결할 예정이면 label을 먼저 안정적으로 정해야 한다. label은 단순 메모가 아니라 selector가 의존하는 API 계약이다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 이름 | metadata.name이 namespace 안에서 고유한가 |
| Label | 나중에 Service/Deployment selector가 참조할 label이 있는가 |
| Image | image tag가 의도한 버전으로 고정되어 있는가 |
| Status | apply 이후 phase와 containerStatuses를 확인했는가 |

## 흔한 실수

- YAML indentation이 틀려 containers가 spec 아래에 들어가지 않는다.
- label 없이 Pod를 만들고 나중에 Service selector를 붙이려 한다.
- containerPort를 열면 자동으로 외부 접근이 된다고 생각한다.
- Pod를 장기 운영 단위로 직접 관리한다.

## 시험 포인트

- Pod manifest는 `apiVersion`, `kind`, `metadata`, `spec` 네 영역으로 읽는다. `spec.containers`는 이름 있는 항목이 최소 하나 필요한 리스트이고, indentation이 틀리면 `containers`가 `spec` 밖으로 빠지므로 apply 전에 계층부터 눈으로 확인한다.
- `status`는 작성 대상이 아니라 관측 결과다. apply 후 `kubectl get pod web -o yaml`로 `phase`와 `containerStatuses`를 읽어 실제 준비 상태를 판단한다.
- `containerPort`는 외부 노출이 아니라 문서화에 가까운 필드다. 접근 경로는 Service가 만들므로 Pod만으로 접속되기를 기대하지 않는다.
- label은 selector가 의존하는 API 계약이다. 이후 Service나 Deployment가 이 label을 참조하므로, 시험 문제의 label 요구사항을 놓치면 연결이 어긋난다.

## 관련 문서

- [[ckad-02-kubernetes-architecture|Kubernetes 아키텍처]] - 이전 글, 이 Pod가 API server와 kubelet을 거치는 경로
- [[ckad-04-kubectl-imperative|kubectl 명령형과 YAML 생성]] - 다음 글, 이 manifest 골격을 명령으로 빠르게 만드는 법
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment 기본기]] - Pod를 직접 관리하지 않고 상위 controller로 다루는 편
- [[ckad-11-multicontainer-pods|멀티컨테이너 Pod]] - 하나의 Pod에 sidecar/init container를 함께 두는 패턴
- [[ckad-14-label-selector-annotation|라벨, 셀렉터, 애노테이션]] - label을 selector 계약으로 다루는 편
- [[ckad-06-namespace-service-basics|Namespace와 Service 기본]] - containerPort를 실제 트래픽으로 노출하는 Service
- [[ckad-00-kubernetes-application-map|CKAD 애플리케이션 지도]] - 전체 시리즈 지도

## 참고 자료

- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Kubernetes Object Management](https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/)
