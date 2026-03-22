---
title: AWS Glue Workflow
slug: "aws-glue-workflow"
category: cloud
tags: ["aws", "aws-glue", "crawler", "data-catalog", "etl", "orchestration", "spark", "step-functions", "workflow"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:03.984599+00:00"
---

**AWS Glue Workflow**는 여러 개의 AWS Glue Job와 Glue Crawler를 **의존성 기반으로 연결·조율**하는 **ETL 오케스트레이션 기능**입니다.

---

## 한 줄 정의

> **AWS Glue Workflow는 Glue Job과 Crawler를 순서와 조건에 따라 실행하도록 관리하는 오케스트레이션 도구이다.**

---

## 왜 Glue Workflow가 필요한가?

ETL 파이프라인은 보통:

- 크롤러 실행
- 정제 Job 실행
- 변환 Job 실행
- 적재 Job 실행

처럼 **여러 단계**로 구성됩니다.

👉 Workflow 없이 구성하면:

- 수동 트리거가 필요
- 실패 시 재실행이 복잡
- 의존성 관리가 어려움

---

## 핵심 구성 요소

### 1️⃣ Workflow

- 전체 파이프라인을 담는 컨테이너

---

### 2️⃣ Trigger

- **언제 무엇을 실행할지** 정의
- 종류:
  - On-demand
  - Scheduled
  - Conditional (성공/실패 기반)

---

### 3️⃣ Job

- Spark ETL 작업
- Python Shell 작업

---

### 4️⃣ Crawler

- 데이터 스키마 탐색
- Glue Data Catalog 갱신

---

## 동작 예시 (개념)

```text
Crawler
   ↓ (성공 시)
ETL Job 1
   ↓
ETL Job 2
```

---

## Workflow의 특징

- 조건부 실행 가능
- 실패 분기 처리
- 시각적 DAG 형태로 관리
- 재사용·재실행이 용이

---

## Glue Workflow vs Step Functions

|항목|Glue Workflow|Step Functions|
|---|---|---|
|Glue 전용|✅|❌|
|범용 오케스트레이션|❌|✅|
|복잡한 로직|제한|강력|
|설정 난이도|낮음|중간|
|운영 오버헤드|낮음|중간|

👉 **Glue만 묶으면 Workflow**,  
Glue + 타 서비스면 Step Functions

---

## 언제 Glue Workflow를 쓰나?

- Glue Job + Crawler로 구성된 파이프라인
- 단순한 ETL 의존성 관리가 필요할 때
- Glue 중심의 데이터 레이크 환경

---

## 시험 대비 핵심 포인트

- “Glue 작업 간 의존성” → **Workflow**
- “조건부 실행” → **Trigger**
- “Crawler → Job 순서” → **Workflow**

---

## 한 문장 암기

> **Glue Workflow는 여러 Glue 작업을 순서·조건에 따라 실행하는 ETL 오케스트레이션 기능이다.**

원하시면

- **Workflow vs Trigger 차이**
- **시험 단골 Glue 오케스트레이션 문제**

도 이어서 정리해 드릴게요.