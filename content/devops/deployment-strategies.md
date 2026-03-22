---
title: "배포 전략 비교: Rolling, Blue-Green, Canary 완벽 가이드"
slug: "deployment-strategies"
category: cloud
tags: ["devops", "deployment", "blue-green", "canary", "rolling"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# 배포 전략 비교: Rolling, Blue-Green, Canary 완벽 가이드

## 1. 배포 전략이 중요한 이유

애플리케이션을 프로덕션에 배포할 때 가장 중요한 두 가지 목표가 있다:

1. **가용성 유지**: 배포 과정에서 사용자가 서비스 중단을 경험하지 않아야 한다
2. **안전한 롤백**: 문제가 발생하면 빠르게 이전 버전으로 되돌릴 수 있어야 한다

단순히 서버를 멈추고 새 버전을 올리는 **Recreate(재생성)** 방식은 다운타임이 발생하므로, 현대 서비스에서는 무중단 배포 전략이 필수다.

```
사용자 요청 ──▶ 로드 밸런서 ──▶ ???
                                  │
                    어떤 전략으로 새 버전을 투입할 것인가?
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 Rolling     Blue-Green      Canary
```

---

## 2. Rolling 배포

### 개념

인스턴스를 **하나씩 또는 일정 비율씩** 순차적으로 새 버전으로 교체하는 방식이다. Kubernetes의 기본 배포 전략이기도 하다.

```
시점 1: [v1] [v1] [v1] [v1]     ← 모두 v1

시점 2: [v2] [v1] [v1] [v1]     ← 하나 교체 시작

시점 3: [v2] [v2] [v1] [v1]     ← 순차 교체 중

시점 4: [v2] [v2] [v2] [v1]     ← 거의 완료

시점 5: [v2] [v2] [v2] [v2]     ← 모두 v2 완료
```

### Kubernetes 설정 예시

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1           # 동시에 추가 생성 가능한 Pod 수
      maxUnavailable: 1     # 동시에 사용 불가능한 Pod 수
  template:
    spec:
      containers:
        - name: app
          image: my-registry.example.com/my-app:v2
          readinessProbe:    # 준비 상태 확인 필수!
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```

### 장점과 단점

| 장점 | 단점 |
|------|------|
| 구현이 간단 (K8s 기본값) | 배포 중 두 버전이 공존 |
| 추가 인프라 불필요 | 롤백 시 다시 롤링해야 함 (느림) |
| 점진적 교체로 리스크 분산 | API 호환성 관리 필요 |
| 리소스 효율적 | 배포 시간이 인스턴스 수에 비례 |

---

## 3. Blue-Green 배포

### 개념

**동일한 두 환경(Blue, Green)**을 준비하고, 트래픽을 한 번에 전환하는 방식이다. 현재 운영 중인 환경이 Blue라면, 새 버전을 Green에 배포한 후 로드 밸런서를 전환한다.

```
┌──────────────────────────────────────────────────┐
│                 배포 전                            │
│                                                  │
│  사용자 ──▶ LB ──▶ [Blue: v1] ✅ (현재 서비스)    │
│                    [Green: idle] 💤               │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              Green에 v2 배포                      │
│                                                  │
│  사용자 ──▶ LB ──▶ [Blue: v1] ✅ (현재 서비스)    │
│                    [Green: v2] 🔄 (배포 & 테스트)  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              트래픽 전환                           │
│                                                  │
│  사용자 ──▶ LB ──▶ [Blue: v1] 💤 (대기/롤백용)    │
│               └──▶ [Green: v2] ✅ (현재 서비스)    │
└──────────────────────────────────────────────────┘
```

### 구현 예시: Nginx 기반

```nginx
# /etc/nginx/conf.d/app.conf

# Blue 환경 (현재 운영)
upstream blue {
    server app-blue-1.internal:8080;
    server app-blue-2.internal:8080;
}

# Green 환경 (새 버전)
upstream green {
    server app-green-1.internal:8080;
    server app-green-2.internal:8080;
}

# 전환은 이 한 줄만 변경
# include /etc/nginx/active-upstream.conf;
# active-upstream.conf 내용: "set $active_upstream blue;"

server {
    listen 80;
    server_name app.example.com;

    location / {
        # 전환 스크립트가 이 값을 blue/green으로 변경
        proxy_pass http://blue;   # ← blue 또는 green
    }
}
```

### 전환 스크립트

```bash
#!/bin/bash
# switch-traffic.sh

CURRENT=$(cat /etc/nginx/active-env)

if [ "$CURRENT" = "blue" ]; then
    NEW="green"
else
    NEW="blue"
fi

# Nginx 설정 변경
sed -i "s/proxy_pass http:\/\/$CURRENT/proxy_pass http:\/\/$NEW/" \
    /etc/nginx/conf.d/app.conf

# Nginx 리로드 (무중단)
nginx -s reload

echo "$NEW" > /etc/nginx/active-env
echo "Switched traffic from $CURRENT to $NEW"
```

### 장점과 단점

| 장점 | 단점 |
|------|------|
| 즉각적인 트래픽 전환 | 2배의 인프라 비용 |
| 매우 빠른 롤백 (LB 전환만) | 데이터베이스 마이그레이션 주의 |
| 배포 전 새 환경에서 충분한 테스트 가능 | 두 환경 간 상태 동기화 필요 |
| 다운타임 제로 | 환경 구성/관리 복잡도 증가 |

---

## 4. Canary 배포

### 개념

새 버전을 **소수의 인스턴스에만 먼저 배포**하고, 문제가 없으면 점진적으로 트래픽 비율을 늘려가는 방식이다. 새처럼 "탄광의 카나리아"가 먼저 위험을 감지하는 역할을 한다.

```
Phase 1: 5% 트래픽 → v2 (Canary)
┌──────────────────────────────────────────┐
│  LB ──▶ 95% ──▶ [v1] [v1] [v1] [v1]    │
│     └──▶  5% ──▶ [v2]                   │
│                                          │
│  📊 에러율, 응답시간, CPU 모니터링         │
└──────────────────────────────────────────┘

Phase 2: 25% 트래픽 → v2 (메트릭 정상 확인 후)
┌──────────────────────────────────────────┐
│  LB ──▶ 75% ──▶ [v1] [v1] [v1]         │
│     └──▶ 25% ──▶ [v2]                   │
│                                          │
│  📊 계속 모니터링                         │
└──────────────────────────────────────────┘

Phase 3: 75% 트래픽 → v2
┌──────────────────────────────────────────┐
│  LB ──▶ 25% ──▶ [v1]                    │
│     └──▶ 75% ──▶ [v2] [v2] [v2]         │
│                                          │
│  📊 계속 모니터링                         │
└──────────────────────────────────────────┘

Phase 4: 100% 전환 완료
┌──────────────────────────────────────────┐
│  LB ──▶ 100% ──▶ [v2] [v2] [v2] [v2]   │
│                                          │
│  ✅ 배포 완료                             │
└──────────────────────────────────────────┘
```

### Kubernetes + Istio 구현 예시

```yaml
# VirtualService로 트래픽 가중치 설정
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app.example.com
  http:
    - route:
        - destination:
            host: my-app-stable
            port:
              number: 80
          weight: 95           # 기존 버전 95%
        - destination:
            host: my-app-canary
            port:
              number: 80
          weight: 5            # 카나리 5%
```

### Argo Rollouts를 활용한 자동 카나리

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause: { duration: 5m }          # 5분 관찰
        - analysis:                        # 자동 메트릭 분석
            templates:
              - templateName: success-rate
        - setWeight: 25
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 5m }
        - setWeight: 75
        - pause: { duration: 5m }
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2
        args:
          - name: service-name
            value: my-app-canary

---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
    - name: success-rate
      interval: 60s
      successCondition: result[0] >= 0.99    # 99% 이상 성공률
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",status=~"2.."}[5m]))
            /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
```

### 장점과 단점

| 장점 | 단점 |
|------|------|
| 실제 트래픽으로 검증 | 구현 복잡도 높음 |
| 문제 시 소수 사용자만 영향 | 모니터링 체계 필수 |
| 데이터 기반 배포 의사결정 | 배포 시간이 길어질 수 있음 |
| 점진적 신뢰 구축 | 트래픽 라우팅 인프라 필요 |

---

## 5. A/B 테스트 배포와의 차이

Canary 배포와 A/B 테스트는 비슷해 보이지만 **목적이 다르다**:

| 구분 | Canary 배포 | A/B 테스트 |
|------|------------|-----------|
| **목적** | 기술적 안정성 검증 | 비즈니스 지표 비교 |
| **트래픽 분배 기준** | 비율 (랜덤) | 사용자 속성 (지역, 디바이스 등) |
| **측정 지표** | 에러율, 응답시간, CPU | 전환율, 클릭률, 매출 |
| **결정 기준** | 기술 메트릭 임계값 | 통계적 유의성 |
| **기간** | 수 분 ~ 수 시간 | 수 일 ~ 수 주 |

```
Canary: "새 버전이 기술적으로 문제 없는가?"
A/B:    "어떤 버전이 비즈니스적으로 더 나은가?"
```

---

## 6. 전략별 비교표

| 항목 | Recreate | Rolling | Blue-Green | Canary |
|------|----------|---------|------------|--------|
| **다운타임** | 있음 | 없음 | 없음 | 없음 |
| **롤백 속도** | 느림 (재배포) | 느림 (재롤링) | 즉시 (LB 전환) | 즉시 (가중치 0) |
| **리소스 비용** | 1x | 1x + alpha | 2x | 1x + alpha |
| **배포 복잡도** | 낮음 | 낮음 | 중간 | 높음 |
| **버전 공존** | 없음 | 일시적 | 없음 | 일시적 |
| **실사용자 검증** | 불가 | 제한적 | 전환 후만 | 가능 |
| **인프라 요구** | 최소 | 최소 | LB + 2환경 | LB + 메트릭 |
| **K8s 지원** | 기본 | 기본 | 수동/Argo | Istio/Argo |

---

## 7. 롤백 전략

### 자동 롤백

```yaml
# Kubernetes: 자동 롤백 조건 설정
spec:
  progressDeadlineSeconds: 300     # 5분 내 완료 안 되면 실패
  minReadySeconds: 30              # 30초간 Ready 유지해야 성공

# 실패 시 수동 롤백 명령
# kubectl rollout undo deployment/my-app
```

### 자동 vs 수동 롤백 비교

| 구분 | 자동 롤백 | 수동 롤백 |
|------|----------|----------|
| **트리거** | 헬스체크 실패, 메트릭 임계값 초과 | 운영자 판단 |
| **속도** | 즉시 (초 단위) | 분 ~ 시간 |
| **장점** | 빠른 대응, 24/7 가능 | 복잡한 상황 대응 가능 |
| **단점** | 오탐 (False Positive) 가능 | 사람 의존, 대응 지연 |
| **적합한 경우** | 명확한 장애 패턴 | 부분 장애, 데이터 이슈 |

### 롤백 체크리스트

```
롤백 전 확인사항:
├── DB 마이그레이션이 역방향 호환되는가?
├── API 스키마 변경이 이전 버전과 호환되는가?
├── 캐시/세션 데이터가 이전 버전에서 문제 없는가?
├── 외부 서비스 연동에 영향이 있는가?
└── 롤백 후 데이터 정합성이 유지되는가?
```

---

## 8. 트래픽 라우팅 기법

배포 전략을 실현하는 핵심은 **트래픽 라우팅**이다:

### DNS 기반 라우팅

```
장점: 구현 간단, 인프라 독립적
단점: DNS 캐시로 인한 전환 지연, 세밀한 제어 불가

사용자 → DNS (app.example.com)
           ├── A record → 10.x.x.1 (Blue)    ← 변경 전
           └── A record → 10.x.x.2 (Green)   ← 변경 후
               (TTL 만료까지 전환 지연 가능)
```

### Load Balancer 기반 라우팅

```
장점: 즉각적 전환, 헬스체크 통합
단점: LB가 단일 장애점(SPOF)이 될 수 있음

사용자 → LB (가중치 설정)
          ├── 95% → Backend Pool A (v1)
          └──  5% → Backend Pool B (v2)
```

### Service Mesh 기반 라우팅

```
장점: L7 레벨 세밀한 제어, 헤더 기반 라우팅
단점: 복잡도 높음, 학습 곡선

사용자 → Ingress Gateway → Sidecar Proxy
                             ├── header: x-canary=true → v2
                             └── 기본 → v1
```

```yaml
# Istio: 특정 헤더가 있는 요청만 카나리로 라우팅
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app.example.com
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: my-app-canary
    - route:
        - destination:
            host: my-app-stable
```

---

## 9. 각 전략의 적합한 상황

### Rolling 배포가 적합한 경우

- Kubernetes 기반으로 운영하며 **간단한 무중단 배포**가 필요할 때
- 인프라 비용을 최소화하고 싶을 때
- 버전 간 API 호환성이 잘 관리되고 있을 때
- 소규모 ~ 중규모 서비스

### Blue-Green 배포가 적합한 경우

- **즉각적인 롤백**이 비즈니스에 매우 중요할 때
- 배포 전 **충분한 통합 테스트**를 새 환경에서 수행하고 싶을 때
- 인프라 비용보다 안정성이 우선일 때
- 배포 빈도가 상대적으로 낮은 서비스

### Canary 배포가 적합한 경우

- **대규모 트래픽**을 처리하는 서비스 (장애 영향 최소화)
- **데이터 기반 배포 의사결정**을 원할 때
- 모니터링 인프라가 잘 갖춰져 있을 때
- 배포 자동화 성숙도가 높은 조직

### 의사결정 플로우

```
배포 전략 선택:

Q1. 다운타임이 허용되는가?
    └── YES → Recreate (가장 단순)
    └── NO → Q2

Q2. 인프라 비용을 2배로 쓸 수 있는가?
    └── YES → Q3
    └── NO → Rolling Update

Q3. 즉각적인 롤백이 필수인가?
    └── YES → Blue-Green
    └── NO → Q4

Q4. 점진적 트래픽 검증이 필요한가?
    └── YES → Canary
    └── NO → Blue-Green
```

---

## 마무리

배포 전략은 서비스의 규모, 비즈니스 요구사항, 팀의 역량에 따라 달라진다. 핵심은 다음과 같다:

- **Rolling**은 간단하고 리소스 효율적이지만 롤백이 느리다
- **Blue-Green**은 즉각적인 전환과 롤백이 가능하지만 인프라 비용이 2배다
- **Canary**는 가장 안전하지만 구현과 운영 복잡도가 높다
- **어떤 전략이든 모니터링과 롤백 계획이 없으면 무의미**하다

실무에서는 단일 전략만 사용하기보다, 서비스 특성에 따라 **혼합 전략**을 사용하는 경우가 많다. 예를 들어 내부 서비스는 Rolling, 사용자 대면 서비스는 Canary로 운영하는 식이다.
