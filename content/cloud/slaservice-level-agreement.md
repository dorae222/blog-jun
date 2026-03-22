---
title: SLA(Service Level Agreement)
slug: "slaservice-level-agreement"
category: cloud
tags: ["availability", "cloud", "data-mesh", "data-quality", "disaster-recovery", "rpo", "rto", "sla", "sli", "slo"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.847024+00:00"
---

**SLA(Service Level Agreement)** 는 서비스 제공자와 사용자(또는 내부 고객) 간에 **서비스 품질 수준을 명확히 약속한 계약**입니다.

---

## 한 줄 정의

> **SLA는 서비스가 어느 수준의 가용성·성능·응답을 보장해야 하는지를 수치로 명시한 약속이다.**

---

## SLA에 포함되는 핵심 요소

### 1️⃣ 가용성(Availability)

- 서비스가 **얼마나 자주 정상 동작해야 하는지**

- 예:

    - 99.9% (월 최대 약 43분 다운)
    - 99.99%

---

### 2️⃣ 성능(Performance)

- 응답 시간
- 처리량
- 지연 시간

예:

- API 응답 시간 ≤ 200ms
- 쿼리 평균 실행 시간 ≤ 5초

---

### 3️⃣ 신뢰성(Reliability)

- 오류율
- 실패 허용 범위
- 데이터 정확성

---

### 4️⃣ 지원/복구(Support & Recovery)

- 장애 대응 시간
- 복구 목표
    - **RTO** (복구 시간 목표)
    - **RPO** (복구 시점 목표)

---

### 5️⃣ 측정 방법 & 보고

- 어떤 지표로 측정할지
- 측정 주기
- 위반 시 조치(크레딧 등)

---

## SLA vs SLO vs SLI (중요)

| 용어 | 의미 |
| ------------------------------------ | ---------------- |
| **SLI** | 측정 지표 (예: 응답 시간) |
| **SLO** | 목표 수준 (예: 99.9%) |
| **SLA** | 공식 계약/약속 |

관계:

> **SLI → SLO → SLA**

---

## 데이터/플랫폼 관점의 SLA 예시

- 데이터 파이프라인:
    - “매일 08:00 이전 데이터 적재 완료”
- 데이터 품질:
    - “누락률 < 0.1%”
- 분석 서비스:
    - “대시보드 가용성 99.9%”

---

## Data Mesh에서의 SLA

Data Mesh에서는 각 **데이터 제품(Data Product)** 이 명시적인 SLA를 갖고 내부 사용자(다른 도메인 팀)에게 약속합니다.

예:

- 갱신 주기
- 최신성(Freshness)
- 정확도
