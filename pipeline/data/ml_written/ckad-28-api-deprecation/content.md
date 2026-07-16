<!-- infographic-hero -->
![API version과 deprecation 점검 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: API version과 deprecation 점검 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# API version과 deprecation 점검

Kubernetes 리소스는 `apiVersion`과 `kind` 조합으로 식별된다. 같은 kind라도 API group/version이 달라질 수 있고, 오래된 beta API는 제거될 수 있다.

manifest를 복사해서 쓸 때는 현재 cluster가 해당 API를 지원하는지 확인해야 한다. 특히 Ingress, CronJob, PodDisruptionBudget처럼 과거에 version 변화가 있었던 리소스는 apiVersion 확인이 중요하다.

## 핵심 개념

- `apiVersion: apps/v1`의 `apps`는 API group이고 `v1`은 version이다.
- core group은 `apiVersion: v1`처럼 group 이름이 비어 있다.
- deprecated API는 경고가 보일 수 있고 이후 release에서 제거될 수 있다.
- version migration은 단순 문자열 교체가 아니라 field 구조 변경을 포함할 수 있다.

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl api-resources
kubectl api-versions
kubectl explain ingress.spec
kubectl apply --dry-run=server -f manifest.yaml
kubectl get --raw /apis | head
```

![API version과 deprecation 점검 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: API version과 deprecation 점검 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

API version 글에서는 `apiVersion`을 단순 버전 번호로 설명하지 않는다. group/version 구조와 현재 cluster discovery 과정을 같이 보여주는 것이 핵심이다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| 지원 여부 | 현재 cluster가 manifest의 apiVersion/kind를 지원하는가 |
| Field | 새 apiVersion에서 field 구조가 동일한가 |
| Dry run | server-side dry-run으로 API validation을 거쳤는가 |
| 경고 | kubectl apply 경고 메시지를 무시하지 않았는가 |

## 시험 포인트

- **apiVersion은 버전 번호가 아니라 group/version이다** - `apps/v1`은 group `apps`와 version `v1`이고, core group은 `v1`처럼 group이 비어 있다. 이 구조를 모르면 `kubectl api-resources`와 `kubectl explain` 출력을 해석하지 못한다.
- **apiVersion 문자열만 바꾸면 안 된다** - deprecated API를 새 version으로 옮길 때 field 구조가 함께 바뀌는 경우가 많다. Ingress처럼 backend 스펙이 통째로 달라진 리소스는 `kubectl explain <kind>.spec`으로 새 스키마를 확인한 뒤 옮긴다.
- **client dry-run과 server dry-run은 다르다** - `--dry-run=client`는 로컬 검증뿐이라 실제 API 지원 여부를 못 잡는다. deprecation과 지원 여부는 `--dry-run=server`로 API Server 검증을 거쳐야 한다.
- **apply 경고를 무시하지 않는다** - deprecated API는 apply 시 경고를 출력하고 이후 release에서 제거된다. 경고를 넘기면 cluster upgrade 뒤 같은 manifest가 갑자기 실패한다.

## 관련 문서

- [[ckad-27-secret-encryption-at-rest|Secret 암호화 at rest]] - 이전 편, Secret 보안 경계
- [[ckad-29-troubleshooting-playbook|트러블슈팅 플레이북]] - 다음 편, apply 실패를 포함한 장애 진단
- [[ckad-03-pod-yaml|Pod YAML 구조]] - apiVersion과 kind가 리소스를 식별하는 출발점
- [[ckad-18-ingress|Ingress]] - networking.k8s.io로 apiVersion이 바뀐 대표 리소스
- [[ckad-16-jobs-cronjobs|Job과 CronJob]] - batch/v1로 정착하기까지 version 변화를 겪은 리소스
- [[ckad-04-kubectl-imperative|kubectl 명령형 사용]] - dry-run과 `-o yaml`로 올바른 apiVersion을 얻는 방법
- [[ckad-23-admission-crd-operator|Admission, CRD, Operator]] - CRD가 새 API group과 version을 cluster에 추가하는 원리
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 시리즈 흐름 다시 보기

## 참고 자료

- [Kubernetes API](https://kubernetes.io/docs/reference/using-api/)
- [Deprecated API Migration Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
- [kubectl api-resources](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#api-resources)
