<!-- infographic-hero -->
![StatefulSet과 Headless Service 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: StatefulSet과 Headless Service 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# StatefulSet과 Headless Service

Deployment는 같은 template의 교체 가능한 Pod 집합에 적합하다. 반면 StatefulSet은 각 replica가 고유한 identity와 storage를 가져야 하는 workload에 적합하다. 대표적으로 database, queue, consensus system이 여기에 해당한다.

StatefulSet의 핵심은 ordinal Pod 이름, stable network identity, Pod별 PVC다. Headless Service는 각 Pod를 직접 찾을 수 있는 DNS 경로를 제공한다.

## 핵심 개념

- StatefulSet Pod는 `<name>-0`, `<name>-1` 같은 stable ordinal 이름을 가진다.
- Headless Service는 `clusterIP: None`으로 설정한다.
- volumeClaimTemplates는 replica마다 별도 PVC를 만든다.
- Pod 삭제 후 재생성되어도 같은 identity와 PVC를 다시 사용한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-headless
spec:
  clusterIP: None
  selector:
    app: web
  ports:
    - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: web-headless
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f statefulset.yaml
kubectl get statefulset,pod,svc
kubectl get pod web-0 -o wide
kubectl exec -it web-0 -- hostname
kubectl get endpoints web-headless
```

![StatefulSet과 Headless Service 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: StatefulSet과 Headless Service 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

StatefulSet 설명은 Deployment와의 차이를 중심으로 쓰면 좋다. 모든 replica가 교체 가능하면 Deployment가 맞고, replica마다 고유한 이름과 storage가 필요하면 StatefulSet을 검토한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Identity | Pod별 stable identity가 실제로 필요한 workload인가 |
| ServiceName | StatefulSet serviceName이 Headless Service를 가리키는가 |
| Storage | Pod별 PVC가 필요한 경우 volumeClaimTemplates를 사용했는가 |
| Update | 순차 update와 삭제 순서가 workload 요구와 맞는가 |

## 자주 틀리는 지점

- **단순 stateless 앱에 StatefulSet을 쓴다** - replica가 서로 교체 가능하면 Deployment가 맞다. StatefulSet은 각 Pod가 고유한 이름과 storage를 유지해야 하는 database, queue, consensus system 같은 workload에만 필요하다.
- **Headless Service 없이 stable DNS를 기대한다** - `<pod>-<ordinal>.<service>` 형태의 per-Pod DNS는 `clusterIP: None`인 Headless Service와 StatefulSet의 serviceName이 연결되어 있어야 생긴다. 일반 ClusterIP Service로는 개별 Pod를 지목할 수 없다.
- **scale down하면 PVC가 자동 삭제된다고 생각한다** - volumeClaimTemplates로 만든 PVC는 replica를 줄이거나 StatefulSet을 지워도 기본적으로 남는다. 데이터를 정리하려면 PVC를 직접 삭제해야 하고, 반대로 실수로 지우지 않도록 주의한다.
- **Pod ordinal에 의존하는 설정을 문서화하지 않는다** - `<name>-0`을 primary로 쓰는 등 ordinal에 기대는 구성은 코드와 문서에 명시해야 한다. 그렇지 않으면 순차 update나 재생성 순서에서 예상치 못한 동작이 생긴다.

## 관련 문서

- [[ckad-19-volumes-pv-pvc|Volume, PV, PVC]] - 이전 글, volumeClaimTemplates가 만드는 Pod별 PVC의 기반
- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - 다음 글, Pod 보안 컨텍스트
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]] - 교체 가능한 Deployment와 identity를 가진 StatefulSet의 대비
- [[ckad-06-namespace-service-basics|Namespace와 Service 기초]] - Headless Service가 변형인 Service의 기본형
- [[ckad-26-deployment-strategies|배포 전략]] - StatefulSet의 순차 update와 대비되는 배포 방식
- [[ckad-13-logs-events-debug|로그와 이벤트로 디버깅]] - Pod와 endpoint 상태를 event로 진단
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 시리즈 전체 흐름

## 참고 자료

- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [Stable Storage](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#stable-storage)
