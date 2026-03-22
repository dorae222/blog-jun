---
title: AWS Glue Trigger
slug: "aws-glue-trigger"
category: cloud
tags: ["aws", "aws-glue", "conditional-execution", "crawler", "etl", "glue-trigger", "job", "scheduling", "workflow"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.974945+00:00"
---

**AWS Glue Trigger**는 AWS Glue Workflow 안에서 **Job이나 Crawler를 언제·어떤 조건으로 실행할지 결정하는 실행 제어 메커니즘**입니다.

---

## 한 줄 정의

> **AWS Glue Trigger는 Glue Job과 Crawler의 실행 시점과 조건을 정의하는 트리거이다.**

---

## Glue Trigger의 역할

- Glue 작업을 **자동으로 시작**
- 실행 순서 제어
- 조건부 분기 처리

👉 **Workflow의 “신호 장치” 역할**

---

## Trigger의 주요 유형

### 1️⃣ On-demand Trigger

- 수동 실행
- API/콘솔/CLI로 시작

---

### 2️⃣ Scheduled Trigger

- cron 기반 실행
- 주기적 ETL

---

### 3️⃣ Conditional Trigger (중요)

- 선행 작업 상태에 따라 실행
- 성공/실패 조건 설정 가능

예:

- Job A 성공 → Job B 실행
- Crawler 완료 → ETL Job 실행

---

## Trigger와 Workflow의 관계

```text
Workflow
 ├─ Trigger 1 → Crawler
 ├─ Trigger 2 → Job A
 └─ Trigger 3 → Job B
```

- Workflow는 컨테이너
- Trigger는 **실행 조건**

---

## 핵심 포인트

- “조건부 실행” → **Glue Trigger**
- “스케줄링” → **Glue Trigger**
- “Job 간 실행 제어” → **Glue Trigger**