---
title: AWS App Mesh
slug: "aws-app-mesh"
category: cloud
tags: ["app-mesh", "aws", "canary-deployment", "ecs", "eks", "envoy", "microservices", "mtls", "observability", "service-mesh"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.274167+00:00"
---

**AWS App Mesh**는
마이크로서비스 환경에서 **서비스 간 통신을 일관되게 제어·관찰·보안**하기 위한
**완전관리형 서비스 메시(Service Mesh)** 입니다.

---

## 한 줄 정의

> **AWS App Mesh는 Envoy 프록시를 기반으로 마이크로서비스 간 트래픽, 보안, 관측성을 중앙에서 제어하는 서비스 메시이다.**

---

## 왜 App Mesh가 필요한가?

마이크로서비스가 많아질수록:

- 서비스 간 호출 복잡
- 장애 전파 위험
- 배포 중 트래픽 제어 어려움
- 공통 보안/관측성 구현 중복

👉 **App Mesh는 이 공통 문제를 인프라 레이어에서 해결**합니다.

---

## 핵심 개념

### 1️⃣ Envoy 프록시

- 각 서비스 옆에 **사이드카 프록시**를 배치합니다.
- 실제 네트워크 트래픽은 Envoy가 처리합니다.
- 애플리케이션 코드를 변경할 필요가 없습니다.

---

### 2️⃣ 논리적 구성 요소

|구성 요소|역할|
|---|---|
|**Mesh**|전체 서비스 메시|
|**Virtual Node**|개별 서비스|
|**Virtual Service**|서비스 이름|
|**Virtual Router**|라우팅 규칙|
|**Route**|트래픽 분기 규칙|

---

### 3️⃣ 고급 트래픽 제어

- Canary 배포
- Blue/Green
- 가중치 기반 라우팅
- 재시도, 타임아웃

---

### 4️⃣ 보안 (mTLS)

- 서비스 간 상호 인증
- 암호화 통신
- IAM + ACM 연계 가능

---

### 5️⃣ 관측성(Observability)

- 분산 트레이싱
- 메트릭 수집
- 로그 집계
- X-Ray / CloudWatch 연동

---

## 지원 플랫폼

|플랫폼|지원|
|---|---|
|Amazon ECS|✅|
|Amazon EKS|✅|
|EC2|✅|
|Lambda|❌|

---

## App Mesh vs Service Connect

|항목|App Mesh|Service Connect|
|---|---|---|
|난이도|높음|낮음|
|트래픽 제어|매우 강력|제한|
|멀티 플랫폼|✅|❌|
|운영 오버헤드|큼|작음|
|권장 대상|대규모|일반 ECS|

---

## 언제 App Mesh를 써야 하나?

- 대규모 마이크로서비스
- Canary/Blue-Green 배포
- 서비스 간 상세 모니터링
- ECS + EKS 혼합 환경

---

## 핵심 포인트

- “서비스 메시” → **App Mesh**
- “Envoy 프록시” → **App Mesh**
- “트래픽 분기” → **App Mesh**