<!-- infographic-hero -->
![Namespace, Service, Cluster DNS 기본기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Namespace, Service, Cluster DNS 기본기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Namespace, Service, Cluster DNS 기본기

Pod IP는 Pod가 재생성될 때 바뀔 수 있으므로 애플리케이션의 안정적인 접근점으로 쓰면 안 된다. Service는 label selector로 Pod 집합을 찾고, 그 앞에 안정적인 ClusterIP와 DNS 이름을 제공한다.

Namespace는 리소스 이름의 범위를 나누고 작업 맥락을 분리한다. 같은 이름의 Service라도 namespace가 다르면 다른 객체다.

## 핵심 개념

- Namespace는 cluster를 물리적으로 나누는 기능이 아니라 API 객체 범위를 나누는 기능이다.
- Service selector는 Pod label과 일치해야 endpoint가 생성된다.
- ClusterIP Service는 cluster 내부 접근에 사용된다.
- Service DNS 이름은 같은 namespace에서는 짧은 이름으로, 다른 namespace에서는 FQDN 또는 `name.namespace` 형식으로 접근한다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl create namespace app
kubectl get ns
kubectl apply -f service.yaml
kubectl get svc web
kubectl get endpoints web
kubectl run curl --image=curlimages/curl -it --rm --restart=Never -- curl http://web.default.svc.cluster.local
```

![Namespace, Service, Cluster DNS 기본기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Namespace, Service, Cluster DNS 기본기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Service를 설명할 때는 Service 자체보다 selector와 endpoint를 함께 보여주는 것이 중요하다. Service가 있는데 통신이 안 된다면 가장 먼저 `kubectl get endpoints`로 실제 backend Pod가 잡혔는지 확인한다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Namespace | 리소스가 의도한 namespace에 생성되었는가 |
| Selector | Service selector가 Pod label과 정확히 일치하는가 |
| Endpoints | Service endpoint가 비어 있지 않은가 |
| Port | Service `port`와 container `targetPort`를 구분했는가 |

## 흔한 실수

- Pod IP를 다른 애플리케이션 설정에 직접 넣는다.
- Service selector label을 Deployment template label과 다르게 쓴다.
- 다른 namespace의 Service를 짧은 이름만으로 호출한다.
- Service port와 targetPort의 의미를 바꿔 이해한다.

## 시험 포인트

- Service가 있는데 통신이 안 되면 가장 먼저 `kubectl get endpoints`를 본다. endpoint 목록이 비어 있으면 Service selector와 Pod label이 어긋난 것이고, 값이 채워져 있으면 문제는 Service 밖에 있다.
- `port`와 `targetPort`를 반대로 이해하지 않는다. `port`는 Service가 cluster 안에서 노출하는 포트이고, `targetPort`는 트래픽이 실제로 도착하는 container 포트다.
- 다른 namespace의 Service는 짧은 이름으로 부를 수 없다. 같은 namespace면 `web`, 다른 namespace면 `web.<namespace>` 또는 FQDN `web.<namespace>.svc.cluster.local`을 쓴다.
- Namespace는 물리 격리가 아니라 API 객체 이름의 범위다. 같은 이름의 Service라도 namespace가 다르면 서로 다른 객체이므로, 문제를 볼 때 `-n` 옵션으로 대상 namespace부터 맞춘다.

## 관련 문서

- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]] - 이전 글, Service가 selector로 붙일 Pod 집합을 만드는 워크로드
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, env 주입]] - 다음 글, Service로 노출한 앱에 설정값을 주입하는 방법
- [[ckad-14-label-selector-annotation|Label과 Selector, Annotation]] - Service selector가 Pod label과 맞는지 판단하는 기준을 더 깊이 다룬다
- [[ckad-18-ingress|Ingress]] - ClusterIP Service를 cluster 밖으로 HTTP 라우팅하는 상위 계층
- [[ckad-17-networkpolicy|NetworkPolicy]] - Service를 통해 흐르는 Pod 간 트래픽을 label 기준으로 제어한다
- [[ckad-13-logs-events-debug|로그, 이벤트, 디버깅]] - endpoint가 비거나 DNS가 안 풀릴 때 원인을 좁히는 순서
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 전체 시리즈에서 이 글의 위치

## 참고 자료

- [Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
