---
title: SLI(Service Level Indicator) 개요
slug: "sliservice-level-indicator-개요"
category: cloud
tags: ["aws", "cloud", "data-mesh", "data-quality", "metrics", "observability", "site-reliability-engineering", "sla", "sli", "slo"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.855534+00:00"
---

**SLI(Service Level Indicator)** 는 서비스 품질을 **객관적으로 측정하는 지표(metric)** 입니다.

---

## 한 줄 정의

> **SLI는 서비스가 실제로 얼마나 잘 동작하고 있는지를 수치로 나타내는 측정값이다.**

---

## SLI의 역할

- "현재 서비스 상태가 어떤가?"를 **숫자로 보여줌**
- SLO 달성 여부 판단의 기준
- SLA 위반 여부 판단의 근거

---

## SLI의 핵심 특징

### 1️⃣ 실제 측정값

- 로그, 메트릭, 트레이스에서 수집
- 관측 가능한 수치

---

### 2️⃣ 단독으로 의미 없음

- **목표(SLO)**와 결합되어야 의미가 있음
- SLA/SLO 판단의 기초 데이터

---

### 3️⃣ 다양한 유형

- 가용성
- 지연 시간
- 오류율
- 처리량
- 데이터 품질

---

## SLI 예시

### 서비스 가용성

- “전체 요청 중 성공한 요청의 비율”

```text
SLI = 성공 요청 수 / 전체 요청 수
```

---

### 응답 시간

- p95 응답 시간 = 180ms

---

### 데이터 파이프라인

- 데이터 최신성(latency)
- 누락률
- 중복률

---

## SLI vs SLO vs SLA (최종 정리)

|용어|의미|질문|
|---|---|---|
|**SLI**|지표|지금 얼마나 잘 동작하나?|
|**SLO**|목표|어느 수준을 목표로 하나?|
|**SLA**|약속|무엇을 보장하나?|

관계:

> **SLI → SLO → SLA**

---

## Data Mesh 관점의 SLI

- 데이터 제품마다 SLI 정의
- 예:
  - Freshness
  - Completeness
  - Accuracy
- 측정 결과를 공개

---

## 시험 대비 핵심 문장

> **SLI는 서비스 품질을 측정하는 수치다.**

---

## 한 문장 암기

> **SLI는 ‘측정’, SLO는 ‘목표’, SLA는 ‘약속’이다.**

원하시면

- **데이터 품질 SLI 예제**
- **SRE 관점의 SLI 설계법**

도 도와드릴게요.