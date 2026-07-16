<!-- infographic-hero -->
![Service와 Ingress로 애플리케이션 노출하기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Service와 Ingress로 애플리케이션 노출하기 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Service와 Ingress로 애플리케이션 노출하기

Service는 Pod 앞의 안정적인 접근 지점이고, Ingress는 HTTP host/path 기반 routing rule이다. Ingress 객체만 만든다고 traffic이 흐르는 것은 아니며, 이를 실제 proxy 설정으로 반영하는 ingress controller가 필요하다.

CKAD 수준에서는 Ingress와 Service의 역할을 구분하고, backend Service와 port가 정확히 연결되는지 확인하는 것이 중요하다.

## 핵심 개념

- ClusterIP Service는 cluster 내부 접근의 기본 형태다.
- Ingress는 HTTP/HTTPS routing rule이며 Service backend를 참조한다.
- Ingress controller가 설치되어 있어야 Ingress rule이 실제 동작한다.
- Service endpoint가 비어 있으면 Ingress rule이 맞아도 backend로 전달되지 않는다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
spec:
  rules:
    - host: web.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl get ingress
kubectl describe ingress web
kubectl get svc web
kubectl get endpoints web
kubectl get ingressclass
curl -H 'Host: web.example.com' http://<ingress-address>/
```

![Service와 Ingress로 애플리케이션 노출하기 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Service와 Ingress로 애플리케이션 노출하기 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Ingress 콘텐츠는 `Client -> Ingress -> Service -> Endpoint -> Pod` 순서로 쓰면 명확하다. 장애도 같은 순서로 좁힌다. 주소가 없으면 controller/IngressClass를 보고, backend가 없으면 Service endpoint를 본다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Controller | Ingress controller와 IngressClass가 존재하는가 |
| Backend | Ingress backend Service 이름과 port가 맞는가 |
| Endpoint | Service endpoint가 준비되어 있는가 |
| Host | 요청 Host header가 Ingress rule과 일치하는가 |

## 자주 틀리는 지점

- **Ingress 객체만 만들면 트래픽이 흐른다고 가정한다** - Ingress rule은 이를 실제 proxy 설정으로 반영하는 ingress controller가 없으면 그냥 선언으로 남는다. controller와 IngressClass가 cluster에 있는지 먼저 확인해야 하며, 없으면 ADDRESS가 채워지지 않는다.
- **Service의 targetPort와 Ingress backend port를 섞어 쓴다** - Ingress backend의 port는 container의 targetPort가 아니라 Service가 노출하는 port(번호 또는 name)를 가리킨다. Service port와 backend port가 어긋나면 rule이 맞아도 502가 난다.
- **Host header 없이 curl해서 rule이 안 먹는다고 판단한다** - host 기반 rule은 요청의 Host header로 매칭하므로 IP로 바로 curl하면 어떤 rule에도 걸리지 않는다. `curl -H 'Host: web.example.com'`처럼 Host를 명시해 테스트한다.
- **Service endpoint가 비어 있는데 Ingress 문제로 본다** - rule과 backend 이름이 맞아도 Service의 endpoint가 없으면 backend로 전달되지 않는다. `Client -> Ingress -> Service -> Endpoint -> Pod` 순서로 좁히면서 selector와 readiness를 확인한다.

## 관련 문서

- [[ckad-17-networkpolicy|NetworkPolicy 기본]] - 이전 글, Pod 간 트래픽 허용 모델
- [[ckad-19-volumes-pv-pvc|Volume, PV, PVC]] - 다음 글, Pod 데이터 영속화
- [[ckad-06-namespace-service-basics|Namespace와 Service 기초]] - Ingress backend가 참조하는 ClusterIP Service
- [[ckad-12-probes-health-checks|Probe와 헬스 체크]] - readiness가 통과해야 Service endpoint가 채워진다
- [[ckad-14-label-selector-annotation|Label과 Selector]] - Service selector가 endpoint 대상 Pod를 고른다
- [[ckad-13-logs-events-debug|로그와 이벤트로 디버깅]] - controller와 Service 장애를 순서대로 좁히기
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 시리즈 전체 흐름

## 참고 자료

- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
- [Service](https://kubernetes.io/docs/concepts/services-networking/service/)
