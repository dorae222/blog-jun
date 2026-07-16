<!-- infographic-hero -->
![NetworkPolicy 기본과 트래픽 허용 모델 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: NetworkPolicy 기본과 트래픽 허용 모델 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# NetworkPolicy 기본과 트래픽 허용 모델

Kubernetes cluster 안 Pod 간 통신은 기본적으로 열려 있는 경우가 많다. NetworkPolicy는 특정 Pod에 대해 ingress와 egress를 명시적으로 허용하는 allow-list 모델을 만든다.

정책을 만들었다고 항상 적용되는 것은 아니다. cluster CNI가 NetworkPolicy를 지원해야 하며, 정책 대상이 되는 Pod selector가 정확해야 한다.

## 핵심 개념

- NetworkPolicy의 `podSelector`는 정책이 적용될 대상 Pod를 고른다.
- ingress rule은 대상 Pod로 들어오는 트래픽을 허용한다.
- egress rule은 대상 Pod에서 나가는 트래픽을 허용한다.
- 정책이 없는 Pod는 기본 네트워크 허용 상태일 수 있다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f networkpolicy.yaml
kubectl get networkpolicy
kubectl describe networkpolicy allow-frontend-to-api
kubectl run test --image=curlimages/curl -it --rm --restart=Never -- curl http://api:8080
```

![NetworkPolicy 기본과 트래픽 허용 모델 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: NetworkPolicy 기본과 트래픽 허용 모델 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

NetworkPolicy 글은 반드시 방향을 그림으로 보여줘야 한다. `podSelector`가 source가 아니라 policy 대상 Pod를 고른다는 점이 가장 자주 헷갈리는 부분이다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| CNI | cluster CNI가 NetworkPolicy를 지원하는가 |
| 대상 | spec.podSelector가 보호하려는 대상 Pod를 고르는가 |
| 방향 | Ingress와 Egress를 올바르게 구분했는가 |
| 검증 | 허용되어야 하는 traffic과 차단되어야 하는 traffic을 둘 다 테스트했는가 |

## 자주 틀리는 지점

- **podSelector를 트래픽 출발지 selector로 착각한다** - `spec.podSelector`는 정책이 적용되는 대상, 즉 보호받는 Pod를 고른다. 트래픽 출발지는 `ingress.from`(또는 `egress.to`) 안의 podSelector로 지정한다. 이 둘을 뒤집으면 엉뚱한 Pod에 정책이 걸린다.
- **CNI 지원을 확인하지 않고 정책이 적용됐다고 믿는다** - NetworkPolicy 객체는 CNI가 이를 구현하지 않으면 만들어져도 아무 효과가 없다. Calico, Cilium처럼 NetworkPolicy를 지원하는 CNI인지 먼저 확인하고, 허용과 차단 트래픽을 실제 요청으로 둘 다 테스트한다.
- **egress를 막으면서 DNS를 함께 막는다** - egress 정책을 걸면 kube-dns로 향하는 UDP/TCP 53번 트래픽까지 차단되어 이름 해석이 실패한다. 외부 통신 장애를 애플리케이션에서 찾기 전에 DNS 허용 rule이 있는지 본다.
- **namespaceSelector와 podSelector 조합의 의미를 헷갈린다** - 하나의 from 항목 안에서 두 selector를 같이 쓰면 "해당 namespace의 그 Pod"라는 AND 조건이고, 별도 항목으로 나누면 OR 조건이 된다. 들여쓰기 한 칸 차이로 허용 범위가 달라진다.

## 관련 문서

- [[ckad-16-jobs-cronjobs|Job과 CronJob]] - 이전 글, 완료되는 배치 워크로드 실행
- [[ckad-18-ingress|Service와 Ingress]] - 다음 글, 외부에서 들어오는 HTTP 트래픽 라우팅
- [[ckad-06-namespace-service-basics|Namespace와 Service 기초]] - NetworkPolicy가 대상으로 삼는 namespace 경계와 Service
- [[ckad-14-label-selector-annotation|Label과 Selector]] - podSelector와 namespaceSelector가 기반하는 label 매칭
- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - 네트워크 경계와 함께 보는 Pod 보안 경계
- [[ckad-13-logs-events-debug|로그와 이벤트로 디버깅]] - 통신 차단 증상을 event와 로그로 좁히기
- [[ckad-00-kubernetes-application-map|CKAD 기준 Kubernetes 애플리케이션 지도]] - 시리즈 전체 흐름

## 참고 자료

- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Declare Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/)
- [Services Networking](https://kubernetes.io/docs/concepts/services-networking/)
