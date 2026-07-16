<!-- infographic-hero -->
![Rolling Update와 Rollback 실전 구조 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Rolling Update와 Rollback 실전 구조 핵심 요약. (Source: 공식 문서 기반 자체 작성)*

# Rolling Update와 Rollback 실전 구조

Deployment의 rolling update는 Pod를 한 번에 모두 바꾸지 않고 새 ReplicaSet을 점진적으로 늘리면서 이전 ReplicaSet을 줄이는 방식이다. 이 과정에서 readiness probe가 중요하다. 새 Pod가 준비되지 않았는데 traffic을 받으면 배포 중 장애가 커진다.

Rollback은 마법이 아니라 이전 Pod template revision으로 되돌리는 작업이다. ConfigMap, Secret, 외부 DB migration처럼 Deployment template 밖 변경은 별도로 관리해야 한다.

## 핵심 개념

- Pod template 변경은 새 rollout revision을 만든다.
- `maxSurge`는 원하는 replica 수보다 추가로 만들 수 있는 Pod 수다.
- `maxUnavailable`은 update 중 사용할 수 없어도 되는 Pod 수다.
- rollback은 Deployment revision을 되돌리지만 외부 상태까지 자동으로 되돌리지는 않는다.

## Manifest 예시

아래 예시는 이 글의 핵심 개념을 가장 작은 Kubernetes manifest로 고정한 것이다. 실제 운영 manifest에서는 namespace, label, resource, security context를 함께 검토한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
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
          readinessProbe:
            httpGet:
              path: /
              port: 80
```

## kubectl 확인 명령

명령어는 결과를 바로 확인할 수 있는 순서로 배치한다. 객체를 만든 뒤에는 `get`, `describe`, `logs`, `events` 계열로 현재 상태를 검증한다.

```bash
kubectl apply -f deployment.yaml
kubectl set image deployment/web web=nginx:1.28
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
kubectl get rs -l app=web
```

![Rolling Update와 Rollback 실전 구조 구조도](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Rolling Update와 Rollback 실전 구조 리소스 구조와 흐름. (Source: 공식 문서 기반 자체 작성)*

## 작성 기준

rolling update 설명에는 ReplicaSet 변화를 같이 보여줘야 한다. `kubectl get rs`를 보면 revision별 ReplicaSet이 어떻게 남는지 알 수 있고, rollout history와 연결해서 이해할 수 있다.

## 체크포인트

| 항목 | 확인 기준 |
|---|---|
| Readiness | 새 Pod가 준비된 뒤 traffic을 받도록 probe가 있는가 |
| Strategy | maxSurge/maxUnavailable이 서비스 특성과 맞는가 |
| History | rollout history로 revision을 확인했는가 |
| Rollback 범위 | Deployment template 밖 변경까지 rollback된다고 착각하지 않는가 |

## 흔한 실수

- readiness 없이 rolling update를 안전하다고 가정한다.
- ConfigMap 변경이 자동으로 rollout revision이 된다고 생각한다.
- rollback으로 DB migration까지 되돌아간다고 착각한다.
- image tag를 재사용해 revision 차이를 추적할 수 없게 만든다.

## 시험 포인트

- readiness probe 없이 rolling update를 안전하다고 가정하면 준비되지 않은 새 Pod가 곧바로 traffic을 받아 배포 중 장애가 커진다. rolling update의 무중단성은 readiness에 의존한다.
- ConfigMap이나 Secret만 바꾸면 Deployment template 해시가 그대로라 새 rollout revision이 생기지 않는다. Pod가 새 설정을 읽게 하려면 template을 변경하거나 재시작을 유도해야 한다.
- `kubectl rollout undo`는 Deployment의 Pod template revision만 되돌린다. 이미 실행된 DB migration이나 외부 상태는 함께 복구되지 않으므로 template 밖 변경은 따로 관리한다.
- image tag를 `latest`처럼 재사용하면 revision 사이의 image 차이가 드러나지 않아 rollout history와 rollback 추적이 무의미해진다. 배포마다 명시적 tag를 쓴다.

## 관련 문서

- 이전 글: [[ckad-14-label-selector-annotation|Label, Selector, Annotation]] - rollout 중 ReplicaSet을 label로 구분하는 기반
- 다음 글: [[ckad-16-jobs-cronjobs|Job과 CronJob]] - Deployment 외 배치성 workload로 확장
- [[ckad-05-replicaset-deployment|ReplicaSet과 Deployment]] - rolling update가 새 ReplicaSet을 세우는 기본 구조
- [[ckad-12-probes-health-checks|Readiness, Liveness, Startup Probe]] - 무중단 배포 안전성을 좌우하는 readiness
- [[ckad-26-deployment-strategies|배포 전략]] - blue-green, canary 등으로 넓히는 배포 방식
- [[ckad-07-configmap-secret-env|ConfigMap, Secret, 환경변수]] - 설정 변경이 rollout revision과 맺는 관계
- [[ckad-00-kubernetes-application-map|CKAD Kubernetes 애플리케이션 지도]] - 전체 학습 흐름에서 이 글의 위치

## 참고 자료

- [Updating a Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment)
- [Rolling Back a Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)
- [Deployment Strategy](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)
