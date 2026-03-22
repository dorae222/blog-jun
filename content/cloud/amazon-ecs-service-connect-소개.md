---
title: Amazon ECS Service Connect 소개
slug: "amazon-ecs-service-connect-소개"
category: cloud
tags: ["alb", "aws", "aws-cloud-map", "cloud", "ecs", "microservices", "mtls", "service-discovery", "service-mesh"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.088909+00:00"
---

**Amazon ECS Service Connect**는
Amazon ECS에서 실행 중인 서비스 간 **서비스 디스커버리, 트래픽 라우팅, 보안 연결을 표준화·자동화**해 주는 **관리형 서비스 통신 기능**입니다.

---

## 한 줄 정의

> **Amazon ECS Service Connect는 ECS 서비스 간 통신을 이름 기반으로 단순화하고, 네트워크·보안 설정을 자동으로 처리하는 서비스 연결 기능이다.**

---

## 왜 Service Connect가 필요한가?

기존 ECS 서비스 간 통신은:

- ALB/NLB 직접 구성
    
- 보안 그룹 복잡
    
- 서비스 이름 기반 통신 어려움
    
- 환경별 설정 차이 큼
    

👉 **Service Connect는 이를 “서비스 이름 기반 통신”으로 단순화**합니다.

---

## 핵심 기능

### 1️⃣ 서비스 이름 기반 통신

- IP 주소나 로드밸런서 DNS ❌
    
- **서비스 이름으로 호출**
    
```text
http://orders:8080
```

---

### 2️⃣ 자동 서비스 디스커버리

- AWS Cloud Map 기반
    
- 서비스 등록/해제 자동
    

---

### 3️⃣ 내장 프록시 기반 트래픽 관리

- 각 태스크에 **관리형 프록시(sidecar)** 자동 주입
    
- 로드밸런싱, 재시도, 헬스체크 자동 처리
    

---

### 4️⃣ 보안 통신 (mTLS)

- 서비스 간 **상호 TLS 인증**
    
- 인증서 자동 생성·회전
    
- 별도 인증서 관리 불필요
    

---

### 5️⃣ 운영 오버헤드 감소

- ALB 최소화 가능
    
- 보안 그룹 단순화
    
- 환경(dev/prod) 일관성 유지
    

---

## Service Connect 동작 개념

```text
Service A ──(Service Name)──▶ Service B
     │                          │
 [Service Connect Proxy]  [Service Connect Proxy]
```

- 실제 네트워크 세부사항은 프록시가 처리
    
- 개발자는 서비스 이름만 신경 쓰면 됨
    

---

## Service Connect vs 기존 방식

|항목|Service Connect|ALB 기반|
|---|---|---|
|서비스 디스커버리|자동|수동|
|통신 방식|이름 기반|DNS/포트|
|보안(mTLS)|기본 제공|별도 구성|
|운영 난이도|낮음|높음|
|마이크로서비스 적합성|**높음**|중간|

---

## 언제 Service Connect를 쓰나?

- ECS 기반 마이크로서비스
    
- 내부 서비스 간 통신
    
- 보안·일관성·단순성 중시
    
- TLS 인증서 자동화 필요
    

❌ 외부 트래픽 진입점은 여전히 ALB/NLB 사용

---

## 핵심 포인트

- “ECS 서비스 간 통신 단순화”
    
- “서비스 이름 기반”
    
- “mTLS 자동”
    
- “운영 오버헤드 감소”
    

→ **ECS Service Connect**