<!-- infographic-hero -->
![Secret 암호화 at rest와 보안 경계 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Secret 암호화 at rest와 보안 경계 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Secret 암호화 at rest와 보안 경계

Kubernetes Secret은 민감정보를 ConfigMap과 구분해 다루는 객체지만, 그 자체가 완전한 비밀 관리 시스템은 아니다. `data` 필드의 base64는 encoding일 뿐 암호화가 아니다.

Secret 보안은 RBAC 접근 제어, etcd encryption at rest, audit, 외부 secret manager 연동까지 함께 봐야 한다. 애플리케이션 관점에서는 Secret을 어떻게 주입하고 노출을 줄일지가 핵심이다.

## 핵심 개념

- Secret `data`는 base64 encoded 값이고 `stringData`는 입력 편의를 위한 평문 필드다.
- Secret을 볼 수 있는 권한은 민감하므로 Role/ClusterRole 범위를 신중히 둔다.
- encryption at rest는 etcd에 저장되는 Secret 데이터를 보호하는 control plane 설정이다.
- Pod에 env로 넣은 Secret은 프로세스 환경에 노출될 수 있으므로 사용 방식을 고려한다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl create secret generic db-secret --from-literal=password='change-me'
kubectl get secret db-secret -o yaml
kubectl auth can-i get secrets
kubectl describe pod <pod-using-secret>
```

![Secret 암호화 at rest와 보안 경계 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Secret 암호화 at rest와 보안 경계 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

Secret 설명에서는 예시 값을 실제 비밀번호처럼 쓰지 않는다. 항상 placeholder를 사용하고, base64를 암호화로 오해하지 않도록 명확히 적는다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Encoding | base64와 encryption의 차이를 구분했는가 |
| RBAC | Secret get/list/watch 권한이 최소화되어 있는가 |
| Mount | env와 volume 중 노출면이 적절한 방식을 골랐는가 |
| At rest | cluster 운영자가 etcd encryption 설정을 관리하는가 |

## 시험 포인트

- **base64는 암호화가 아니다** - `kubectl get secret -o yaml`의 `data` 값은 base64 encoding일 뿐 누구나 `base64 -d`로 되돌린다. "Secret이라 안전하다"가 아니라 접근 권한, 저장 암호화, 노출면을 각각 따져야 한다.
- **encryption at rest는 개발자 manifest가 아니라 cluster 설정이다** - etcd에 저장되는 Secret을 암호화하는 것은 API Server에 EncryptionConfiguration을 거는 control plane 설정이다. CKAD 범위에서는 "이건 운영자 영역"이라는 경계를 아는 것이 핵심이다.
- **Secret 조회 권한은 RBAC로 좁힌다** - `kubectl auth can-i get secrets`로 확인하고, ServiceAccount에 secrets의 get/list/watch를 넓게 주면 Pod 하나가 뚫렸을 때 전체 비밀이 샌다. Role을 namespace와 resourceNames로 제한한다.
- **주입 방식에 따라 노출면이 다르다** - env로 넣은 Secret은 프로세스 환경, 로그, crash dump로 새기 쉽고 volume mount는 파일로만 존재한다. 노출을 줄여야 하는 값이면 env보다 volume을 고른다.

## 관련 문서

- [[ckad-26-deployment-strategies|배포 전략: Blue-Green과 Canary]] - 이전 편, 배포 전략과 selector 전환
- [[ckad-28-api-deprecation|API version과 deprecation 점검]] - 다음 편, manifest의 apiVersion 관리
- [[ckad-07-configmap-secret-env|ConfigMap과 Secret 주입]] - Secret 생성과 env/volume 주입의 기본
- [[ckad-22-rbac-kubeconfig|RBAC와 kubeconfig]] - Secret 조회 권한을 최소화하는 접근 제어
- [[ckad-21-securitycontext-serviceaccount|SecurityContext와 ServiceAccount]] - Secret을 받는 Pod의 보안 주체
- [[ckad-19-volumes-pv-pvc|볼륨과 PV, PVC]] - env 대신 volume mount로 노출면을 줄이는 주입 경로
- [[ckad-17-networkpolicy|NetworkPolicy]] - 비밀을 다루는 Pod의 통신 경계 제한
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 시리즈 흐름 다시 보기

## 참고 자료

- [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
